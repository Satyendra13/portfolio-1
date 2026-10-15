from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import postgresql

from backend.agent_worker.graph import answer_node, greet_node, route_after_analyze
from backend.agent_worker.llm_client import GeminiLLMClient
from backend.agent_worker import audio_pipeline, graph, rag
from backend.app.main import app
from backend.app.services import embedding


@pytest.mark.asyncio
async def test_fallback_embeddings_are_deterministic_and_fixed_size(monkeypatch):
    monkeypatch.setattr(embedding, "get_genai_client", lambda: None)

    first = await embedding.generate_embedding("delivery status policy")
    second = await embedding.generate_embedding("delivery status policy")

    assert len(first) == embedding.settings.EMBEDDING_DIMENSION
    assert first == second


@pytest.mark.asyncio
async def test_local_intent_fallback_recognizes_handoff_and_order_lookup():
    client = GeminiLLMClient()
    client.api_key = ""

    handoff = await client.analyze_intent_json("Please connect me to a real person")
    order_lookup = await client.analyze_intent_json(
        "Check my order status, order number one zero four nine two; phone four eight two one"
    )

    assert handoff["wants_human"] is True
    assert handoff["intent"] == "escalate"
    assert order_lookup["intent"] == "order_status"
    assert order_lookup["order_id"] == "10492"
    assert order_lookup["phone_last4"] == "4821"


@pytest.mark.asyncio
async def test_angry_customer_requesting_help_is_not_automatically_escalated():
    client = GeminiLLMClient()
    client.api_key = ""
    analysis = await client.analyze_intent_json(
        "I'm frustrated that my package is delayed. Can you help me?"
    )
    state = {
        "wants_human": analysis["wants_human"],
        "is_angry": analysis["is_angry"],
        "intent": analysis["intent"],
        "verification_step": "none",
    }

    assert state["is_angry"] is True
    assert state["wants_human"] is False
    assert route_after_analyze(state) == "retrieve"


@pytest.mark.asyncio
async def test_answer_uses_grounded_kb_if_gemini_generation_fails(monkeypatch):
    async def fail_generation(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(graph.llm_client, "generate_text", fail_generation)
    result = await answer_node(
        {
            "intent": "faq",
            "language": "en",
            "user_input": "What is the return policy?",
            "has_grounding": True,
            "kb_context": "[Returns]: Items may be returned within 30 days.",
            "kb_chunks": [
                {"text": "Items may be returned within 30 days of purchase."}
            ],
            "tenant_name": "Test Store",
            "transcript_turns": [],
        }
    )

    assert "returned within 30 days" in result["ai_response"]
    assert "escalation_needed" not in result


@pytest.mark.asyncio
async def test_sqlite_retrieval_uses_lexical_match_when_embedding_is_unhelpful(monkeypatch):
    chunk = SimpleNamespace(
        id="chunk-1",
        chunk_text="Items may be returned within 30 days of purchase.",
        embedding=[0.0, 0.0],
    )

    class FakeResult:
        def all(self):
            return [(chunk, "Return Policy")]

    class FakeDatabase:
        async def execute(self, _statement):
            return FakeResult()

    async def fake_embedding(_query):
        return [0.0, 0.0]

    monkeypatch.setattr(rag.settings, "DATABASE_URL", "sqlite+aiosqlite:///test.db")
    monkeypatch.setattr(rag, "generate_embedding", fake_embedding)
    context, chunks, score, grounded = await rag.retrieve_kb_context(
        tenant_id="tenant-1",
        query="What is the return policy?",
        db=FakeDatabase(),
    )

    assert grounded is True
    assert score >= rag.settings.DEFAULT_KB_MIN_SCORE
    assert chunks[0]["title"] == "Return Policy"
    assert "30 days" in context


@pytest.mark.asyncio
async def test_greeting_discloses_recording_and_ai_independently():
    result = await greet_node(
        {
            "language": "en",
            "script_config": {"welcome_message": {"en": "This call is recorded. How can I help?"}},
            "transcript_turns": [],
        }
    )

    assert "record" in result["ai_response"].lower()
    assert "ai" in result["ai_response"].lower()


def test_elevenlabs_tts_outputs_pcm_matching_livekit_audio_track(monkeypatch):
    captured = {}
    monkeypatch.setattr(audio_pipeline.silero.VAD, "load", lambda: object())
    monkeypatch.setattr(audio_pipeline.elevenlabs, "STT", lambda **_kwargs: object())
    monkeypatch.setattr(
        audio_pipeline.elevenlabs,
        "TTS",
        lambda **kwargs: captured.update(kwargs) or object(),
    )

    audio_pipeline.AudioPipeline()

    assert captured["encoding"] == "pcm_24000"


@pytest.mark.asyncio
async def test_postgres_rag_uses_selected_distance_value(monkeypatch):
    class FakeDatabase:
        query_sql = ""

        async def execute(self, statement):
            self.query_sql = str(statement.compile(dialect=postgresql.dialect()))
            return self

        def all(self):
            chunk = SimpleNamespace(id="chunk-1", chunk_text="Shipping takes three days.")
            return [(chunk, "Shipping policy", 0.2)]

    async def fake_embedding(_query):
        return [0.1, 0.2]

    monkeypatch.setattr(rag.settings, "DATABASE_URL", "postgresql+asyncpg://localhost/test")
    monkeypatch.setattr(rag, "generate_embedding", fake_embedding)

    database = FakeDatabase()
    context, chunks, score, grounded = await rag.retrieve_kb_context(
        tenant_id="tenant-1",
        query="How long is shipping?",
        db=database,
    )

    assert "<=>" in database.query_sql
    assert grounded is True
    assert score == pytest.approx(0.8)
    assert chunks[0]["score"] == pytest.approx(0.8)
    assert "Shipping policy" in context


@pytest.mark.asyncio
async def test_public_livekit_endpoint_rejects_agent_tokens():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/livekit/token",
            json={
                "room_name": "private-room",
                "participant_identity": "attacker",
                "role": "agent",
            },
        )

    assert response.status_code == 422
