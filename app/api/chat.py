from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.db.session import get_session
from app.services.chat_service import create_room, get_user_rooms, send_message, get_room_messages
from app.utils.auth import get_current_user
from app.db.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

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
