import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.db.session import get_db
from backend.app.models.tenant import Tenant
from backend.app.models.call import Call, CallTurn
from backend.app.schemas.call import (
    CallStartRequest,
    CallResponse,
    CallTurnCreate,
    CallTurnResponse,
    CallTranscriptResponse,
)

router = APIRouter(prefix="/calls", tags=["Calls"])

import asyncio
import logging
from fastapi import BackgroundTasks

logger = logging.getLogger("asistline.calls")

active_call_workers = {}

async def _launch_ai_worker(room_name: str, call_id: str, tenant_id: str, language: str):
    if call_id in active_call_workers and getattr(active_call_workers[call_id], "running", False):
        logger.info(f"Worker already running for call {call_id}. Skipping duplicate launch.")
        return
    try:
        from backend.agent_worker.worker import AsistLineVoiceWorker
        worker = AsistLineVoiceWorker(room_name, call_id, tenant_id, language)
        active_call_workers[call_id] = worker
        await worker.start()
    except Exception as e:
        logger.error(f"Error running AI voice worker for room {room_name}: {e}")

@router.post("/start", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def start_call(
    payload: CallStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Verify tenant
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == payload.tenant_id))
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    room_name = f"asistline-{tenant.id[:8]}-{uuid.uuid4().hex[:8]}"
    customer_sess_id = payload.customer_session_id or f"sess-{uuid.uuid4().hex[:12]}"

    call = Call(
        tenant_id=payload.tenant_id,
        livekit_room_name=room_name,
        customer_session_id=customer_sess_id,
        status="ai_active",
        language=payload.language or "en",
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)

    # Spawn AI voice agent worker for this LiveKit room
    background_tasks.add_task(
        _launch_ai_worker,
        room_name,
        call.id,
        tenant.id,
        call.language,
    )

    return call

@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@router.get("/{call_id}/transcript", response_model=CallTranscriptResponse)
async def get_call_transcript(call_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Call).options(selectinload(Call.turns)).where(Call.id == call_id)
    )
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return CallTranscriptResponse(
        call_id=call.id,
        tenant_id=call.tenant_id,
        status=call.status,
        started_at=call.started_at,
        turns=[
            CallTurnResponse(
                id=turn.id,
                call_id=turn.call_id,
                speaker=turn.speaker,
                text=turn.text,
                metadata_json=turn.metadata_json,
                timestamp=turn.timestamp,
            )
            for turn in call.turns
        ],
    )

@router.post("/{call_id}/turns", response_model=CallTurnResponse, status_code=status.HTTP_201_CREATED)
async def add_call_turn(
    call_id: str,
    payload: CallTurnCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    turn = CallTurn(
        call_id=call.id,
        speaker=payload.speaker,
        text=payload.text,
        metadata_json=payload.metadata_json,
    )
    db.add(turn)
    await db.commit()
    await db.refresh(turn)
    return turn

@router.post("/{call_id}/end", response_model=CallResponse)
async def end_call(call_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = "ended"
    call.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(call)

    # Disconnect AI worker if active
    if call_id in active_call_workers:
        try:
            worker = active_call_workers.pop(call_id)
            await worker.stop()
        except Exception as e:
            logger.warning(f"Error stopping worker for call {call_id}: {e}")

    return call
