from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr


class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str   # <-- only exists here


class UserChatRoom(SQLModel, table=True):
    __tablename__ = "user_chatrooms"   # ✅ explicit
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    room_id: int = Field(foreign_key="chatrooms.id", primary_key=True)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_verified: bool = False

    chatrooms: List["ChatRoom"] = Relationship(back_populates="members", link_model=UserChatRoom)
    messages: List["Message"] = Relationship(back_populates="sender")


class ChatRoom(SQLModel, table=True):
    __tablename__ = "chatrooms"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    members: List["User"] = Relationship(back_populates="chatrooms", link_model=UserChatRoom)
    messages: List["Message"] = Relationship(back_populates="room")




class Message(SQLModel, table=True):
    __tablename__ = "messages"   # ✅ plural, explicit
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    sender_id: int = Field(foreign_key="users.id")
    room_id: int = Field(foreign_key="chatrooms.id")

    sender: "User" = Relationship(back_populates="messages")
    room: "ChatRoom" = Relationship(back_populates="messages")
    seen_by: list["MessageSeen"] = Relationship(back_populates="message")


class MessageSeen(SQLModel, table=True):
    __tablename__ = "message_seen"   # ✅ explicit
    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="messages.id", ondelete="CASCADE")
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")
    seen_at: datetime = Field(default_factory=datetime.utcnow)

    message: Optional["Message"] = Relationship(back_populates="seen_by")
    user: Optional["User"] = Relationship()