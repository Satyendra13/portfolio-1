from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ScriptConfig(BaseModel):
    greeting: Dict[str, str]
    not_found: Dict[str, str]
    closing: Dict[str, str]


class VerificationConfig(BaseModel):
    factors: List[str]
    max_attempts: int = 3


class EscalationRulesConfig(BaseModel):
    sentiment_threshold: float = -0.6
    keywords: List[str] = Field(default_factory=list)
    max_kb_misses: int = 2


class TenantAdapterConfig(BaseModel):
    type: str = "mock_rest"
    base_url: str


class TenantConfigSchema(BaseModel):
    tenant_id: str
    display_name: str
    supported_languages: List[str]
    voices: Dict[str, str]
    script: ScriptConfig
    verification: VerificationConfig
    automatable_intents: List[str]
    escalation_rules: EscalationRulesConfig
    kb_min_score: float = 0.55
    adapter: TenantAdapterConfig
    baseline_human_cost_per_call: float = 4.50
    ai_cost_per_min: float = 0.12
    human_cost_per_min: float = 0.75
    baseline_aht_seconds: float = 360.0


class TenantResponse(BaseModel):
    id: str
    display_name: str
    config: Optional[Dict[str, Any]] = None
