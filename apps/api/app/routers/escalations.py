import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.core.db import get_db
from apps.api.app.core.config import settings
from apps.api.app.models.models import Escalation, Call, EscalationFeedback
from apps.api.app.schemas.escalation import (
    EscalationResponse,
    EscalationAcceptResponse,
    EscalationFeedbackRequest,
    HandoffPacketSchema
)
from apps.api.app.services.livekit_service import LiveKitService

router = APIRouter(prefix="/v1/escalations", tags=["Escalations & Handoff"])


@router.get("/queue", response_model=List[EscalationResponse])
async def list_escalation_queue(
    tenant_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Escalation).where(Escalation.status == "queued")
    if tenant_id:
        stmt = stmt.where(Escalation.tenant_id == tenant_id)

    res = await db.execute(stmt)
    escalations = list(res.scalars().all())

    return [
        EscalationResponse(
            id=e.id,
            call_id=e.call_id,
            tenant_id=e.tenant_id,
            status=e.status,
            summary_json=HandoffPacketSchema(**e.summary_json),
            created_at=e.created_at,
            accepted_at=e.accepted_at,
            human_agent_id=e.human_agent_id
        )
        for e in escalations
    ]


@router.post("/trigger", response_model=EscalationResponse)
async def trigger_escalation(
    packet: HandoffPacketSchema,
    db: AsyncSession = Depends(get_db)
):
    esc_id = f"esc_{uuid.uuid4().hex[:10]}"
    escalation = Escalation(
        id=esc_id,
        call_id=packet.call_id,
        tenant_id=packet.tenant_id,
        status="queued",
        summary_json=packet.model_dump(),
        created_at=datetime.utcnow()
    )
    db.add(escalation)

    # Update call status
    call_stmt = select(Call).where(Call.id == packet.call_id)
    call_res = await db.execute(call_stmt)
    call = call_res.scalars().first()
    if call:
        call.outcome = "escalated"
        call.escalated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(escalation)

    return EscalationResponse(
        id=escalation.id,
        call_id=escalation.call_id,
        tenant_id=escalation.tenant_id,
        status=escalation.status,
        summary_json=HandoffPacketSchema(**escalation.summary_json),
        created_at=escalation.created_at,
        accepted_at=escalation.accepted_at,
        human_agent_id=escalation.human_agent_id
    )


@router.post("/{escalation_id}/accept", response_model=EscalationAcceptResponse)
async def accept_escalation(
    escalation_id: str,
    human_agent_id: str = Query(..., description="ID/Name of human agent accepting transfer"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Escalation).where(Escalation.id == escalation_id)
    res = await db.execute(stmt)
    escalation = res.scalars().first()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    if escalation.status != "queued":
        raise HTTPException(status_code=400, detail=f"Escalation is already {escalation.status}")

    escalation.status = "accepted"
    escalation.accepted_at = datetime.utcnow()
    escalation.human_agent_id = human_agent_id

    # Update call record
    call_stmt = select(Call).where(Call.id == escalation.call_id)
    call_res = await db.execute(call_stmt)
    call = call_res.scalars().first()
    if call:
        call.human_agent_id = human_agent_id

    await db.commit()

    # Generate LiveKit Token for human_agent role
    room_name = f"room_{escalation.tenant_id}_{escalation.call_id}"
    agent_token = LiveKitService.generate_token(
        room_name=room_name,
        identity=f"human_agent_{human_agent_id}",
        name=f"Agent {human_agent_id}",
        can_publish=True,
        can_subscribe=True
    )

    return EscalationAcceptResponse(
        escalation_id=escalation.id,
        call_id=escalation.call_id,
        agent_token=agent_token,
        livekit_url=settings.LIVEKIT_URL,
        handoff_packet=HandoffPacketSchema(**escalation.summary_json)
    )


@router.post("/{escalation_id}/feedback")
async def submit_escalation_feedback(
    escalation_id: str,
    req: EscalationFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Escalation).where(Escalation.id == escalation_id)
    res = await db.execute(stmt)
    escalation = res.scalars().first()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    fb_id = f"fb_{uuid.uuid4().hex[:10]}"
    feedback = EscalationFeedback(
        id=fb_id,
        escalation_id=escalation_id,
        tenant_id=escalation.tenant_id,
        rating=req.rating,
        comments=req.comments,
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    await db.commit()

    return {"status": "submitted", "feedback_id": fb_id}
