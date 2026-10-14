from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.models.call import Call
from backend.app.models.escalation import Escalation
from backend.app.models.agent import Agent
from backend.app.schemas.escalation import (
    EscalationCreate,
    EscalationAccept,
    EscalationResponse,
    EscalationAcceptResponse,
)
from backend.app.services.websocket_manager import agent_ws_manager
from backend.app.services.livekit_service import create_livekit_token
from backend.app.core.config import settings

router = APIRouter(prefix="/escalations", tags=["Escalations"])

@router.post("", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
async def trigger_escalation(payload: EscalationCreate, db: AsyncSession = Depends(get_db)):
    # Verify call exists
    call_res = await db.execute(select(Call).where(Call.id == payload.call_id))
    call = call_res.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    escalation = Escalation(
        call_id=payload.call_id,
        tenant_id=payload.tenant_id,
        reason=payload.reason,
        summary=payload.summary,
        status="pending",
    )
    db.add(escalation)
    call.status = "escalated"
    await db.commit()
    await db.refresh(escalation)

    # Broadcast notification to all connected agents for this tenant
    event = {
        "event": "new_escalation",
        "escalation_id": escalation.id,
        "call_id": call.id,
        "tenant_id": escalation.tenant_id,
        "room_name": call.livekit_room_name,
        "reason": escalation.reason,
        "summary": escalation.summary,
        "created_at": escalation.created_at.isoformat(),
    }
    await agent_ws_manager.broadcast_to_tenant(payload.tenant_id, event)

    return escalation

@router.get("/pending", response_model=List[EscalationResponse])
async def list_pending_escalations(
    tenant_id: str = Query(..., description="Tenant ID to filter escalations"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Escalation)
        .where(Escalation.tenant_id == tenant_id, Escalation.status == "pending")
        .order_by(Escalation.created_at.asc())
    )
    return result.scalars().all()

@router.post("/{escalation_id}/accept", response_model=EscalationAcceptResponse)
async def accept_escalation(
    escalation_id: str,
    payload: EscalationAccept,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    escalation = result.scalar_one_or_none()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    if escalation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Escalation is already {escalation.status} (cannot be accepted twice)",
        )

    # Update escalation
    escalation.status = "accepted"
    escalation.accepted_by_agent_id = payload.agent_id
    escalation.accepted_at = datetime.now(timezone.utc)

    # Update call status to human_active
    call_res = await db.execute(select(Call).where(Call.id == escalation.call_id))
    call = call_res.scalar_one_or_none()
    if call:
        call.status = "human_active"

    await db.commit()
    await db.refresh(escalation)

    # Immediately stand down AI worker so it completely stops speaking
    from backend.app.api.endpoints.calls import active_call_workers
    if escalation.call_id in active_call_workers:
        try:
            worker = active_call_workers[escalation.call_id]
            await worker.mute_and_stand_down()
        except Exception as e:
            pass

    # Generate token for the agent to join the exact same LiveKit room
    agent_token = create_livekit_token(
        room_name=call.livekit_room_name,
        participant_identity=f"agent-{payload.agent_id[:8]}",
        participant_name="Human Agent",
        role="agent",
    )

    # Broadcast update that call was claimed
    await agent_ws_manager.broadcast_to_tenant(
        escalation.tenant_id,
        {
            "event": "escalation_claimed",
            "escalation_id": escalation.id,
            "call_id": escalation.call_id,
            "agent_id": payload.agent_id,
        },
    )

    return EscalationAcceptResponse(
        escalation=EscalationResponse.model_validate(escalation),
        livekit_token=agent_token,
        livekit_url=settings.LIVEKIT_URL,
        room_name=call.livekit_room_name,
    )

@router.post("/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_escalation(escalation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    escalation = result.scalar_one_or_none()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    escalation.status = "resolved"
    escalation.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(escalation)
    return escalation

@router.post("/{escalation_id}/callback", response_model=EscalationResponse)
async def request_callback_fallback(escalation_id: str, phone: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Fallback mechanism when no agents are available within queue timeout.
    Converts pending escalation into a callback request with customer phone number.
    """
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    escalation = result.scalar_one_or_none()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    escalation.status = "callback_requested"
    if phone:
        escalation.summary = f"{escalation.summary}\n[Callback requested for: {phone}]"
    await db.commit()
    await db.refresh(escalation)

    # Broadcast to agents
    await agent_ws_manager.broadcast_to_tenant(
        escalation.tenant_id,
        {
            "event": "callback_scheduled",
            "escalation_id": escalation.id,
            "call_id": escalation.call_id,
            "phone": phone or "on file",
        }
    )
    return escalation
