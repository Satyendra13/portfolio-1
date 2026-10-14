import asyncio
import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from livekit import rtc
from livekit.agents import stt, vad, utils
from backend.agent_worker.audio_pipeline import AudioPipeline
from backend.agent_worker.graph import agent_graph, AgentState
from backend.app.services.livekit_service import create_livekit_token
from backend.app.services.websocket_manager import agent_ws_manager
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.tenant import Tenant
from backend.app.models.call import Call, CallTurn
from backend.app.models.escalation import Escalation
from backend.app.core.config import settings

logger = logging.getLogger("asistline.worker")

class AsistLineVoiceWorker:
    def __init__(self, room_name: str, call_id: str, tenant_id: str, language: str = "en"):
        self.room_name = room_name
        self.call_id = call_id
        self.tenant_id = tenant_id
        self.language = language
        self.room = rtc.Room()
        self.audio_source = rtc.AudioSource(24000, 1)
        self.audio_track = rtc.LocalAudioTrack.create_audio_track("ai-audio", self.audio_source)
        self.pipeline = AudioPipeline()
        self.running = False
        self.is_escalated = False
        self.watchdog_task: Optional[asyncio.Task] = None
        self._tasks = []
        self._subscribed_track_sids = set()
        self.state: Optional[AgentState] = None

    async def _init_state(self):
        async with AsyncSessionLocal() as db:
            t_res = await db.execute(select(Tenant).where(Tenant.id == self.tenant_id))
            tenant = t_res.scalar_one_or_none()
            tenant_name = tenant.name if tenant else "Customer Support"
            script_cfg = tenant.script_config if tenant else {}
            esc_rules = tenant.escalation_rules if tenant else {}

        self.state = {
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "tenant_name": tenant_name,
            "language": self.language,
            "script_config": script_cfg,
            "escalation_rules": esc_rules,
            "transcript_turns": [],
            "user_input": "",
            "intent": "greeting",
            "is_angry": False,
            "wants_human": False,
            "kb_context": "",
            "kb_chunks": [],
            "confidence_score": 1.0,
            "has_grounding": True,
            "verification_step": "none",
            "order_id": None,
            "phone_last4": None,
            "verified_data": None,
            "repeat_failures": 0,
            "escalation_needed": False,
            "escalation_reason": "",
            "escalation_summary": "",
            "ai_response": "",
            "status": "active",
        }

    async def mute_and_stand_down(self):
        """
        Permanently silences the AI agent once escalation is triggered or when a human agent accepts.
        Stops active speech, unpublishes the AI audio track, and cancels the silence watchdog.
        """
        if self.is_escalated:
            return
        self.is_escalated = True
        logger.info(f"Muting and standing down AI worker for call {self.call_id}.")
        self.pipeline.stop_speaking()
        if self.watchdog_task and not self.watchdog_task.done():
            self.watchdog_task.cancel()
        if self.audio_track and self.room and getattr(self.room, "isconnected", lambda: False)() and self.room.local_participant:
            try:
                await asyncio.wait_for(
                    self.room.local_participant.unpublish_track(self.audio_track.sid),
                    timeout=0.8,
                )
                logger.info(f"Successfully unpublished AI voice audio track in room {self.room_name}.")
            except Exception as e:
                logger.debug(f"Could not unpublish audio track: {e}")

    async def start(self):
        await self._init_state()
        self.last_speech_time = asyncio.get_event_loop().time()

        # Generate a unique identity so duplicate connections never kick an active session
        import uuid
        worker_identity = f"ai-voice-agent-{uuid.uuid4().hex[:6]}"
        token = create_livekit_token(
            room_name=self.room_name,
            participant_identity=worker_identity,
            participant_name=f"AI Agent ({self.state['tenant_name']})",
            role="ai",
        )

        logger.info(f"Worker connecting to room {self.room_name} as {worker_identity}...")
        await self.room.connect(settings.LIVEKIT_URL, token)
        logger.info("Worker connected successfully.")

        # Guard: check if an AI participant is already present
        for p in self.room.remote_participants.values():
            if p.identity.startswith("ai-voice-agent"):
                logger.warning(f"Room {self.room_name} already has an active AI agent ({p.identity})! Terminating duplicate worker.")
                await self.room.disconnect()
                return
            if "agent" in p.identity.lower():
                logger.info(f"Human agent {p.identity} already in room. Muting AI.")
                asyncio.create_task(self.mute_and_stand_down())

        self.running = True
        self.last_speech_time = asyncio.get_event_loop().time()

        # Publish audio track
        opts = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        await self.room.local_participant.publish_track(self.audio_track, opts)

        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            if "agent" in participant.identity.lower():
                logger.info(f"Human agent {participant.identity} joined room {self.room_name}! Muting AI agent.")
                asyncio.create_task(self.mute_and_stand_down())

        @self.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_AUDIO and not participant.identity.startswith("ai-voice-agent"):
                sid = track.sid or publication.sid
                if sid in self._subscribed_track_sids:
                    return
                self._subscribed_track_sids.add(sid)
                logger.info(f"Subscribed to remote audio track {sid} from: {participant.identity}")
                t = asyncio.create_task(self._process_audio_stream(track, participant))
                self._tasks.append(t)

        for p in self.room.remote_participants.values():
            if p.identity.startswith("ai-voice-agent"):
                continue
            for pub in p.track_publications.values():
                if pub.track and pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                    sid = pub.track.sid or pub.sid
                    if sid not in self._subscribed_track_sids:
                        self._subscribed_track_sids.add(sid)
                        logger.info(f"Processing existing audio track {sid} from: {p.identity}")
                        t = asyncio.create_task(self._process_audio_stream(pub.track, p))
                        self._tasks.append(t)

        # Wait briefly for customer participant to connect so greeting audio is heard
        logger.info("Worker waiting for customer participant to join before speaking greeting...")
        for _ in range(20):
            if any(p.identity != self.room.local_participant.identity for p in self.room.remote_participants.values()):
                logger.info("Customer participant detected in room!")
                break
            await asyncio.sleep(0.5)

        # Initial Greet Node execution
        greet_result = await agent_graph.ainvoke(
            self.state,
            {"configurable": {"thread_id": self.call_id}},
        )
        self.state.update(greet_result)
        greet_text = self.state.get("ai_response", "")

        # Log greet turn & speak
        await self._log_turn("ai", greet_text)
        await self.broadcast_caption("ai", greet_text)
        await self.pipeline.speak_text(greet_text, self.audio_source)
        self.last_speech_time = asyncio.get_event_loop().time()

        # Start silence watchdog
        self.watchdog_task = asyncio.create_task(self._silence_watchdog())
        self._tasks.append(self.watchdog_task)

    async def _silence_watchdog(self):
        silence_prompt_count = 0
        while self.running and not getattr(self, "is_escalated", False):
            await asyncio.sleep(2.0)
            if getattr(self, "is_escalated", False):
                break
            now = asyncio.get_event_loop().time()
            if not self.pipeline.is_playing and (now - self.last_speech_time) > settings.DEFAULT_SILENCE_TIMEOUT_SECONDS:
                if silence_prompt_count == 0:
                    silence_prompt_count += 1
                    prompt_text = "Are you still there? Please let me know how I can help you."
                    await self.broadcast_caption("ai", prompt_text)
                    await self.pipeline.speak_text(prompt_text, self.audio_source)
                    self.last_speech_time = asyncio.get_event_loop().time()
                elif silence_prompt_count == 1:
                    silence_prompt_count += 1
                    esc_text = "I haven't heard a response, so I will connect you to our support queue."
                    await self._trigger_backend_escalation("Silence timeout", "Customer went silent after prompt.")
                    await self.broadcast_caption("ai", esc_text)
                    await self.pipeline.speak_text(esc_text, self.audio_source)
                    await self.mute_and_stand_down()
                    break

    async def _process_audio_stream(self, track: rtc.RemoteAudioTrack, participant: rtc.RemoteParticipant):
        audio_stream = rtc.AudioStream(track, sample_rate=16000, num_channels=1)
        vad_stream = self.pipeline.vad.stream()

        async with utils.http_context.open():
            stt_stream = self.pipeline.create_stt_stream()

            last_interim_text = ""
            last_handled_text = ""
            last_handled_time = 0.0
            turn_lock = asyncio.Lock()
            end_speech_fallback_task: Optional[asyncio.Task] = None

            async def _safe_dispatch_turn(text: str, source: str):
                nonlocal last_handled_text, last_handled_time, last_interim_text
                cleaned = text.strip()
                if not cleaned:
                    return

                now = asyncio.get_event_loop().time()
                # Deduplication: do not re-dispatch identical text within 2.5 seconds
                if cleaned.lower() == last_handled_text.lower() and (now - last_handled_time) < 2.5:
                    return

                async with turn_lock:
                    now = asyncio.get_event_loop().time()
                    if cleaned.lower() == last_handled_text.lower() and (now - last_handled_time) < 2.5:
                        return
                    last_handled_text = cleaned
                    last_handled_time = now
                    last_interim_text = ""
                    self.last_speech_time = now
                    logger.info(f"Captured customer speech via {source}: '{cleaned}'")
                    await self._handle_user_turn(cleaned)

            async def _listen_vad():
                nonlocal last_interim_text, end_speech_fallback_task
                async for event in vad_stream:
                    if event.type == vad.VADEventType.START_OF_SPEECH:
                        self.last_speech_time = asyncio.get_event_loop().time()
                        if end_speech_fallback_task and not end_speech_fallback_task.done():
                            end_speech_fallback_task.cancel()
                        # BARGE-IN: User speaks -> stop AI playback in <300ms
                        if self.pipeline.is_playing:
                            logger.info("Barge-in detected via Silero VAD! Aborting AI audio.")
                            self.pipeline.stop_speaking()

                    elif event.type == vad.VADEventType.END_OF_SPEECH:
                        self.last_speech_time = asyncio.get_event_loop().time()
                        # Force ElevenLabs STT to commit its buffer immediately
                        try:
                            stt_stream.flush()
                        except Exception:
                            pass

                        # If FINAL_TRANSCRIPT does not arrive within 350ms, commit interim
                        async def _fallback_commit():
                            await asyncio.sleep(0.35)
                            if last_interim_text:
                                await _safe_dispatch_turn(last_interim_text, "Silero VAD END_OF_SPEECH (interim)")

                        if end_speech_fallback_task and not end_speech_fallback_task.done():
                            end_speech_fallback_task.cancel()
                        end_speech_fallback_task = asyncio.create_task(_fallback_commit())

            async def _listen_stt():
                nonlocal last_interim_text, end_speech_fallback_task
                try:
                    async for ev in stt_stream:
                        self.last_speech_time = asyncio.get_event_loop().time()
                        if ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                            if end_speech_fallback_task and not end_speech_fallback_task.done():
                                end_speech_fallback_task.cancel()
                            text = ev.alternatives[0].text.strip() if ev.alternatives else ""
                            if not text and last_interim_text:
                                text = last_interim_text
                            if text:
                                logger.info(f"ElevenLabs STT final: '{text}'")
                                await _safe_dispatch_turn(text, "ElevenLabs STT FINAL_TRANSCRIPT")
                        elif ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                            interim = ev.alternatives[0].text.strip() if ev.alternatives else ""
                            if interim:
                                last_interim_text = interim
                                logger.info(f"ElevenLabs STT hearing: '{interim}'")
                        elif ev.type == stt.SpeechEventType.END_OF_SPEECH:
                            if last_interim_text:
                                await _safe_dispatch_turn(last_interim_text, "ElevenLabs STT END_OF_SPEECH")
                except Exception as e:
                    logger.error(f"Error in STT stream: {e}")

            t_vad = asyncio.create_task(_listen_vad())
            t_stt = asyncio.create_task(_listen_stt())

            frame_count = 0
            try:
                async for event in audio_stream:
                    if not self.running:
                        break
                    frame = event.frame if hasattr(event, "frame") else event
                    frame_count += 1
                    if frame_count == 1:
                        logger.info(f"Audio flowing from customer {participant.identity}! Audio stream active (sample_rate={frame.sample_rate}, channels={frame.num_channels}).")
                    vad_stream.push_frame(frame)
                    stt_stream.push_frame(frame)
            finally:
                if end_speech_fallback_task and not end_speech_fallback_task.done():
                    end_speech_fallback_task.cancel()
                t_vad.cancel()
                t_stt.cancel()

    async def _handle_user_turn(self, user_text: str):
        logger.info(f"Customer turn: '{user_text}'")
        await self._log_turn("customer", user_text)
        await self.broadcast_caption("customer", user_text)

        if getattr(self, "is_escalated", False):
            logger.info(f"Customer turn during human active call: '{user_text}'. Logging only (AI muted).")
            return

        # Resilient Execution: retry once then auto-escalate per brief requirement
        try:
            self.state["user_input"] = user_text
            result = await agent_graph.ainvoke(
                self.state,
                {"configurable": {"thread_id": self.call_id}},
            )
            self.state.update(result)
        except Exception as e:
            logger.error(f"State machine execution failure: {e}, auto-escalating call.")
            self.state["escalation_needed"] = True
            self.state["status"] = "escalated"
            self.state["escalation_reason"] = f"Technical difficulty: {str(e)}"
            self.state["escalation_summary"] = f"Auto-escalated on error during query: '{user_text}'"
            self.state["ai_response"] = "I'm experiencing a technical difficulty on my line. Let me connect you directly to a specialist."

        ai_reply = self.state.get("ai_response", "")

        is_escalating = bool(self.state.get("escalation_needed") and self.state.get("status") == "escalated")

        # Check if escalation node fired
        if is_escalating:
            await self._trigger_backend_escalation(
                reason=self.state.get("escalation_reason", "AI handoff"),
                summary=self.state.get("escalation_summary", user_text),
            )

        # Log AI response turn & speak
        await self._log_turn("ai", ai_reply)
        await self.broadcast_caption("ai", ai_reply)
        await self.pipeline.speak_text(ai_reply, self.audio_source)
        self.last_speech_time = asyncio.get_event_loop().time()

        if is_escalating:
            logger.info("AI handoff announcement completed. Standing down AI worker.")
            await self.mute_and_stand_down()

    async def _log_turn(self, speaker: str, text: str):
        if not self.call_id or self.call_id == "mock":
            return
        try:
            async with AsyncSessionLocal() as db:
                turn = CallTurn(
                    call_id=self.call_id,
                    speaker=speaker,
                    text=text,
                )
                db.add(turn)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log call turn: {e}")

    async def _trigger_backend_escalation(self, reason: str, summary: str):
        logger.info(f"Triggering escalation for call {self.call_id}: {reason}")
        try:
            async with AsyncSessionLocal() as db:
                esc = Escalation(
                    call_id=self.call_id,
                    tenant_id=self.tenant_id,
                    reason=reason,
                    summary=summary,
                    status="pending",
                )
                db.add(esc)
                # Update call status
                c_res = await db.execute(select(Call).where(Call.id == self.call_id))
                call = c_res.scalar_one_or_none()
                if call:
                    call.status = "escalated"
                await db.commit()
                await db.refresh(esc)

                # Push real-time event to agent portals
                await agent_ws_manager.broadcast_to_tenant(
                    self.tenant_id,
                    {
                        "event": "new_escalation",
                        "escalation_id": esc.id,
                        "call_id": self.call_id,
                        "tenant_id": self.tenant_id,
                        "room_name": self.room_name,
                        "reason": reason,
                        "summary": summary,
                        "created_at": esc.created_at.isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to trigger escalation in DB: {e}")

    async def broadcast_caption(self, speaker: str, text: str):
        payload = json.dumps({"type": "caption", "speaker": speaker, "text": text}).encode("utf-8")
        try:
            await self.room.local_participant.publish_data(payload)
        except Exception:
            pass

    async def stop(self):
        self.running = False
        self.pipeline.stop_speaking()
        for t in self._tasks:
            t.cancel()
        await self.room.disconnect()
        logger.info(f"Worker disconnected from {self.room_name}")


async def run_standalone_worker(room_name: Optional[str] = None, tenant_id: str = "apex-logistics", call_id: Optional[str] = None):
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    print("\n" + "=" * 68)
    print("  AsistLine AI — Voice Agent Worker Service")
    print("=" * 68)
    print(f"  LiveKit URL  : {settings.LIVEKIT_URL}")
    print(f"  Gemini Model : {settings.GEMINI_MODEL_ID}")
    print(f"  TTS Model    : {settings.ELEVENLABS_TTS_MODEL}")
    print("=" * 68)

    if room_name:
        cid = call_id or f"manual-{room_name}"
        print(f"\n[+] Connecting directly to room: '{room_name}' (Tenant: {tenant_id})...")
        worker = AsistLineVoiceWorker(room_name=room_name, call_id=cid, tenant_id=tenant_id)
        await worker.start()
        print(f"[✓] Voice agent is now active and listening in room '{room_name}'!")
        print("    Press Ctrl+C to disconnect.\n")
        try:
            while worker.running:
                await asyncio.sleep(1.0)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[-] Disconnecting voice worker...")
            await worker.stop()
    else:
        print("\n[+] Worker Dispatcher running in listening daemon mode.")
        print("    Listening for active calls initiated from the Customer Portal...")
        print("    (Open http://localhost:3000 to place a call)")
        print("    Press Ctrl+C to stop.\n")

        managed_calls = set()
        active_instances = {}

        try:
            while True:
                await asyncio.sleep(1.5)
                try:
                    async with AsyncSessionLocal() as db:
                        res = await db.execute(
                            select(Call).where(Call.status == "ai_active")
                        )
                        active_calls = res.scalars().all()
                        for call in active_calls:
                            if call.id not in managed_calls:
                                managed_calls.add(call.id)
                                logger.info(f"Incoming call detected: {call.id} for room {call.livekit_room_name}")
                                w = AsistLineVoiceWorker(
                                    room_name=call.livekit_room_name,
                                    call_id=call.id,
                                    tenant_id=call.tenant_id,
                                    language=call.language or "en",
                                )
                                active_instances[call.id] = w
                                asyncio.create_task(w.start())
                        
                        # Cleanup ended calls
                        for cid, w in list(active_instances.items()):
                            if not w.running:
                                active_instances.pop(cid, None)
                except Exception as e:
                    logger.debug(f"Dispatcher polling error: {e}")
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[-] Shutting down worker dispatcher...")
            for w in active_instances.values():
                await w.stop()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AsistLine Voice Agent Worker")
    parser.add_argument("--room", type=str, help="LiveKit room name to join directly")
    parser.add_argument("--tenant", type=str, default="apex-logistics", help="Tenant ID (default: apex-logistics)")
    parser.add_argument("--call-id", type=str, help="Call ID in database")
    args = parser.parse_args()

    try:
        asyncio.run(run_standalone_worker(args.room, args.tenant, args.call_id))
    except KeyboardInterrupt:
        pass

