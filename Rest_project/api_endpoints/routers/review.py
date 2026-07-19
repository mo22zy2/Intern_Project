from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Review, Menu
from ..schemas import ReviewCreate, ReviewOut, MessageResponse
from ..auth_utils import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/")
def my_reviews(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
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
    db: Session = Depends(get_db),
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu item not found")

    existing = (
        db.query(Review)
        .filter(Review.user_id == user.id, Review.menu_id == menu_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this item")

    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    review = Review(
        user_id=user.id,
        menu_id=menu_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    db.commit()
    return MessageResponse(message="Review added successfully")


@router.put("/{review_id}/edit", response_model=MessageResponse)
def edit_review(
    review_id: int,
    body: ReviewCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user.id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if body.rating < 1 or body.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    review.rating = body.rating
    review.comment = body.comment
    db.commit()
    return MessageResponse(message="Review updated successfully")


@router.delete("/{review_id}/delete", response_model=MessageResponse)
def delete_review(
    review_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user.id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return MessageResponse(message="Review deleted successfully")
