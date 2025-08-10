from fastapi import APIRouter, WebSocket, Depends
from app.sockets.chat_socket import websocket_endpoint

router = APIRouter()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, user=Depends(websocket_endpoint)):
    pass  # The logic is handled in chat_websocket_endpoint
