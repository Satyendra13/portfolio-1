from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ScriptConfigSchema(BaseModel):
    welcome_message: Dict[str, str] = Field(
        default_factory=lambda: {
            "en": "Thank you for calling support. This call may be recorded for quality and training purposes, and you are speaking with an AI assistant. How can I help you today?",
            "hi": "सपोर्ट में कॉल करने के लिए धन्यवाद। गुणवत्ता और प्रशिक्षण के लिए इस कॉल को रिकॉर्ड किया जा सकता है, और आप एक एआई सहायक से बात कर रहे हैं। आज मैं आपकी क्या मदद कर सकता हूँ?"
        }
    )
    languages: List[str] = Field(default_factory=lambda: ["en", "hi"])
    escalation_triggers: List[str] = Field(
        default_factory=lambda: ["angry_sentiment", "repeat_failure", "explicit_request", "no_kb_match"]
    )
    verification_required_for: List[str] = Field(
        default_factory=lambda: ["order_status", "refund", "account_change"]
    )
    voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM")  # Default ElevenLabs Rachel/generic voice

class EscalationRulesSchema(BaseModel):
    max_retries_before_escalate: int = 1
    queue_timeout_seconds: int = 45
    fallback_action: str = "callback_offer"  # callback_offer or voicemail
    allowed_agent_roles: List[str] = Field(default_factory=lambda: ["tier1", "tier2"])

class TenantCreate(BaseModel):
    name: str
    script_config: Optional[ScriptConfigSchema] = None
    escalation_rules: Optional[EscalationRulesSchema] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    script_config: Optional[Dict[str, Any]] = None
    escalation_rules: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    script_config: Dict[str, Any]
    escalation_rules: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
