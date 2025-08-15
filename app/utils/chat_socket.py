import logging
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from typing import Dict, List
from app.db.session import get_session
from app.db.models import User
from app.services.auth_service import get_current_user
from app.services.chat_service import get_room_messages, send_message
from app.utils.templates import templates

logger = logging.getLogger("app.utils.chat_socket")

class WebSocketManager:
    def __init__(self):
        # Active connections per room_id
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        """Accept WebSocket and add to the active connections for the room."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(f"WebSocket connected for room {room_id}. Total connections: {len(self.active_connections[room_id])}")

    def disconnect(self, room_id: int, websocket: WebSocket):
        """Remove WebSocket connection from the room."""
        self.active_connections[room_id].remove(websocket)
        logger.info(f"WebSocket disconnected for room {room_id}. Remaining connections: {len(self.active_connections.get(room_id, []))}")
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
            logger.info(f"No more connections for room {room_id}, removed from active connections.")

    async def broadcast(self, room_id: int, content: str):
        """Send the message content to all clients connected to the room."""
        connections = self.active_connections.get(room_id, [])
        logger.info(f"Broadcasting message to {len(connections)} clients in room {room_id}")
        for connection in connections:
            try:
                await connection.send_text(content)
            except Exception as e:
                logger.error(f"Failed to send message to a client in room {room_id}: {e}")

manager = WebSocketManager()

async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    WebSocket endpoint for chat room.
    Handles:
    - Accepting connection
    - Receiving messages
    - Saving messages to DB
    - Broadcasting updated message list HTML to all clients
    """
    await manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from user {current_user.username} in room {room_id}: {data}")

            # Save message to DB
            send_message(room_id, data, current_user, session)

            # Fetch updated messages list
            messages = get_room_messages(room_id, current_user, session)

            # Render HTML partial for updated messages
            html_content = templates.get_template("partials/message_list.html").render(messages=messages)

            # Broadcast updated messages to all connected clients
            await manager.broadcast(room_id, html_content)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected by user {current_user.username} in room {room_id}")
        manager.disconnect(room_id, websocket)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint: {e}")
        manager.disconnect(room_id, websocket)