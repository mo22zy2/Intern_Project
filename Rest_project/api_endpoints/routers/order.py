import base64
from io import BytesIO
from datetime import date, time, datetime

import qrcode
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, Cart, CartItem, Inventory, MenuCustomizationOption, PaymentMethod, Payment, ReservationSystem
from ..schemas import PlaceOrderRequest, OrderOut, OrderItemOut, MessageResponse
from ..auth_utils import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/checkout")
def checkout(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    items = []
    total = 0.0
    for ci in cart.items:
        base = ci.menu.price if ci.menu else 0
        extra = 0
        if ci.options_text:
            option_names = [s.strip() for s in ci.options_text.split(",") if s.strip()]
            extras = db.query(MenuCustomizationOption.extra_price).filter(
                MenuCustomizationOption.menu_id == ci.menu_id,
                MenuCustomizationOption.option_name.in_(option_names),
            ).all()
            extra = sum(e[0] for e in extras)
        elif ci.option_id:
            opt = db.query(MenuCustomizationOption).filter(MenuCustomizationOption.id == ci.option_id).first()
            extra = opt.extra_price if opt else 0
        line_total = (base + extra) * ci.quantity
        total += line_total
        items.append({
            "menu_id": ci.menu_id,
            "item_name": ci.menu.item_ref.item_name if ci.menu and ci.menu.item_ref else "",
            "quantity": ci.quantity,
            "unit_price": base + extra,
            "options_text": ci.options_text or "",
        })
    payment_methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).all()
    return {
        "items": items,
        "total": round(total, 2),
        "payment_methods": [{"id": pm.id, "method_type": pm.method_type, "is_default": pm.is_default} for pm in payment_methods],
    }


@router.post("/checkout/place", response_model=MessageResponse, status_code=201)
def place_order(
    body: PlaceOrderRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    delivery_type = body.delivery_type
    reservation = None
    delivery_address = ""

    if delivery_type == "delivery":
        delivery_address = body.delivery_address.strip() if body.delivery_address else ""
        if not delivery_address:
            raise HTTPException(status_code=400, detail="Please enter a delivery address")
    else:
        if not body.reservation_date or not body.reservation_time or not body.seats:
            raise HTTPException(status_code=400, detail="Please fill in all reservation details")
        if body.seats < 1:
            raise HTTPException(status_code=400, detail="Seats must be a positive number")
        reservation = ReservationSystem(
            user_id=user.id,
            reservation_date=body.reservation_date,
            reservation_time=body.reservation_time,
            seats=body.seats,
            status="confirmed",
        )
        db.add(reservation)
        db.flush()

    total_price = 0.0
    for ci in cart.items:
        base = ci.menu.price if ci.menu else 0
        extra = 0
        if ci.options_text:
            option_names = [s.strip() for s in ci.options_text.split(",") if s.strip()]
            extras = db.query(MenuCustomizationOption.extra_price).filter(
                MenuCustomizationOption.menu_id == ci.menu_id,
                MenuCustomizationOption.option_name.in_(option_names),
            ).all()
            extra = sum(e[0] for e in extras)
        elif ci.option_id:
            opt = db.query(MenuCustomizationOption).filter(MenuCustomizationOption.id == ci.option_id).first()
            extra = opt.extra_price if opt else 0
        total_price += (base + extra) * ci.quantity

    order = Order(
        user_id=user.id,
        delivery_type=delivery_type,
        delivery_address=delivery_address,
        reservation_id=reservation.id if reservation else (body.reservation_id if body.reservation_id and body.reservation_id > 0 else None),
        status="confirmed",
        total_price=round(total_price, 2),
    )
    db.add(order)
    db.flush()

    for ci in cart.items:
        base = ci.menu.price if ci.menu else 0
        extra = 0
        opts_text = ci.options_text or ""
        if ci.options_text:
            option_names = [s.strip() for s in ci.options_text.split(",") if s.strip()]
            extras = db.query(MenuCustomizationOption.extra_price).filter(
                MenuCustomizationOption.menu_id == ci.menu_id,
                MenuCustomizationOption.option_name.in_(option_names),
            ).all()
            extra = sum(e[0] for e in extras)
        elif ci.option_id:
            opt = db.query(MenuCustomizationOption).filter(MenuCustomizationOption.id == ci.option_id).first()
            extra = opt.extra_price if opt else 0
            opts_text = opt.option_name if opt else opts_text
        unit_price = base + extra
        oi = OrderItem(
            order_id=order.id,
            menu_id=ci.menu_id,
            option_id=ci.option_id,
            quantity=ci.quantity,
            unit_price=unit_price,
            options_text=opts_text,
        )
        db.add(oi)
        inv = db.query(Inventory).filter(Inventory.id == ci.menu.item_id).first() if ci.menu else None
        if inv:
            inv.ordered = (inv.ordered or 0) + ci.quantity

    qr = qrcode.make(f"http://localhost:8000/menu?from=order_{order.id}")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    order.qr_data = base64.b64encode(buf.getvalue()).decode()

    if body.payment_type == "cash":
        existing = db.query(PaymentMethod).filter(
            PaymentMethod.user_id == user.id,
            PaymentMethod.method_type == "Cash on Restaurant",
        ).first()
        if not existing:
            pm = PaymentMethod(user_id=user.id, method_type="Cash on Restaurant")
            db.add(pm)
            db.flush()
            existing = pm
        payment_method_id = existing.id
        payment_status = "confirmed"
        paid_at = None
    else:
        if body.payment_method_id:
            payment_method = db.query(PaymentMethod).filter(
                PaymentMethod.id == body.payment_method_id,
                PaymentMethod.user_id == user.id,
            ).first()
            if not payment_method:
                raise HTTPException(status_code=404, detail="Payment method not found")
            payment_method_id = payment_method.id
        elif body.card_number:
            digits = "".join(c for c in body.card_number if c.isdigit())
            if len(digits) < 13:
                raise HTTPException(status_code=400, detail="Invalid card number")
            last_four = digits[-4:]
            method_type = f"\u2022\u2022\u2022\u2022 {last_four}"
            pm = PaymentMethod(user_id=user.id, method_type=method_type)
            db.add(pm)
            db.flush()
            payment_method_id = pm.id
        else:
            raise HTTPException(status_code=400, detail="Please select or enter a payment method")
        payment_status = "completed"
        paid_at = datetime.now()

    payment = Payment(
        order_id=order.id,
        payment_method_id=payment_method_id,
        amount=round(total_price, 2),
        status=payment_status,
        paid_at=paid_at,
    )
    db.add(payment)

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session='fetch')
    db.delete(cart)

    db.commit()
    return MessageResponse(message="Order placed successfully")


@router.get("/")
def order_history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_order_to_out(o, db) for o in orders]


@router.get("/{order_id}")
def order_detail(
    order_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_out(order, db)


def _order_to_out(o: Order, db: Session) -> dict:
    payment = db.query(Payment).filter(Payment.order_id == o.id).first()
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
            "id": payment.id if payment else None,
            "amount": payment.amount if payment else None,
            "status": payment.status if payment else None,
            "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None,
        } if payment else None,
        "items": [
            {
                "id": oi.id,
                "menu_id": oi.menu_id,
                "item_name": oi.menu.item_ref.item_name if oi.menu and oi.menu.item_ref else "",
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
                "options_text": oi.options_text or "",
            }
            for oi in o.items
        ],
    }
