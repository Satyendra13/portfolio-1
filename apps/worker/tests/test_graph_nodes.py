import pytest
from apps.worker.graph.state import CallState
from apps.worker.graph.nodes.nodes import (
    node_greet,
    node_detect_language,
    node_classify_intent,
    node_verify_caller,
    node_check_escalation
)


@pytest.fixture
def sample_tenant_config():
    return {
        "tenant_id": "acme_telecom",
        "display_name": "Acme Telecom",
        "supported_languages": ["en", "hi"],
        "script": {
            "greeting": {
                "en": "Thank you for calling Acme Telecom.",
                "hi": "एक्मे टेलीकॉम में कॉल करने के लिए धन्यवाद।"
            }
        },
        "verification": {
            "factors": ["order_id", "phone_last4"],
            "max_attempts": 3
        },
        "escalation_rules": {
            "sentiment_threshold": -0.6,
            "keywords": ["legal", "fraud"],
            "max_kb_misses": 2
        }
    }


@pytest.mark.asyncio
async def test_node_greet(sample_tenant_config):
    state = CallState(call_id="c1", tenant_id="acme_telecom", language="en")
    updated = await node_greet(state, sample_tenant_config)
    assert updated.ai_response == "Thank you for calling Acme Telecom."

    # Test Hindi greeting
    state_hi = CallState(call_id="c2", tenant_id="acme_telecom", language="hi")
    updated_hi = await node_greet(state_hi, sample_tenant_config)
    assert "एक्मे टेलीकॉम" in updated_hi.ai_response


@pytest.mark.asyncio
async def test_node_detect_language(sample_tenant_config):
    state = CallState(
        call_id="c1",
        tenant_id="acme_telecom",
        transcript=[{"speaker": "caller", "text": "नमस्ते, मुझे सहायता चाहिए"}]
    )
    updated = await node_detect_language(state, sample_tenant_config)
    assert updated.language == "hi"


@pytest.mark.asyncio
async def test_node_classify_intent(sample_tenant_config):
    # Test human request
    s1 = CallState(call_id="c1", tenant_id="acme_telecom", transcript=[{"text": "I want to talk to a representative"}])
    u1 = await node_classify_intent(s1, sample_tenant_config)
    assert u1.intent == "human_request"

    # Test order status
    s2 = CallState(call_id="c2", tenant_id="acme_telecom", transcript=[{"text": "Where is my package order?"}])
    u2 = await node_classify_intent(s2, sample_tenant_config)
    assert u2.intent == "order_status"


@pytest.mark.asyncio
async def test_node_verify_caller_locks_out_after_3_failures(sample_tenant_config):
    state = CallState(
        call_id="c1",
        tenant_id="acme_telecom",
        transcript=[{"text": "My order number is 00000 and phone PIN 9999"}]
    )

    # Attempt 1
    s1 = await node_verify_caller(state, sample_tenant_config)
    assert s1.verified is False
    assert s1.verify_attempts == 1

    # Attempt 2
    s2 = await node_verify_caller(s1, sample_tenant_config)
    assert s2.verify_attempts == 2

    # Attempt 3 (Must set escalation flag)
    s3 = await node_verify_caller(s2, sample_tenant_config)
    assert s3.verify_attempts == 3
    assert s3.escalation_reason == "verification_failed_3_times"
    assert s3.status == "escalated"
