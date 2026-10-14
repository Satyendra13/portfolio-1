import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["livekit_configured"] is True

@pytest.mark.asyncio
async def test_livekit_test_page():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/test-livekit")
        assert resp.status_code == 200
        assert "LiveKit Connectivity Test (M2)" in resp.text

@pytest.mark.asyncio
async def test_tenant_crud_and_kb_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Tenant
        tenant_payload = {
            "name": "Apex Logistics Support",
            "script_config": {
                "welcome_message": {
                    "en": "Thank you for calling Apex Logistics. This call is recorded and answered by an AI assistant. How may I help you?",
                    "hi": "एपेक्स लॉजिस्टिक्स में कॉल करने के लिए धन्यवाद। यह कॉल रिकॉर्ड की जाती है। मैं आपकी क्या सहायता कर सकता हूँ?"
                },
                "languages": ["en", "hi"],
                "voice_id": "eleven-test-voice"
            }
        }
        res = await client.post("/tenants", json=tenant_payload)
        assert res.status_code == 201
        tenant_data = res.json()
        tenant_id = tenant_data["id"]
        assert tenant_data["name"] == "Apex Logistics Support"
        assert "recorded" in tenant_data["script_config"]["welcome_message"]["en"]

        # 2. Upload KB Document
        kb_payload = {
            "title": "Shipping and Tracking Policy",
            "content": (
                "Standard ground delivery takes 3 to 5 business days. "
                "Expedited next-day shipping cut-off is 2 PM PST.\n\n"
                "Customers can check real-time tracking by providing their 5-digit Order ID "
                "along with the last 4 digits of their registered phone number."
            ),
            "source_url": "https://apexlogistics.example.com/shipping"
        }
        kb_res = await client.post(f"/tenants/{tenant_id}/kb/upload", json=kb_payload)
        assert kb_res.status_code == 201
        kb_data = kb_res.json()
        assert len(kb_data["chunks"]) >= 1

        # 3. Test Semantic Search
        search_res = await client.get(
            f"/tenants/{tenant_id}/kb/search",
            params={"q": "How long does standard delivery take?", "top_k": 2}
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert len(search_data["results"]) > 0
        assert "Standard ground delivery" in search_data["results"][0]["chunk_text"]

        # 4. Start Call
        call_res = await client.post(
            "/calls/start",
            json={"tenant_id": tenant_id, "customer_session_id": "cust-101"}
        )
        assert call_res.status_code == 201
        call_data = call_res.json()
        call_id = call_data["id"]
        room_name = call_data["livekit_room_name"]
        assert "asistline" in room_name

        # 5. Issue LiveKit Token
        token_res = await client.post(
            "/livekit/token",
            json={
                "room_name": room_name,
                "participant_identity": "customer-101",
                "role": "customer"
            }
        )
        assert token_res.status_code == 200
        token_data = token_res.json()
        assert "token" in token_data
        assert token_data["room_name"] == room_name

        # 6. Verify Customer Order
        verify_res = await client.post(
            "/verify",
            json={
                "call_id": call_id,
                "tenant_id": tenant_id,
                "order_id": "10492",
                "phone_last4": "4821"
            }
        )
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["verified"] is True
        assert verify_data["customer_name"] == "Sarah Connor"
