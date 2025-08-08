# app/main.py
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.api import auth
from app.db.session import engine

app = FastAPI()
app.include_router(auth.router)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)  # ✅ Creates tables on startup

@app.get("/")
def root():
    return {"message": "Chat API is running!"}
