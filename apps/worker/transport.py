import asyncio
from typing import Protocol, AsyncIterator, List, Optional


class MediaTransport(Protocol):
    """Abstraction for WebRTC audio transport (LiveKit today, SIP/WebSocket later)."""

    async def join(self, call_id: str) -> None:
        ...

    async def audio_in(self) -> AsyncIterator[bytes]:
        ...

    async def audio_out(self, chunks: AsyncIterator[bytes]) -> None:
        ...

    async def interrupt(self) -> None:
        ...

    async def add_participant(self, role: str, identity: str) -> None:
        ...

    async def leave(self) -> None:
        ...


class MockMediaTransport:
    """Mock MediaTransport implementation for automated unit testing and simulation."""

    def __init__(self):
        self.connected = False
        self.room_id: Optional[str] = None
        self.input_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.output_chunks: List[bytes] = []
        self.interrupted_count: int = 0
        self.participants: List[dict] = []

    async def join(self, call_id: str) -> None:
        self.connected = True
        self.room_id = call_id

    async def simulate_caller_audio(self, pcm_chunk: bytes) -> None:
        await self.input_queue.put(pcm_chunk)

    async def audio_in(self) -> AsyncIterator[bytes]:
        while self.connected:
            try:
                chunk = await asyncio.wait_for(self.input_queue.get(), timeout=0.1)
                yield chunk
            except asyncio.TimeoutError:
                if not self.connected:
                    break

    async def audio_out(self, chunks: AsyncIterator[bytes]) -> None:
        async for chunk in chunks:
            if not self.connected:
                break
            self.output_chunks.append(chunk)

    async def interrupt(self) -> None:
        self.interrupted_count += 1

    async def add_participant(self, role: str, identity: str) -> None:
        self.participants.append({"role": role, "identity": identity})

    async def leave(self) -> None:
        self.connected = False
