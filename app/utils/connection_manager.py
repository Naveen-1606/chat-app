# app/utils/connection_manager.py
from typing import Dict, List
from fastapi import WebSocket
from app.db.models import User


class ConnectionManager:
    def __init__(self):
        # { room_id: [ (websocket, user), ... ] }
        self.active_connections: Dict[int, List[tuple[WebSocket, User]]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user: User):
        """Register a new websocket connection for a user in a room."""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, user))

    def disconnect(self, websocket: WebSocket, room_id: int, user: User):
        """Remove a websocket connection when user disconnects."""
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, u) for ws, u in self.active_connections[room_id] if ws != websocket
            ]
            # Clean up empty room
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        """Send a message to all users in a room."""
        if room_id not in self.active_connections:
            return
        dead_connections = []
        for ws, _ in self.active_connections[room_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        # Cleanup dead connections
        if dead_connections:
            self.active_connections[room_id] = [
                (ws, u) for ws, u in self.active_connections[room_id] if ws not in dead_connections
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    def get_users_in_room(self, room_id: int) -> list[User]:
        """Return list of connected users in a room."""
        return [u for _, u in self.active_connections.get(room_id, [])]
    

    def get_user_ws(self, room_id: int, user_id: int):
        """Return the WebSocket for a specific user in a room (if connected)."""
        for ws, user in self.active_connections.get(room_id, []):
            if user.id == user_id:
                return ws
        return None

