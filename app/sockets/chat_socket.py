from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.sockets.connection_manager import ConnectionManager
from app.db.session import get_session
from app.db.models import Message, ChatRoom
from sqlmodel import Session, select
import json
from datetime import datetime

manager = ConnectionManager()

async def chat_endpoint(websocket: WebSocket, room_id: str, session: Session = Depends(get_session)):
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

                # Save to DB (same as before)
                ...
            except json.JSONDecodeError:
                await websocket.send_text("Invalid message format")

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        # ✅ Wrap this to avoid crash after disconnect
        try:
            await manager.broadcast("A user left the room.", room_id)
        except RuntimeError:
            pass  # silently handle already closed socket
