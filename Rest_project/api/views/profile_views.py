from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg
from django.utils.translation import gettext as _
from ..models import User, UserSettings, Review, PaymentMethod


@login_required(login_url="login")
def profile(request):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
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
    settings, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user = request.user
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

        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, _("Email already in use."))
            return render(request, "profile/profile.html", {"settings": settings, "editing": True})

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.birth = birth
        user.save()

        settings.dark_mode = dark_mode
        settings.locale = locale
        settings.save()

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

    if not request.user.check_password(old):
        messages.error(request, _("Current password is incorrect."))
        return redirect("profile")

    if new != confirm:
        messages.error(request, _("New passwords do not match."))
        return redirect("profile")

    try:
        validate_password(new, request.user)
    except ValidationError as e:
        for error in e.messages:
            messages.error(request, error)
        return redirect("profile")

    request.user.set_password(new)
    request.user.save()
    update_session_auth_hash(request, request.user)
    messages.success(request, _("Password changed."))
    return redirect("profile")
