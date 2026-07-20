from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Avg
from django.utils.translation import gettext as _
from ..models import Review, PaymentMethod
from ..services import profile_service, auth_service


@login_required(login_url="login")
def profile(request):
    data = profile_service.get_profile_data(request.user)
    settings = data["settings"]
    reviews_qs = Review.objects.filter(user=request.user).select_related("menu__item", "menu__category").annotate(
        avg_rating=Avg("menu__reviews__rating")
    ).order_by("-created_at")
    paginator = Paginator(reviews_qs, 5)
    page_number = request.GET.get("page")
    reviews = paginator.get_page(page_number)
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    return render(request, "profile/profile.html", {
        "settings": settings,
        "reviews": reviews,
        "payment_methods": payment_methods,
    })


@login_required(login_url="login")
def edit_profile(request):
    data = profile_service.get_profile_data(request.user)
    settings = data["settings"]

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        birth = request.POST.get("birth") or None
        dark_mode = request.POST.get("dark_mode") == "on"
        locale = request.POST.get("locale", "en").strip()

        if not all([first_name, last_name, email, phone, birth]):
            messages.error(request, _("All fields are required."))
            return render(request, "profile/profile.html", {"settings": settings, "editing": True})

        try:
            profile_service.update_profile(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                birth=birth,
                dark_mode=dark_mode,
                locale=locale,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "profile/profile.html", {"settings": settings, "editing": True})

        messages.success(request, _("Profile updated."))
        return redirect("profile")

    return render(request, "profile/profile.html", {"settings": settings, "editing": True})


@login_required(login_url="login")
def change_password(request):
    if request.method != "POST":
        return redirect("profile")

    old = request.POST.get("old_password", "")
    new = request.POST.get("new_password", "")
    confirm = request.POST.get("confirm_password", "")

    try:
        auth_service.change_password(request.user, old, new, confirm)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("profile")

    update_session_auth_hash(request, request.user)
    messages.success(request, _("Password changed."))
    return redirect("profile")
