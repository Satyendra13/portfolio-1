from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HandoffPacketSchema(BaseModel):
    call_id: str
    tenant_id: str
    language: str = "en"
    intent: Optional[str] = None
    reason: str
    verified: bool = False
    caller: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    kb_answers_given: List[Dict[str, Any]] = Field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    sentiment: str = "neutral"


class EscalationResponse(BaseModel):
    id: str
    call_id: str
    tenant_id: str
    status: str  # queued | accepted | resolved | callback_offered
    summary_json: HandoffPacketSchema
    created_at: datetime
    accepted_at: Optional[datetime] = None
    human_agent_id: Optional[str] = None


class EscalationAcceptResponse(BaseModel):
    escalation_id: str
    call_id: str
    agent_token: str
    livekit_url: str
    handoff_packet: HandoffPacketSchema


class EscalationFeedbackRequest(BaseModel):
    rating: str  # appropriate | could_have_been_automated | wrong_queue
    comments: Optional[str] = None
