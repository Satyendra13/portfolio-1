from typing import Dict, List, Set
from fastapi import WebSocket
import json

class AgentWebSocketManager:
    def __init__(self):
        # Maps tenant_id -> set of active WebSockets
        self.tenant_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, tenant_id: str, websocket: WebSocket):
        await websocket.accept()
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(websocket)

    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self.tenant_connections:
            self.tenant_connections[tenant_id].discard(websocket)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        if tenant_id in self.tenant_connections:
            dead_sockets = set()
            for ws in self.tenant_connections[tenant_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.tenant_connections[tenant_id].discard(ws)

agent_ws_manager = AgentWebSocketManager()
