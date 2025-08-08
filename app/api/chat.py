from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session
from typing import List
from app.utils.ws_manager import WebSocketManager
import json
from app.db.models import Message
from datetime import datetime

from app.db.session import get_session
from app.services.chat_service import create_room, get_user_rooms, send_message, get_room_messages
from app.utils.auth import get_current_user
from app.db.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

ws_manager = WebSocketManager()


class RoomCreateInput(BaseModel):
    name: str

@router.post("/rooms")
def create_chat_room(data: RoomCreateInput, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return create_room(data.name, current_user, session)

@router.get("/rooms")
def get_rooms(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_user_rooms(current_user, session)

class MessageInput(BaseModel):
    content: str

@router.post("/rooms/{room_id}/messages")
def send_msg(room_id: int, data: MessageInput, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return send_message(room_id, data.content, current_user, session)

@router.get("/rooms/{room_id}/messages")
def get_msgs(room_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_room_messages(room_id, current_user, session)


@router.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user: User = Depends(get_current_user)):
    await ws_manager.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = Message(
                content=data,
                timestamp=datetime.utcnow(),
                sender_id=user.id,
                room_id=room_id
            )
            session = next(get_session())
            session.add(msg)
            session.commit()
            await ws_manager.broadcast(room_id, f"{user.username}: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(room_id, websocket)
