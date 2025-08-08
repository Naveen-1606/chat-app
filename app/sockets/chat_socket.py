# app/sockets/chat_socket.py

from fastapi import WebSocket, WebSocketDisconnect
from app.sockets.connection_manager import ConnectionManager
import json

manager = ConnectionManager()

async def chat_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                username = payload.get("username", "Anonymous")
                message = payload.get("message", "")
                formatted = f"{username}: {message}"
                await manager.broadcast(formatted, room_id)
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON message format.")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(f"A user left the room.", room_id)
