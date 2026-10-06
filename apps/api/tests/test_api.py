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
    
    # Seed tenants
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
async def test_health_check(test_app_client: AsyncClient):
    res = await test_app_client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "AsistLine AI API"}


@pytest.mark.asyncio
async def test_start_and_get_call(test_app_client: AsyncClient):
    # Start call for Acme Telecom
    payload = {"tenant_id": "acme_telecom", "language": "en", "caller_name": "Test User"}
    res = await test_app_client.post("/v1/calls/start", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "call_id" in data
    assert "caller_token" in data
    assert data["room_name"].startswith("room_acme_telecom_")

    call_id = data["call_id"]

    # Fetch call detail
    detail_res = await test_app_client.get(f"/v1/calls/{call_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == call_id
    assert detail["tenant_id"] == "acme_telecom"
    assert detail["outcome"] == "active"

    # End call
    end_res = await test_app_client.post(f"/v1/calls/{call_id}/end")
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "success"
