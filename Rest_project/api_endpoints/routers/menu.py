from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Menu, Category, Review, User, Inventory
from ..schemas import MenuItemOut
from ..auth_utils import get_current_user_optional

router = APIRouter(prefix="/menu", tags=["Menu"])


def _menu_to_out(m: Menu, avg_rating: Optional[float] = None) -> dict:
    return {
        "id": m.id,
        "item_name": m.item_ref.item_name if m.item_ref else "",
        "category_name": m.category.category_name if m.category else "",
        "image_url": m.image_url,
        "price": m.price,
        "popularity_score": m.popularity_score,
        "available": m.available,
        "avg_rating": avg_rating,
        "customization_options": [
            {"id": o.id, "option_name": o.option_name, "extra_price": o.extra_price}
            for o in m.customization_options
        ],
    }


@router.get("/")
def menu_list(
    category_id: int = None,
    search: str = None,
    sort: str = "",
    db: Session = Depends(get_db),
):
    avg_rating_subq = (
        db.query(func.avg(Review.rating))
        .filter(Review.menu_id == Menu.id)
        .correlate(Menu)
        .scalar_subquery()
    )

    q = db.query(Menu, avg_rating_subq.label("avg_rating")).filter(
        Menu.available == True
    )

    if category_id:
        q = q.filter(Menu.category_id == category_id)
    if search:
        q = q.filter(
            Menu.item_ref.has(Inventory.item_name.ilike(f"%{search}%"))
        )

    if sort == "price_low":
        q = q.order_by(Menu.price.asc())
    elif sort == "price_high":
        q = q.order_by(Menu.price.desc())
    elif sort == "newest":
        q = q.order_by(Menu.created_at.desc())
    else:
        q = q.order_by(Menu.popularity_score.desc())

    rows = q.all()
    items = [_menu_to_out(m, avg_rating=avg_rating) for m, avg_rating in rows]
    categories = db.query(Category).all()
    return {
        "items": items,
        "categories": [{"id": c.id, "name": c.category_name} for c in categories],
    }


@router.get("/{item_id}")
def menu_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    m = (
        db.query(Menu)
        .filter(Menu.id == item_id, Menu.available == True)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Menu item not found")

    reviews_query = (
        db.query(Review, User.username)
        .join(User, Review.user_id == User.id)
        .filter(Review.menu_id == item_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    reviews = [
        {
            "username": username,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        }
        for r, username in reviews_query
    ]

    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.menu_id == item_id)
        .scalar()
    )

    user_review = None
    if current_user:
        ur = (
            db.query(Review)
            .filter(
                Review.menu_id == item_id,
                Review.user_id == current_user.id,
            )
            .first()
        )
        if ur:
            user_review = {
                "rating": ur.rating,
                "comment": ur.comment,
                "created_at": ur.created_at.isoformat(),
            }

    result = _menu_to_out(m, avg_rating=avg_rating)
    result["reviews"] = reviews
    result["user_review"] = user_review
    return result
