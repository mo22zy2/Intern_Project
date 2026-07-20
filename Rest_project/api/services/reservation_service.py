from datetime import date, datetime, time, timedelta, timezone

OPEN_TIME = time(10, 0)
CLOSE_TIME = time(4, 0)


def _imports():
    from ..models import ReservationSystem
    return ReservationSystem,


def _valid_reservation_hour(t):
    return t >= OPEN_TIME or t <= CLOSE_TIME


def _reservation_datetime(d, t):
    """
    If the reservation time is between midnight and 4 AM,
    treat it as belonging to the NEXT calendar day.
    Example:
        Date = 2026-07-20
        Time = 02:00
        => 2026-07-21 02:00
    """
    if t <= CLOSE_TIME:
        d = d + timedelta(days=1)
    return datetime.combine(d, t, tzinfo=timezone.utc)


def validate_reservation_input(reservation_date, reservation_time, seats):
    if not reservation_date or not reservation_time or not seats:
        raise ValueError("All fields are required")

    try:
        parsed_date = date.fromisoformat(reservation_date)
        parsed_time = time.fromisoformat(reservation_time)
        if parsed_time.tzinfo is not None:
            parsed_time = parsed_time.replace(tzinfo=None)
        seats = int(seats)
        if seats < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Invalid date, time, or seats value")

    now = datetime.now(timezone.utc)
    dt = _reservation_datetime(parsed_date, parsed_time)

    if dt <= now:
        raise ValueError("Reservation cannot be in the past")

    if not _valid_reservation_hour(parsed_time):
        raise ValueError(
            "Restaurant hours are 10:00 AM – 4:00 AM. "
            "Please choose a valid reservation time."
        )

    return parsed_date, parsed_time, seats


def _to_date_str(d):
    if isinstance(d, date) and not isinstance(d, str):
        return d.isoformat()
    return str(d)


def _to_time_str(t):
    if isinstance(t, time) and not isinstance(t, str):
        return t.isoformat()
    return str(t)


def create_reservation(user, reservation_date, reservation_time, seats):
    parsed_date, parsed_time, parsed_seats = validate_reservation_input(
        _to_date_str(reservation_date),
        _to_time_str(reservation_time),
        seats,
    )
    ReservationSystem, = _imports()
    return ReservationSystem.objects.create(
        user=user,
        reservation_date=parsed_date,
        reservation_time=parsed_time,
        seats=parsed_seats,
        status="pending",
    )


def get_user_reservations(user):
    ReservationSystem, = _imports()
    return ReservationSystem.objects.filter(user=user).order_by("-created_at")


def get_reservation(user, reservation_id):
    from django.core.exceptions import ObjectDoesNotExist
    ReservationSystem, = _imports()
    try:
        return ReservationSystem.objects.get(id=reservation_id, user=user)
    except ObjectDoesNotExist:
        return None


def update_reservation(reservation, reservation_date=None, reservation_time=None, seats=None):
    if reservation.status == "cancelled":
        raise ValueError("Cannot edit a cancelled reservation")

    new_date = _to_date_str(reservation_date) if reservation_date else None
    new_time = _to_time_str(reservation_time) if reservation_time else None

    parsed_date, parsed_time, parsed_seats = validate_reservation_input(
        new_date or reservation.reservation_date.isoformat(),
        new_time or reservation.reservation_time.isoformat(),
        seats or reservation.seats,
    )
    if reservation_date:
        reservation.reservation_date = parsed_date
    if reservation_time:
        reservation.reservation_time = parsed_time
    if seats:
        reservation.seats = parsed_seats
    reservation.save()


def cancel_reservation(reservation):
    if reservation.status == "cancelled":
        return False
    reservation.status = "cancelled"
    reservation.save()
    return True