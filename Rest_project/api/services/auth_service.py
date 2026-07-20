def _imports():
    from django.contrib.auth import authenticate
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    from ..models import User, UserSettings
    return authenticate, validate_password, ValidationError, User, UserSettings


def register_user(username, email, password, first_name, last_name, phone, birth):
    _, _, _, User, UserSettings = _imports()
    if User.objects.filter(username=username).exists():
        raise ValueError("Username Already Exists")

    if User.objects.filter(email=email).exists():
        raise ValueError("Email Already Exists")

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
    except ValidationError as e:
        raise ValueError("; ".join(e.messages))


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
    except ValidationError as e:
        raise ValueError("; ".join(e.messages))

    user.set_password(new_password)
    user.save()
