from sqlmodel import Session, select
from app.db.models import ChatRoom, Message, UserChatRoom
from app.db.models import User
from fastapi import HTTPException

def create_room(name: str, user: User, session: Session):
    room = ChatRoom(name=name)
    session.add(room)
    session.commit()
    session.refresh(room)

    # Link user to room
    link = UserChatRoom(user_id=user.id, room_id=room.id)
    session.add(link)
    session.commit()
    return room

def get_user_rooms(user: User, session: Session):
    stmt = select(ChatRoom).join(UserChatRoom).where(UserChatRoom.user_id == user.id)
    return session.exec(stmt).all()

def send_message(room_id: int, content: str, sender: User, session: Session):
    # Check membership
    member_stmt = select(UserChatRoom).where(
        (UserChatRoom.user_id == sender.id) & (UserChatRoom.room_id == room_id)
    )
    if not session.exec(member_stmt).first():
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    msg = Message(content=content, sender_id=sender.id, room_id=room_id)
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg

def get_room_messages(room_id: int, user: User, session: Session):
    # Check membership
    member_stmt = select(UserChatRoom).where(
        (UserChatRoom.user_id == user.id) & (UserChatRoom.room_id == room_id)
    )
    if not session.exec(member_stmt).first():
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    stmt = select(Message).where(Message.room_id == room_id).order_by(Message.timestamp)
    return session.exec(stmt).all()
