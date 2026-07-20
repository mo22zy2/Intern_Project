from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ProfileUpdate, ChangePasswordRequest, MessageResponse
from ..auth_utils import get_current_user
from api.services import profile_service, auth_service

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
def profile(user=Depends(get_current_user)):
    from api.models import Review, PaymentMethod
    data = profile_service.get_profile_data(user)
    settings = data["settings"]
    reviews = Review.objects.filter(user=user).order_by("-created_at")
    payment_methods = PaymentMethod.objects.filter(user=user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "birth": user.birth.isoformat() if user.birth else None,
        "settings": {
            "dark_mode": settings.dark_mode,
            "locale": settings.locale,
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
):
    try:
        profile_service.update_profile(
            user=user,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
            birth=body.birth,
            dark_mode=body.dark_mode,
            locale=body.locale,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Profile updated successfully")


@router.put("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_user),
):
    try:
        auth_service.change_password(
            user,
            body.old_password,
            body.new_password,
            body.confirm_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Password changed successfully")
