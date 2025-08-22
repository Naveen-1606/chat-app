from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse
from app.services.chat_service import (
    get_user_rooms, get_room, create_room, join_room_service,
    leave_room_service, get_membership_map
)
from app.services.auth_service import get_current_user
from app.db.models import User, ChatRoom
from app.db.session import get_session
from app.utils.templates import templates

router = APIRouter(prefix="/chat", tags=["chat"])


# Main chat page
@router.get("")
def chat(request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rooms = session.exec(select(ChatRoom)).all()
    membership_map = get_membership_map(current_user.id, session)
    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": None,
            "messages": [],
            "membership_map": membership_map,
        }
    )


# Open a room page
@router.get("/rooms/{room_id}")
def chat_room(room_id: int, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    if not selected_room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership_map = get_membership_map(current_user.id, session)

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": selected_room,
            "messages": [],  # messages now handled via WebSocket
            "membership_map": membership_map,
        }
    )


# Create a new room
@router.post("/rooms")
def create_new_room(request: Request, name: str = Form(...), current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    create_room(name, current_user, session)
    return RedirectResponse(url="/chat", status_code=303)


# Join a room
@router.post("/rooms/{room_id}/join")
def join_room(room_id: int, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    join_room_service(room_id, current_user.id, session)
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    membership_map = get_membership_map(current_user.id, session)
    return templates.TemplateResponse(
        "partials/join_leave_sync.html",
        {
            "request": request,
            "rooms": rooms,
            "membership_map": membership_map,
            "selected_room": selected_room,
        },
    )


# Leave a room
@router.post("/rooms/{room_id}/leave")
def leave_room(room_id: int, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    leave_room_service(room_id, current_user.id, session)
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    membership_map = get_membership_map(current_user.id, session)
    return templates.TemplateResponse(
        "partials/join_leave_sync.html",
        {
            "request": request,
            "rooms": rooms,
            "membership_map": membership_map,
            "selected_room": selected_room,
        },
    )