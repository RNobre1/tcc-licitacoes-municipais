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

    return debug, secret_key, allowed_hosts


DEBUG, SECRET_KEY, ALLOWED_HOSTS = load_environment()
