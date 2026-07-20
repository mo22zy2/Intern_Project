from fastapi import APIRouter, HTTPException

from ..schemas import RegisterRequest, LoginRequest, TokenResponse, MessageResponse
from ..auth_utils import create_access_token
from api.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    username = body.username.strip().lower()

    try:
        auth_service.validate_registration_data(body.password, body.confirm_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        user = auth_service.register_user(
            username=username,
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
            phone=body.phone,
            birth=body.birth,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = auth_service.authenticate_user(
        username=body.username.strip().lower(),
        password=body.password,
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/logout", response_model=MessageResponse)
def logout():
    return MessageResponse(message="Logged out successfully")
