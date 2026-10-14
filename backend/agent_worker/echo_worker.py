import asyncio
import json
import logging
from typing import Optional
from livekit import rtc
from livekit.agents import stt, vad, utils
from backend.app.services.livekit_service import create_livekit_token
from backend.agent_worker.audio_pipeline import AudioPipeline
from backend.app.core.config import settings

logger = logging.getLogger("asistline.echo_worker")

class EchoAgentWorker:
    def __init__(self, room_name: str, call_id: Optional[str] = None):
        self.room_name = room_name
        self.call_id = call_id
        self.room = rtc.Room()
        self.pipeline = AudioPipeline()
        self.audio_source = rtc.AudioSource(24000, 1)
        self.audio_track = rtc.LocalAudioTrack.create_audio_track("ai-audio", self.audio_source)
        self.running = False
        self._tasks = []

    async def start(self):
        token = create_livekit_token(
            room_name=self.room_name,
            participant_identity="ai-agent-v0",
            participant_name="AsistLine AI (Echo v0)",
            role="ai",
        )

        logger.info(f"Connecting AI worker to room: {self.room_name}")
        await self.room.connect(settings.LIVEKIT_URL, token)
        logger.info(f"AI worker connected to room {self.room_name}")

        # Publish audio track
        opts = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        await self.room.local_participant.publish_track(self.audio_track, opts)
        logger.info("Published AI audio track to room")

        # Initial California recording disclosure & greeting
        greet_text = (
            "Thank you for calling support. This call may be recorded for quality and "
            "training purposes, and you are speaking with an echo test AI assistant. "
            "Please speak, and I will echo your words."
        )
        await self.broadcast_caption("ai", greet_text)
        await self.pipeline.speak_text(greet_text, self.audio_source)

        # Set up listeners
        self.running = True

        @self.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Subscribed to audio track from {participant.identity}")
                t = asyncio.create_task(self._process_customer_audio(track, participant))
                self._tasks.append(t)

        # Check existing remote participants
        for participant in self.room.remote_participants.values():
            for pub in participant.track_publications.values():
                if pub.track and pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                    t = asyncio.create_task(self._process_customer_audio(pub.track, participant))
                    self._tasks.append(t)

    async def _process_customer_audio(self, track: rtc.RemoteAudioTrack, participant: rtc.RemoteParticipant):
        audio_stream = rtc.AudioStream(track)
        vad_stream = self.pipeline.vad.stream()

        async with utils.http_context.open():
            stt_stream = self.pipeline.stt.stream()

            async def _listen_vad():
                async for event in vad_stream:
                    if event.type == vad.VADEventType.START_OF_SPEECH:
                        # BARGE-IN: Customer spoke, stop AI playback immediately
                        if self.pipeline.is_playing:
                            logger.info("Barge-in detected via Silero VAD! Interrupting playback.")
                            self.pipeline.stop_speaking()

            async def _listen_stt():
                async for ev in stt_stream:
                    if ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                        transcript = ev.alternatives[0].text.strip()
                        if transcript:
                            logger.info(f"Received customer speech: '{transcript}'")
                            await self.broadcast_caption("customer", transcript)
                            
                            # Echo response (M3 requirement: echo back customer words)
                            echo_response = f"Echo: {transcript}"
                            await self.broadcast_caption("ai", echo_response)
                            await self.pipeline.speak_text(echo_response, self.audio_source)

            t_vad = asyncio.create_task(_listen_vad())
            t_stt = asyncio.create_task(_listen_stt())

            try:
                async for frame in audio_stream:
                    if not self.running:
                        break
                    vad_stream.push_frame(frame)
                    stt_stream.push_frame(frame)
            finally:
                t_vad.cancel()
                t_stt.cancel()

    async def broadcast_caption(self, speaker: str, text: str):
        payload = json.dumps({"type": "caption", "speaker": speaker, "text": text}).encode("utf-8")
        try:
            await self.room.local_participant.publish_data(payload)
        except Exception as e:
            logger.debug(f"Failed to publish caption data: {e}")

    async def stop(self):
        self.running = False
        self.pipeline.stop_speaking()
        for t in self._tasks:
            t.cancel()
        await self.room.disconnect()
        logger.info(f"AI Worker disconnected from {self.room_name}")
