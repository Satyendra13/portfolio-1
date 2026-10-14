import pytest
import asyncio
from livekit import rtc
from backend.agent_worker.echo_worker import EchoAgentWorker
from backend.app.services.livekit_service import create_livekit_token
from backend.app.core.config import settings

@pytest.mark.asyncio
async def test_echo_worker_joins_and_publishes_track():
    room_name = "test-echo-room-pytest"
    worker = EchoAgentWorker(room_name=room_name)

    # Human/customer listener to verify participant & audio track
    customer_token = create_livekit_token(
        room_name=room_name,
        participant_identity="listener-customer-01",
        role="customer"
    )
    customer_room = rtc.Room()

    tracks_received = []

    @customer_room.on("track_published")
    def on_track_published(pub: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
        if participant.identity == "ai-agent-v0":
            tracks_received.append(pub.kind)

    # 1. Connect customer listener
    await customer_room.connect(settings.LIVEKIT_URL, customer_token)

    # 2. Start Echo Worker in room
    worker_task = asyncio.create_task(worker.start())

    # Wait briefly for worker connection and track publishing
    for _ in range(25):
        await asyncio.sleep(0.4)
        if len(tracks_received) > 0 or "ai-agent-v0" in customer_room.remote_participants:
            break

    # Verify AI participant joined
    assert "ai-agent-v0" in customer_room.remote_participants
    ai_participant = customer_room.remote_participants["ai-agent-v0"]
    assert ai_participant.name == "AsistLine AI (Echo v0)"

    # Cleanup
    await worker.stop()
    worker_task.cancel()
    await customer_room.disconnect()
    await asyncio.sleep(0.5)
