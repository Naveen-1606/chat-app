from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status, WebSocket, Request
from jose import JWTError
from app.db.models import User
from app.db.session import get_session
from app.utils.auth import hash_password, verify_password, oauth2_scheme, decode_access_token
from app.core.config import settings

def register_user(data, session: Session):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        return None
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def authenticate_user(email: str, password: str, session: Session):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = None
    # Check Authorization header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    # If not found, check cookies
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



async def get_current_user_ws(
    websocket: WebSocket,
    session: Session = Depends(get_session)
) -> User:
    """
    Extract user from WebSocket connection using JWT token.
    Token can come from query param, header, or cookie.
    """

    token = None

    # 1. Try cookies
    if "access_token" in websocket.cookies:
        token = websocket.cookies["access_token"]

    # 2. Try headers
    elif "authorization" in websocket.headers:
        auth_header = websocket.headers["authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    # 3. Try query params
    elif "token" in websocket.query_params:
        token = websocket.query_params["token"]

    if not token:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except (JWTError, ValueError):
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Look up user in DB
    user = session.get(User, user_id)
    if not user:
        await websocket.close(code=1008)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user