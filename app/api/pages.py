# from fastapi import APIRouter, Request
# from fastapi.responses import HTMLResponse
# import os

# from app.utils.templates import templates

# router = APIRouter()

# @router.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("base.html", {"request": request})

# @router.get("/login", response_class=HTMLResponse)
# def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# @router.get("/register", response_class=HTMLResponse)
# def register_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})
