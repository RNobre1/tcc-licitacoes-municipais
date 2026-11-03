import pytest
from django.db import connection
from django.db.utils import OperationalError


@pytest.mark.integration
@pytest.mark.django_db
class TestPostgresConnectionIntegration:
    """Integration test verifying direct connectivity to PostgreSQL."""

    def test_database_connection_uses_postgresql_and_succeeds_or_gives_helpful_message(self):
        """Integration: connects to PostgreSQL or raises helpful error pointing to make up."""
        assert connection.vendor == "postgresql", (
            f"Expected database vendor 'postgresql', got '{connection.vendor}'. "
            "settings.DATABASES['default'] has not been switched to PostgreSQL."
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                assert row == (1,)
        except OperationalError as exc:
            pytest.fail(
                f"Could not connect to PostgreSQL database: {exc}.\n"
                "Ensure local services are running by executing 'make up' in code/."
            )
