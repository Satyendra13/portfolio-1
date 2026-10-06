from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class CallStartRequest(BaseModel):
    tenant_id: str
    language: str = "en"
    caller_name: Optional[str] = "Caller"


class CallStartResponse(BaseModel):
    call_id: str
    room_name: str
    caller_token: str
    livekit_url: str


class CallTurnSchema(BaseModel):
    id: str
    call_id: str
    seq: int
    speaker: str  # caller | ai | human
    text: str
    language: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    interrupted: bool = False
    used_chunk_ids: Optional[List[str]] = None
    latency_ms: Optional[float] = None


class CallEventSchema(BaseModel):
    id: str
    call_id: str
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    timestamp: datetime


class ConverseRequest(BaseModel):
    """Caller sends text; backend runs LangGraph turn and returns AI response."""
    tenant_id: str
    text: str
    language: str = "en"
    transcript: List[Dict[str, Any]] = []


class ConverseResponse(BaseModel):
    """AI response after a full LangGraph orchestrator turn."""
    ai_response: str
    language: str
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    verified: bool = False
    escalated: bool = False
    escalation_reason: Optional[str] = None
    sentiment: str = "neutral"
    used_chunk_ids: List[str] = []
    tool_results: List[Dict[str, Any]] = []
    latency_ms: float = 0.0


class CallDetailResponse(BaseModel):
    id: str
    tenant_id: str
    room_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    language: str
    primary_intent: Optional[str] = None
    verified: bool
    verify_attempts: int
    outcome: str
    escalated_at: Optional[datetime] = None
    human_agent_id: Optional[str] = None
    ai_talk_seconds: float
    human_talk_seconds: float
    turns: List[CallTurnSchema] = []
    events: List[CallEventSchema] = []
    summary: Optional[Dict[str, Any]] = None
