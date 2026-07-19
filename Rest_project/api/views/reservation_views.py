from datetime import date, datetime, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import ReservationSystem

OPEN_TIME = time(10, 0)
CLOSE_TIME = time(4, 0)


def _valid_reservation_hour(t):
    return t >= OPEN_TIME or t <= CLOSE_TIME


def _reservation_datetime(d, t):
    return datetime.combine(d, t)


@login_required(login_url="login")
def make_reservation(request):
    if request.method == "POST":
        reservation_date = request.POST.get("reservation_date", "").strip()
        reservation_time = request.POST.get("reservation_time", "").strip()
        seats = request.POST.get("seats", "").strip()

        if not reservation_date or not reservation_time or not seats:
            messages.error(request, "All fields are required.")
            return render(request, "reservation/reservation_form.html", {"today": date.today()})

        try:
            parsed_date = date.fromisoformat(reservation_date)
            parsed_time = time.fromisoformat(reservation_time)
            seats = int(seats)
            if seats < 1:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid date, time, or seats value.")
            return render(request, "reservation/reservation_form.html", {"today": date.today()})

        now = datetime.now()
        dt = _reservation_datetime(parsed_date, parsed_time)

        if dt <= now:
            messages.error(request, "Reservation cannot be in the past.")
            return render(request, "reservation/reservation_form.html", {"today": date.today()})

        if not _valid_reservation_hour(parsed_time):
            messages.error(request, "Restaurant hours are 10:00 – 04:00. Please pick a time within operating hours.")
            return render(request, "reservation/reservation_form.html", {"today": date.today()})

        ReservationSystem.objects.create(
            user=request.user,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            seats=seats,
            status="confirmed",
        )

        messages.success(request, _("Reservation confirmed!"))
        return redirect("my_reservations")

    return render(request, "reservation/reservation_form.html", {"today": date.today()})


@login_required(login_url="login")
def my_reservations(request):
    reservations = ReservationSystem.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "reservation/my_reservations.html", {"reservations": reservations})


@login_required(login_url="login")
def edit_reservation(request, reservation_id):
    reservation = get_object_or_404(ReservationSystem, id=reservation_id, user=request.user)

    if request.method == "POST":
        if reservation.status == "cancelled":
            messages.error(request, _("Cannot edit a cancelled reservation."))
            return redirect("my_reservations")

        reservation_date = request.POST.get("reservation_date", "").strip()
        reservation_time = request.POST.get("reservation_time", "").strip()
        seats = request.POST.get("seats", "").strip()

        if not reservation_date or not reservation_time or not seats:
            messages.error(request, "All fields are required.")
            return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})

        try:
            parsed_date = date.fromisoformat(reservation_date)
            parsed_time = time.fromisoformat(reservation_time)
            seats = int(seats)
            if seats < 1:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid date, time, or seats value.")
            return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})

        now = datetime.now()
        dt = _reservation_datetime(parsed_date, parsed_time)

        if dt <= now:
            messages.error(request, "Reservation cannot be in the past.")
            return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})

        if not _valid_reservation_hour(parsed_time):
            messages.error(request, "Restaurant hours are 10:00 – 04:00. Please pick a time within operating hours.")
            return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})

        reservation.reservation_date = reservation_date
        reservation.reservation_time = reservation_time
        reservation.seats = seats
        reservation.save()

        messages.success(request, _("Reservation updated."))
        return redirect("my_reservations")

    return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})


@login_required(login_url="login")
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(ReservationSystem, id=reservation_id, user=request.user)
    if reservation.status == "cancelled":
        messages.info(request, _("This reservation is already cancelled."))
    else:
        reservation.status = "cancelled"
        reservation.save()
        messages.success(request, _("Reservation cancelled."))
    return redirect("my_reservations")
