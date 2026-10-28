import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory


def _render_base() -> str:
    return render_to_string("base.html", request=RequestFactory().get("/"))


def test_declares_brazilian_portuguese():
    assert '<html lang="pt-br">' in _render_base()


def test_default_title_is_the_system_name():
    assert settings.SYSTEM_NAME, "settings.SYSTEM_NAME must not be empty"
    rendered = _render_base()
    assert f"<title>{settings.SYSTEM_NAME}</title>" in rendered


def test_stylesheet_link_resolves_to_a_vendored_file():
    rendered = _render_base()
    match = re.search(r'<link rel="stylesheet" href="/static/([^"]+)">', rendered)
    assert match, "base.html has no stylesheet link under /static/"
    assert finders.find(match.group(1)), f"{match.group(1)} is not a static file"
