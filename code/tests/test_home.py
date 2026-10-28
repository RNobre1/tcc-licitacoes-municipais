from django.conf import settings


def test_home_page_renders_system_name_and_header(client):
    response = client.get("/")

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    # 1. System name in <title>
    assert f"<title>{settings.SYSTEM_NAME}</title>" in content

    # 2. System name in the header / nav
    assert "<header" in content and f"<strong>{settings.SYSTEM_NAME}</strong>" in content

    # 3. The page has its own <h1>
    assert "<h1>" in content
