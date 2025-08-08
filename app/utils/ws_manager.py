from typing import Dict, List
from fastapi import WebSocket
from collections import defaultdict

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: str):
        for connection in self.active_connections.get(room_id, []):
            await connection.send_text(message)
