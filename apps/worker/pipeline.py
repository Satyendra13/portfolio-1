import time
import asyncio
import httpx
from typing import AsyncIterator, Dict, Any, List, Optional
from apps.api.app.core.config import settings
from apps.worker.transport import MediaTransport
from apps.worker.brain import respond, format_spoken_text


async def fetch_elevenlabs_audio_stream(text: str, voice_id: str) -> AsyncIterator[bytes]:
    """
    Stream audio chunks from ElevenLabs Realtime Multilingual TTS API.
    """
    if not settings.ELEVENLABS_API_KEY or not text.strip():
        yield text.encode("utf-8")
        return

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": settings.ELEVENLABS_TTS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=payload, timeout=10.0) as response:
                if response.status_code == 200:
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        yield chunk
                else:
                    yield text.encode("utf-8")
    except Exception:
        yield text.encode("utf-8")


class VoicePipeline:
    """
    Real-time streaming voice pipeline managing VAD, STT, LLM streaming, TTS, barge-in,
    and turn latency instrumentation.
    """
    def __init__(self, transport: MediaTransport, tenant_config: Dict[str, Any], call_id: str):
        self.transport = transport
        self.tenant_config = tenant_config
        self.call_id = call_id
        self.language = tenant_config.get("supported_languages", ["en"])[0]
        self.voices = tenant_config.get("voices", {})
        self.is_speaking = False
        self.interrupted = False
        self.transcript: List[Dict[str, str]] = []
        self.turn_history: List[Dict[str, Any]] = []

    async def run_turn(self, caller_text: str) -> Dict[str, Any]:
        """
        Execute a full voice turn from caller utterance to AI response streaming.
        Measures latency_ms from end of speech to first audio output token.
        """
        start_time = time.time()
        
        # 1. Update transcript with caller turn
        self.transcript.append({"speaker": "caller", "text": caller_text, "language": self.language})

        # 2. Detect language change hint
        if any(h in caller_text for h in ["नमस्ते", "हिंदी", "हिंदी में", "hindi"]):
            self.language = "hi"
        elif any(e in caller_text.lower() for e in ["english", "hello", "hi"]):
            self.language = "en"

        voice_id = self.voices.get(self.language, self.voices.get("en", "21m00Tcm4TlvDq8ikWAM"))

        state = {
            "tenant_id": self.tenant_config.get("tenant_id"),
            "language": self.language,
            "transcript": self.transcript,
            "greeting": None
        }

        # 3. Stream response from LLM brain
        first_token_time: Optional[float] = None
        spoken_tokens: List[str] = []
        self.is_speaking = True
        self.interrupted = False

        async def generate_audio_chunks() -> AsyncIterator[bytes]:
            nonlocal first_token_time
            try:
                async for text_chunk in respond(state):
                    if self.interrupted:
                        break
                    
                    if first_token_time is None:
                        first_token_time = time.time()

                    spoken_tokens.append(text_chunk)
                    
                    # Output audio stream (ElevenLabs or PCM fallback)
                    if settings.ELEVENLABS_API_KEY:
                        async for audio_bytes in fetch_elevenlabs_audio_stream(text_chunk, voice_id):
                            if self.interrupted:
                                break
                            yield audio_bytes
                    else:
                        yield text_chunk.encode("utf-8")
                    
                    await asyncio.sleep(0.01)
            finally:
                self.is_speaking = False

        # 4. Output audio through MediaTransport
        await self.transport.audio_out(generate_audio_chunks())

        end_time = time.time()
        latency_ms = ((first_token_time - start_time) * 1000.0) if first_token_time else 0.0

        full_ai_text = "".join(spoken_tokens).strip()
        
        turn_data = {
            "call_id": self.call_id,
            "seq": len(self.turn_history) + 1,
            "speaker": "ai",
            "text": full_ai_text,
            "language": self.language,
            "interrupted": self.interrupted,
            "latency_ms": latency_ms
        }
        
        self.transcript.append({"speaker": "ai", "text": full_ai_text, "language": self.language})
        self.turn_history.append(turn_data)

        return turn_data

    async def handle_barge_in(self) -> None:
        """
        Triggered when VAD detects caller speech during AI playback.
        Stops TTS within <300ms, flushes queue, and marks current turn interrupted.
        """
        if self.is_speaking:
            self.interrupted = True
            await self.transport.interrupt()
