from datetime import date, time, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ReservationSystem
from ..schemas import ReservationCreate, ReservationUpdate, ReservationOut, MessageResponse
from ..auth_utils import get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])

OPEN_TIME = time(10, 0)
CLOSE_TIME = time(4, 0)


def _naive(t: time) -> time:
    return t.replace(tzinfo=None) if t.tzinfo else t


def _validate_reservation(res_date: date, res_time: time):
    now = datetime.now()
    now_date = now.date()
    if res_date < now_date:
        raise HTTPException(status_code=400, detail="Reservation date cannot be in the past")
    if res_date == now_date and _naive(res_time) < _naive(now.time()):
        raise HTTPException(status_code=400, detail="Reservation time cannot be in the past")
    if _naive(res_time) >= CLOSE_TIME and _naive(res_time) < OPEN_TIME:
        raise HTTPException(status_code=400, detail="Reservation time must be between 10:00 and 04:00 (next day)")


@router.get("/")
def my_reservations(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reservations = (
        db.query(ReservationSystem)
        .filter(ReservationSystem.user_id == user.id)
        .order_by(ReservationSystem.reservation_date.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
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
    db: Session = Depends(get_db),
):
    _validate_reservation(body.reservation_date, body.reservation_time)
    res = ReservationSystem(
        user_id=user.id,
        reservation_date=body.reservation_date,
        reservation_time=body.reservation_time,
        seats=body.seats,
        status="confirmed",
    )
    db.add(res)
    db.commit()
    return MessageResponse(message="Reservation created successfully")


@router.put("/{reservation_id}/edit", response_model=MessageResponse)
def edit_reservation(
    reservation_id: int,
    body: ReservationUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = (
        db.query(ReservationSystem)
        .filter(ReservationSystem.id == reservation_id, ReservationSystem.user_id == user.id)
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot edit a cancelled reservation")

    new_date = body.reservation_date or res.reservation_date
    new_time = body.reservation_time or res.reservation_time
    _validate_reservation(new_date, new_time)

    if body.reservation_date:
        res.reservation_date = body.reservation_date
    if body.reservation_time:
        res.reservation_time = body.reservation_time
    if body.seats:
        res.seats = body.seats
    db.commit()
    return MessageResponse(message="Reservation updated successfully")


@router.delete("/{reservation_id}/cancel", response_model=MessageResponse)
def cancel_reservation(
    reservation_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = (
        db.query(ReservationSystem)
        .filter(ReservationSystem.id == reservation_id, ReservationSystem.user_id == user.id)
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status == "cancelled":
        return MessageResponse(message="This reservation is already cancelled")
    res.status = "cancelled"
    db.commit()
    return MessageResponse(message="Reservation cancelled")
