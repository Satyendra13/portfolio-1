import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.app.main import app
from apps.api.app.core.db import Base, get_db
from apps.api.app.services.tenant_service import TenantService


@pytest_asyncio.fixture
async def test_app_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        await TenantService.seed_tenants_from_files(session, tenants_dir="data/tenants")

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_escalation_lifecycle_and_agent_handoff(test_app_client: AsyncClient):
    # 1. Start call
    call_res = await test_app_client.post("/v1/calls/start", json={"tenant_id": "acme_telecom", "language": "en"})
    call_id = call_res.json()["call_id"]

    # 2. Trigger escalation with Handoff Packet
    packet_payload = {
        "call_id": call_id,
        "tenant_id": "acme_telecom",
        "language": "en",
        "intent": "complaint",
        "reason": "caller_requested_human",
        "verified": True,
        "caller": {"name": "Test Caller", "order_id": "48213"},
        "summary": "Caller requested human agent regarding damaged fiber ONT router.",
        "kb_answers_given": [{"q": "How to restart ONT?", "chunk_ids": ["c1"]}],
        "actions_taken": [{"type": "ticket_created", "id": "TICK-1042"}],
        "transcript": [{"speaker": "caller", "text": "I want to talk to a person"}],
        "sentiment": "frustrated"
    }

    trig_res = await test_app_client.post("/v1/escalations/trigger", json=packet_payload)
    assert trig_res.status_code == 200
    esc_data = trig_res.json()
    assert esc_data["status"] == "queued"
    esc_id = esc_data["id"]

    # 3. List Queue
    queue_res = await test_app_client.get("/v1/escalations/queue?tenant_id=acme_telecom")
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert len(queue) == 1
    assert queue[0]["id"] == esc_id

    # 4. Human Agent Accepts Escalation
    accept_res = await test_app_client.post(f"/v1/escalations/{esc_id}/accept?human_agent_id=Agent_Priya")
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert "agent_token" in accept_data
    assert accept_data["handoff_packet"]["intent"] == "complaint"

    # 5. Submit Disposition Feedback
    fb_res = await test_app_client.post(f"/v1/escalations/{esc_id}/feedback", json={
        "rating": "appropriate",
        "comments": "Caller needed hardware replacement authorization."
    })
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "submitted"
