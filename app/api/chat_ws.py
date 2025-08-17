from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlmodel import Session

from app.utils.connection_manager import ConnectionManager
from app.db.session import get_session
from app.services.chat_service import send_message, get_room_messages, is_user_member
from app.services.auth_service import get_current_user_ws
from app.db.models import User
from datetime import datetime

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_ws),
):
    # Accept the websocket connection
    await websocket.accept()

    # Check if user is a member of this room
    if not is_user_member(current_user.id, room_id, session):
        await websocket.send_json({
            "type": "error",
            "message": "You are not a member of this room."
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Register connection
    await manager.connect(websocket, room_id, current_user)

    # Send recent chat history to the newly joined user
    messages = get_room_messages(room_id, current_user, session)
    await websocket.send_json(
        {
            "type": "history",
            "messages": [
                {
                    "id": m.id,
                    "sender": m.sender.username,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in messages
            ],
        }
    )

    # Broadcast "user joined"
    await manager.broadcast(
        room_id,
        {
            "type": "system",
            "room_id": room_id,
            "message": f"{current_user.username} joined the room.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    try:
        while True:
            # Wait for messages from this client
            data = await websocket.receive_json()
            content = data.get("content")

            if not content:
                continue

            # Save message in DB
            msg = send_message(room_id, content, current_user, session)

            # Broadcast to everyone in the room
            await manager.broadcast(
                room_id,
                {
                    "type": "chat_message",
                    "room_id": room_id,
                    "id": msg.id,
                    "sender": msg.sender.username,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                },
            )

    except WebSocketDisconnect:
        # Cleanup connection
        manager.disconnect(websocket, room_id, current_user)

        # Broadcast "user left"
        await manager.broadcast(
            room_id,
            {
                "type": "system",
                "room_id": room_id,
                "message": f"{current_user.username} left the room.",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
