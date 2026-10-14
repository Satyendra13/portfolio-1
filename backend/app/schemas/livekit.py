from typing import Optional
from pydantic import BaseModel, Field

class LiveKitTokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None
    role: str = Field(default="customer", description="'customer', 'agent', or 'ai'")
    tenant_id: Optional[str] = None

class LiveKitTokenResponse(BaseModel):
    token: str
    server_url: str
    room_name: str
    participant_identity: str
