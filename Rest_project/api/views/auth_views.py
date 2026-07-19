from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..models import User, UserSettings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


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
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, "auth/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, _("Username Already Exists"))
            return render(request, "auth/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, _("Email Already Exists"))
            return render(request, "auth/register.html")

        if password != confirm_password:
            messages.error(request, _("Passwords do not match."))
            return render(request, "auth/register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            birth=birth
        )

        UserSettings.objects.create(user=user)

        auth_login(request, user)
        messages.success(request, _("Signed up successfully"))
        return redirect("menu")

    return render(request, "auth/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password")

        user = authenticate(request=request, username=username, password=password)

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