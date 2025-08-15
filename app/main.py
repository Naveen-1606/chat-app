from fastapi import FastAPI, Request
from sqlmodel import SQLModel
from app.db.session import engine
from app.api import auth, chat, pages, auth_htmx, websocket_router, chat_htmx
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from fastapi.staticfiles import StaticFiles
from app.db.models import *
import os
import logging
from app.api import auth_htmx
from app.utils.templates import templates


app = FastAPI()

logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Routers
# app.include_router(auth.router)
# app.include_router(chat.router)
# app.include_router(pages.router)
app.include_router(auth_htmx.router)
app.include_router(websocket_router.router)
app.include_router(chat_htmx.router)

# Static & templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Entry point
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})