from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import MenuItemOut
from ..auth_utils import get_current_user_optional
from api.services import menu_service

router = APIRouter(prefix="/menu", tags=["Menu"])


def _menu_to_out(m, avg_rating=None):
    return {
        "id": m.id,
        "item_name": m.item.item_name,
        "category_name": m.category.category_name,
        "image_url": m.image_url,
        "price": m.price,
        "popularity_score": m.popularity_score,
        "available": m.available,
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "customization_options": [
            {"id": o.id, "option_name": o.option_name, "extra_price": o.extra_price}
            for o in m.menucustomizationoption_set.all()
        ],
    }


@router.get("/")
def menu_list(
    category_id: int = None,
    search: str = None,
    sort: str = "",
):
    items = menu_service.get_available_menu_items(
        category_id=category_id,
        search=search,
        sort=sort,
    )
    categories = menu_service.get_all_categories()
    return {
        "items": [_menu_to_out(m, avg_rating=m.avg_rating) for m in items],
        "categories": [{"id": c.id, "name": c.category_name} for c in categories],
    }


@router.get("/{item_id}")
def menu_detail(
    item_id: int,
    current_user=Depends(get_current_user_optional),
):
    detail = menu_service.get_menu_detail(item_id, user=current_user)
    if not detail:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item = detail["item"]
    reviews = detail["reviews"]
    avg_rating = detail["avg_rating"]
    user_review_obj = detail["user_review"]

    result = _menu_to_out(item, avg_rating=avg_rating)
    result["reviews"] = [
        {
            "username": r.user.username,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]
    result["user_review"] = (
        {
            "rating": user_review_obj.rating,
            "comment": user_review_obj.comment,
            "created_at": user_review_obj.created_at.isoformat(),
        }
        if user_review_obj
        else None
    )
    return result
