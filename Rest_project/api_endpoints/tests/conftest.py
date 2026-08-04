import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def django_settings():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Rest_project.settings")
    import django

    django.setup()
