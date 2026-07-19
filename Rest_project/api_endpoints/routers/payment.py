from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PaymentMethod, Payment, Order
from ..schemas import PaymentMethodCreate, PaymentMethodOut, PaymentOut, MessageResponse
from ..auth_utils import get_current_user

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


@router.get("/")
def payment_methods(user=Depends(get_current_user), db: Session = Depends(get_db)):
    methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).all()
    return [
        {"id": m.id, "method_type": m.method_type, "is_default": m.is_default}
        for m in methods
    ]


@router.post("/add", response_model=MessageResponse, status_code=201)
def add_payment_method(
    body: PaymentMethodCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    digits = "".join(c for c in body.card_number if c.isdigit())
    if len(digits) < 13:
        raise HTTPException(status_code=400, detail="Invalid card number")
    last_four = digits[-4:]
    method_type = f"\u2022\u2022\u2022\u2022 {last_four}"

    if body.is_default:
        db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).update({"is_default": False})

    method = PaymentMethod(
        user_id=user.id,
        method_type=method_type,
        is_default=body.is_default or not db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).first(),
    )
    db.add(method)
    db.commit()
    return MessageResponse(message="Card saved successfully")


@router.delete("/{method_id}/delete", response_model=MessageResponse)
def delete_payment_method(
    method_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    db.delete(method)
    db.commit()
    return MessageResponse(message="Payment method deleted successfully")


@router.put("/{method_id}/default", response_model=MessageResponse)
def set_default_payment_method(
    method_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    method = (
        db.query(PaymentMethod)
        .filter(PaymentMethod.id == method_id, PaymentMethod.user_id == user.id)
        .first()
    )
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    db.query(PaymentMethod).filter(PaymentMethod.user_id == user.id).update({"is_default": False})
    method.is_default = True
    db.commit()
    return MessageResponse(message="Default payment method updated")


# Payment endpoints
@router.get("/payments")
def payment_history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    payments = (
        db.query(Payment)
        .join(Order)
        .filter(Order.user_id == user.id)
        .order_by(Payment.paid_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "order_id": p.order_id,
            "amount": p.amount,
            "status": p.status,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        }
        for p in payments
    ]
