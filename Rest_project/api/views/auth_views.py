from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..services import auth_service


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        birth = request.POST.get("birth") or None

        if not all([username, email, password, confirm_password, first_name, last_name, phone, birth]):
            messages.error(request, _("All fields are required."))
            return render(request, "auth/register.html")

        try:
            auth_service.validate_registration_data(password, confirm_password)
        except ValueError as e:
            for msg in str(e).split("; "):
                messages.error(request, msg)
            return render(request, "auth/register.html")

        try:
            user = auth_service.register_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                birth=birth,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "auth/register.html")

        auth_login(request, user)
        messages.success(request, _("Signed up successfully"))
        return redirect("menu")

    return render(request, "auth/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password")

        try:
            user = auth_service.authenticate_user(request=request, username=username, password=password)
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "auth/login.html")

        if user is not None:
            auth_login(request=request, user=user)
            messages.success(request, _("Signed in successfully"))
            return redirect("menu")
        else:
            messages.error(request, _("Invalid Username or Password"))

    return render(request, "auth/login.html")


@login_required(login_url="login")
def logout_view(request):
    if request.method == "POST":
        auth_logout(request=request)
        messages.success(request, _("You have been logged out successfully."))
        return redirect("home")
    return redirect("home")