from html import escape

import pytest
from django.test import Client
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


def _decide(client, candidate_id, decision):
    return client.post(reverse("pricing:decide", args=[candidate_id]), {"decision": decision})


def test_decide_stores_every_decision_and_the_last_one_for_a_candidate_wins(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "reject")
    _decide(client, 1, "reject")

    assert client.session["screening_decisions"] == {"1": "reject", "2": "reject"}


def test_decide_returns_the_row_of_the_candidate_that_was_asked_for(client):
    for candidate_id in (1, 2, 5):
        candidate = demo_data.get_candidate(candidate_id)
        assert candidate is not None
        html = _decide(client, candidate_id, "reject").content.decode()

        assert html.lstrip().startswith(f'<tr id="candidate-{candidate_id}">')
        assert html.count("<tr") == 1
        assert f'hx-target="#candidate-{candidate_id}"' in html
        assert escape(candidate.description) in html


@pytest.mark.parametrize("value", [None, "", "banana", "ACCEPT", "maybe"])
def test_decide_rejects_anything_but_accept_or_reject_and_stores_nothing(client, value):
    data = {} if value is None else {"decision": value}
    response = client.post(reverse("pricing:decide", args=[1]), data)

    assert response.status_code == 400
    assert response.content == b"Invalid decision"
    assert "screening_decisions" not in client.session


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_decide_is_post_only_and_a_wrong_method_changes_nothing(client, method):
    response = getattr(client, method)(reverse("pricing:decide", args=[1]))

    assert response.status_code == 405
    assert "screening_decisions" not in client.session


def test_decide_is_csrf_protected():
    client = Client(enforce_csrf_checks=True)
    url = reverse("pricing:decide", args=[1])

    assert client.post(url, {"decision": "accept"}).status_code == 403

    client.cookies["csrftoken"] = "a" * 32
    response = client.post(url, {"decision": "accept", "csrfmiddlewaretoken": "a" * 32})
    assert response.status_code == 200
