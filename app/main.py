# app/main.py

from fastapi import FastAPI
from sqlmodel import SQLModel
from app.db.session import engine
from app.api import auth, websocket_router, chat

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(websocket_router.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "Chat API is running!"}
