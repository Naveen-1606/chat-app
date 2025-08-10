from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from datetime import timedelta
from app.db.session import get_session
from app.db.models import Message
from app.db.models import User, UserCreate
from app.services.auth_service import register_user, authenticate_user, get_current_user
from app.utils.auth import create_access_token
from app.utils.templates import templates


# router = APIRouter(prefix="/htmx/auth", tags=["auth-htmx"])
router = APIRouter(tags=["auth-htmx"])



@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

# -------------------------
# Render Login Form
# -------------------------
@router.get("/login", response_class=HTMLResponse)
def get_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# -------------------------
# Render Register Form
# -------------------------
@router.get("/register", response_class=HTMLResponse)
def get_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# -------------------------
# Handle Login Submission
# -------------------------
@router.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = authenticate_user(email, password, session)
    if not user:
        return HTMLResponse(
            content="<div class='text-red-500'>Invalid email or password.</div>",
            status_code=401
        )

    # Create JWT
    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=60))

    response_html = f"""
    <div class='text-green-600 font-semibold'>
        ✅ Login successful! Redirecting...
    </div>
    <script>
        document.cookie = "access_token={token}; path=/";
        window.location.href = "/chat";
    </script>
    """
    return HTMLResponse(content=response_html)

# -------------------------
# Handle Register Submission
# -------------------------
@router.post("/register", response_class=HTMLResponse)
def register_new_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user_data = UserCreate(username=username, email=email, password=password)
    new_user = register_user(user_data, session)

    if not new_user:
        return HTMLResponse(
            content="<div class='text-red-500'>Email already registered.</div>",
            status_code=400
        )

    token = create_access_token({"sub": str(new_user.id)}, timedelta(minutes=60))

    response_html = f"""
    <div class='text-green-600 font-semibold'>
        🎉 Registration successful! Redirecting to chat...
    </div>
    <script>
        document.cookie = "access_token={token}; path=/";
        window.location.href = "/login";
    </script>
    """
    return HTMLResponse(content=response_html)


@router.get("/chat")
def chat_page(
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login")

    messages = session.exec(
        select(Message).order_by(Message.timestamp)
    ).all()

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "messages": messages,
            "user": user
        }
    )


@router.post("/send")
def send_message(
    request: Request,
    content: str = Form(...),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login")

    msg = Message(sender_id=user.id, content=content)
    session.add(msg)
    session.commit()
    session.refresh(msg)

    return templates.TemplateResponse(
        "partials/message.html",
        {
            "request": request,
            "msg": msg
        }
    )