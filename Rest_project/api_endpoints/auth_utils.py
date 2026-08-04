import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(50)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def _get_user_model():
    from django.contrib.auth import get_user_model
    return get_user_model()


security = HTTPBearer()


def hash_password(password: str) -> str:
    from django.contrib.auth.hashers import make_password
    return make_password(password)


def verify_password(plain: str, hashed: str) -> bool:
    from django.contrib.auth.hashers import check_password
    return check_password(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    User = _get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception
    return user


def get_current_staff_user(
    current_user=Depends(get_current_user),
):
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        User = _get_user_model()
        user = User.objects.get(id=user_id)
        if not user.is_active:
            return None
        return user
    except (JWTError, _get_user_model().DoesNotExist):
        return None
