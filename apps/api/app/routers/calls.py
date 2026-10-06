import uuid
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.app.core.db import get_db
from apps.api.app.core.config import settings
from apps.api.app.models.models import Call, CallTurn, CallEvent, CallSummary
from apps.api.app.schemas.call import (
    CallStartRequest, CallStartResponse, CallDetailResponse,
    CallTurnSchema, CallEventSchema, ConverseRequest, ConverseResponse
)
from apps.api.app.services.livekit_service import LiveKitService
from apps.api.app.services.tenant_service import TenantService
from apps.worker.graph.build import CallGraphOrchestrator
from apps.worker.graph.state import CallState

router = APIRouter(prefix="/v1/calls", tags=["Calls"])


@router.post("/start", response_model=CallStartResponse)
async def start_call(req: CallStartRequest, db: AsyncSession = Depends(get_db)):
    # Verify tenant exists or load seed config
    tenant_cfg = await TenantService.get_tenant_config(db, req.tenant_id)
    if not tenant_cfg:
        # Seed if empty
        await TenantService.seed_tenants_from_files(db)
        tenant_cfg = await TenantService.get_tenant_config(db, req.tenant_id)
        if not tenant_cfg:
            raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found.")

    call_id = f"call_{uuid.uuid4().hex[:12]}"
    room_name = f"room_{req.tenant_id}_{call_id}"
    caller_identity = f"caller_{uuid.uuid4().hex[:8]}"

    call = Call(
        id=call_id,
        tenant_id=req.tenant_id,
        room_name=room_name,
        started_at=datetime.utcnow(),
        language=req.language,
        outcome="active"
    )
    db.add(call)
    await db.commit()

    token = LiveKitService.generate_token(
        room_name=room_name,
        identity=caller_identity,
        name=req.caller_name or "Caller"
    )

    return CallStartResponse(
        call_id=call_id,
        room_name=room_name,
        caller_token=token,
        livekit_url=settings.LIVEKIT_URL
    )


@router.post("/{call_id}/end")
async def end_call(call_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Call).where(Call.id == call_id)
    res = await db.execute(stmt)
    call = res.scalars().first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.ended_at = datetime.utcnow()
    if call.outcome == "active":
        call.outcome = "resolved_by_ai"
    await db.commit()
    return {"status": "success", "call_id": call_id}


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_detail(call_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Call)
        .options(selectinload(Call.turns), selectinload(Call.events))
        .where(Call.id == call_id)
    )
    res = await db.execute(stmt)
    call = res.scalars().first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Get summary if exists
    sum_stmt = select(CallSummary).where(CallSummary.call_id == call_id)
    sum_res = await db.execute(sum_stmt)
    summary_obj = sum_res.scalars().first()
    summary_dict = None
    if summary_obj:
        summary_dict = {
            "intent": summary_obj.intent,
            "resolution": summary_obj.resolution,
            "actions": summary_obj.actions,
            "sentiment": summary_obj.sentiment,
            "follow_ups": summary_obj.follow_ups,
            "summary_text": summary_obj.summary_text
        }

    turns_list = [
        CallTurnSchema(
            id=t.id,
            call_id=t.call_id,
            seq=t.seq,
            speaker=t.speaker,
            text=t.text,
            language=t.language,
            started_at=t.started_at,
            ended_at=t.ended_at,
            interrupted=t.interrupted,
            used_chunk_ids=t.used_chunk_ids,
            latency_ms=t.latency_ms
        ) for t in call.turns
    ]

    events_list = [
        CallEventSchema(
            id=e.id,
            call_id=e.call_id,
            event_type=e.event_type,
            payload=e.payload,
            timestamp=e.timestamp
        ) for e in call.events
    ]

    return CallDetailResponse(
        id=call.id,
        tenant_id=call.tenant_id,
        room_name=call.room_name,
        started_at=call.started_at,
        ended_at=call.ended_at,
        language=call.language,
        primary_intent=call.primary_intent,
        verified=call.verified,
        verify_attempts=call.verify_attempts,
        outcome=call.outcome,
        escalated_at=call.escalated_at,
        human_agent_id=call.human_agent_id,
        ai_talk_seconds=call.ai_talk_seconds,
        human_talk_seconds=call.human_talk_seconds,
        turns=turns_list,
        events=events_list,
        summary=summary_dict
    )


@router.post("/{call_id}/converse", response_model=ConverseResponse)
async def converse(call_id: str, req: ConverseRequest, db: AsyncSession = Depends(get_db)):
    """
    Process a caller utterance through the full LangGraph orchestrator:
    language detection → intent classification → escalation check →
    KB grounded answer / tool execution → AI response.
    """
    start_time = time.time()

    # 1. Verify call exists
    stmt = select(Call).where(Call.id == call_id)
    res = await db.execute(stmt)
    call = res.scalars().first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # 2. Load tenant config
    tenant_cfg = await TenantService.get_tenant_config(db, req.tenant_id)
    if not tenant_cfg:
        raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' config not found")

    # 3. Build CallState from request
    call_state = CallState(
        call_id=call_id,
        tenant_id=req.tenant_id,
        language=req.language,
        transcript=req.transcript,
        verified=False,
    )

    # 4. Run LangGraph orchestrator turn
    orchestrator = CallGraphOrchestrator(tenant_cfg)
    updated_state = await orchestrator.run_turn(call_state, req.text, db_session=db)

    # 5. Persist the caller + AI turns in DB
    turn_seq_stmt = select(CallTurn).where(CallTurn.call_id == call_id)
    turn_res = await db.execute(turn_seq_stmt)
    existing_turns = list(turn_res.scalars().all())
    next_seq = len(existing_turns) + 1

    now = datetime.utcnow()

    # Caller turn
    caller_turn = CallTurn(
        id=f"turn_{uuid.uuid4().hex[:10]}",
        call_id=call_id,
        seq=next_seq,
        speaker="caller",
        text=req.text,
        language=req.language,
        started_at=now,
        ended_at=now,
    )
    db.add(caller_turn)

    end_time = time.time()
    latency_ms = round((end_time - start_time) * 1000, 1)

    # AI turn
    ai_turn = CallTurn(
        id=f"turn_{uuid.uuid4().hex[:10]}",
        call_id=call_id,
        seq=next_seq + 1,
        speaker="ai",
        text=updated_state.ai_response,
        language=updated_state.language,
        started_at=now,
        ended_at=datetime.utcnow(),
        used_chunk_ids=updated_state.used_chunk_ids,
        latency_ms=latency_ms,
    )
    db.add(ai_turn)

    # Update call language if changed
    call.language = updated_state.language
    if updated_state.intent:
        call.primary_intent = updated_state.intent

    await db.commit()

    return ConverseResponse(
        ai_response=updated_state.ai_response,
        language=updated_state.language,
        intent=updated_state.intent,
        intent_confidence=updated_state.intent_confidence,
        verified=updated_state.verified,
        escalated=updated_state.status == "escalated",
        escalation_reason=updated_state.escalation_reason,
        sentiment=updated_state.sentiment,
        used_chunk_ids=updated_state.used_chunk_ids,
        tool_results=updated_state.tool_results,
        latency_ms=latency_ms,
    )

