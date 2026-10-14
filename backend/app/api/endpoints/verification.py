from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.models.call import Call
from backend.app.models.verification import Verification
from backend.app.schemas.verification import VerificationRequest, VerificationResponse

router = APIRouter(prefix="/verify", tags=["Verification"])

# Seeded Mock Order Database for testing verification flows
MOCK_ORDERS: Dict[str, Dict[str, Any]] = {
    "10492": {
        "phone_last4": "4821",
        "customer_name": "Sarah Connor",
        "order_status": "Out for delivery",
        "delivery_date": "Today by 6:00 PM PST",
        "items_count": 2,
        "total_amount": "$149.99",
    },
    "88231": {
        "phone_last4": "1994",
        "customer_name": "James Rodriguez",
        "order_status": "Shipped via FedEx",
        "delivery_date": "Tomorrow, Oct 15",
        "items_count": 1,
        "total_amount": "$89.50",
    },
    "55120": {
        "phone_last4": "3340",
        "customer_name": "David Miller",
        "order_status": "Processing - Warehouse",
        "delivery_date": "Oct 18",
        "items_count": 3,
        "total_amount": "$320.00",
    },
}

@router.post("", response_model=VerificationResponse)
async def verify_caller(payload: VerificationRequest, db: AsyncSession = Depends(get_db)):
    # Verify call exists if call_id provided
    if payload.call_id and payload.call_id != "test-call":
        call_res = await db.execute(select(Call).where(Call.id == payload.call_id))
        call = call_res.scalar_one_or_none()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

    order_info = MOCK_ORDERS.get(payload.order_id.strip())
    is_verified = False
    details = {}
    message = "Verification failed: Order ID not found or phone number does not match."

    if order_info and order_info["phone_last4"] == payload.phone_last4.strip():
        is_verified = True
        details = order_info
        message = f"Caller verified successfully as {order_info['customer_name']}."

    # Record verification entry
    verification_record = Verification(
        call_id=payload.call_id,
        tenant_id=payload.tenant_id,
        order_id=payload.order_id,
        phone_last4=payload.phone_last4,
        verified_bool=is_verified,
        verified_at=datetime.now(timezone.utc) if is_verified else None,
        details=details if is_verified else None,
    )
    db.add(verification_record)
    await db.commit()

    return VerificationResponse(
        verified=is_verified,
        order_id=payload.order_id,
        phone_last4=payload.phone_last4,
        customer_name=details.get("customer_name"),
        order_status=details.get("order_status"),
        delivery_date=details.get("delivery_date"),
        items_count=details.get("items_count"),
        total_amount=details.get("total_amount"),
        message=message,
    )
