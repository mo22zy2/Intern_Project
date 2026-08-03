from datetime import date, datetime


def _imports():
    from ..models import User, UserSettings
    return User, UserSettings


def _parse_birth(birth):
    if birth is None or birth == "":
        return None
    if isinstance(birth, date):
        return birth
    if isinstance(birth, str):
        try:
            return datetime.strptime(birth, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid birth date format.")
    return birth


def get_profile_data(user):
    _, UserSettings = _imports()
    settings, _ = UserSettings.objects.get_or_create(user=user)
    return {
        "user": user,
        "settings": settings,
    }


def update_profile(user, first_name=None, last_name=None, email=None, phone=None, birth=None, address=None, dark_mode=None, locale=None):
    User, UserSettings = _imports()
    if email is not None and email != user.email:
        if User.objects.filter(email=email).exists():
            raise ValueError("This email is already in use.")

    birth = _parse_birth(birth)
    if birth is not None and birth > date.today():
        raise ValueError("Birth date cannot be in the future.")

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
    if address is not None:
        user.address = address
    user.save()

    if dark_mode is not None:
        settings.dark_mode = dark_mode
    if locale is not None:
        settings.locale = locale
    settings.save()
