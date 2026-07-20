from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ReservationCreate, ReservationUpdate, MessageResponse
from ..auth_utils import get_current_user
from api.services import reservation_service

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("/")
def my_reservations(user=Depends(get_current_user)):
    reservations = reservation_service.get_user_reservations(user)
    return [
        {
            "id": r.id,
            "user_id": r.user.id,
            "reservation_date": r.reservation_date.isoformat(),
            "reservation_time": r.reservation_time.strftime("%H:%M:%S"),
            "seats": r.seats,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reservations
    ]


@router.post("/new", response_model=MessageResponse, status_code=201)
def make_reservation(
    body: ReservationCreate,
    user=Depends(get_current_user),
):
    try:
        reservation_service.create_reservation(
            user=user,
            reservation_date=body.reservation_date,
            reservation_time=body.reservation_time,
            seats=body.seats,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Reservation created successfully")


@router.put("/{reservation_id}/edit", response_model=MessageResponse)
def edit_reservation(
    reservation_id: int,
    body: ReservationUpdate,
    user=Depends(get_current_user),
):
    reservation = reservation_service.get_reservation(user, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    try:
        reservation_service.update_reservation(
            reservation,
            reservation_date=body.reservation_date,
            reservation_time=body.reservation_time,
            seats=body.seats,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageResponse(message="Reservation updated successfully")


@router.delete("/{reservation_id}/cancel", response_model=MessageResponse)
def cancel_reservation(
    reservation_id: int,
    user=Depends(get_current_user),
):
    reservation = reservation_service.get_reservation(user, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    reservation_service.cancel_reservation(reservation)
    return MessageResponse(message="Reservation cancelled")
