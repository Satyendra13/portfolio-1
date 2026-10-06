from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="AsistLine AI Mock Client Backends")

# Mock CRM/OMS Database
ORDERS = {
    "acme_telecom": {
        "48213": {"order_id": "48213", "status": "Shipped", "item": "5G SIM Kit", "delivery_date": "2026-09-29"},
        "10042": {"order_id": "10042", "status": "Processing", "item": "Fiber Broadband Router", "delivery_date": "2026-10-01"}
    },
    "quickcart": {
        "48213": {"order_id": "48213", "status": "Out for Delivery", "item": "Wireless Headphones", "delivery_date": "Today by 5 PM"},
        "9901": {"order_id": "9901", "status": "Delivered", "item": "Smart Watch", "delivery_date": "Yesterday"}
    }
}

VERIFICATION_DATA = {
    "acme_telecom": {"order_id": "48213", "phone_last4": "1234"},
    "quickcart": {"order_id": "48213", "phone_last4": "1234"}
}


class VerifyPayload(BaseModel):
    order_id: str
    phone_last4: str


class TicketPayload(BaseModel):
    subject: str
    description: str


class CallbackPayload(BaseModel):
    phone_number: str
    preferred_time: Optional[str] = "ASAP"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Mock Client Backends"}


@app.post("/{tenant_id}/verify")
async def verify_caller(tenant_id: str, payload: VerifyPayload):
    expected = VERIFICATION_DATA.get(tenant_id, {})
    if payload.order_id == expected.get("order_id") and payload.phone_last4 == expected.get("phone_last4"):
        return {"verified": True, "account_id": f"ACC-{tenant_id[:4].upper()}-99"}
    return {"verified": False, "reason": "Factors mismatch"}


@app.get("/{tenant_id}/orders/{order_id}")
async def get_order_status(tenant_id: str, order_id: str):
    tenant_orders = ORDERS.get(tenant_id, {})
    order = tenant_orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/{tenant_id}/tickets")
async def create_ticket(tenant_id: str, payload: TicketPayload):
    import uuid
    ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
    return {
        "ticket_id": ticket_id,
        "tenant_id": tenant_id,
        "subject": payload.subject,
        "status": "open"
    }


@app.post("/{tenant_id}/callbacks")
async def schedule_callback(tenant_id: str, payload: CallbackPayload):
    import uuid
    callback_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
    return {
        "callback_id": callback_id,
        "tenant_id": tenant_id,
        "phone_number": payload.phone_number,
        "status": "scheduled",
        "preferred_time": payload.preferred_time
    }
