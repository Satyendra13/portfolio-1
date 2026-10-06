import pytest
from apps.worker.graph.state import CallState
from apps.worker.graph.build import CallGraphOrchestrator


@pytest.fixture
def acme_config():
    return {
        "tenant_id": "acme_telecom",
        "display_name": "Acme Telecom",
        "supported_languages": ["en", "hi"],
        "verification": {"factors": ["order_id", "phone_last4"], "max_attempts": 3},
        "automatable_intents": ["order_status", "faq", "complaint", "callback"],
        "escalation_rules": {"sentiment_threshold": -0.6, "keywords": ["legal", "fraud"], "max_kb_misses": 2},
        "kb_min_score": 0.55
    }


@pytest.fixture
def quickcart_config():
    return {
        "tenant_id": "quickcart",
        "display_name": "QuickCart E-Commerce",
        "supported_languages": ["en", "hi"],
        "verification": {"factors": ["order_id", "phone_last4"], "max_attempts": 3},
        "automatable_intents": ["order_status", "account_inquiry", "faq", "callback"],
        "escalation_rules": {"sentiment_threshold": -0.6, "keywords": ["refund", "fraud"], "max_kb_misses": 2},
        "kb_min_score": 0.55
    }


@pytest.mark.asyncio
async def test_e2e_use_case_1_order_status_acme(acme_config):
    """Use Case 1: Order Status check requiring verification."""
    orchestrator = CallGraphOrchestrator(acme_config)
    state = CallState(call_id="call_e2e_1", tenant_id="acme_telecom")

    # Turn 1: Ask for order status
    s1 = await orchestrator.run_turn(state, "I want to check my order status for 48213 PIN 1234")
    assert s1.intent == "order_status"
    assert s1.verified is True
    assert "Shipped" in s1.ai_response
    assert len(s1.tool_results) == 1
    assert s1.tool_results[0]["status"] == "Shipped"


@pytest.mark.asyncio
async def test_e2e_use_case_2_account_inquiry_quickcart(quickcart_config):
    """Use Case 2: Account Inquiry check requiring verification."""
    orchestrator = CallGraphOrchestrator(quickcart_config)
    state = CallState(call_id="call_e2e_2", tenant_id="quickcart")

    # Turn 1: Ask for account info with verification factors
    s1 = await orchestrator.run_turn(state, "Can I see my account plan details? Order 48213 PIN 1234")
    assert s1.intent == "account_inquiry"
    assert s1.verified is True
    assert "Gold Member" in s1.ai_response
    assert len(s1.tool_results) == 1


@pytest.mark.asyncio
async def test_e2e_use_case_3_complaint_ticket_with_spoken_confirmation(acme_config):
    """Use Case 3: Complaint ticket creation requiring spoken write confirmation."""
    orchestrator = CallGraphOrchestrator(acme_config)
    state = CallState(call_id="call_e2e_3", tenant_id="acme_telecom", verified=True)

    # Turn 1: File complaint -> Orchestrator requests spoken confirmation
    s1 = await orchestrator.run_turn(state, "I have a complaint about my broken router")
    assert s1.intent == "complaint"
    assert s1.awaiting_confirmation is True
    assert "Should I go ahead" in s1.ai_response
    assert len(s1.tool_results) == 0  # No ticket created before confirmation!

    # Turn 2: Caller says "Yes proceed" -> Ticket created
    s2 = await orchestrator.run_turn(s1, "Yes, please confirm and create the ticket")
    assert s2.awaiting_confirmation is False
    assert "successfully created" in s2.ai_response
    assert len(s2.tool_results) == 1
    assert s2.tool_results[0]["status"] == "open"
    assert s2.tool_results[0]["ticket_id"].startswith("TICK-")


@pytest.mark.asyncio
async def test_e2e_use_case_4_callback_scheduling_quickcart(quickcart_config):
    """Use Case 4: Callback scheduling with spoken write confirmation."""
    orchestrator = CallGraphOrchestrator(quickcart_config)
    state = CallState(call_id="call_e2e_4", tenant_id="quickcart", verified=True)

    # Turn 1: Request callback
    s1 = await orchestrator.run_turn(state, "Please schedule a callback for me")
    assert s1.intent == "callback"
    assert s1.awaiting_confirmation is True

    # Turn 2: Spoken confirmation
    s2 = await orchestrator.run_turn(s1, "Yes, confirm booking")
    assert s2.awaiting_confirmation is False
    assert len(s2.tool_results) == 1
    assert s2.tool_results[0]["status"] == "scheduled"
    assert s2.tool_results[0]["callback_id"].startswith("CB-")


@pytest.mark.asyncio
async def test_e2e_use_case_5_human_escalation_routing(acme_config):
    """Use Case 5: Direct human request routes immediately to escalation."""
    orchestrator = CallGraphOrchestrator(acme_config)
    state = CallState(call_id="call_e2e_5", tenant_id="acme_telecom")

    s1 = await orchestrator.run_turn(state, "Transfer me to a live specialist right now")
    assert s1.intent == "human_request"
    assert s1.status == "escalated"
    assert s1.escalation_reason == "caller_requested_human"
    assert "connecting you to a specialist" in s1.ai_response
