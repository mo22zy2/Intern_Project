def _imports():
    from ..models import User, UserSettings
    return User, UserSettings


def get_profile_data(user):
    _, UserSettings = _imports()
    settings, _ = UserSettings.objects.get_or_create(user=user)
    return {
        "user": user,
        "settings": settings,
    }


def update_profile(user, first_name=None, last_name=None, email=None, phone=None, birth=None, dark_mode=None, locale=None):
    User, UserSettings = _imports()
    if email is not None and email != user.email:
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already in use")

    settings, _ = UserSettings.objects.get_or_create(user=user)

    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
    if phone is not None:
        user.phone = phone
    if birth is not None:
        user.birth = birth
    user.save()

    if dark_mode is not None:
        settings.dark_mode = dark_mode
    if locale is not None:
        settings.locale = locale
    settings.save()
