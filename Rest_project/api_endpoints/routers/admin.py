from django.core.exceptions import ObjectDoesNotExist
from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import (
    MessageResponse,
    CategoryCreate,
    MenuItemCreate,
    CustomizationCreate,
    StatusUpdate,
    InventoryUpdate,
)
from ..auth_utils import get_current_staff_user
from api.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Dashboard ────────────────────────────────────────────────────

@router.get("/dashboard")
def admin_dashboard(user=Depends(get_current_staff_user)):
    stats = admin_service.get_dashboard_stats()
    revenue_data = admin_service.get_revenue_last_30_days()
    status_counts = admin_service.get_order_status_counts()
    top_items = admin_service.get_top_selling_items()
    recent = admin_service.get_recent_orders()
    demographics = admin_service.get_user_demographics()
    return {
        "stats": stats,
        "revenue_data": revenue_data,
        "order_status_counts": status_counts,
        "top_items": top_items,
        "recent_orders": [
            {
                "id": o.id,
                "user": o.user.username,
                "total_price": o.total_price,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in recent
        ],
        "demographics": demographics,
    }


# ── Orders ───────────────────────────────────────────────────────

@router.get("/orders")
def admin_orders(user=Depends(get_current_staff_user)):
    orders = admin_service.get_all_orders()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "user": o.user.username,
            "delivery_type": o.delivery_type,
            "delivery_address": o.delivery_address,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
            "reservation_id": o.reservation_id,
        }
        for o in orders
    ]


@router.put("/orders/{order_id}/status", response_model=MessageResponse)
def admin_update_order(
    order_id: int,
    body: StatusUpdate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.update_order_status(order_id, body.status)
        return MessageResponse(message=f"Order #{order_id} status updated to '{body.status}'")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Reservations ─────────────────────────────────────────────────

@router.get("/reservations")
def admin_reservations(user=Depends(get_current_staff_user)):
    reservations = admin_service.get_all_reservations()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user": r.user.username,
            "reservation_date": r.reservation_date.isoformat(),
            "reservation_time": r.reservation_time.strftime("%H:%M:%S"),
            "seats": r.seats,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in reservations
    ]


@router.put("/reservations/{reservation_id}/status", response_model=MessageResponse)
def admin_update_reservation(
    reservation_id: int,
    body: StatusUpdate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.update_reservation_status(reservation_id, body.status)
        return MessageResponse(
            message=f"Reservation #{reservation_id} status updated to '{body.status}'"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Menu ─────────────────────────────────────────────────────────

@router.get("/menu")
def admin_menu_list(user=Depends(get_current_staff_user)):
    items = admin_service.get_all_menu_items_admin()
    return [
        {
            "id": m.id,
            "item_name": m.item.item_name,
            "category": m.category.category_name,
            "category_id": m.category_id,
            "price": m.price,
            "image_url": m.image_url,
            "available": m.available,
            "stock_count": m.item.item_count,
            "created_at": m.created_at.isoformat(),
        }
        for m in items
    ]


@router.post("/menu", response_model=MessageResponse, status_code=201)
def admin_menu_add(
    body: MenuItemCreate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.add_menu_item(
            body.item_name,
            body.category_id,
            body.price,
            body.image_url,
            body.available,
            body.stock_count,
        )
        return MessageResponse(message="Menu item added")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ObjectDoesNotExist:
        raise HTTPException(status_code=400, detail="Invalid category")


@router.delete("/menu/{item_id}", response_model=MessageResponse)
def admin_menu_delete(
    item_id: int,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.delete_menu_item(item_id)
        return MessageResponse(message="Menu item deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/menu/{item_id}/toggle", response_model=MessageResponse)
def admin_menu_toggle(
    item_id: int,
    user=Depends(get_current_staff_user),
):
    try:
        menu = admin_service.toggle_menu_availability(item_id)
        status = "available" if menu.available else "unavailable"
        return MessageResponse(message=f"Item is now {status}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Categories ───────────────────────────────────────────────────

@router.get("/categories")
def admin_categories(user=Depends(get_current_staff_user)):
    cats = admin_service.get_all_categories()
    return [{"id": c.id, "category_name": c.category_name} for c in cats]


@router.post("/categories", response_model=MessageResponse, status_code=201)
def admin_category_add(
    body: CategoryCreate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.add_category(body.category_name)
        return MessageResponse(message=f"Category '{body.category_name}' added")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/categories/{category_id}", response_model=MessageResponse)
def admin_category_edit(
    category_id: int,
    body: CategoryCreate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.update_category(category_id, body.category_name)
        return MessageResponse(message="Category updated")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/categories/{category_id}", response_model=MessageResponse)
def admin_category_delete(
    category_id: int,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.delete_category(category_id)
        return MessageResponse(message="Category deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Customizations ───────────────────────────────────────────────

@router.get("/menu/{menu_id}/customizations")
def admin_customizations(
    menu_id: int,
    user=Depends(get_current_staff_user),
):
    try:
        menu, options = admin_service.get_customizations_for_menu(menu_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "menu_id": menu.id,
        "menu_name": menu.item.item_name,
        "options": [
            {
                "id": o.id,
                "option_name": o.option_name,
                "extra_price": o.extra_price,
            }
            for o in options
        ],
    }


@router.post("/menu/{menu_id}/customizations", response_model=MessageResponse, status_code=201)
def admin_customization_add(
    menu_id: int,
    body: CustomizationCreate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.add_customization(menu_id, body.option_name, body.extra_price)
        return MessageResponse(message="Customization added")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/customizations/{customization_id}", response_model=MessageResponse)
def admin_customization_delete(
    customization_id: int,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.delete_customization(customization_id)
        return MessageResponse(message="Customization deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Inventory ────────────────────────────────────────────────────

@router.get("/inventory")
def admin_inventory(user=Depends(get_current_staff_user)):
    inventory = admin_service.get_all_inventory()
    return [
        {
            "id": inv.id,
            "item_name": inv.item_name,
            "item_count": inv.item_count,
            "ordered": inv.ordered,
            "status": "out_of_stock" if inv.item_count == 0
                      else "low_stock" if inv.item_count < 10
                      else "in_stock",
        }
        for inv in inventory
    ]


@router.put("/inventory/{inventory_id}", response_model=MessageResponse)
def admin_update_inventory(
    inventory_id: int,
    body: InventoryUpdate,
    user=Depends(get_current_staff_user),
):
    try:
        admin_service.update_inventory_stock(inventory_id, body.item_count)
        return MessageResponse(message="Inventory updated")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Users ────────────────────────────────────────────────────────

@router.get("/users")
def admin_users(user=Depends(get_current_staff_user)):
    users = admin_service.get_all_users()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email or "",
            "is_staff": u.is_staff,
            "is_active": u.is_active,
            "date_joined": u.date_joined.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.put("/users/{user_id}/toggle-staff", response_model=MessageResponse)
def admin_toggle_staff(
    user_id: int,
    admin_user=Depends(get_current_staff_user),
):
    if not admin_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    if user_id == admin_user.id:
        raise HTTPException(status_code=403, detail="You cannot change your own staff status")
    try:
        u = admin_service.toggle_user_staff(user_id)
        role = "staff" if u.is_staff else "regular"
        return MessageResponse(message=f"User is now {role}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}/toggle-active", response_model=MessageResponse)
def admin_toggle_active(
    user_id: int,
    admin_user=Depends(get_current_staff_user),
):
    if not admin_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")
    if user_id == admin_user.id:
        raise HTTPException(status_code=403, detail="You cannot change your own account status")
    try:
        u = admin_service.toggle_user_active(user_id)
        status = "active" if u.is_active else "banned"
        return MessageResponse(message=f"User is now {status}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Reports ──────────────────────────────────────────────────────

@router.get("/reports/sales")
def admin_sales_report(
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_staff_user),
):
    data = admin_service.get_sales_report(days)
    return {
        "total_orders": data["total_orders"],
        "total_revenue": data["total_revenue"],
        "by_status": [
            {"status": row["status"], "count": row["count"]}
            for row in data["by_status"]
        ],
        "daily": [
            {
                "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
                "count": row["count"],
                "revenue": float(row["revenue"]),
            }
            for row in data["daily"]
        ],
    }


@router.get("/reports/inventory")
def admin_inventory_report(user=Depends(get_current_staff_user)):
    from api.models import Menu
    inventory = admin_service.get_all_inventory()
    prices = dict(Menu.objects.values_list("item_id", "price"))
    return {
        "items": [
            {
                "id": inv.id,
                "item_name": inv.item_name,
                "item_count": inv.item_count,
                "ordered": inv.ordered,
                "status": "out_of_stock" if inv.item_count == 0
                          else "low_stock" if inv.item_count < 10
                          else "in_stock",
            }
            for inv in inventory
        ],
        "total_value": sum(
            (inv.item_count or 0) * prices.get(inv.id, 0) for inv in inventory
        ),
    }


@router.get("/reports/feedback")
def admin_feedback_report(
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_staff_user),
):
    data = admin_service.get_feedback_report(days)
    return {
        "total_reviews": data["total_reviews"],
        "avg_rating": data["avg_rating"],
        "rating_distribution": [
            {"rating": row["rating"], "count": row["count"]}
            for row in data["rating_dist"]
        ],
        "recent_reviews": [
            {
                "user": r.user.username,
                "item_name": r.menu.item.item_name,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat(),
            }
            for r in data["reviews"]
        ],
    }


@router.get("/reports/reservations")
def admin_reservations_report(
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_staff_user),
):
    data = admin_service.get_reservation_report(days)
    return {
        "total_reservations": data["total_reservations"],
        "by_status": [
            {"status": row["status"], "count": row["count"]}
            for row in data["by_status"]
        ],
    }
