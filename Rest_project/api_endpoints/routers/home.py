from datetime import date

from fastapi import APIRouter, Depends

from ..auth_utils import get_current_user_optional
from api.services import menu_service

router = APIRouter(tags=["Home"])


@router.get("/")
def home(
    current_user=Depends(get_current_user_optional),
):
    featured = menu_service.get_featured_items()
    categories = menu_service.get_all_categories()

    result = {
        "popular": [_menu_to_out(m) for m in featured],
        "categories": [{"id": c.id, "name": c.category_name} for c in categories],
        "total_menu_items": menu_service.get_total_menu_items_count(),
        "total_categories": menu_service.get_total_categories_count(),
    }

    if current_user is not None:
        from api.models import Order, ReservationSystem
        today = date.today()
        recent_orders = list(
            Order.objects.filter(user=current_user).order_by("-created_at")[:3]
        )
        upcoming_reservations = list(
            ReservationSystem.objects.filter(
                user=current_user,
                reservation_date__gte=today,
            ).exclude(status="cancelled").order_by("reservation_date", "reservation_time")
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
        result["total_orders"] = Order.objects.filter(user=current_user).count()
        result["total_reservations"] = ReservationSystem.objects.filter(user=current_user).count()

    return result


def _menu_to_out(m):
    return {
        "id": m.id,
        "item_name": m.item.item_name,
        "category_name": m.category.category_name,
        "image_url": m.image_url,
        "price": m.price,
        "popularity_score": m.popularity_score,
        "available": m.available,
        "avg_rating": round(m.avg_rating, 2) if hasattr(m, "avg_rating") and m.avg_rating is not None else None,
        "customization_options": [
            {"id": o.id, "option_name": o.option_name, "extra_price": o.extra_price}
            for o in m.menucustomizationoption_set.all()
        ],
    }
