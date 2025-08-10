from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from app.db.session import get_session
from app.services.chat_service import create_room, get_user_rooms, send_message, get_room_messages
from app.services.auth_service import get_current_user
from app.db.models import User, ChatRoom
from app.sockets.chat_socket import manager
from app.utils.templates import templates

router = APIRouter(prefix="/chat", tags=["chat"])


class RoomCreateInput(BaseModel):
    name: str


@router.post("/rooms")
def create_chat_room(
    data: RoomCreateInput,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return create_room(data.name, current_user, session)


@router.get("/rooms")
def get_rooms(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return get_user_rooms(current_user, session)


@router.get("/{room_id}", response_class=HTMLResponse)
def chat_room_page(
    request: Request,
    room_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    room = session.get(ChatRoom, room_id)
    if not room:
        return HTMLResponse("Room not found", status_code=404)

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "room": room,
        "current_user": current_user
    })


class MessageInput(BaseModel):
    content: str


@router.post("/rooms/{room_id}/messages")
async def send_msg(
    room_id: int,
    data: MessageInput,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Save message to DB
    send_message(room_id, data.content, current_user, session)

    # Fetch updated messages
    messages = get_room_messages(room_id, current_user, session)

    # Render HTML partial
    html_content = templates.get_template("partials/message_list.html").render(
        messages=messages
    )

    # Broadcast to WebSocket clients in the same room
    await manager.broadcast(room_id, html_content)

    # Return HTML for HTMX response (sender sees update immediately)
    return html_content


@router.get("/rooms/{room_id}/messages")
def get_msgs(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    messages = get_room_messages(room_id, current_user, session)
    html_content = templates.get_template("partials/message_list.html").render(
        messages=messages,
        current_user=current_user
    )
    return html_content