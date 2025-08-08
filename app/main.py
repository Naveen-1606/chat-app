from fastapi import FastAPI
from sqlmodel import SQLModel
from app.db.session import engine
from app.api import auth, websocket_router, chat
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(auth.router)
app.include_router(websocket_router.router)
app.include_router(chat.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Chat API is running!"}
