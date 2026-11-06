import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse


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


def test_header_links_system_name_to_home():
    rendered = _render_base()
    home_url = reverse("procurement:home")
    assert re.search(
        rf'<header\b[^>]*>.*?<a\s+[^>]*href="{re.escape(home_url)}"[^>]*>.*?{re.escape(settings.SYSTEM_NAME)}.*?</a>.*?</header>',
        rendered,
        re.DOTALL,
    )


def test_header_nav_links_to_procurement_list():
    rendered = _render_base()
    list_url = reverse("procurement:list")
    assert re.search(
        rf'<header\b[^>]*>.*?<nav\b[^>]*>.*?<a\s+[^>]*href="{re.escape(list_url)}"[^>]*>\s*Processos\s*</a>.*?</nav>.*?</header>',
        rendered,
        re.DOTALL,
    )
