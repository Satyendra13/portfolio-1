from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class EscalationCreate(BaseModel):
    call_id: str
    tenant_id: str
    reason: str
    summary: str

class EscalationAccept(BaseModel):
    agent_id: str

class EscalationResponse(BaseModel):
    id: str
    call_id: str
    tenant_id: str
    reason: str
    summary: str
    status: str
    accepted_by_agent_id: Optional[str] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EscalationAcceptResponse(BaseModel):
    escalation: EscalationResponse
    livekit_token: str
    livekit_url: str
    room_name: str
