import django
from django.conf import settings


def test_project_is_wired():
    django.setup()
    assert settings.ROOT_URLCONF == "config.urls"
