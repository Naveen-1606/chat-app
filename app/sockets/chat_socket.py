from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from typing import Dict, List
from app.db.session import get_session
from app.db.models import User
from app.services.auth_service import get_current_user
from app.services.chat_service import get_room_messages, send_message
from starlette.requests import Request

router = APIRouter(prefix="/ws", tags=["websocket"])

from app.utils.templates import templates

# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, room_id: int, content: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(content)

manager = WebSocketManager()

@router.websocket("/chat/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()

            # Save the message
            send_message(room_id, data, current_user, session)

            # Get updated messages
            messages = get_room_messages(room_id, current_user, session)

            # Render HTML partial
            html_content = templates.get_template("partials/message_list.html").render(
                messages=messages
            )

            # Broadcast updated HTML to all clients in the room
            await manager.broadcast(room_id, html_content)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
