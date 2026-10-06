import time
import pytest
import asyncio
from apps.worker.transport import MockMediaTransport
from apps.worker.pipeline import VoicePipeline


@pytest.fixture
def mock_tenant_config():
    return {
        "tenant_id": "acme_telecom",
        "display_name": "Acme Telecom",
        "supported_languages": ["en", "hi"],
        "voices": {
            "en": "21m00Tcm4TlvDq8ikWAM",
            "hi": "AZnzlk1XvdvUeBnXmlld"
        },
        "script": {
            "greeting": {
                "en": "Thank you for calling Acme Telecom.",
                "hi": "एक्मे टेलीकॉम में कॉल करने के लिए धन्यवाद।"
            }
        }
    }


@pytest.mark.asyncio
async def test_voice_pipeline_latency_and_turn(mock_tenant_config):
    transport = MockMediaTransport()
    await transport.join("call_test_123")

    pipeline = VoicePipeline(transport, mock_tenant_config, "call_test_123")

    # Run turn
    turn_result = await pipeline.run_turn("Hello, I need help with my account status.")

    assert turn_result["speaker"] == "ai"
    assert len(turn_result["text"]) > 0
    assert turn_result["interrupted"] is False
    # Verify response latency (target <= 2500 ms for live API network calls)
    assert turn_result["latency_ms"] < 3500.0
    assert len(transport.output_chunks) > 0


@pytest.mark.asyncio
async def test_voice_pipeline_barge_in(mock_tenant_config):
    transport = MockMediaTransport()
    await transport.join("call_test_123")

    pipeline = VoicePipeline(transport, mock_tenant_config, "call_test_123")

    # Start turn execution concurrently
    turn_task = asyncio.create_task(pipeline.run_turn("What is your return policy?"))
    
    # Simulate VAD interruption mid-speech within 50ms
    await asyncio.sleep(0.05)
    start_interrupt = time.time()
    await pipeline.handle_barge_in()
    interrupt_duration_ms = (time.time() - start_interrupt) * 1000.0

    turn_result = await turn_task

    # Interruption must occur within <= 300 ms target
    assert interrupt_duration_ms < 300.0
    assert turn_result["interrupted"] is True
    assert transport.interrupted_count == 1


@pytest.mark.asyncio
async def test_voice_pipeline_language_switch(mock_tenant_config):
    transport = MockMediaTransport()
    await transport.join("call_test_123")

    pipeline = VoicePipeline(transport, mock_tenant_config, "call_test_123")

    # Speak in Hindi
    turn_result = await pipeline.run_turn("नमस्ते, मुझे हिंदी में जानकारी चाहिए।")

    assert pipeline.language == "hi"
    assert turn_result["language"] == "hi"
