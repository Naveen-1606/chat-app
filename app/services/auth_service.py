from sqlmodel import Session, select
from app.db.models import User
from app.utils.auth import hash_password, verify_password

def register_user(data, session: Session):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        return None  # user exists
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
