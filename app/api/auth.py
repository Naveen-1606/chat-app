# from fastapi import APIRouter, HTTPException, Depends
# from sqlmodel import Session
# from app.db.session import get_session
# from app.utils.auth import create_access_token
# from app.services.auth_service import register_user, authenticate_user
# from pydantic import BaseModel
# from datetime import timedelta

# router = APIRouter(prefix="/auth", tags=["auth"])

# class RegisterInput(BaseModel):
#     username: str
#     email: str
#     password: str

# class TokenResponse(BaseModel):
#     access_token: str
#     token_type: str = "bearer"

# @router.post("/register", response_model=TokenResponse)
# def register(data: RegisterInput, session: Session = Depends(get_session)):
#     new_user = register_user(data, session)
#     if not new_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     token = create_access_token({"sub": str(new_user.id)}, timedelta(minutes=60))
#     return {"access_token": token}

# class LoginInput(BaseModel):
#     email: str
#     password: str

# @router.post("/login", response_model=TokenResponse)
# def login(data: LoginInput, session: Session = Depends(get_session)):
#     user = authenticate_user(data.email, data.password, session)
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")
    
#     token = create_access_token({"sub": str(user.id)}, timedelta(minutes=60))
#     return {"access_token": token}
