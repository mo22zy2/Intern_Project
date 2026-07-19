from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ..database import get_db
from ..models import User, UserSettings, Review, PaymentMethod
from ..schemas import ProfileUpdate, ChangePasswordRequest, UserOut, MessageResponse
from ..auth_utils import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
def profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    reviews = db.query(Review).filter(Review.user_id == user.id).order_by(Review.created_at.desc()).all()
    payment_methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).all()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "birth": user.birth.isoformat() if user.birth else None,
        "settings": {
            "dark_mode": settings.dark_mode if settings else False,
            "locale": settings.locale if settings else "en",
        },
        "reviews": [
            {
                "id": r.id,
                "menu_id": r.menu_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
        "payment_methods": [
            {"id": pm.id, "method_type": pm.method_type, "is_default": pm.is_default}
            for pm in payment_methods
        ],
    }


@router.put("/edit", response_model=MessageResponse)
def edit_profile(
    body: ProfileUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.email is not None:
        existing = db.query(User).filter(User.email == body.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.phone is not None:
        user.phone = body.phone
    if body.birth is not None:
        user.birth = body.birth
    if body.dark_mode is not None or body.locale is not None:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
        if body.dark_mode is not None:
            settings.dark_mode = body.dark_mode
        if body.locale is not None:
            settings.locale = body.locale
    db.commit()
    return MessageResponse(message="Profile updated successfully")


@router.put("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    try:
        validate_password(body.new_password)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="; ".join(e.messages))
    user.password = hash_password(body.new_password)
    db.commit()
    return MessageResponse(message="Password changed successfully")
