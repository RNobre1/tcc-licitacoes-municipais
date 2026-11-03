import re
from pathlib import Path

import pytest

from config.environment import load_environment


class TestDatabaseEnvironmentVariables:
    """Unit tests for reading database connection settings from environment."""

    def test_load_environment_reads_all_database_variables(self):
        """load_environment parses DATABASE_HOST, PORT, NAME, USER, PASSWORD."""
        fake_env = {
            "SECRET_KEY": "any-valid-key",
            "DATABASE_HOST": "127.0.0.1",
            "DATABASE_PORT": "5433",
            "DATABASE_NAME": "preparatory_phase",
            "DATABASE_USER": "preparatory_phase",
            "DATABASE_PASSWORD": "local-dev-password",
        }
        res = load_environment(fake_env)
        # We unpack database configuration from load_environment result
        # (debug, secret_key, allowed_hosts, db_config) or dict attributes
        assert len(res) == 4
        db_config = res[3]
        assert db_config == {
            "HOST": "127.0.0.1",
            "PORT": "5433",
            "NAME": "preparatory_phase",
            "USER": "preparatory_phase",
            "PASSWORD": "local-dev-password",
        }

    def test_database_port_defaults_to_5433_when_unset(self):
        """When DATABASE_PORT is unset, default to 5433 (isolated container port)."""
        fake_env = {
            "SECRET_KEY": "any-valid-key",
            "DATABASE_HOST": "127.0.0.1",
            "DATABASE_NAME": "preparatory_phase",
            "DATABASE_USER": "preparatory_phase",
            "DATABASE_PASSWORD": "local-dev-password",
        }
        _, _, _, db_config = load_environment(fake_env)
        assert db_config["PORT"] == "5433"


class TestDatabaseSettingsDjango:
    """Unit tests for Django settings.DATABASES configuration."""

    def test_settings_databases_default_uses_postgresql_backend(self, settings):
        """settings.DATABASES['default'] uses django.db.backends.postgresql with psycopg."""
        assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_settings_databases_default_matches_environment_variables(self, monkeypatch, settings):
        """settings.DATABASES['default'] pulls credentials from environment."""
        assert settings.DATABASES["default"]["HOST"] == "127.0.0.1"
        assert settings.DATABASES["default"]["PORT"] in (5433, "5433")
        assert settings.DATABASES["default"]["NAME"] == "preparatory_phase"
        assert settings.DATABASES["default"]["USER"] == "preparatory_phase"


class TestComposePostgresEnvironmentVariablesN10:
    """Guard test (N10) ensuring compose.yaml binds PostgreSQL settings to the correct variables."""

    @pytest.mark.parametrize(
        ("env_var", "expected_var_name"),
        [
            ("POSTGRES_DB", "DATABASE_NAME"),
            ("POSTGRES_USER", "DATABASE_USER"),
            ("POSTGRES_PASSWORD", "DATABASE_PASSWORD"),
        ],
    )
    def test_compose_yaml_maps_postgres_setting_to_exact_variable(self, env_var, expected_var_name):
        """N10: compose.yaml maps POSTGRES_* setting to its exact DATABASE_* variable name."""
        compose_path = Path(__file__).resolve().parent.parent / "compose.yaml"
        content = compose_path.read_text(encoding="utf-8")

        # Pattern matches e.g. POSTGRES_DB: ${DATABASE_NAME} or default/required syntax
        pattern = rf"{env_var}:\s*(\${{[^}}]+}})"
        match = re.search(pattern, content)
        assert match is not None, f"Could not find {env_var} mapping in compose.yaml"

        raw_val = match.group(1)
        var_match = re.match(r"\$\{\s*([A-Za-z0-9_]+)(?:[:-?].*)?\s*\}", raw_val)
        assert var_match is not None, f"Value {raw_val} for {env_var} is not a valid ${{VAR}}"
        assert var_match.group(1) == expected_var_name, (
            f"{env_var} mapped to ${{{var_match.group(1)}}} instead of ${{{expected_var_name}}}"
        )
