from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ReviewCreate, MessageResponse
from ..auth_utils import get_current_user
from api.services import review_service, menu_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/")
def my_reviews(user=Depends(get_current_user)):
    reviews = review_service.get_user_reviews(user)
    return [
        {
            "id": r.id,
            "user_id": r.user.id,
            "menu_id": r.menu_id,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]


@router.post("/add/{menu_id}", response_model=MessageResponse, status_code=201)
def add_review(
    menu_id: int,
    body: ReviewCreate,
    user=Depends(get_current_user),
):
    menu = menu_service.get_menu_item_by_id(menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu item not found")

    try:
        review_service.add_review(
            user=user,
            menu=menu,
            rating=body.rating,
            comment=body.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Review added successfully")


@router.put("/{review_id}/edit", response_model=MessageResponse)
def edit_review(
    review_id: int,
    body: ReviewCreate,
    user=Depends(get_current_user),
):
    review = review_service.get_review(user, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    try:
        review_service.update_review(
            review,
            rating=body.rating,
            comment=body.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Review updated successfully")


@router.delete("/{review_id}/delete", response_model=MessageResponse)
def delete_review(
    review_id: int,
    user=Depends(get_current_user),
):
    review = review_service.get_review(user, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review_service.delete_review(review)
    return MessageResponse(message="Review deleted successfully")
