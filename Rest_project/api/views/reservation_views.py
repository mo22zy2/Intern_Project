from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..services import reservation_service


@login_required(login_url="login")
def make_reservation(request):
    if request.method == "POST":
        reservation_date = request.POST.get("reservation_date", "").strip()
        reservation_time = request.POST.get("reservation_time", "").strip()
        seats = request.POST.get("seats", "").strip()

        try:
            reservation_service.create_reservation(
                user=request.user,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                seats=seats,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "reservation/reservation_form.html", {"today": date.today()})

        messages.success(request, _("Reservation confirmed!"))
        return redirect("my_reservations")

    return render(request, "reservation/reservation_form.html", {"today": date.today()})


@login_required(login_url="login")
def my_reservations(request):
    reservations = reservation_service.get_user_reservations(request.user)
    return render(request, "reservation/my_reservations.html", {"reservations": reservations})


@login_required(login_url="login")
def edit_reservation(request, reservation_id):
    reservation = reservation_service.get_reservation(request.user, reservation_id)
    if not reservation:
        from django.shortcuts import get_object_or_404
        from ..models import ReservationSystem
        get_object_or_404(ReservationSystem, id=reservation_id, user=request.user)

    if request.method == "POST":
        reservation_date = request.POST.get("reservation_date", "").strip()
        reservation_time = request.POST.get("reservation_time", "").strip()
        seats = request.POST.get("seats", "").strip()

        try:
            reservation_service.update_reservation(
                reservation,
                reservation_date=reservation_date or None,
                reservation_time=reservation_time or None,
                seats=int(seats) if seats else None,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})

        messages.success(request, _("Reservation updated."))
        return redirect("my_reservations")

    return render(request, "reservation/reservation_form.html", {"reservation": reservation, "today": date.today()})


@login_required(login_url="login")
def cancel_reservation(request, reservation_id):
    reservation = reservation_service.get_reservation(request.user, reservation_id)
    if not reservation:
        from django.shortcuts import get_object_or_404
        from ..models import ReservationSystem
        get_object_or_404(ReservationSystem, id=reservation_id, user=request.user)

    cancelled = reservation_service.cancel_reservation(reservation)
    if cancelled:
        messages.success(request, _("Reservation cancelled."))
    else:
        messages.info(request, _("This reservation is already cancelled."))
    return redirect("my_reservations")
