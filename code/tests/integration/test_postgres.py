import pytest
from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError


@pytest.mark.integration
def test_connects_to_the_configured_database(django_db_blocker):
    """Integration test verifying direct connectivity to PostgreSQL."""
    assert connection.vendor == "postgresql"
    failure = None
    current = None
    with django_db_blocker.unblock():
        try:
            with connection.cursor() as cursor:
                cursor.execute("select current_database()")
                current = cursor.fetchone()
        except OperationalError as exc:
            failure = str(exc)
        finally:
            connection.close()
    if failure:
        pytest.fail(
            f"Could not connect to PostgreSQL: {failure}\n"
            "Start the services with 'make up' in code/.",
            pytrace=False,
        )
    assert current == (settings.DATABASES["default"]["NAME"],)
