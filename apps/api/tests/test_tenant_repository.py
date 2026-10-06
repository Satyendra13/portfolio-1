import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from apps.api.app.core.db import Base
from apps.api.app.models.models import Tenant, KBDocument, Call
from apps.api.app.repositories.base import TenantRepository
from apps.api.app.core.exceptions import TenantFilterRequiredError


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
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_repository_fails_without_tenant_id(test_session: AsyncSession):
    repo = TenantRepository(KBDocument, test_session)

    # Attempting list_all without tenant_id must raise TenantFilterRequiredError
    with pytest.raises(TenantFilterRequiredError) as exc_info:
        await repo.list_all()
    assert "missing required tenant_id filter" in str(exc_info.value)

    # Attempting get_by_id without tenant_id must raise TenantFilterRequiredError
    with pytest.raises(TenantFilterRequiredError) as exc_info:
        await repo.get_by_id("doc_123")
    assert "missing required tenant_id filter" in str(exc_info.value)

    # Attempting delete_by_id without tenant_id must raise TenantFilterRequiredError
    with pytest.raises(TenantFilterRequiredError) as exc_info:
        await repo.delete_by_id("doc_123")
    assert "missing required tenant_id filter" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tenant_repository_isolates_tenant_data(test_session: AsyncSession):
    doc_repo = TenantRepository(KBDocument, test_session)

    # Create document for Acme Telecom
    doc1 = KBDocument(
        id="doc_acme_1",
        tenant_id="acme_telecom",
        title="Acme Billing Policy",
        file_type="txt",
        content_hash="hash_1"
    )
    await doc_repo.create(doc1, tenant_id="acme_telecom")

    # Create document for QuickCart
    doc2 = KBDocument(
        id="doc_quickcart_1",
        tenant_id="quickcart",
        title="QuickCart Return Policy",
        file_type="txt",
        content_hash="hash_2"
    )
    await doc_repo.create(doc2, tenant_id="quickcart")

    # Fetch Acme docs
    acme_docs = await doc_repo.list_all(tenant_id="acme_telecom")
    assert len(acme_docs) == 1
    assert acme_docs[0].id == "doc_acme_1"

    # Fetch QuickCart docs
    qc_docs = await doc_repo.list_all(tenant_id="quickcart")
    assert len(qc_docs) == 1
    assert qc_docs[0].id == "doc_quickcart_1"

    # Fetch Acme doc with QuickCart tenant_id yields None
    cross_tenant_doc = await doc_repo.get_by_id("doc_acme_1", tenant_id="quickcart")
    assert cross_tenant_doc is None
