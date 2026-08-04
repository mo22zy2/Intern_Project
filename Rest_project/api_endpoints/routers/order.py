from django.core.exceptions import ObjectDoesNotExist
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import PlaceOrderRequest, OrderOut
from ..auth_utils import get_current_user
from api.services import order_service


def _sync_cart_from_items(user, items):
    from api.models import Cart, CartItem, Menu
    cart, _ = Cart.objects.get_or_create(user=user)
    resolved = []
    for item in items:
        try:
            menu = Menu.objects.get(id=item.menu_id)
        except Menu.DoesNotExist:
            raise ValueError(f"Invalid menu item id {item.menu_id}")
        resolved.append((menu, item))
    CartItem.objects.filter(cart=cart).delete()
    for menu, item in resolved:
        CartItem.objects.create(
            cart=cart,
            menu=menu,
            quantity=item.quantity,
            options_text=item.options_text or "",
        )

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/checkout")
def checkout(user=Depends(get_current_user)):
    data = order_service.get_checkout_data(user)
    if not data:
        raise HTTPException(status_code=400, detail="Cart is empty")
    items = []
    for entry in data["items"]:
        ci = entry["item"]
        items.append({
            "menu_id": ci.menu.id,
            "item_name": ci.menu.item.item_name,
            "quantity": ci.quantity,
            "unit_price": entry["unit_price"],
            "options_text": ci.options_text or "",
        })
    return {
        "items": items,
        "total": round(data["subtotal"], 2),
        "payment_methods": [
            {"id": pm.id, "method_type": pm.method_type, "is_default": pm.is_default}
            for pm in data["payment_methods"]
        ],
    }


@router.post("/checkout/place", response_model=OrderOut, status_code=201)
def place_order(
    body: PlaceOrderRequest,
    user=Depends(get_current_user),
):
    try:
        _sync_cart_from_items(user, body.items)
        order = order_service.place_order(
            user=user,
            delivery_type=body.delivery_type,
            delivery_address=body.delivery_address.strip() if body.delivery_address else "",
            pickup_date=body.pickup_date,
            pickup_time=body.pickup_time,
            reservation_date=str(body.reservation_date) if body.reservation_date else None,
            reservation_time=str(body.reservation_time) if body.reservation_time else None,
            seats=body.seats,
            payment_type=body.payment_type,
            payment_method_id=body.payment_method_id,
            card_number=body.card_number.strip() if body.card_number else None,
        )
        if body.save_address and body.delivery_address:
            user.address = body.delivery_address.strip()
            user.save(update_fields=["address"])
    except (ValueError, ObjectDoesNotExist) as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": order.id,
        "user_id": order.user_id,
        "delivery_type": order.delivery_type,
        "delivery_address": order.delivery_address,
        "order_number": order.order_number,
        "status": order.status,
        "total_price": order.total_price,
        "created_at": order.created_at,
        "qr_data": order.qr_data,
        "items": [
            {
                "id": oi.id,
                "menu_id": oi.menu_id,
                "item_name": oi.menu.item.item_name,
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
                "options_text": oi.options_text or "",
            }
            for oi in order.orderitem_set.all()
        ],
    }


@router.get("/")
def order_history(user=Depends(get_current_user)):
    orders = order_service.get_user_orders(user)
    return [_order_to_out(o) for o in orders]


@router.get("/{order_id}")
def order_detail(
    order_id: int,
    user=Depends(get_current_user),
):
    order = order_service.get_order_detail(user, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_out(order)


def _order_to_out(o):
    payment = getattr(o, "payment", None)
    if not payment:
        try:
            payment = o.payment_rel
        except AttributeError:
            payment = None
    return {
        "id": o.id,
        "user_id": o.user_id,
        "delivery_type": o.delivery_type,
        "delivery_address": o.delivery_address,
        "order_number": o.order_number,
        "status": o.status,
        "total_price": o.total_price,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "qr_data": o.qr_data,
        "payment": {
            "id": payment.id,
            "amount": payment.amount,
            "status": payment.status,
            "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None,
        } if payment else None,
        "items": [
            {
                "id": oi.id,
                "menu_id": oi.menu_id,
                "item_name": oi.menu.item.item_name,
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
                "options_text": oi.options_text or "",
            }
            for oi in o.orderitem_set.all()
        ],
    }
