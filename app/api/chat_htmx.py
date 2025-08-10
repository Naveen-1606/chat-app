from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlmodel import Session
from fastapi.responses import RedirectResponse
from app.services.chat_service import (
    get_user_rooms, get_room, get_room_messages, create_room, send_message
)
from app.services.auth_service import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.utils.templates import templates
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("")
def chat(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    logger.info(f"User '{current_user.username}' accessed /chat")

    rooms = get_user_rooms(current_user, session)

    logger.info(f"Rooms found for user '{current_user.username}': {[room.name for room in rooms]}")

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": None,
            "messages": [],
        },
    )


@router.get("/rooms/{room_id}")
def chat_room(
    request: Request,
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    room = get_room(room_id, current_user, session)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or access denied")

    rooms = get_user_rooms(current_user, session)
    messages = get_room_messages(room_id, current_user, session)

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": room,
            "messages": messages,
        },
    )


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

