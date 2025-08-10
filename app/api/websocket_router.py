from fastapi import APIRouter, WebSocket
from app.utils.chat_socket import websocket_endpoint

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: int):
    """
    WebSocket route for chat messages.
    Delegates all logic to websocket_endpoint in utils.
    """
    await websocket_endpoint(websocket, room_id)
