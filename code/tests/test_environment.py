import pytest

from config.environment import load_environment


def test_missing_debug_defaults_to_false():
    """When DEBUG is not set, it should default to False."""
    fake_env = {"SECRET_KEY": "any-valid-key"}
    debug, _, _ = load_environment(fake_env)
    assert not debug


def test_debug_is_true_with_different_values():
    """DEBUG should be True when set to '1', 'true', or 'yes'."""
    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "DEBUG": "1",
    }
    debug, _, _ = load_environment(fake_env)
    assert debug

    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "DEBUG": "true",
    }
    debug, _, _ = load_environment(fake_env)
    assert debug

    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "DEBUG": "yes",
    }
    debug, _, _ = load_environment(fake_env)
    assert debug


def test_missing_secret_key_raises_error_when_debug_is_false_or_true():
    """When DEBUG is False, a missing SECRET_KEY must raise a RuntimeError."""
    fake_env = {
        "DEBUG": "False",
        "SECRET_KEY": "",
    }

    with pytest.raises(RuntimeError, match="SECRET_KEY environment variable is required"):
        load_environment(fake_env)

    fake_env = {
        "DEBUG": "True",
        "SECRET_KEY": "",
    }

    with pytest.raises(RuntimeError, match="SECRET_KEY environment variable is required"):
        load_environment(fake_env)


def test_allowed_hosts_parsed_from_comma_separated_string():
    """ALLOWED_HOSTS should parse comma-separated strings into a list of hosts."""
    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "ALLOWED_HOSTS": "localhost, 127.0.0.1, example.gov.br",
    }
    _, _, allowed_hosts = load_environment(fake_env)

    assert allowed_hosts == ["localhost", "127.0.0.1", "example.gov.br"]


def test_allowed_hosts_handles_empty_string():
    """ALLOWED_HOSTS should handle an empty string as an empty list."""
    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "ALLOWED_HOSTS": "",
    }
    _, _, allowed_hosts = load_environment(fake_env)

    assert allowed_hosts == []


def test_allowed_hosts_handles_whitespace_string():
    """ALLOWED_HOSTS should handle a whitespace string as an empty list."""
    fake_env = {
        "SECRET_KEY": "any-valid-key",
        "ALLOWED_HOSTS": " ",
    }
    _, _, allowed_hosts = load_environment(fake_env)

    assert allowed_hosts == []
