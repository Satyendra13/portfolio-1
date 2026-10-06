from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.core.exceptions import TenantFilterRequiredError, TenantNotFoundError
from apps.api.app.models.models import TenantScopedMixin

T = TypeVar("T")


class TenantRepository(Generic[T]):
    """
    Repository layer that enforces tenant_id filtering on all queries targeting tenant-scoped models.
    """
    def __init__(self, model_class: Type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session

    def _is_tenant_scoped(self) -> bool:
        return getattr(self.model_class, "is_tenant_scoped", False) or hasattr(self.model_class, "tenant_id")

    async def get_by_id(self, item_id: Any, tenant_id: Optional[str] = None) -> Optional[T]:
        if self._is_tenant_scoped():
            if not tenant_id:
                raise TenantFilterRequiredError(self.model_class.__name__)
            stmt = select(self.model_class).where(
                self.model_class.id == item_id,
                self.model_class.tenant_id == tenant_id
            )
        else:
            stmt = select(self.model_class).where(self.model_class.id == item_id)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, tenant_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[T]:
        if self._is_tenant_scoped():
            if not tenant_id:
                raise TenantFilterRequiredError(self.model_class.__name__)
            stmt = select(self.model_class).where(self.model_class.tenant_id == tenant_id).limit(limit).offset(offset)
        else:
            stmt = select(self.model_class).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, item: T, tenant_id: Optional[str] = None) -> T:
        if self._is_tenant_scoped():
            if not tenant_id and not getattr(item, "tenant_id", None):
                raise TenantFilterRequiredError(self.model_class.__name__)
            if tenant_id and not getattr(item, "tenant_id", None):
                item.tenant_id = tenant_id

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete_by_id(self, item_id: Any, tenant_id: Optional[str] = None) -> bool:
        if self._is_tenant_scoped():
            if not tenant_id:
                raise TenantFilterRequiredError(self.model_class.__name__)
            stmt = delete(self.model_class).where(
                self.model_class.id == item_id,
                self.model_class.tenant_id == tenant_id
            )
        else:
            stmt = delete(self.model_class).where(self.model_class.id == item_id)

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
