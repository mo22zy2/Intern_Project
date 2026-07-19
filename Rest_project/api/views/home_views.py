from datetime import date
from django.shortcuts import render
from django.db.models import Avg
from ..models import Menu, Category, Order, ReservationSystem


def home(request):
    featured_items = Menu.objects.select_related("item", "category").filter(available=True).annotate(
        avg_rating=Avg("reviews__rating")
    ).order_by("-popularity_score")[:4]

    context = {
        "featured_items": featured_items,
        "total_menu_items": Menu.objects.filter(available=True).count(),
        "total_categories": Category.objects.count(),
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
