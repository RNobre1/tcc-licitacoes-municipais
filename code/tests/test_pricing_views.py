import re
from decimal import Decimal
from html import escape

import pytest
from django.test import Client
from django.urls import reverse

from pricing import demo_data
from pricing.ranking import rank_candidates
from procurement.demo_data import get_item


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


@pytest.mark.parametrize("method", [["get", "put", "delete"][i] for i in range(3)])
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


# =====================================================================
# Step 3: Screening View Tests
# =====================================================================


def test_pricing_screening_route_matches_contract():
    assert reverse("pricing:screening", args=[1]) == "/items/1/screening/"


def test_pricing_screening_returns_404_for_unknown_item(client):
    url = reverse("pricing:screening", args=[9999])
    response = client.get(url)
    assert response.status_code == 404


def test_pricing_screening_renders_screening_template_and_base(client):
    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert "pricing/screening.html" in [t.name for t in response.templates]
    assert "base.html" in [t.name for t in response.templates]


def test_pricing_screening_context_without_expected_price(client):
    item = get_item(1)
    assert item is not None
    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["item"] == item
    assert response.context["expected_price"] is None

    expected_candidates = rank_candidates(demo_data.candidates_for(1), None, item.unit)
    assert [c.id for c in response.context["candidates"]] == [c.id for c in expected_candidates]

    for candidate in response.context["candidates"]:
        assert response.context["proximities"][candidate.id] == "—"


def test_pricing_screening_context_with_expected_price_ranks_and_calculates_proximities(client):
    item = get_item(1)
    assert item is not None

    url = reverse("pricing:screening", args=[1]) + "?expected_price=28.00"
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["expected_price"] == Decimal("28.00")

    candidate_ids = [c.id for c in response.context["candidates"]]
    # Proximity reorders candidates within high similarity band:
    # 2 (price 27.90) and 3 (price 29.00) are closer to 28.00 than 1 (price 26.50)
    assert candidate_ids == [2, 3, 1, 4]

    proximities = response.context["proximities"]
    assert proximities[2] == "1,00× abaixo"
    assert proximities[3] == "1,04× acima"
    assert proximities[1] == "1,06× abaixo"
    assert proximities[4] == "unidade diferente"


@pytest.mark.parametrize(
    "raw_query,expected_val",
    [
        ("28,00", Decimal("28.00")),
        ("12.50", Decimal("12.50")),
        ("  15,75  ", Decimal("15.75")),
    ],
)
def test_pricing_screening_accepts_comma_and_dot_expected_price(client, raw_query, expected_val):
    url = reverse("pricing:screening", args=[1]) + f"?expected_price={raw_query}"
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["expected_price"] == expected_val


@pytest.mark.parametrize("invalid_raw", ["", "banana", "-5.00", "0", "0,00"])
def test_pricing_screening_ignores_invalid_or_non_positive_expected_price(client, invalid_raw):
    url = reverse("pricing:screening", args=[1]) + f"?expected_price={invalid_raw}"
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["expected_price"] is None


def test_pricing_screening_adapts_string_session_decisions_to_integer_keys(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "reject")
    assert client.session["screening_decisions"] == {"1": "accept", "2": "reject"}

    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["decisions"] == {1: "accept", 2: "reject"}
    html = response.content.decode()
    assert "Aceito" in html
    assert "Descartado" in html


# =====================================================================
# Step 4: HTMX Row Swap Proximity Preservation Tests
# =====================================================================


def test_decide_preserves_proximity_when_expected_price_is_posted(client):
    url = reverse("pricing:decide", args=[1])
    response = client.post(url, {"decision": "accept", "expected_price": "28.00"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "1,06× abaixo" in html
    assert "<td>—</td>" not in html


def test_decide_preserves_unit_mismatch_proximity_when_expected_price_is_posted(client):
    url = reverse("pricing:decide", args=[4])
    response = client.post(url, {"decision": "reject", "expected_price": "28.00"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "unidade diferente" in html


def test_decide_preserves_expected_price_in_hidden_input(client):
    url = reverse("pricing:decide", args=[1])
    response = client.post(url, {"decision": "accept", "expected_price": "28.00"})

    assert response.status_code == 200
    html = response.content.decode()
    assert '<input type="hidden" name="expected_price" value="28.00">' in html


def test_decide_accepts_comma_in_posted_expected_price(client):
    url = reverse("pricing:decide", args=[1])
    response = client.post(url, {"decision": "accept", "expected_price": "28,00"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "1,06× abaixo" in html
    assert '<input type="hidden" name="expected_price" value="28.00">' in html


def test_decide_without_expected_price_renders_dash_and_empty_hidden_input(client):
    url = reverse("pricing:decide", args=[1])
    response = client.post(url, {"decision": "accept"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "<td>—</td>" in html
    assert '<input type="hidden" name="expected_price" value="">' in html


@pytest.mark.parametrize("raw", ["Infinity", "inf", "1e999", "1e-999", "NaN"])
def test_screening_and_decide_treat_unusable_expected_prices_as_none(client, raw):
    page = client.get(reverse("pricing:screening", args=[1]) + f"?expected_price={raw}")
    assert page.status_code == 200
    assert page.context["expected_price"] is None

    row = client.post(
        reverse("pricing:decide", args=[1]), {"decision": "accept", "expected_price": raw}
    )
    assert row.status_code == 200
    html = row.content.decode()
    assert "<td>—</td>" in html
    assert '<input type="hidden" name="expected_price" value="">' in html


def test_a_swapped_row_shows_the_same_proximity_as_the_screening_page(client):
    for item_id in (1, 2, 3, 5):
        page = client.get(reverse("pricing:screening", args=[item_id]) + "?expected_price=20")
        assert page.status_code == 200
        for candidate in page.context["candidates"]:
            row = client.post(
                reverse("pricing:decide", args=[candidate.id]),
                {"decision": "accept", "expected_price": "20"},
            ).content.decode()

            assert f"<td>{page.context['proximities'][candidate.id]}</td>" in row, candidate.id


def test_decide_uses_the_unit_of_the_candidates_own_item(client):
    # candidate 5 belongs to item 2 (unit "unidade"), whereas item 1 is sold by "pacote"
    row = client.post(
        reverse("pricing:decide", args=[5]), {"decision": "accept", "expected_price": "1.50"}
    ).content.decode()

    assert "unidade diferente" not in row
    assert "<td>1,20× abaixo</td>" in row


def test_screening_view_announces_ignored_expected_price_when_unusable_query_param_given(client):
    url = reverse("pricing:screening", args=[1]) + "?expected_price=1.234,50"
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["expected_price"] is None
    assert response.context["expected_price_ignored"] is True
    assert "Preço esperado ignorado" in response.content.decode()


def test_screening_view_does_not_announce_ignored_expected_price_when_empty_query(client):
    url = reverse("pricing:screening", args=[1])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["expected_price"] is None
    assert response.context.get("expected_price_ignored") in (False, None)
    assert "Preço esperado ignorado" not in response.content.decode()


@pytest.mark.parametrize("raw", ["1.234,50", "1,234.50", "banana", "0", "-5", "Infinity", "1e999"])
def test_screening_announces_every_unusable_expected_price(client, raw):
    response = client.get(reverse("pricing:screening", args=[1]), {"expected_price": raw})

    assert response.status_code == 200
    assert response.context["expected_price"] is None
    assert "Preço esperado ignorado" in response.content.decode()


@pytest.mark.parametrize("raw", ["12,50", "12.50", "  12,50  ", "28"])
def test_screening_does_not_announce_a_usable_expected_price(client, raw):
    response = client.get(reverse("pricing:screening", args=[1]), {"expected_price": raw})

    assert response.context["expected_price"] is not None
    assert "Preço esperado ignorado" not in response.content.decode()


def test_screening_does_not_announce_a_blank_expected_price(client):
    response = client.get(reverse("pricing:screening", args=[1]), {"expected_price": "   "})

    assert response.context["expected_price"] is None
    assert "Preço esperado ignorado" not in response.content.decode()


def test_the_ignored_expected_price_notice_sits_in_the_form_of_the_field(client):
    html = client.get(
        reverse("pricing:screening", args=[1]), {"expected_price": "1.234,50"}
    ).content.decode()

    form = re.search(r'<form method="get".*?</form>', html, re.S).group(0)
    assert 'name="expected_price"' in form
    assert "Preço esperado ignorado" in form


def test_an_ignored_expected_price_leaves_the_order_without_a_price(client):
    url = reverse("pricing:screening", args=[1])
    plain = [c.id for c in client.get(url).context["candidates"]]
    priced = [c.id for c in client.get(url, {"expected_price": "28"}).context["candidates"]]
    ignored = [c.id for c in client.get(url, {"expected_price": "1.234,50"}).context["candidates"]]

    assert priced != plain  # the price does reorder this item, so the comparison means something
    assert ignored == plain
