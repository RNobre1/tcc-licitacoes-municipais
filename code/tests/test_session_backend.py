import pytest
from django.conf import settings
from django.contrib.sessions.models import Session


def test_settings_session_engine_uses_database_backend():
    """SESSION_ENGINE must use database backend (D10)."""
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"


@pytest.mark.django_db
def test_session_persists_in_database(client):
    """Session data must be persisted in the database django_session table."""
    session = client.session
    session["test_key"] = "test_value"
    session.save()

    session_record = Session.objects.filter(session_key=session.session_key).first()
    assert session_record is not None
    decoded = session_record.get_decoded()
    assert decoded.get("test_key") == "test_value"
