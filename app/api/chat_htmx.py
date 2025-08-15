from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.chat_service import (
    get_user_rooms, get_room, get_room_messages, create_room, send_message
)
from app.services.auth_service import get_current_user
from app.db.models import User, ChatRoom, UserChatRoom
from app.db.session import get_session
from app.utils.templates import templates
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Helper to check membership
def is_user_member(user_id: int, room_id: int, session: Session = Depends(get_session)) -> bool:
    return session.exec(
        select(UserChatRoom)
        .where(UserChatRoom.user_id == user_id)
        .where(UserChatRoom.room_id == room_id)
    ).first() is not None


@router.get("")
def chat(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    rooms = session.exec(select(ChatRoom)).all()
    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": None,
            "messages": [],
            "is_member": False
        }
    )

@router.get("/rooms/{room_id}")
def chat_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)

    if not selected_room:
        raise HTTPException(status_code=404, detail="Room not found")

    messages = selected_room.messages or []

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": selected_room,
            "messages": messages,
            "is_member": is_user_member(current_user.id, selected_room.id, session)
        }
    )


@router.get("/rooms", response_class=HTMLResponse)
def get_room(room_id: int, current_user: User, session: Session = Depends(get_session)):
    return session.exec(
        select(ChatRoom).where(ChatRoom.id == room_id)
    ).first()


@router.post("/rooms")
def create_new_room(
    request: Request,
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    create_room(name, current_user, session)
    return RedirectResponse(url="/chat", status_code=303)


@router.post("/rooms/{room_id}/messages")
def post_message(
    request: Request,
    room_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    send_message(room_id, content, current_user, session)
    messages = get_room_messages(room_id, current_user, session)
    return templates.TemplateResponse(
        "partials/message_list.html",
        {
            "request": request,  # include this!
            "messages": messages,
        },
    )


@router.get("/rooms/{room_id}/messages")
def get_messages_partial(
    request: Request,
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    messages = get_room_messages(room_id, current_user, session)
    return templates.TemplateResponse(
        "partials/message_list.html",
        {
            "request": request,  # include this!
            "messages": messages,
        },
    )

# Join a room
@router.post("/rooms/{room_id}/join")
def join_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not is_user_member(current_user.id, room_id, session):
        membership = UserChatRoom(user_id=current_user.id, room_id=room_id)
        session.add(membership)
        session.commit()

    return RedirectResponse(url=f"/chat/rooms/{room_id}", status_code=303)


@router.post("/rooms/{room_id}/leave")
def leave_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    membership = session.exec(
        select(UserChatRoom)
        .where(UserChatRoom.user_id == current_user.id)
        .where(UserChatRoom.room_id == room_id)
    ).first()

    if membership:
        session.delete(membership)
        session.commit()

    return RedirectResponse(url=f"/chat/rooms/{room_id}", status_code=303)