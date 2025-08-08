# app/main.py

from fastapi import FastAPI
from sqlmodel import SQLModel
from app.db.session import engine
from app.api import auth
from app.api import websocket_router  # ✅ import here

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(websocket_router.router)

@app.get("/")
def root():
    return {"message": "Chat API is running!"}
