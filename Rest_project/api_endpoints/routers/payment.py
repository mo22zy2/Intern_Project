from django.core.exceptions import ObjectDoesNotExist
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import PaymentMethodCreate, MessageResponse
from ..auth_utils import get_current_user
from api.services import payment_service

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


@router.get("/")
def payment_methods(user=Depends(get_current_user)):
    methods = payment_service.get_user_payment_methods(user)
    return [
        {"id": m.id, "method_type": m.method_type, "is_default": m.is_default}
        for m in methods
    ]


@router.post("/add", response_model=MessageResponse, status_code=201)
def add_payment_method(
    body: PaymentMethodCreate,
    user=Depends(get_current_user),
):
    try:
        payment_service.add_payment_method(user, body.card_number, body.is_default)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Card saved successfully")


@router.delete("/{method_id}/delete", response_model=MessageResponse)
def delete_payment_method(
    method_id: int,
    user=Depends(get_current_user),
):
    try:
        payment_service.delete_payment_method(user, method_id)
    except ObjectDoesNotExist:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return MessageResponse(message="Payment method deleted successfully")


@router.put("/{method_id}/default", response_model=MessageResponse)
def set_default_payment_method(
    method_id: int,
    user=Depends(get_current_user),
):
    try:
        payment_service.set_default_payment_method(user, method_id)
    except ObjectDoesNotExist:
        raise HTTPException(status_code=404, detail="Payment method not found")
    return MessageResponse(message="Default payment method updated")


@router.get("/payments")
def payment_history(user=Depends(get_current_user)):
    payments = payment_service.get_user_payments(user)
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
