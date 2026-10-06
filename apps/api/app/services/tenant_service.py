import os
import yaml
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.models.models import Tenant, TenantConfig
from apps.api.app.schemas.tenant import TenantConfigSchema


class TenantService:
    @staticmethod
    async def get_tenant_config(session: AsyncSession, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
        res = await session.execute(stmt)
        cfg = res.scalars().first()
        if cfg:
            return cfg.config_json
        return None

    @staticmethod
    async def seed_tenants_from_files(session: AsyncSession, tenants_dir: str = "data/tenants") -> List[str]:
        seeded_ids = []
        if not os.path.exists(tenants_dir):
            return seeded_ids

        for fname in os.listdir(tenants_dir):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                filepath = os.path.join(tenants_dir, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_data = yaml.safe_load(f)

                if not raw_data or "tenant_id" not in raw_data:
                    continue

                tenant_id = raw_data["tenant_id"]
                display_name = raw_data.get("display_name", tenant_id)

                # Check if tenant exists
                t_stmt = select(Tenant).where(Tenant.id == tenant_id)
                t_res = await session.execute(t_stmt)
                tenant = t_res.scalars().first()

                if not tenant:
                    tenant = Tenant(id=tenant_id, display_name=display_name)
                    session.add(tenant)

                tc_stmt = select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
                tc_res = await session.execute(tc_stmt)
                t_config = tc_res.scalars().first()

                if not t_config:
                    t_config = TenantConfig(tenant_id=tenant_id, config_json=raw_data)
                    session.add(t_config)
                else:
                    t_config.config_json = raw_data

                seeded_ids.append(tenant_id)

        await session.commit()
        return seeded_ids
