from django.urls import reverse

from pricing import demo_data


def test_pricing_decide_route_matches_contract():
    assert reverse("pricing:decide", args=[1]) == "/candidates/1/decision/"


def test_pricing_decide_accept_updates_session_and_renders_partial_fragment(client):
    candidate = demo_data.get_candidate(1)
    assert candidate is not None

    url = reverse("pricing:decide", args=[candidate.id])
    response = client.post(url, {"decision": "accept"})

    assert response.status_code == 200
    assert "pricing/_candidate.html" in [t.name for t in response.templates]
    assert "base.html" not in [t.name for t in response.templates]

    html = response.content.decode()
    assert "Aceito" in html
    assert candidate.description in html
    assert "<!DOCTYPE" not in html

    assert client.session["screening_decisions"][str(candidate.id)] == "accept"


def test_pricing_decide_reject_updates_session_and_renders_partial_fragment(client):
    candidate = demo_data.get_candidate(2)
    assert candidate is not None

    url = reverse("pricing:decide", args=[candidate.id])
    response = client.post(url, {"decision": "reject"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "Descartado" in html
    assert client.session["screening_decisions"][str(candidate.id)] == "reject"


def test_pricing_decide_returns_404_for_unknown_candidate(client):
    url = reverse("pricing:decide", args=[9999])
    response = client.post(url, {"decision": "accept"})

    assert response.status_code == 404
