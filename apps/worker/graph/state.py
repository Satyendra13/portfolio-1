from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CallState(BaseModel):
    """
    CallState schema for LangGraph orchestrator checkpointer.
    """
    call_id: str
    tenant_id: str
    language: str = "en"
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    verified: bool = False
    verify_attempts: int = 0
    caller_profile: Dict[str, Any] = Field(default_factory=dict)
    pending_action: Optional[Dict[str, Any]] = None
    awaiting_confirmation: bool = False
    kb_hits: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_reason: Optional[str] = None
    sentiment: str = "neutral"
    turn_count: int = 0
    status: str = "active"
    ai_response: str = ""
    used_chunk_ids: List[str] = Field(default_factory=list)
