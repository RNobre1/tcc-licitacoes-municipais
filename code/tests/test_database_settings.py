import json
import os
import subprocess
import sys
from pathlib import Path

from config.environment import load_environment

CODE_DIR = Path(__file__).resolve().parent.parent


def load_env_example_vars():
    env_file = CODE_DIR / ".env.example"
    assert env_file.is_file(), f".env.example not found at {env_file}"
    vars_dict = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vars_dict[k.strip()] = v.strip()
    return vars_dict


class TestDatabaseEnvironmentVariables:
    """Unit tests for reading database connection settings from environment."""

    def test_load_environment_reads_all_database_variables_with_distinct_inputs(self):
        """load_environment parses all database variables using distinct non-default inputs."""
        fake_env = {
            "SECRET_KEY": "any-valid-key",
            "DATABASE_HOST": "db.example.test",
            "DATABASE_PORT": "6543",
            "DATABASE_NAME": "other_database",
            "DATABASE_USER": "other_user",
            "DATABASE_PASSWORD": "local-dev-password",
        }
        res = load_environment(fake_env)
        assert len(res) == 4
        db_config = res[3]
        assert db_config == {
            "HOST": "db.example.test",
            "PORT": "6543",
            "NAME": "other_database",
            "USER": "other_user",
            "PASSWORD": "local-dev-password",
        }

    def test_load_environment_database_defaults(self):
        """When database variables are unset, defaults match expected local-dev settings."""
        fake_env = {
            "SECRET_KEY": "any-valid-key",
        }
        _, _, _, db_config = load_environment(fake_env)
        assert db_config == {
            "HOST": "127.0.0.1",
            "PORT": "5433",
            "NAME": "preparatory_phase",
            "USER": "preparatory_phase",
            "PASSWORD": "",
        }

    def test_database_defaults_match_env_example(self):
        """Freshness guard asserting load_environment defaults mirror .env.example."""
        env_vars = load_env_example_vars()
        _, _, _, db_config = load_environment({"SECRET_KEY": "any-valid-key"})
        assert db_config["HOST"] == env_vars.get("DATABASE_HOST")
        assert db_config["PORT"] == env_vars.get("DATABASE_PORT")
        assert db_config["NAME"] == env_vars.get("DATABASE_NAME")
        assert db_config["USER"] == env_vars.get("DATABASE_USER")


class TestDatabaseSettingsDjango:
    """Unit tests for Django settings.DATABASES configuration."""

    def test_settings_databases_default_uses_postgresql_backend(self, settings):
        """settings.DATABASES['default'] uses django.db.backends.postgresql with psycopg."""
        assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_settings_wire_every_database_variable_to_its_own_key(self):
        """settings.DATABASES['default'] wires each configuration key in a fresh interpreter."""
        env = {
            "PATH": os.environ["PATH"],
            "SECRET_KEY": "any-valid-key",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DATABASE_HOST": "db.example.test",
            "DATABASE_PORT": "6543",
            "DATABASE_NAME": "other_database",
            "DATABASE_USER": "other_user",
            "DATABASE_PASSWORD": "local-dev-password",
        }
        code = (
            "import json, django; django.setup(); from django.conf import settings; "
            "print(json.dumps(settings.DATABASES['default']))"
        )
        out = subprocess.run(
            [sys.executable, "-c", code],
            cwd=CODE_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        default = json.loads(out.stdout)
        assert default["ENGINE"] == "django.db.backends.postgresql"
        assert default["HOST"] == "db.example.test"
        assert default["PORT"] == "6543"
        assert default["NAME"] == "other_database"
        assert default["USER"] == "other_user"
        assert default["PASSWORD"] == "local-dev-password"
