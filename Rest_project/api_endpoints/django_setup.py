import os
import django
from pathlib import Path


def setup_django():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "Rest_project.settings"
    )
    _ = Path(__file__).resolve().parent.parent
    django.setup()
