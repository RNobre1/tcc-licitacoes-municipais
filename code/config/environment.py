import os


def load_environment(env=None):
    if env is None:
        env = os.environ

    debug = env.get("DEBUG", "False").lower() in ("1", "true", "yes")
    secret_key = env.get("SECRET_KEY", "").strip()

    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required")

    allowed_hosts = [
        host for host in map(str.strip, env.get("ALLOWED_HOSTS", "").split(",")) if host
    ]

    test_name = env.get("DATABASE_TEST_NAME", "").strip() or None
    if test_name is not None and not test_name.startswith("test_"):
        # Django drops the test database after the run, so any other name could erase a real one.
        raise RuntimeError("DATABASE_TEST_NAME must start with test_")

    db_config = {
        "HOST": env.get("DATABASE_HOST", "127.0.0.1"),
        "PORT": env.get("DATABASE_PORT", "5433"),
        "NAME": env.get("DATABASE_NAME", "preparatory_phase"),
        "USER": env.get("DATABASE_USER", "preparatory_phase"),
        "PASSWORD": env.get("DATABASE_PASSWORD", ""),
        "TEST_NAME": test_name,
    }

    return debug, secret_key, allowed_hosts, db_config


DEBUG, SECRET_KEY, ALLOWED_HOSTS, DATABASE_CONFIG = load_environment()
