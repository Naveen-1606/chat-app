# app/api/websocket_router.py

from fastapi import APIRouter, WebSocket
from app.sockets.chat_socket import chat_endpoint

router = APIRouter()

@router.websocket("/ws/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: str):
    await chat_endpoint(websocket, room_id)
