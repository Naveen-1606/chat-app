from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import User
from app.utils.auth import hash_password, verify_password, create_access_token
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterInput(BaseModel):
    username: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
def register(data: RegisterInput, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)}, timedelta(minutes=60))
    return {"access_token": token}

class LoginInput(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(data: LoginInput, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=60))
    return {"access_token": token}
