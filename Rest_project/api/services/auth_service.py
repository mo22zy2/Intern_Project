import random
from datetime import date


def _imports():
    from django.contrib.auth import authenticate
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    from ..models import User, UserSettings
    return authenticate, validate_password, ValidationError, User, UserSettings


def _username_suggestions(username):
    User, _, _, _, _ = None, None, None, None, None
    from ..models import User
    suggestions = []
    for suffix in ["123", "1234", "1", "2024", "2025", "00"]:
        sug = f"{username}{suffix}"
        if not User.objects.filter(username=sug).exists():
            suggestions.append(sug)
            if len(suggestions) >= 3:
                break
    if not suggestions:
        for _ in range(3):
            sug = f"{username}{random.randint(10, 999)}"
            if not User.objects.filter(username=sug).exists():
                suggestions.append(sug)
    return suggestions


def register_user(username, email, password, first_name, last_name, phone, birth):
    _, _, _, User, UserSettings = _imports()
    if User.objects.filter(username=username).exists():
        sug = _username_suggestions(username)
        msg = "This username is taken. Try a different one."
        if sug:
            msg += f" For example: {', '.join(sug)}"
        raise ValueError(msg)

    if User.objects.filter(email=email).exists():
        raise ValueError("This email is already registered. Try logging in instead.")

    if birth and birth > date.today():
        raise ValueError("Birth date cannot be in the future.")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        birth=birth,
    )
    UserSettings.objects.create(user=user)
    return user


def validate_registration_data(password, confirm_password):
    _, validate_password, ValidationError, _, _ = _imports()
    if password != confirm_password:
        raise ValueError("Passwords do not match")

    try:
        validate_password(password)
    except ValidationError:
        raise ValueError("Password is too weak. Try a mix of letters, numbers, and symbols (8+ characters).")


def authenticate_user(username, password, request=None):
    authenticate, _, _, _, _ = _imports()
    user = authenticate(request=request, username=username, password=password)
    return user


def change_password(user, old_password, new_password, confirm_password):
    _, validate_password, ValidationError, _, _ = _imports()
    if not user.check_password(old_password):
        raise ValueError("Current password is incorrect")

    if new_password != confirm_password:
        raise ValueError("New passwords do not match")

    try:
        validate_password(new_password, user)
    except ValidationError:
        raise ValueError("Password is too weak. Try a mix of letters, numbers, and symbols (8+ characters).")

    user.set_password(new_password)
    user.save()
