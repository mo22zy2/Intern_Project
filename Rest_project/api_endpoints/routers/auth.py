from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ..database import get_db
from ..models import User, UserSettings
from ..schemas import RegisterRequest, LoginRequest, TokenResponse, MessageResponse
from ..auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    username = body.username.strip().lower()

    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        validate_password(body.password)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Invalid Username, Try Another one")

    if body.email:
        existing_email = db.query(User).filter(User.email == body.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=username,
        password=hash_password(body.password),
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        birth=body.birth,
    )
    db.add(user)
    db.flush()

    settings = UserSettings(user_id=user.id)
    db.add(settings)
    db.commit()

    token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/logout", response_model=MessageResponse)
def logout():
    return MessageResponse(message="Logged out successfully")
