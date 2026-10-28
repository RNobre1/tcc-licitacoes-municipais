import os


def load_environment(env=os.environ):
    if env is None:
        env = os.environ

    DEBUG = env.get("DEBUG", "True").lower() in ('1', 'true', "yes")
    SECRET_KEY = env.get("SECRET_KEY", "")

    if not DEBUG and not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is required when DEBUG is False")

    if not SECRET_KEY:
        SECRET_KEY = "dev-insecure-secret-key-not-for-production"

    ALLOWED_HOSTS = [
        host
        for host in map(str.strip, env.get("ALLOWED_HOSTS", "").split(","))
        if host
    ]

    return DEBUG, SECRET_KEY, ALLOWED_HOSTS

DEBUG, SECRET_KEY, ALLOWED_HOSTS = load_environment()
