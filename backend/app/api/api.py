from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.api.endpoints import tenants, kb, calls, livekit, escalations, verification
from backend.app.services.websocket_manager import agent_ws_manager

api_router = APIRouter()

api_router.include_router(tenants.router)
api_router.include_router(kb.router)
api_router.include_router(calls.router)
api_router.include_router(livekit.router)
api_router.include_router(escalations.router)
api_router.include_router(verification.router)

@api_router.websocket("/ws/agent/{tenant_id}")
async def agent_notifications_websocket(websocket: WebSocket, tenant_id: str):
    await agent_ws_manager.connect(tenant_id, websocket)
    try:
        while True:
            # Keep socket alive and receive client pings/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        agent_ws_manager.disconnect(tenant_id, websocket)
    except Exception:
        agent_ws_manager.disconnect(tenant_id, websocket)
