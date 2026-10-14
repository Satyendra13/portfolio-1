from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.models.tenant import Tenant
from backend.app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse, ScriptConfigSchema, EscalationRulesSchema

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    script_cfg = payload.script_config.model_dump() if payload.script_config else ScriptConfigSchema().model_dump()
    esc_rules = payload.escalation_rules.model_dump() if payload.escalation_rules else EscalationRulesSchema().model_dump()

    tenant = Tenant(
        name=payload.name,
        script_config=script_cfg,
        escalation_rules=esc_rules,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant

@router.get("", response_model=List[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return result.scalars().all()

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, payload: TenantUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if payload.name is not None:
        tenant.name = payload.name
    if payload.script_config is not None:
        tenant.script_config = payload.script_config
    if payload.escalation_rules is not None:
        tenant.escalation_rules = payload.escalation_rules

    await db.commit()
    await db.refresh(tenant)
    return tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    await db.delete(tenant)
    await db.commit()
    return None
