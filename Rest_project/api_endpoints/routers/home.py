from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Menu, Category, Review, Order, ReservationSystem
from ..auth_utils import get_current_user_optional
from ..models import User

router = APIRouter(tags=["Home"])


@router.get("/")
def home(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    avg_rating_subq = (
        db.query(Review.menu_id, func.avg(Review.rating).label("avg_rating"))
        .group_by(Review.menu_id)
        .subquery()
    )
    popular = (
        db.query(Menu, avg_rating_subq.c.avg_rating)
        .outerjoin(avg_rating_subq, Menu.id == avg_rating_subq.c.menu_id)
        .filter(Menu.available == True)
        .order_by(Menu.popularity_score.desc())
        .limit(4)
        .all()
    )

    categories = db.query(Category).all()
    total_menu_items = db.query(Menu).filter(Menu.available == True).count()
    total_categories = db.query(Category).count()

    result = {
        "popular": [_menu_to_out(m, avg) for m, avg in popular],
        "categories": [{"id": c.id, "name": c.category_name} for c in categories],
        "total_menu_items": total_menu_items,
        "total_categories": total_categories,
    }

    if current_user is not None:
        today = date.today()
        recent_orders = (
            db.query(Order)
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .limit(3)
            .all()
        )
        upcoming_reservations = (
            db.query(ReservationSystem)
            .filter(
                ReservationSystem.user_id == current_user.id,
                ReservationSystem.reservation_date >= today,
                ReservationSystem.status != "cancelled",
            )
            .order_by(ReservationSystem.reservation_date, ReservationSystem.reservation_time)
            .all()
        )
        total_orders = (
            db.query(Order)
            .filter(Order.user_id == current_user.id)
            .count()
        )
        total_reservations = (
            db.query(ReservationSystem)
            .filter(ReservationSystem.user_id == current_user.id)
            .count()
        )

        result["recent_orders"] = [
            {
                "id": o.id,
                "status": o.status,
                "total_price": o.total_price,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in recent_orders
        ]
        result["upcoming_reservations"] = [
            {
                "id": r.id,
                "reservation_date": r.reservation_date.isoformat() if r.reservation_date else None,
                "reservation_time": str(r.reservation_time) if r.reservation_time else None,
                "seats": r.seats,
                "status": r.status,
            }
            for r in upcoming_reservations
        ]
        result["total_orders"] = total_orders
        result["total_reservations"] = total_reservations

    return result


def _menu_to_out(m: Menu, avg_rating: Optional[float] = None) -> dict:
    return {
        "id": m.id,
        "item_name": m.item_ref.item_name if m.item_ref else "",
        "category_name": m.category.category_name if m.category else "",
        "image_url": m.image_url,
        "price": m.price,
        "popularity_score": m.popularity_score,
        "available": m.available,
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "customization_options": [
            {"id": o.id, "option_name": o.option_name, "extra_price": o.extra_price}
            for o in m.customization_options
        ],
    }
