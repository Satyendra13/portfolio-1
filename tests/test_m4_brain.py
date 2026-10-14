import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import init_db
from backend.agent_worker.graph import agent_graph, AgentState

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_greet_node_includes_recording_disclosure():
    initial_state: AgentState = {
        "call_id": "test-call-greet",
        "tenant_id": "test-tenant-1",
        "tenant_name": "Acme Retail",
        "language": "en",
        "script_config": {
            "welcome_message": {
                "en": "Thank you for calling Acme Retail. This call is recorded for quality assurance and you are speaking with an AI assistant. How may I help?"
            }
        },
        "escalation_rules": {},
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

    result = await agent_graph.ainvoke(initial_state)
    reply = result["ai_response"].lower()
    assert "recorded" in reply or "recording" in reply
    assert "ai" in reply

@pytest.mark.asyncio
async def test_rag_grounded_answer_and_hallucination_refusal():
    # 1. Setup tenant & KB document in database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        t_resp = await client.post("/tenants", json={"name": "Pacific Electronics"})
        assert t_resp.status_code == 201
        tenant_id = t_resp.json()["id"]

        kb_payload = {
            "title": "Return and Warranty Policy",
            "content": (
                "Items may be returned within 30 days of purchase with the original receipt. "
                "All returned electronics must be in original packaging. "
                "Laptops have a 1-year manufacturer warranty covering hardware defects."
            ),
        }
        kb_resp = await client.post(f"/tenants/{tenant_id}/kb/upload", json=kb_payload)
        assert kb_resp.status_code == 201

    base_state: AgentState = {
        "call_id": "test-call-qa",
        "tenant_id": tenant_id,
        "tenant_name": "Pacific Electronics",
        "language": "en",
        "script_config": {},
        "escalation_rules": {"max_retries_before_escalate": 1},
        "transcript_turns": [],
        "user_input": "",
        "intent": "faq",
        "is_angry": False,
        "wants_human": False,
        "kb_context": "",
        "kb_chunks": [],
        "confidence_score": 0.0,
        "has_grounding": False,
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

    # 2. Test Grounded Answer
    grounded_state = base_state.copy()
    grounded_state["user_input"] = "What is the return window for purchased items?"
    res_grounded = await agent_graph.ainvoke(grounded_state)
    reply = res_grounded["ai_response"].lower()
    assert "30" in reply or "30 days" in reply or "thirty" in reply

    # 3. Test Hallucination Refusal (Question NOT in KB)
    ungrounded_state = base_state.copy()
    ungrounded_state["user_input"] = "Do you sell rocket fuel to Mars and what is the interstellar price?"
    res_ungrounded = await agent_graph.ainvoke(ungrounded_state)
    refusal_reply = res_ungrounded["ai_response"].lower()
    # Must refuse to guess and mention absence of info or connect with specialist
    assert (
        "do not have that information" in refusal_reply
        or "knowledge base" in refusal_reply
        or "specialist" in refusal_reply
        or "connect you" in refusal_reply
    )

@pytest.mark.asyncio
async def test_explicit_escalation_intent_routes_to_escalate():
    state: AgentState = {
        "call_id": "test-call-esc",
        "tenant_id": "test-tenant-1",
        "tenant_name": "Acme Retail",
        "language": "en",
        "script_config": {},
        "escalation_rules": {},
        "transcript_turns": [
            {"speaker": "customer", "text": "I received a broken item."},
            {"speaker": "ai", "text": "I apologize for that inconvenience."}
        ],
        "user_input": "I am furious, transfer me to a human representative right now!",
        "intent": "escalate",
        "is_angry": True,
        "wants_human": True,
        "kb_context": "",
        "kb_chunks": [],
        "confidence_score": 0.0,
        "has_grounding": False,
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

    result = await agent_graph.ainvoke(state)
    assert result["escalation_needed"] is True
    assert result["status"] == "escalated"
    assert "specialist" in result["ai_response"].lower() or "hold" in result["ai_response"].lower()
    assert len(result["escalation_summary"]) > 0

@pytest.mark.asyncio
async def test_verification_node_flow():
    base_state: AgentState = {
        "call_id": "test-call-verify",
        "tenant_id": "test-tenant-1",
        "tenant_name": "Apex Retail",
        "language": "en",
        "script_config": {},
        "escalation_rules": {},
        "transcript_turns": [],
        "user_input": "I need to check the status of my order",
        "intent": "order_status",
        "is_angry": False,
        "wants_human": False,
        "kb_context": "",
        "kb_chunks": [],
        "confidence_score": 0.0,
        "has_grounding": False,
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

    # Step 1: Request credentials
    res1 = await agent_graph.ainvoke(base_state)
    assert res1["verification_step"] == "requested"
    assert "order id" in res1["ai_response"].lower()

    # Step 2: Provide valid credentials
    step2_state = res1.copy()
    step2_state["user_input"] = "My order ID is 10492 and phone number ends in 4821"
    step2_state["order_id"] = "10492"
    step2_state["phone_last4"] = "4821"
    res2 = await agent_graph.ainvoke(step2_state)
    assert res2["verification_step"] == "verified"
    assert "sarah connor" in res2["ai_response"].lower()
    assert "out for delivery" in res2["ai_response"].lower()
