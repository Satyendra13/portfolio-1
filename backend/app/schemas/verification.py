from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class VerificationRequest(BaseModel):
    call_id: str
    tenant_id: str
    order_id: str
    phone_last4: str

class VerificationResponse(BaseModel):
    verified: bool
    order_id: str
    phone_last4: str
    customer_name: Optional[str] = None
    order_status: Optional[str] = None
    delivery_date: Optional[str] = None
    items_count: Optional[int] = None
    total_amount: Optional[str] = None
    message: str
