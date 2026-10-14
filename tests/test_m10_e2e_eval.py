import asyncio
import pytest
import pytest_asyncio
import time
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.agent_worker.graph import agent_graph, AgentState

EVAL_QUESTION_SET = [
    # --- Tenant 1: Apex Logistics ---
    {
        "tenant_id": "apex-logistics",
        "tenant_name": "Apex Logistics Support",
        "question": "How many business days does standard ground shipping take?",
        "is_grounded": True,
        "expected_substrings": ["3 to 5", "3-5", "5 business days", "three to five"],
    },
    {
        "tenant_id": "apex-logistics",
        "tenant_name": "Apex Logistics Support",
        "question": "What is the cut-off time for Express Overnight shipping?",
        "is_grounded": True,
        "expected_substrings": ["2:00 pm", "2 pm", "2:00"],
    },
    {
        "tenant_id": "apex-logistics",
        "tenant_name": "Apex Logistics Support",
        "question": "Within how many hours must a customer report damaged packages?",
        "is_grounded": True,
        "expected_substrings": ["48 hours", "48"],
    },
    {
        "tenant_id": "apex-logistics",
        "tenant_name": "Apex Logistics Support",
        "question": "Do you deliver hot pizza or fresh groceries to residential homes?",
        "is_grounded": False,
        "expected_substrings": [],
    },
    {
        "tenant_id": "apex-logistics",
        "tenant_name": "Apex Logistics Support",
        "question": "Can I ship live tigers across international borders on your cargo planes?",
        "is_grounded": False,
        "expected_substrings": [],
    },

    # --- Tenant 2: Pacific Electronics ---
    {
        "tenant_id": "pacific-electronics",
        "tenant_name": "Pacific Electronics",
        "question": "What is the restocking fee for opened items in like-new condition?",
        "is_grounded": True,
        "expected_substrings": ["10%", "10 percent"],
    },
    {
        "tenant_id": "pacific-electronics",
        "tenant_name": "Pacific Electronics",
        "question": "How long is the limited manufacturer warranty on laptops and monitors?",
        "is_grounded": True,
        "expected_substrings": ["1-year", "1 year", "one year", "one-year"],
    },
    {
        "tenant_id": "pacific-electronics",
        "tenant_name": "Pacific Electronics",
        "question": "Do you accept old cords, batteries, and electronics for recycling?",
        "is_grounded": True,
        "expected_substrings": ["free", "recycling", "e-waste", "batteries"],
    },
    {
        "tenant_id": "pacific-electronics",
        "tenant_name": "Pacific Electronics",
        "question": "Do you sell high-powered laser weapons for alien defense?",
        "is_grounded": False,
        "expected_substrings": [],
    },
    {
        "tenant_id": "pacific-electronics",
        "tenant_name": "Pacific Electronics",
        "question": "What is the secret recipe for Kentucky Fried Chicken?",
        "is_grounded": False,
        "expected_substrings": [],
    },

    # --- Tenant 3: CalCoast Health ---
    {
        "tenant_id": "calcoast-health",
        "tenant_name": "CalCoast Health",
        "question": "What are the regular clinic operating hours from Monday to Friday?",
        "is_grounded": True,
        "expected_substrings": ["8:00 am", "8 am", "6:00 pm", "6 pm"],
    },
    {
        "tenant_id": "calcoast-health",
        "tenant_name": "CalCoast Health",
        "question": "How much is the fee if I cancel an appointment with less than 24 hours notice?",
        "is_grounded": True,
        "expected_substrings": ["$35", "35"],
    },
    {
        "tenant_id": "calcoast-health",
        "tenant_name": "CalCoast Health",
        "question": "Are telehealth virtual visits available on weekends?",
        "is_grounded": True,
        "expected_substrings": ["7 days", "available", "virtual"],
    },
    {
        "tenant_id": "calcoast-health",
        "tenant_name": "CalCoast Health",
        "question": "Can I buy commercial airline tickets from your health clinic?",
        "is_grounded": False,
        "expected_substrings": [],
    },
    {
        "tenant_id": "calcoast-health",
        "tenant_name": "CalCoast Health",
        "question": "What is the capital city of Australia?",
        "is_grounded": False,
        "expected_substrings": [],
    },
]

@pytest.mark.asyncio
async def test_full_call_escalate_accept_resolve_flow():
    """
    End-to-End manual test flow:
    Call Start -> Trigger Escalation -> Agent Accepts -> Resolve Call
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start Call
        start_res = await client.post(
            "/calls/start",
            json={"tenant_id": "apex-logistics", "customer_session_id": "e2e-cust-1"}
        )
        assert start_res.status_code == 201
        call_data = start_res.json()
        call_id = call_data["id"]
        assert call_data["status"] == "ai_active"

        # 2. Add Customer Turn
        turn_res = await client.post(
            f"/calls/{call_id}/turns",
            json={"speaker": "customer", "text": "My package hasn't arrived in 10 days, this is unacceptable!"}
        )
        assert turn_res.status_code == 201

        # 3. Trigger Escalation
        esc_res = await client.post(
            "/escalations",
            json={
                "call_id": call_id,
                "tenant_id": "apex-logistics",
                "reason": "Package lost / customer angry",
                "summary": "Customer shipment 10 days late. Demanding immediate agent refund.",
            }
        )
        assert esc_res.status_code == 201
        esc_data = esc_res.json()
        esc_id = esc_data["id"]
        assert esc_data["status"] == "pending"

        # 4. Agent Portal checks pending queue
        queue_res = await client.get("/escalations/pending?tenant_id=apex-logistics")
        assert queue_res.status_code == 200
        pending_list = queue_res.json()
        assert any(x["id"] == esc_id for x in pending_list)

        # 5. Agent Accepts Escalation
        accept_res = await client.post(
            f"/escalations/{esc_id}/accept",
            json={"agent_id": "agent-alex-mercer"}
        )
        assert accept_res.status_code == 200
        accept_data = accept_res.json()
        assert accept_data["escalation"]["status"] == "accepted"
        assert len(accept_data["livekit_token"]) > 30
        assert accept_data["livekit_token"].startswith("eyJ")
        assert accept_data["room_name"] == call_data["livekit_room_name"]

        # 6. Verify Call Status changed to human_active
        c_check = await client.get(f"/calls/{call_id}")
        assert c_check.json()["status"] == "human_active"

        # 7. Agent resolves and ends call
        resolve_res = await client.post(f"/escalations/{esc_id}/resolve")
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "resolved"

        end_res = await client.post(f"/calls/{call_id}/end")
        assert end_res.status_code == 200
        assert end_res.json()["status"] == "ended"

@pytest.mark.asyncio
async def test_15_question_eval_set_grounding_and_hallucination():
    """
    Evaluates grounding accuracy and zero-hallucination rate on 15 benchmark questions.
    Logs latency per question.
    """
    latencies = []
    correct_grounded = 0
    total_grounded = 0
    correct_refusals = 0
    total_refusals = 0

    for item in EVAL_QUESTION_SET:
        t0 = time.time()
        state: AgentState = {
            "call_id": "eval-session",
            "tenant_id": item["tenant_id"],
            "tenant_name": item["tenant_name"],
            "language": "en",
            "script_config": {},
            "escalation_rules": {"max_retries_before_escalate": 1},
            "transcript_turns": [],
            "user_input": item["question"],
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

        result = await agent_graph.ainvoke(state)
        latency = round(time.time() - t0, 3)
        latencies.append(latency)

        reply = result["ai_response"].lower()

        if item["is_grounded"]:
            total_grounded += 1
            matched = any(sub in reply for sub in item["expected_substrings"])
            if matched:
                correct_grounded += 1
            else:
                print(f"[GROUNDING MISS] Q: '{item['question']}' -> Reply: '{result['ai_response']}'")
        else:
            total_refusals += 1
            # Grounding rule: Must refuse to answer outside KB
            refused = (
                "do not have that information" in reply
                or "knowledge base" in reply
                or "specialist" in reply
                or "connect you" in reply
                or "trouble retrieving" in reply
                or "hold" in reply
                or "don't handle" in reply
                or "do not handle" in reply
                or "don't offer" in reply
                or "do not offer" in reply
                or "sorry, but" in reply
                or "unable to" in reply
                or "cannot" in reply
            )
            if refused:
                correct_refusals += 1
            else:
                print(f"[HALLUCINATION LEAK] Q: '{item['question']}' -> Reply: '{result['ai_response']}'")

        # Pacing sleep to prevent exceeding free tier 15 RPM
        await asyncio.sleep(2.0)

    avg_latency = round(sum(latencies) / len(latencies), 3)
    grounding_accuracy = (correct_grounded / total_grounded) * 100
    refusal_accuracy = (correct_refusals / total_refusals) * 100

    print(f"\n=================== EVAL BENCHMARK RESULTS ===================")
    print(f"Total Questions Evaluated: {len(EVAL_QUESTION_SET)}")
    print(f"Grounded Questions Accuracy: {correct_grounded}/{total_grounded} ({grounding_accuracy:.1f}%)")
    print(f"Hallucination Refusal Accuracy: {correct_refusals}/{total_refusals} ({refusal_accuracy:.1f}%)")
    print(f"Average Answer Latency: {avg_latency}s (Target: < 1.5s)")
    print(f"==============================================================")

    # Hard requirements:
    # 1. Hallucination refusal must be 100% (never invent answers outside KB)
    assert refusal_accuracy == 100.0
    # 2. Grounded accuracy must be >= 80%
    assert grounding_accuracy >= 80.0
