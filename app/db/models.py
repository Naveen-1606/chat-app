from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr


class UserChatRoom(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    room_id: int = Field(foreign_key="chatroom.id", primary_key=True)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    chatrooms: List["ChatRoom"] = Relationship(back_populates="members", link_model=UserChatRoom)
    messages: List["Message"] = Relationship(back_populates="sender")

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

class ChatRoom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    members: List["User"] = Relationship(back_populates="chatrooms", link_model=UserChatRoom)
    messages: List["Message"] = Relationship(back_populates="room")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    sender_id: int = Field(foreign_key="user.id")
    room_id: int = Field(foreign_key="chatroom.id")

    sender: "User" = Relationship(back_populates="messages")
    room: "ChatRoom" = Relationship(back_populates="messages")