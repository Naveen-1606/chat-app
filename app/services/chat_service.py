from sqlmodel import Session, select
from app.db.models import ChatRoom, Message, UserChatRoom, MessageSeen
from app.db.models import User
from fastapi import HTTPException
import logging
from datetime import datetime

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
    rooms = session.exec(stmt).all()
    logging.info(f"get_user_rooms: Found {len(rooms)} rooms for user '{user.username}'")
    return rooms

def get_room(room_id: int, user: User, session: Session):
    # Verify that the user is a member of the room
    member_stmt = select(UserChatRoom).where(
        (UserChatRoom.user_id == user.id) & (UserChatRoom.room_id == room_id)
    )
    if not session.exec(member_stmt).first():
        return None  # Or raise HTTPException if you prefer

    # Fetch the ChatRoom
    room = session.get(ChatRoom, room_id)
    return room


def send_message(room_id: int, content: str, sender: User, session: Session):
    # 1. Check if room exists
    room = session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Check membership
    member_stmt = select(UserChatRoom).where(
        (UserChatRoom.user_id == sender.id) & (UserChatRoom.room_id == room_id)
    )
    if not session.exec(member_stmt).first():
        raise HTTPException(status_code=403, detail="Not a member of this room")

    # 3. Create message
    msg = Message(
        content=content,
        sender_id=sender.id,
        room_id=room_id,
        timestamp=datetime.utcnow()
    )

    # 4. Save to DB
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

# Helper to check membership
def is_user_member(user_id: int, room_id: int, session: Session) -> bool:
    return session.exec(
        select(UserChatRoom)
        .where(UserChatRoom.user_id == user_id)
        .where(UserChatRoom.room_id == room_id)
    ).first() is not None


def join_room_service(room_id: int, user_id: int, session: Session) -> ChatRoom:
    # 1. Check if room exists
    room = session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Check if user is already a member
    membership = session.exec(
        select(UserChatRoom).where(
            (UserChatRoom.room_id == room_id) & (UserChatRoom.user_id == user_id)
        )
    ).first()

    if not membership:
        # Add membership
        membership = UserChatRoom(user_id=user_id, room_id=room_id)
        session.add(membership)
        session.commit()
    
    return room


def leave_room_service(room_id: int, user_id: int, session: Session) -> ChatRoom:
    # 1. Check if room exists
    room = session.get(ChatRoom, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Check if user is a member
    membership = session.exec(
        select(UserChatRoom).where(
            (UserChatRoom.room_id == room_id) & (UserChatRoom.user_id == user_id)
        )
    ).first()

    if membership:
        session.delete(membership)
        session.commit()

    return room


def get_membership_map(user_id: int, session: Session) -> dict[int, bool]:
    """
    Returns a map {room_id: True/False} indicating whether the user is a member of each room.
    """
    # Get all room memberships for the user
    stmt = select(UserChatRoom.room_id).where(UserChatRoom.user_id == user_id)
    memberships = session.exec(stmt).all()  # list of room_ids

    # Build map: room_id -> True/False
    membership_map = {room.id: (room.id in memberships) for room in session.exec(select(ChatRoom)).all()}
    return membership_map


def mark_message_seen(message_id: int, user_id: int, session: Session) -> MessageSeen | None:
    """Mark a message as seen by a user, return the MessageSeen entry (or None if already seen)."""

    seen_entry = session.exec(
        select(MessageSeen).where(
            (MessageSeen.message_id == message_id) &
            (MessageSeen.user_id == user_id)
        )
    ).first()

    if seen_entry:
        return None  # Already marked as seen

    seen_entry = MessageSeen(
        message_id=message_id,
        user_id=user_id,
        seen_at=datetime.utcnow()
    )
    session.add(seen_entry)
    session.commit()
    session.refresh(seen_entry)
    return seen_entry