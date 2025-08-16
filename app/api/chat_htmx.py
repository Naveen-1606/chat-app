from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.chat_service import (
    get_user_rooms, get_room, get_room_messages, create_room, send_message, join_room_service, leave_room_service, get_membership_map
)
from app.services.auth_service import get_current_user
from app.db.models import User, ChatRoom, UserChatRoom, Message
from app.db.session import get_session
from app.utils.templates import templates
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


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



@router.get("/rooms/{room_id}")
def chat_room(room_id: int, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    if not selected_room:
        raise HTTPException(status_code=404, detail="Room not found")

    messages = selected_room.messages or []
    membership_map = get_membership_map(current_user.id, session)

    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
            "user": current_user,
            "selected_room": selected_room,
            "messages": messages,
            "membership_map": membership_map,
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
    # Save and return the new message
    message = send_message(room_id, content, current_user, session)

    # Fetch updated messages for this room
    messages = get_room_messages(room_id, current_user, session)

    return templates.TemplateResponse(
        "partials/message_item.html",
        {
            "request": request,
            "message": message,
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
            "request": request,
            "messages": messages,
        },
    )


@router.post("/rooms/{room_id}/join")
def join_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Add user to the room
    join_room_service(room_id, current_user.id, session)
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    membership_map = get_membership_map(current_user.id, session)

    # # If triggered from sidebar -> return sidebar item
    # if "rooms-container" in request.headers.get("Hx-Target", ""):
    #     return templates.TemplateResponse(
    #         "partials/room_list.html",
    #         {"rooms": rooms, "membership_map": membership_map,
    #          "selected_room": selected_room, "request": request}
    #     )

    # # If triggered from chat area join button -> return input area
    # if "message-input-container" in request.headers.get("Hx-Target", ""):
    #     return templates.TemplateResponse(
    #         "partials/message_input.html",
    #         {"rooms": rooms, "membership_map": membership_map,
    #          "selected_room": selected_room, "request": request}
    #     )

    # Return BOTH sidebar + message input
    return templates.TemplateResponse(
        "partials/join_leave_sync.html",
        {
            "request": request,
            "rooms": rooms,
            "membership_map": membership_map,
            "selected_room": selected_room,
        },
    )
    

@router.post("/rooms/{room_id}/leave")
def leave_room(room_id: int, request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    leave_room_service(room_id, current_user.id, session)
    rooms = session.exec(select(ChatRoom)).all()
    selected_room = session.get(ChatRoom, room_id)
    membership_map = get_membership_map(current_user.id, session)
    
    # # If triggered from sidebar -> return sidebar item
    # if "rooms-container" in request.headers.get("Hx-Target", ""):
    #     return templates.TemplateResponse(
    #         "partials/room_list.html",
    #         {"rooms": rooms, "membership_map": membership_map,
    #          "selected_room": selected_room, "request": request}
    #     )

    # # If triggered from chat area join button -> return input area
    # if "message-input-container" in request.headers.get("Hx-Target", ""):
    #     return templates.TemplateResponse(
    #         "partials/message_input.html",
    #         {"rooms": rooms, "membership_map": membership_map,
    #          "selected_room": selected_room, "request": request}
    #     )

    # Return BOTH sidebar + message input
    return templates.TemplateResponse(
        "partials/join_leave_sync.html",
        {
            "request": request,
            "rooms": rooms,
            "membership_map": membership_map,
            "selected_room": selected_room,
        },
    )
