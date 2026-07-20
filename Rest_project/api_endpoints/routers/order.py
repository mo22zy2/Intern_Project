from fastapi import APIRouter, Depends, HTTPException

from ..schemas import PlaceOrderRequest, MessageResponse
from ..auth_utils import get_current_user
from api.services import order_service

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


@router.post("/checkout/place", response_model=MessageResponse, status_code=201)
def place_order(
    body: PlaceOrderRequest,
    user=Depends(get_current_user),
):
    try:
        order_service.place_order(
            user=user,
            delivery_type=body.delivery_type,
            delivery_address=body.delivery_address.strip() if body.delivery_address else "",
            reservation_date=str(body.reservation_date) if body.reservation_date else None,
            reservation_time=str(body.reservation_time) if body.reservation_time else None,
            seats=body.seats,
            payment_type=body.payment_type,
            payment_method_id=body.payment_method_id,
            card_number=body.card_number.strip() if body.card_number else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MessageResponse(message="Order placed successfully")


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
        except:
            payment = None
    return {
        "id": o.id,
        "user_id": o.user_id,
        "delivery_type": o.delivery_type,
        "delivery_address": o.delivery_address,
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
