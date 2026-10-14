from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CallStartRequest(BaseModel):
    tenant_id: str
    customer_session_id: Optional[str] = None
    language: Optional[str] = "en"

class CallTurnCreate(BaseModel):
    speaker: str # customer, ai, human
    text: str
    metadata_json: Optional[Dict[str, Any]] = None

class CallTurnResponse(BaseModel):
    id: str
    call_id: str
    speaker: str
    text: str
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class CallResponse(BaseModel):
    id: str
    tenant_id: str
    livekit_room_name: str
    customer_session_id: str
    status: str
    language: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CallTranscriptResponse(BaseModel):
    call_id: str
    tenant_id: str
    status: str
    started_at: datetime
    turns: List[CallTurnResponse]
