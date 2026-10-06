from typing import Protocol, Dict, Any, Optional
import httpx
from apps.api.app.core.config import settings


class TenantToolAdapter(Protocol):
    """Protocol interface for tenant backend adapters (CRM, OMS, ticketing)."""

    async def verify_caller(self, tenant_id: str, factors: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def get_order_status(self, tenant_id: str, order_id: str) -> Dict[str, Any]:
        ...

    async def get_account_info(self, tenant_id: str, account_id: str) -> Dict[str, Any]:
        ...

    async def create_ticket(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def schedule_callback(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MockRestTenantToolAdapter:
    """HTTP client adapter communicating with mock CRM/OMS backends."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.MOCK_BACKENDS_URL

    async def verify_caller(self, tenant_id: str, factors: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{tenant_id}/verify"
        payload = {
            "order_id": factors.get("order_id", ""),
            "phone_last4": factors.get("phone_last4", "")
        }
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        
        # High-fidelity offline fallback for testing
        if factors.get("order_id") == "48213" and factors.get("phone_last4") == "1234":
            return {"verified": True, "account_id": f"ACC-{tenant_id[:4].upper()}-99"}
        return {"verified": False, "reason": "Factors mismatch"}

    async def get_order_status(self, tenant_id: str, order_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{tenant_id}/orders/{order_id}"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass

        # Offline fallback for testing
        if tenant_id == "acme_telecom":
            return {"order_id": order_id, "status": "Shipped", "item": "5G SIM Kit", "delivery_date": "Tomorrow"}
        return {"order_id": order_id, "status": "Out for Delivery", "item": "Wireless Headphones", "delivery_date": "Today by 5 PM"}

    async def get_account_info(self, tenant_id: str, account_id: str) -> Dict[str, Any]:
        return {
            "account_id": account_id,
            "tenant_id": tenant_id,
            "status": "Active",
            "balance_usd": 0.00,
            "plan": "Unlimited Ultra" if tenant_id == "acme_telecom" else "Gold Member"
        }

    async def create_ticket(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{tenant_id}/tickets"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass

        import uuid
        ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
        return {
            "ticket_id": ticket_id,
            "tenant_id": tenant_id,
            "subject": payload.get("subject", "Support Inquiry"),
            "status": "open"
        }

    async def schedule_callback(self, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{tenant_id}/callbacks"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass

        import uuid
        callback_id = f"CB-{uuid.uuid4().hex[:6].upper()}"
        return {
            "callback_id": callback_id,
            "tenant_id": tenant_id,
            "phone_number": payload.get("phone_number", "555-0199"),
            "status": "scheduled",
            "preferred_time": payload.get("preferred_time", "ASAP")
        }
