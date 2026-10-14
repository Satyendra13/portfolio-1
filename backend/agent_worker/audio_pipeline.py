import asyncio
import logging
from typing import Optional, Callable
from livekit import rtc
from livekit.agents import utils
from livekit.plugins import elevenlabs, silero
from backend.app.core.config import settings

logger = logging.getLogger("asistline.audio_pipeline")

class AudioPipeline:
    def __init__(self, voice_id: Optional[str] = None):
        self.voice_id = voice_id or "JBFqnCBsd6RMkjVDRZzb"
        self.vad = silero.VAD.load()
        self.stt = elevenlabs.STT(
            api_key=settings.ELEVENLABS_API_KEY,
            model=settings.ELEVENLABS_STT_MODEL or "scribe_v2_realtime",
            server_vad=elevenlabs.stt.VADOptions(
                vad_silence_threshold_secs=0.8,
                min_speech_duration_ms=100,
                min_silence_duration_ms=200,
            ),
        )
        self.tts = elevenlabs.TTS(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=self.voice_id,
            encoding="mp3_44100_128",
            voice_settings=elevenlabs.VoiceSettings(
                stability=0.71,
                similarity_boost=0.8,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        self.active_speech_task: Optional[asyncio.Task] = None
        self.is_playing: bool = False

    def create_stt_stream(self):
        """Always reset cached aiohttp session before creating stream to avoid RuntimeError: Session is closed"""
        self.stt._session = None
        return self.stt.stream()

    async def _stream_edge_tts(self, text: str, audio_source: rtc.AudioSource):
        import io
        import av
        import edge_tts

        voice = "hi-IN-SwaraNeural" if any('\u0900' <= c <= '\u097f' for c in text) else "en-US-JennyNeural"
        logger.info(f"Synthesizing via Edge Neural TTS ({voice}) for text: '{text[:45]}...'")
        communicate = edge_tts.Communicate(text, voice)
        mp3_data = b""
        async for chunk in communicate.stream():
            if not self.is_playing:
                break
            if chunk["type"] == "audio":
                mp3_data += chunk["data"]

        if not self.is_playing or not mp3_data:
            return

        container = av.open(io.BytesIO(mp3_data))
        reformat = av.AudioResampler(format='s16', layout='mono', rate=24000)
        for frame in container.decode(audio=0):
            if not self.is_playing:
                break
            for r in reformat.resample(frame):
                if not self.is_playing:
                    break
                lk_frame = rtc.AudioFrame(
                    data=r.to_ndarray().tobytes(),
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=r.samples,
                )
                await audio_source.capture_frame(lk_frame)
                # Real-time streaming pacing to ensure smooth, natural playback
                await asyncio.sleep((r.samples / 24000) * 0.95)

    async def speak_text(
        self,
        text: str,
        audio_source: rtc.AudioSource,
        on_barge_in: Optional[Callable[[], None]] = None,
    ):
        """
        Synthesize text using ElevenLabs TTS (with automatic Edge Neural fallback)
        and stream frames to audio_source. Allows cancellation within <300ms if barge-in occurs.
        """
        # Cancel any previous speaking task
        self.stop_speaking()

        async def _stream_audio():
            self.is_playing = True
            resampler = None
            eleven_success = False

            try:
                try:
                    if hasattr(self.tts, "_session"):
                        sess = getattr(self.tts, "_session")
                        if sess is None or getattr(sess, "closed", False):
                            self.tts._session = None

                    async with utils.http_context.open():
                        stream = self.tts.synthesize(text)
                        async for chunk in stream:
                            if not self.is_playing:
                                break
                            if chunk.frame:
                                eleven_success = True
                                if (
                                    chunk.frame.sample_rate != audio_source.sample_rate
                                    or chunk.frame.num_channels != audio_source.num_channels
                                ):
                                    if resampler is None or getattr(resampler, "_input_rate", None) != chunk.frame.sample_rate:
                                        resampler = rtc.AudioResampler(
                                            chunk.frame.sample_rate,
                                            audio_source.sample_rate,
                                            num_channels=audio_source.num_channels,
                                        )
                                    for f in resampler.push(chunk.frame):
                                        await audio_source.capture_frame(f)
                                else:
                                    await audio_source.capture_frame(chunk.frame)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(f"ElevenLabs TTS unavailable ({e}), engaging Edge Neural fallback...")
                    eleven_success = False

                if not eleven_success and self.is_playing:
                    try:
                        await self._stream_edge_tts(text, audio_source)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.error(f"Error in fallback Edge TTS streaming: {e}")
            except asyncio.CancelledError:
                logger.info("Speech playback cancelled due to barge-in.")
                if on_barge_in:
                    on_barge_in()
                raise
            finally:
                self.is_playing = False

        self.active_speech_task = asyncio.create_task(_stream_audio())
        try:
            await self.active_speech_task
        except asyncio.CancelledError:
            pass

    def stop_speaking(self):
        """
        Immediate interrupt/barge-in handler (<300ms).
        """
        self.is_playing = False
        if self.active_speech_task and not self.active_speech_task.done():
            self.active_speech_task.cancel()
            self.active_speech_task = None
            logger.info("Barge-in triggered: AI playback aborted.")
