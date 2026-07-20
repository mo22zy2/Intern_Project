from datetime import date
from django.shortcuts import render
from ..services import menu_service
from ..models import Order, ReservationSystem


def home(request):
    context = {
        "featured_items": menu_service.get_featured_items(),
        "total_menu_items": menu_service.get_total_menu_items_count(),
        "total_categories": menu_service.get_total_categories_count(),
    }

    if request.user.is_authenticated:
        context["recent_orders"] = Order.objects.filter(user=request.user).order_by("-created_at")[:3]
        context["upcoming_reservations"] = ReservationSystem.objects.filter(
            user=request.user,
            reservation_date__gte=date.today(),
        ).exclude(status="cancelled").order_by("reservation_date", "reservation_time")[:3]
        context["total_orders"] = Order.objects.filter(user=request.user).count()
        context["total_reservations"] = ReservationSystem.objects.filter(user=request.user).count()

    return render(request, "home.html", context)
