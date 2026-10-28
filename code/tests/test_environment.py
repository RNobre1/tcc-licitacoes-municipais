import pytest

from config.environment import load_environment


def test_missing_secret_key_raises_error_when_debug_is_false():
  """When DEBUG is False, a missing SECRET_KEY must raise a RuntimeError."""
  fake_env = {
      "DEBUG": "False",
      "SECRET_KEY": "",
  }

  with pytest.raises(
      RuntimeError, match="SECRET_KEY environment variable is required"
  ):
    load_environment(fake_env)


def test_allowed_hosts_parsed_from_comma_separated_string():
  """ALLOWED_HOSTS should parse comma-separated strings into a list of hosts."""
  fake_env = {
      "ALLOWED_HOSTS": "localhost, 127.0.0.1, example.gov.br",
  }
  _, _, allowed_hosts = load_environment(fake_env)

  assert allowed_hosts == ["localhost", "127.0.0.1", "example.gov.br"]
