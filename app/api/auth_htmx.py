from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from sqlmodel import Session, select
from datetime import timedelta
from app.db.session import get_session
from app.db.models import User, UserCreate
from app.services.auth_service import register_user, authenticate_user
from app.utils.auth import (
    create_access_token,
    create_verification_token,
    decode_verification_token
)
from app.utils.templates import templates
from app.services.email_service import send_verification_email

router = APIRouter(tags=["auth-htmx"])

# -------------------------
# Email Verification Endpoint
# -------------------------
@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_session)):
    try:
        email = decode_verification_token(token)
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            return HTMLResponse("<div>User not found</div>", status_code=404)

        # Mark user as verified
        user.is_verified = True
        db.add(user)
        db.commit()

        # Redirect to login page with query parameter
        return RedirectResponse(url="/login?verified=1", status_code=302)

    except HTTPException as e:
        return HTMLResponse(f"<div>{e.detail}</div>", status_code=400)





# -------------------------
# Home
# -------------------------
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
        return HTMLResponse("<div class='text-red-500'>Invalid email or password.</div>", status_code=401)

    if not user.is_verified:
        return HTMLResponse("<div class='text-yellow-500'>⚠ Please verify your email before logging in.</div>", status_code=403)

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
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    # Create user
    user_data = UserCreate(username=username, email=email, password=password)
    new_user = register_user(user_data, session)
    if not new_user:
        return HTMLResponse(
            "<div class='text-red-500'>Email already registered.</div>", status_code=400
        )

    # Generate verification token
    verification_token = create_verification_token(email)
    
    # Send verification email via background task
    send_verification_email(background_tasks, email, verification_token)

    return HTMLResponse("""
        <div class='text-green-600 font-semibold'>
            🎉 Registration successful! Please check your email to verify your account.
        </div>
    """)


# -------------------------
# Logout
# -------------------------
@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
