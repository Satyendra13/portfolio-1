import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.app.core.db import Base
from apps.api.app.models.models import Tenant
from apps.api.app.services.kb_ingest import KBIngestService
from apps.api.app.services.kb_search import KBSearchService
from apps.worker.grounding import evaluate_grounded_answer


@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        # Seed test tenants
        t1 = Tenant(id="acme_telecom", display_name="Acme Telecom")
        t2 = Tenant(id="quickcart", display_name="QuickCart")
        session.add_all([t1, t2])
        await session.commit()

        # Seed KB documents
        await KBIngestService.seed_tenant_kbs(session, kb_dir="data/kb")
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_kb_ingest_and_search(test_session: AsyncSession):
    # Search Acme Telecom KB
    acme_hits = await KBSearchService.hybrid_search(
        session=test_session,
        tenant_id="acme_telecom",
        query="What is the price of the Starter Mobile Plan?",
        top_k=2
    )

    assert len(acme_hits) > 0
    assert "$30" in acme_hits[0].chunk_text

    # Search QuickCart KB
    qc_hits = await KBSearchService.hybrid_search(
        session=test_session,
        tenant_id="quickcart",
        query="What is the return policy window?",
        top_k=2
    )

    assert len(qc_hits) > 0
    assert "30 days" in qc_hits[0].chunk_text


@pytest.mark.asyncio
async def test_tenant_isolation_in_kb_search(test_session: AsyncSession):
    # Searching QuickCart KB for Acme Telecom specific queries must return empty or QuickCart-only chunks
    qc_hits = await KBSearchService.hybrid_search(
        session=test_session,
        tenant_id="quickcart",
        query="Fiber Home Broadband 1000 ONT router",
        top_k=4
    )

    for hit in qc_hits:
        # Ensure no Acme document chunks are returned for QuickCart tenant search
        assert "Acme" not in hit.chunk_text


@pytest.mark.asyncio
async def test_grounding_guard_in_kb_and_out_of_kb(test_session: AsyncSession):
    tenant_config = {
        "tenant_id": "acme_telecom",
        "kb_min_score": 0.50,
        "script": {
            "not_found": {
                "en": "I do not have that specific information in my knowledge base."
            }
        }
    }

    # 1. In-KB query evaluation
    hits = await KBSearchService.hybrid_search(
        session=test_session,
        tenant_id="acme_telecom",
        query="How much is the late payment fee?",
        top_k=2
    )

    answer_obj = await evaluate_grounded_answer(
        query="How much is the late payment fee?",
        retrieved_chunks=hits,
        tenant_config=tenant_config,
        language="en"
    )

    assert answer_obj.is_grounded is True
    assert len(answer_obj.used_chunk_ids) > 0
    assert "$15" in answer_obj.answer

    # 2. Out-of-KB query evaluation (low/zero score or unknown topic)
    out_hits = await KBSearchService.hybrid_search(
        session=test_session,
        tenant_id="acme_telecom",
        query="What is the CEO's personal cell phone number?",
        top_k=2
    )

    out_answer_obj = await evaluate_grounded_answer(
        query="What is the CEO's personal cell phone number?",
        retrieved_chunks=out_hits,
        tenant_config=tenant_config,
        language="en"
    )

    assert out_answer_obj.is_grounded is False
    assert out_answer_obj.answer == "I do not have that specific information in my knowledge base."
    assert len(out_answer_obj.used_chunk_ids) == 0
