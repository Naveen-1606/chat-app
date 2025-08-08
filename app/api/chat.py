from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import ChatRoom, Message

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/room", response_model=ChatRoom)
def create_room(name: str, session: Session = Depends(get_session)):
    existing = session.exec(select(ChatRoom).where(ChatRoom.name == name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")
    
    room = ChatRoom(name=name)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room

@router.get("/rooms", response_model=list[ChatRoom])
def get_rooms(session: Session = Depends(get_session)):
    return session.exec(select(ChatRoom)).all()

@router.get("/room/{room_id}/messages", response_model=list[Message])
def get_room_messages(room_id: int, session: Session = Depends(get_session)):
    messages = session.exec(
        select(Message).where(Message.room_id == room_id).order_by(Message.timestamp)
    ).all()
    return messages
