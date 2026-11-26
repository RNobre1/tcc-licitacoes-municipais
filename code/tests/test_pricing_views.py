import datetime
import re
from decimal import Decimal
from html import escape
from unittest.mock import MagicMock

import pytest
from django.test import Client
from django.urls import reverse

from pricing import demo_data, views
from pricing.ranking import rank_candidates
from pricing.views import build_estimate_panel
from procurement.demo_data import get_item, get_procurement_for_item, list_procurements

pytestmark = pytest.mark.django_db

NO_PRICES = {
    "mean": None,
    "median": None,
    "min": None,
    "count": 0,
    "requires_justification": False,
}


def _flat(text: str) -> str:
    return " ".join(text.split())


def _row(html: str, candidate_id: int) -> str:
    match = re.search(rf'<tr id="candidate-{candidate_id}".*?</tr>', html, re.S)
    return match.group(0) if match else ""


def _estimate(client, item_id):
    return client.get(reverse("pricing:screening", args=[item_id])).context["estimate"]


def _demo_estimate(item, decisions):
    return build_estimate_panel(item, decisions, candidates=demo_data.candidates_for(item.id))


@pytest.fixture(autouse=True)
def _inject_fake_search_for_views(monkeypatch):
    def _fake_search(query, date_window, limit=20):
        for proc in list_procurements():
            for it in proc.items:
                if it.description == query:
                    return demo_data.candidates_for(it.id)
        return []

    monkeypatch.setattr(views, "search_function", _fake_search)


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

    assert client.session["screening_decisions"][f"{candidate.item_id}:{candidate.id}"] == "accept"


def test_pricing_decide_reject_updates_session_and_renders_partial_fragment(client):
    candidate = demo_data.get_candidate(2)
    assert candidate is not None

    url = reverse("pricing:decide", args=[candidate.id])
    response = client.post(url, {"decision": "reject"})

    assert response.status_code == 200
    html = response.content.decode()
    assert "Descartado" in html
    assert client.session["screening_decisions"][f"{candidate.item_id}:{candidate.id}"] == "reject"


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

    assert client.session["screening_decisions"] == {"1:1": "reject", "1:2": "reject"}


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


def test_pricing_screening_provides_procurement_in_context_and_links_back(client):
    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    procurement = get_procurement_for_item(1)
    assert procurement is not None
    assert response.context.get("procurement") == procurement
    detail_url = reverse("procurement:detail", args=[procurement.id])
    assert re.search(
        rf'<a\s+[^>]*href="{re.escape(detail_url)}"[^>]*>\s*Voltar para o processo\s*</a>',
        response.content.decode(),
    )


def test_screening_links_back_to_the_procurement_of_every_item(client):
    for procurement in list_procurements():
        for item in procurement.items:
            response = client.get(reverse("pricing:screening", args=[item.id]))
            detail_url = reverse("procurement:detail", args=[procurement.id])
            assert response.context["procurement"] is procurement
            assert re.search(
                rf'<a\s+[^>]*href="{re.escape(detail_url)}"[^>]*>\s*Voltar para o processo\s*</a>',
                response.content.decode(),
            ), f"item {item.id}"


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
    assert client.session["screening_decisions"] == {"1:1": "accept", "1:2": "reject"}

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


# =====================================================================
# Step 5: Estimate Panel and Parity Tests (T07.2)
# =====================================================================


def test_build_estimate_panel_with_zero_accepted_prices_returns_none_values():
    item = get_item(1)
    assert item is not None
    panel = _demo_estimate(item, {})
    assert panel == {
        "mean": None,
        "median": None,
        "min": None,
        "count": 0,
        "requires_justification": False,
    }


def test_build_estimate_panel_with_one_accepted_price_requires_justification():
    item = get_item(1)
    assert item is not None
    # Candidate 1: price 26.50, unit "pacote"
    panel = _demo_estimate(item, {1: "accept"})
    assert panel == {
        "mean": Decimal("26.50"),
        "median": Decimal("26.50"),
        "min": Decimal("26.50"),
        "count": 1,
        "requires_justification": True,
    }


def test_build_estimate_panel_with_two_accepted_prices_requires_justification():
    item = get_item(1)
    assert item is not None
    # Candidates 1 (26.50) and 2 (27.90)
    panel = _demo_estimate(item, {1: "accept", 2: "accept"})
    assert panel == {
        "mean": Decimal("27.20"),
        "median": Decimal("27.20"),
        "min": Decimal("26.50"),
        "count": 2,
        "requires_justification": True,
    }


def test_build_estimate_panel_with_three_accepted_prices_does_not_require_justification():
    item = get_item(1)
    assert item is not None
    # Candidates 1 (26.50), 2 (27.90), and 3 (29.00)
    panel = _demo_estimate(item, {1: "accept", 2: "accept", 3: "accept"})
    assert panel == {
        "mean": Decimal("27.80"),
        "median": Decimal("27.90"),
        "min": Decimal("26.50"),
        "count": 3,
        "requires_justification": False,
    }


def test_build_estimate_panel_rn13_excludes_unit_mismatch_and_does_not_count_them():
    item = get_item(1)
    assert item is not None
    # Candidate 4 belongs to item 1, but has unit "unidade" whereas item 1 is "pacote"
    panel_only_mismatch = _demo_estimate(item, {4: "accept"})
    assert panel_only_mismatch == {
        "mean": None,
        "median": None,
        "min": None,
        "count": 0,
        "requires_justification": False,
    }

    panel_with_valid = _demo_estimate(item, {1: "accept", 4: "accept"})
    assert panel_with_valid == {
        "mean": Decimal("26.50"),
        "median": Decimal("26.50"),
        "min": Decimal("26.50"),
        "count": 1,
        "requires_justification": True,
    }


def test_build_estimate_panel_preserves_exact_decimal_without_rounding():
    # Item 6: candidate 24 (4.90), candidate 23 (4.60), candidate 25 (5.10)
    # 4.90 + 4.60 = 9.50 / 2 = 4.75
    item6 = get_item(6)
    assert item6 is not None
    panel = _demo_estimate(item6, {23: "accept", 24: "accept"})
    assert panel["mean"] == Decimal("4.75")
    assert isinstance(panel["mean"], Decimal)
    assert panel["median"] == Decimal("4.75")
    assert isinstance(panel["median"], Decimal)


def test_a_rejected_candidate_stays_out_of_the_estimate(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "accept")
    _decide(client, 3, "reject")
    estimate = _estimate(client, 1)
    assert (estimate["count"], estimate["mean"]) == (2, Decimal("27.20"))


def test_rejecting_an_accepted_candidate_takes_its_price_out(client):
    for candidate_id in (1, 2, 3):
        _decide(client, candidate_id, "accept")
    _decide(client, 1, "reject")
    estimate = _estimate(client, 1)
    assert (estimate["count"], estimate["mean"], estimate["min"]) == (
        2,
        Decimal("28.45"),
        Decimal("27.90"),
    )


def test_a_decision_on_another_item_never_enters_this_items_estimate(client):
    _decide(client, 21, "accept")  # item 5, unit "pacote" like item 1
    assert _estimate(client, 1) == NO_PRICES
    assert _estimate(client, 5)["count"] == 1


def test_screening_view_provides_estimate_context_with_zero_prices(client):
    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert "estimate" in response.context
    assert response.context["estimate"] == NO_PRICES
    html = response.content.decode()
    assert 'id="estimate-panel"' in html
    assert re.search(r"Preços no cálculo:</strong>\s*0\s*</p>", html)
    assert "Menos de três preços" not in html


def test_the_page_shows_the_count_of_the_accepted_prices(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "accept")
    html = client.get(reverse("pricing:screening", args=[1])).content.decode()
    assert re.search(r"Preços no cálculo:</strong>\s*2\s*</p>", html)


def test_screening_view_provides_estimate_context_with_accepted_candidates(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "accept")

    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["estimate"]["count"] == 2
    assert response.context["estimate"]["mean"] == Decimal("27.20")
    assert response.context["estimate"]["requires_justification"] is True

    html = response.content.decode()
    assert 'id="estimate-panel"' in html
    assert re.search(r"R\$ 27,20(?!\d)", html)
    assert re.search(r"Preços no cálculo:</strong>\s*2\s*</p>", html)
    assert (
        "Menos de três preços: a pesquisa exige justificativa (IN 65/2021, art. 6º, § 5º; RN06)."
        in html
    )


def test_screening_view_lists_unit_mismatched_accepted_candidate_as_fora_do_calculo(client):
    _decide(client, 4, "accept")

    url = reverse("pricing:screening", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["estimate"]["count"] == 0
    assert response.context["estimate"]["requires_justification"] is False

    html = response.content.decode()
    assert "fora do cálculo: unidade diferente" in html
    assert "Menos de três preços" not in html


def test_decide_post_returns_candidate_row_and_out_of_band_estimate_panel(client):
    url = reverse("pricing:decide", args=[1])
    response = client.post(url, {"decision": "accept"})

    assert response.status_code == 200
    html = response.content.decode()

    # The candidate row is returned
    assert html.lstrip().startswith('<tr id="candidate-1">')
    assert html.count("<tr") == 1
    assert "Aceito" in html

    # The estimate panel is returned as an out-of-band swap with stable id
    assert 'id="estimate-panel"' in html
    assert 'hx-swap-oob="true"' in html
    assert re.search(r"Preços no cálculo:</strong>\s*1\s*</p>", html)
    assert re.search(r"R\$ 26,50(?!\d)", html)
    assert (
        "Menos de três preços: a pesquisa exige justificativa (IN 65/2021, art. 6º, § 5º; RN06)."
        in html
    )


def test_decide_post_unit_mismatch_shows_fora_do_calculo_and_panel_zero(client):
    url = reverse("pricing:decide", args=[4])
    response = client.post(url, {"decision": "accept"})

    assert response.status_code == 200
    html = response.content.decode()

    assert html.lstrip().startswith('<tr id="candidate-4">')
    assert "fora do cálculo: unidade diferente" in html
    assert "Aceito" not in html

    assert 'id="estimate-panel"' in html
    assert 'hx-swap-oob="true"' in html
    assert re.search(r"Preços no cálculo:</strong>\s*0\s*</p>", html)
    assert "Menos de três preços" not in html


def test_estimate_panel_page_and_swap_parity(client):
    # Verify that screening GET and decide POST return identical panel content
    for item_id in (1, 2, 6):
        url = reverse("pricing:screening", args=[item_id])
        page = client.get(url)
        assert page.status_code == 200

        cands = demo_data.candidates_for(item_id)
        if cands:
            cand = cands[0]
            swap_resp = client.post(
                reverse("pricing:decide", args=[cand.id]),
                {"decision": "accept"},
            )
            assert swap_resp.status_code == 200
            updated_page = client.get(url)

            # Context estimate parity
            assert swap_resp.context["estimate"] == updated_page.context["estimate"]

            # Panel content parity (excluding hx-swap-oob attribute)
            swap_panel = re.search(
                r'<section id="estimate-panel".*?</section>', swap_resp.content.decode(), re.S
            ).group(0)
            page_panel = re.search(
                r'<section id="estimate-panel".*?</section>', updated_page.content.decode(), re.S
            ).group(0)
            swap_panel_clean = re.sub(r'\s+hx-swap-oob="true"', "", swap_panel)
            assert _flat(swap_panel_clean) == _flat(page_panel)


def test_candidate_calculation_label_agrees_with_builder_counted_candidates(client):
    _decide(client, 1, "accept")
    _decide(client, 2, "accept")
    _decide(client, 4, "accept")

    estimate = _estimate(client, 1)
    assert estimate["count"] == 2
    assert estimate["counted_candidate_ids"] == {1, 2}

    page_html = client.get(reverse("pricing:screening", args=[1])).content.decode()
    row_1 = re.search(r'<tr id="candidate-1".*?</tr>', page_html, re.S).group(0)
    row_2 = re.search(r'<tr id="candidate-2".*?</tr>', page_html, re.S).group(0)
    row_4 = re.search(r'<tr id="candidate-4".*?</tr>', page_html, re.S).group(0)

    assert "Aceito" in row_1 and "fora do cálculo: unidade diferente" not in row_1
    assert "Aceito" in row_2 and "fora do cálculo: unidade diferente" not in row_2
    assert "fora do cálculo: unidade diferente" in row_4 and "Aceito" not in row_4

    swap_4 = _decide(client, 4, "accept").content.decode()
    assert "fora do cálculo: unidade diferente" in swap_4 and "Aceito" not in swap_4


def test_the_page_has_no_justification_notice_with_three_accepted_prices(client):
    for candidate_id in (1, 2, 3):
        _decide(client, candidate_id, "accept")
    html = client.get(reverse("pricing:screening", args=[1])).content.decode()
    assert "Menos de três preços" not in html


def test_the_row_label_follows_the_builder_and_not_a_rule_of_its_own(client, monkeypatch):
    real = views.build_estimate_panel

    def builder_that_counts_nothing(item, decisions, candidates):
        panel = real(item, decisions, candidates=candidates)
        panel.counted_candidate_ids = set()
        return panel

    monkeypatch.setattr(views, "build_estimate_panel", builder_that_counts_nothing)
    swapped = _decide(client, 1, "accept").content.decode()  # candidate 1: same unit as item 1
    assert "fora do cálculo: unidade diferente" in swapped and "Aceito" not in swapped
    page = client.get(reverse("pricing:screening", args=[1])).content.decode()
    assert "fora do cálculo: unidade diferente" in _row(page, 1)


def test_get_screening_date_window_covers_12_months():
    from datetime import date

    from pricing.views import get_screening_date_window

    ref = date(2026, 11, 24)
    start, end = get_screening_date_window(ref)
    assert end == ref
    assert start == date(2025, 11, 24)
    assert (end - start).days in (365, 366)


def test_get_embedding_model_loads_lazily_and_caches_instance(monkeypatch):
    from pricing import views

    monkeypatch.setattr(views, "_EMBEDDING_MODEL", None)
    mock_st_class = MagicMock()
    mock_instance = MagicMock()
    mock_st_class.return_value = mock_instance

    import semantic_index.embedding

    monkeypatch.setattr(
        semantic_index.embedding, "SentenceTransformerEmbeddingModel", mock_st_class
    )

    # First call initializes
    model1 = views.get_embedding_model()
    assert mock_st_class.called
    assert model1 == mock_instance

    # Second call returns cached instance without re-instantiating
    mock_st_class.reset_mock()
    model2 = views.get_embedding_model()
    assert not mock_st_class.called
    assert model2 == model1


def test_get_screening_candidates_calls_search_and_ranks():
    from unittest.mock import MagicMock

    from pricing.views import get_screening_candidates

    mock_item = MagicMock()
    mock_item.id = 1
    mock_item.description = "Papel sulfite A4"
    mock_item.unit = "pacote"

    mock_search = MagicMock(return_value=[])

    candidates = get_screening_candidates(
        mock_item,
        expected_price=Decimal("25.00"),
        search_fn=mock_search,
        limit=20,
    )
    assert candidates == []
    assert mock_search.called
    assert mock_search.call_args.kwargs["query"] == "Papel sulfite A4"
    assert mock_search.call_args.kwargs["limit"] == 20


def test_get_screening_candidates_caps_fetches_to_the_requested_limit(monkeypatch):
    from types import SimpleNamespace

    from semantic_index.search import ScoredPublicItem

    fetched_ids = []
    search_results = [
        ScoredPublicItem(
            item=SimpleNamespace(
                pk=12000 + i,
                cnpj="00000000000007",
                year=2026,
                purchase_sequence=1,
                item_number=i + 1,
                description=f"Item {i}",
                unit="pacote",
                quantity=Decimal("1"),
                agency_name="Órgão fictício",
                published_on=datetime.date(2026, 11, 24),
                awarded_unit_price=None,
                estimated_unit_price=Decimal("10.00"),
                secret_budget=False,
            ),
            score=0.9,
        )
        for i in range(25)
    ]

    def fake_fetch(public_item, **kwargs):
        fetched_ids.append(public_item.pk)

    monkeypatch.setattr(views, "fetch_awarded_price_on_demand", fake_fetch)
    candidates = views.get_screening_candidates(
        views.get_item(1),
        search_fn=lambda **kwargs: search_results,
        limit=20,
    )

    assert len(candidates) == 20
    assert len(fetched_ids) == 20


def test_screening_renders_real_candidates_from_semantic_search(client, monkeypatch):
    from ingestion.models import PublicItem
    from semantic_index.search import ScoredPublicItem

    pi_awarded = PublicItem(
        id=1001,
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=42,
        item_number=1,
        description="Papel A4 homologado",
        unit="pacote",
        quantity=Decimal("100"),
        agency_name="Prefeitura Alpha",
        published_on=datetime.date(2026, 11, 1),
        awarded_unit_price=Decimal("25.50"),
        estimated_unit_price=Decimal("30.00"),
        secret_budget=False,
    )
    pi_estimated = PublicItem(
        id=1002,
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=42,
        item_number=2,
        description="Papel A4 sem resultado",
        unit="pacote",
        quantity=Decimal("100"),
        agency_name="Prefeitura Alpha",
        published_on=datetime.date(2026, 11, 2),
        awarded_unit_price=None,
        estimated_unit_price=Decimal("28.00"),
        secret_budget=False,
    )
    pi_secret = PublicItem(
        id=1003,
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=42,
        item_number=3,
        description="Papel A4 sigiloso",
        unit="pacote",
        quantity=Decimal("100"),
        agency_name="Prefeitura Alpha",
        published_on=datetime.date(2026, 11, 3),
        awarded_unit_price=None,
        estimated_unit_price=Decimal("0.00"),
        secret_budget=True,
    )

    def _fake_real_search(query, date_window, limit=20):
        return [
            ScoredPublicItem(item=pi_awarded, score=0.95),
            ScoredPublicItem(item=pi_estimated, score=0.85),
            ScoredPublicItem(item=pi_secret, score=0.75),
        ]

    monkeypatch.setattr(views, "search_function", _fake_real_search)

    url = reverse("pricing:screening", args=[1])
    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode()

    assert "https://pncp.gov.br/app/editais/00000000000007/2026/42" in html
    assert "25,50" in html
    assert "28,00 (estimado)" in html

    row_secret = _row(html, 1003)
    assert "<td>—</td>" in row_secret


def test_screening_estimate_panel_ignores_estimated_prices(client, monkeypatch):
    from ingestion.models import PublicItem
    from semantic_index.search import ScoredPublicItem

    pi_awarded = PublicItem(
        id=2001,
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Papel A4",
        unit="pacote",
        quantity=Decimal("100"),
        agency_name="Prefeitura Alpha",
        published_on=datetime.date(2026, 11, 1),
        awarded_unit_price=Decimal("20.00"),
        estimated_unit_price=Decimal("30.00"),
        secret_budget=False,
    )
    pi_estimated = PublicItem(
        id=2002,
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=2,
        description="Papel A4",
        unit="pacote",
        quantity=Decimal("100"),
        agency_name="Prefeitura Alpha",
        published_on=datetime.date(2026, 11, 2),
        awarded_unit_price=None,
        estimated_unit_price=Decimal("40.00"),
        secret_budget=False,
    )

    def _fake_search(query, date_window, limit=20):
        return [
            ScoredPublicItem(item=pi_awarded, score=0.90),
            ScoredPublicItem(item=pi_estimated, score=0.88),
        ]

    monkeypatch.setattr(views, "search_function", _fake_search)

    session = client.session
    session["screening_decisions"] = {"1:2001": "accept", "1:2002": "accept"}
    session.save()

    response = client.get(reverse("pricing:screening", args=[1]))
    estimate = response.context["estimate"]

    assert estimate["count"] == 1
    assert estimate["mean"] == Decimal("20.00")
    assert estimate["counted_candidate_ids"] == {2001}


def test_get_corpus_info_returns_qdrant_count_and_indexed_date_range():
    from django.core.cache import cache

    from ingestion.models import PublicItem
    from pricing.views import get_corpus_info

    PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Item 1",
        unit="unidade",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão 1",
        published_on=datetime.date(2026, 10, 26),
        modality=6,
        state="PA",
        item_kind="product",
    )
    PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=2,
        description="Item 2",
        unit="unidade",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão 1",
        published_on=datetime.date(2026, 10, 30),
        modality=6,
        state="PA",
        item_kind="product",
    )

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count_res = MagicMock()
    mock_count_res.count = 5111
    mock_client.count.return_value = mock_count_res
    p_min = MagicMock()
    p_min.payload = {"published_on": "2026-10-26"}
    p_max = MagicMock()
    p_max.payload = {"published_on": "2026-10-30"}
    mock_client.scroll.side_effect = [([p_min], None), ([p_max], None)]
    cache.delete("corpus_db_items_count")

    mock_model = MagicMock()
    mock_model.name = "indexed-date-range-partial-test"
    mock_model.revision = "rev1"

    ref_date = datetime.date(2026, 11, 24)
    info = get_corpus_info(client=mock_client, model=mock_model, reference_date=ref_date)

    assert info.indexed_items_count == 5111
    assert info.start_date == datetime.date(2026, 10, 26)
    assert info.end_date == datetime.date(2026, 10, 30)
    assert info.is_partial is True


def test_get_corpus_info_is_not_partial_when_full_window_covered():
    from django.core.cache import cache

    from ingestion.models import PublicItem
    from pricing.views import get_corpus_info

    ref_date = datetime.date(2026, 11, 24)
    PublicItem.objects.create(
        cnpj="00000000000007",
        year=2025,
        purchase_sequence=1,
        item_number=1,
        description="Item Antigo",
        unit="unidade",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão 1",
        published_on=datetime.date(2025, 11, 20),
        modality=6,
        state="PA",
        item_kind="product",
    )
    PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=2,
        description="Item Novo",
        unit="unidade",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão 1",
        published_on=datetime.date(2026, 11, 24),
        modality=6,
        state="PA",
        item_kind="product",
    )

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count_res = MagicMock()
    mock_count_res.count = 2
    mock_client.count.return_value = mock_count_res
    p_min = MagicMock()
    p_min.payload = {"published_on": "2025-11-20"}
    p_max = MagicMock()
    p_max.payload = {"published_on": "2026-11-24"}
    mock_client.scroll.side_effect = [([p_min], None), ([p_max], None)]
    cache.delete("corpus_db_items_count")

    mock_model = MagicMock()
    mock_model.name = "indexed-date-range-full-test"
    mock_model.revision = "rev1"

    info = get_corpus_info(client=mock_client, model=mock_model, reference_date=ref_date)

    assert info.indexed_items_count == 2
    assert info.start_date == datetime.date(2025, 11, 20)
    assert info.end_date == datetime.date(2026, 11, 24)
    assert info.is_partial is False


def test_screening_view_passes_corpus_info_and_renders_notice_when_partial(client, monkeypatch):
    from pricing.views import CorpusInfo

    partial_info = CorpusInfo(
        indexed_items_count=5111,
        start_date=datetime.date(2026, 10, 26),
        end_date=datetime.date(2026, 10, 30),
        is_partial=True,
        db_items_count=6000,
    )
    monkeypatch.setattr(views, "corpus_info_function", lambda: partial_info)

    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    assert response.context["corpus_info"] == partial_info
    html = response.content.decode()
    assert "Busca realizada em corpus parcial" in html
    assert "5111 de 6000" in html
    assert "26/10/2026 a 30/10/2026" in html


def test_get_embedding_model_thread_safe_concurrent_first_calls(monkeypatch):
    """N3: Concurrent calls to get_embedding_model load the model exactly once under lock."""
    import threading
    import time
    from unittest.mock import MagicMock

    load_count = 0

    def fake_loader(*args, **kwargs):
        nonlocal load_count
        time.sleep(0.02)
        load_count += 1
        return MagicMock(name="fake_sentence_transformer")

    monkeypatch.setattr(views, "_EMBEDDING_MODEL", None)
    # Patch SentenceTransformerEmbeddingModel import target or class
    import semantic_index.embedding

    monkeypatch.setattr(semantic_index.embedding, "SentenceTransformerEmbeddingModel", fake_loader)

    models_loaded = []

    def worker():
        m = views.get_embedding_model()
        models_loaded.append(m)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert load_count == 1
    assert len(models_loaded) == 8
    assert all(m is models_loaded[0] for m in models_loaded)


def test_decide_and_screening_keys_decisions_by_requested_item_and_candidate(client):
    """N4: Decisions are isolated per requested item so accepts do not leak across items."""
    url_decide = reverse("pricing:decide", args=[1])
    # Decide accept for candidate 1 on item 1
    resp = client.post(url_decide, {"decision": "accept", "item_id": "1"})
    assert resp.status_code == 200

    # Screening for item 1 sees candidate 1 as accepted
    resp1 = client.get(reverse("pricing:screening", args=[1]))
    assert resp1.context["decisions"].get(1) == "accept"
    assert resp1.context["estimate"]["count"] >= 1

    # Screening for item 2 sees candidate 1 as NOT decided
    resp2 = client.get(reverse("pricing:screening", args=[2]))
    assert 1 not in resp2.context["decisions"]
    # Panel on item 2 must not count candidate 1
    assert 1 not in resp2.context["estimate"]["counted_candidate_ids"]


def test_screening_ignores_legacy_unscoped_decisions(client, monkeypatch):
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    session = client.session
    session["screening_decisions"] = {"1": "accept"}
    session.save()

    response = client.get(reverse("pricing:screening", args=[2]))

    assert response.status_code == 200
    assert response.context["decisions"] == {}


def test_decide_rejects_real_candidate_without_requested_item_id(client):
    from ingestion.models import PublicItem

    public_item = PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=83001,
        item_number=1,
        description="Item público sintético",
        unit="pacote",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão fictício",
        published_on=datetime.date(2026, 11, 24),
        modality=6,
        state="PA",
        item_kind="product",
    )

    response = client.post(
        reverse("pricing:decide", args=[public_item.pk]),
        {"decision": "accept"},
    )

    assert response.status_code == 400
    assert "screening_decisions" not in client.session


def test_screening_view_displays_twenty_candidates_not_ten(client, monkeypatch):
    """Mutant killer 2: The screening request displays the full top 20."""
    from pricing.candidates import Candidate

    recorded_limit = None
    fake_candidates = [
        Candidate(
            id=20000 + i,
            description=f"Candidato {i}",
            unit="pacote",
            quantity=Decimal("1"),
            agency="Órgão fictício",
            date=datetime.date(2026, 11, 24),
            awarded_unit_price=Decimal("10.00"),
            similarity=0.9,
            item_id=1,
        )
        for i in range(20)
    ]

    def fake_search(**kwargs):
        nonlocal recorded_limit
        recorded_limit = kwargs.get("limit")
        return fake_candidates[:recorded_limit]

    monkeypatch.setattr(views, "search_function", fake_search)
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    response = client.get(reverse("pricing:screening", args=[1]))

    assert recorded_limit == 20
    assert response.status_code == 200
    assert len(response.context["candidates"]) == 20
    assert response.context["candidates"][-1].id == 20019


def test_get_corpus_info_reads_date_range_from_qdrant_payload(monkeypatch):
    """N1: get_corpus_info queries Qdrant scroll for min and max published_on payload."""
    from pricing.views import get_corpus_info

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count = MagicMock()
    mock_count.count = 3
    mock_client.count.return_value = mock_count

    p_min = MagicMock()
    p_min.payload = {"published_on": "2026-10-26"}
    p_max = MagicMock()
    p_max.payload = {"published_on": "2026-10-30"}

    mock_client.scroll.side_effect = [
        ([p_min], None),
        ([p_max], None),
    ]

    mock_model = MagicMock()
    mock_model.name = "date-range-payload-test"
    mock_model.revision = "rev1"

    info = get_corpus_info(
        client=mock_client, model=mock_model, reference_date=datetime.date(2026, 11, 24)
    )
    assert info.start_date == datetime.date(2026, 10, 26)
    assert info.end_date == datetime.date(2026, 10, 30)
    assert info.indexed_items_count == 3
    assert info.is_partial is True


def test_get_corpus_info_does_not_substitute_database_dates_for_missing_index_dates():
    from django.core.cache import cache

    from ingestion.models import PublicItem
    from pricing.views import get_corpus_info

    PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=82001,
        item_number=1,
        description="Item sintético sem data no payload do índice",
        unit="unidade",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão fictício",
        published_on=datetime.date(2026, 11, 23),
        modality=6,
        state="PA",
        item_kind="product",
    )
    cache.delete("corpus_db_items_count")

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count = MagicMock()
    mock_count.count = 1
    mock_client.count.return_value = mock_count
    mock_client.scroll.return_value = ([], None)

    mock_model = MagicMock()
    mock_model.name = "missing-index-dates-test"
    mock_model.revision = "rev1"

    info = get_corpus_info(
        client=mock_client,
        model=mock_model,
        reference_date=datetime.date(2026, 11, 24),
    )

    assert info.start_date is None
    assert info.end_date is None
    assert info.is_partial is True


def test_get_corpus_info_marks_extra_index_points_as_partial():
    from django.core.cache import cache

    from pricing.views import get_corpus_info

    cache.set("corpus_db_items_count", 10, 300)
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count = MagicMock()
    mock_count.count = 14
    mock_client.count.return_value = mock_count

    start_date = datetime.date(2025, 11, 24)
    yesterday = datetime.date(2026, 11, 23)
    p_min = MagicMock()
    p_min.payload = {"published_on": start_date.isoformat()}
    p_max = MagicMock()
    p_max.payload = {"published_on": yesterday.isoformat()}
    mock_client.scroll.side_effect = [([p_min], None), ([p_max], None)]

    mock_model = MagicMock()
    mock_model.name = "extra-index-points-test"
    mock_model.revision = "rev1"

    info = get_corpus_info(
        client=mock_client,
        model=mock_model,
        reference_date=datetime.date(2026, 11, 24),
    )

    assert info.indexed_items_count == 14
    assert info.db_items_count == 10
    assert info.is_partial is True


def test_get_corpus_info_caches_both_database_and_index_counts(monkeypatch):
    from django.core.cache import cache

    from ingestion.models import PublicItem
    from pricing.views import get_corpus_info

    cache.delete("corpus_db_items_count")
    public_item_manager = PublicItem.objects
    original_count = public_item_manager.count
    db_count_calls = 0

    def counted_db_count():
        nonlocal db_count_calls
        db_count_calls += 1
        return original_count()

    monkeypatch.setattr(public_item_manager, "count", counted_db_count)

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count = MagicMock()
    mock_count.count = 1
    mock_client.count.return_value = mock_count
    p_min = MagicMock()
    p_min.payload = {"published_on": "2026-10-26"}
    p_max = MagicMock()
    p_max.payload = {"published_on": "2026-11-23"}
    mock_client.scroll.side_effect = [([p_min], None), ([p_max], None)]

    mock_model = MagicMock()
    mock_model.name = "cached-corpus-counts-test"
    mock_model.revision = "rev1"
    parameters = {
        "client": mock_client,
        "model": mock_model,
        "reference_date": datetime.date(2026, 11, 24),
    }

    first = get_corpus_info(**parameters)
    second = get_corpus_info(**parameters)

    assert first == second
    assert db_count_calls == 1
    assert mock_client.count.call_count == 1
    assert mock_client.scroll.call_count == 2


def test_get_corpus_info_handles_qdrant_exception_without_500():
    """N1 & N7: When Qdrant raises exception, returns CorpusInfo with qdrant_error=True."""
    from pricing.views import get_corpus_info

    mock_client = MagicMock()
    mock_client.collection_exists.side_effect = Exception("Qdrant connection refused")
    mock_model = MagicMock()

    info = get_corpus_info(client=mock_client, model=mock_model)
    assert info.qdrant_error is True
    assert info.indexed_items_count == 0
    assert info.is_partial is True


def test_get_corpus_info_tolerates_one_day_of_lag():
    """N1: Tolerate one day lag: if latest item in index is yesterday, do not mark partial."""
    from pricing.views import get_corpus_info

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_count = MagicMock()
    mock_count.count = 10
    mock_client.count.return_value = mock_count

    ref_date = datetime.date(2026, 11, 24)
    yesterday = ref_date - datetime.timedelta(days=1)
    one_year_ago = ref_date - datetime.timedelta(days=365)

    p_min = MagicMock()
    p_min.payload = {"published_on": one_year_ago.isoformat()}
    p_max = MagicMock()
    p_max.payload = {"published_on": yesterday.isoformat()}

    mock_client.scroll.side_effect = [
        ([p_min], None),
        ([p_max], None),
    ]

    mock_model = MagicMock()
    mock_model.name = "one-day-lag-test"
    mock_model.revision = "rev1"

    # Monkeypatch cached DB count to match 10
    from django.core.cache import cache

    cache.set("corpus_db_items_count", 10, 60)

    info = get_corpus_info(client=mock_client, model=mock_model, reference_date=ref_date)
    assert info.is_partial is False


def test_screening_view_handles_qdrant_down_gracefully_without_500(client, monkeypatch):
    """N7: Qdrant failures render a Portuguese notice and never return HTTP 500."""
    from pricing.views import CorpusInfo

    def failing_search(**kwargs):
        raise RuntimeError("Qdrant down")

    monkeypatch.setattr(views, "search_function", failing_search)
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: CorpusInfo(0, None, None, True, qdrant_error=True),
    )
    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Nenhum preço candidato encontrado." in html
    assert "Índice de busca semântica temporariamente indisponível." in html


def test_screening_view_notifies_when_semantic_index_is_empty(client, monkeypatch):
    from pricing.views import CorpusInfo

    monkeypatch.setattr(views, "search_function", lambda **kwargs: [])
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: CorpusInfo(0, None, None, True, db_items_count=10, empty_index=True),
    )

    response = client.get(reverse("pricing:screening", args=[1]))

    assert response.status_code == 200
    html = response.content.decode()
    assert "Índice de busca semântica vazio" in html
    assert "0 de 10 itens do banco indexados" in html


def test_partial_corpus_notice_says_when_index_dates_are_unavailable(client, monkeypatch):
    from pricing.views import CorpusInfo

    monkeypatch.setattr(views, "search_function", lambda **kwargs: [])
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: CorpusInfo(1, None, None, True, db_items_count=2),
    )

    response = client.get(reverse("pricing:screening", args=[1]))

    assert response.status_code == 200
    html = response.content.decode()
    assert "1 de 2 itens do banco indexados" in html
    assert "período de publicação do índice indisponível" in html


def test_screening_does_not_label_a_nonsecret_item_without_price_as_secret(client, monkeypatch):
    from pricing.candidates import Candidate

    candidate = Candidate(
        id=99001,
        description="Item sintético sem preço",
        unit="pacote",
        quantity=Decimal("1"),
        agency="Órgão fictício",
        date=datetime.date(2026, 11, 24),
    )
    monkeypatch.setattr(views, "search_function", lambda **kwargs: [candidate])
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    session = client.session
    session["screening_decisions"] = {"1:99001": "accept"}
    session.save()

    response = client.get(reverse("pricing:screening", args=[1]))
    row = _row(response.content.decode(), candidate.id)

    assert "fora do cálculo: sem preço" in row
    assert "orçamento sigiloso" not in row


def test_build_estimate_panel_normalizes_units_so_case_and_spacing_variations_count():
    """B1: Three awarded candidates with case/space differences count in panel."""
    from ingestion.models import PublicItem
    from pricing.candidates import candidate_from_public_item

    item = views.get_item(1)  # item.unit is 'pacote'

    pi1 = PublicItem(
        id=7001,
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Papel A4",
        unit="Pacote",  # Title case
        quantity=Decimal("100"),
        agency_name="Órgão",
        published_on=datetime.date.today(),
        awarded_unit_price=Decimal("10.00"),
    )
    pi2 = PublicItem(
        id=7002,
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=2,
        description="Papel A4",
        unit=" PACOTE ",  # Upper with spacing
        quantity=Decimal("100"),
        agency_name="Órgão",
        published_on=datetime.date.today(),
        awarded_unit_price=Decimal("20.00"),
    )
    pi3 = PublicItem(
        id=7003,
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=3,
        description="Papel A4",
        unit="pacote",  # Lower
        quantity=Decimal("100"),
        agency_name="Órgão",
        published_on=datetime.date.today(),
        awarded_unit_price=Decimal("30.00"),
    )

    cands = [
        candidate_from_public_item(pi1),
        candidate_from_public_item(pi2),
        candidate_from_public_item(pi3),
    ]

    decisions = {7001: "accept", 7002: "accept", 7003: "accept"}
    panel = views.build_estimate_panel(item, decisions, candidates=cands)

    assert panel["count"] == 3
    assert panel["counted_candidate_ids"] == {7001, 7002, 7003}
    assert panel["mean"] == Decimal("20.00")


def test_screening_view_executes_single_semantic_search_per_request(client, monkeypatch):
    """B3: One semantic search per request. build_estimate_panel must not call search again."""
    search_call_count = 0

    def counting_search(**kwargs):
        nonlocal search_call_count
        search_call_count += 1
        return []

    monkeypatch.setattr(views, "search_function", counting_search)
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    assert search_call_count == 1


def test_decide_post_does_not_run_an_extra_semantic_search(client, monkeypatch):
    search_call_count = 0

    def counting_search(**kwargs):
        nonlocal search_call_count
        search_call_count += 1
        return []

    monkeypatch.setattr(views, "search_function", counting_search)
    response = client.post(
        reverse("pricing:decide", args=[1]),
        {"decision": "accept", "item_id": "1"},
    )

    assert response.status_code == 200
    assert search_call_count == 0


def test_screening_page_with_20_hanging_fetches_renders_within_budget(client, monkeypatch):
    """B3: Twenty blocked fetches do not hold the whole page beyond its shared budget."""
    import threading
    import time
    from types import SimpleNamespace

    from semantic_index.search import ScoredPublicItem

    fake_items = []
    for i in range(20):
        pi = SimpleNamespace(
            pk=8000 + i,
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=i + 1,
            description=f"Item {i}",
            unit="pacote",
            quantity=Decimal("1"),
            agency_name="Órgão",
            published_on=datetime.date.today(),
            awarded_unit_price=None,
            estimated_unit_price=Decimal("10.00"),
            secret_budget=False,
        )
        fake_items.append(ScoredPublicItem(item=pi, score=0.85))

    monkeypatch.setattr(views, "search_function", lambda **kw: fake_items)

    release_fetches = threading.Event()
    started_ids = []

    def hanging_fetch(public_item, **kw):
        started_ids.append(public_item.pk)
        release_fetches.wait()

    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    monkeypatch.setattr(views, "fetch_awarded_price_on_demand", hanging_fetch)

    timeout_release = threading.Timer(4.5, release_fetches.set)
    timeout_release.daemon = True
    timeout_release.start()

    started_at = time.monotonic()
    try:
        response = client.get(reverse("pricing:screening", args=[1]))
        elapsed = time.monotonic() - started_at
    finally:
        release_fetches.set()
        timeout_release.cancel()

    assert response.status_code == 200
    assert len(response.context["candidates"]) == 20
    assert len(started_ids) == 20
    assert elapsed < 4.0


def test_screening_view_does_not_call_embedding_model_loader_when_search_function_is_injected(
    client, monkeypatch
):
    """View must never call get_embedding_model when search_function is injected."""
    loader_called = False

    def fake_loader():
        nonlocal loader_called
        loader_called = True
        raise AssertionError("get_embedding_model called while fake search in use")

    monkeypatch.setattr(views, "get_embedding_model", fake_loader)
    monkeypatch.setattr(views, "search_function", lambda **kwargs: [])

    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    assert not loader_called


def test_estimate_panel_parity_and_notice_when_accepted_candidate_is_out_of_current_list(
    client, monkeypatch
):
    """B2: POST decide and GET screening build identical panels from all accepted candidates."""
    from ingestion.models import PublicItem
    from semantic_index.search import ScoredPublicItem

    today = datetime.date.today()
    pi_a = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=7101,
        item_number=1,
        description="Papel A4 fora da lista depois",
        unit="pacote",
        quantity=Decimal("10"),
        agency_name="Órgão A",
        published_on=today,
        awarded_unit_price=Decimal("20.00"),
        estimated_unit_price=Decimal("22.00"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )
    pi_b = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=7102,
        item_number=1,
        description="Papel A4 na lista atual",
        unit="pacote",
        quantity=Decimal("10"),
        agency_name="Órgão B",
        published_on=today,
        awarded_unit_price=Decimal("30.00"),
        estimated_unit_price=Decimal("32.00"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )
    pi_c = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=7103,
        item_number=1,
        description="Papel A4 segundo fora da lista",
        unit="pacote",
        quantity=Decimal("10"),
        agency_name="Órgão C",
        published_on=today,
        awarded_unit_price=Decimal("40.00"),
        estimated_unit_price=Decimal("42.00"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )

    current_items = [pi_a, pi_b, pi_c]
    monkeypatch.setattr(
        views,
        "search_function",
        lambda **kwargs: [ScoredPublicItem(item=pi, score=0.9) for pi in current_items],
    )
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(3, today, today, is_partial=False, db_items_count=3),
    )

    # Accept A while A is in list
    resp_a = client.post(
        reverse("pricing:decide", args=[pi_a.pk]),
        {"decision": "accept", "item_id": "1"},
    )
    assert resp_a.status_code == 200
    assert resp_a.context["estimate"]["count"] == 1

    # When all accepted items are in the current list, no out-of-list notice appears
    page_all_in = client.get(reverse("pricing:screening", args=[1]))
    assert "fora da lista atual" not in page_all_in.content.decode()

    # Now A drops out of the current search results; only B remains
    current_items = [pi_b]

    resp_b = client.post(
        reverse("pricing:decide", args=[pi_b.pk]),
        {"decision": "accept", "item_id": "1"},
    )
    assert resp_b.status_code == 200
    assert resp_b.context["estimate"]["count"] == 2
    assert resp_b.context["estimate"]["mean"] == Decimal("25.00")

    page_one_out = client.get(reverse("pricing:screening", args=[1]))
    assert page_one_out.status_code == 200
    assert page_one_out.context["estimate"] == resp_b.context["estimate"]

    swap_panel = re.search(
        r'<section id="estimate-panel".*?</section>', resp_b.content.decode(), re.S
    ).group(0)
    page_panel = re.search(
        r'<section id="estimate-panel".*?</section>', page_one_out.content.decode(), re.S
    ).group(0)
    swap_panel_clean = re.sub(r'\s+hx-swap-oob="true"', "", swap_panel)
    assert _flat(swap_panel_clean) == _flat(page_panel)
    assert "1 aceito fora da lista atual" in page_one_out.content.decode()

    # Accept C (also out of current list) -> 2 accepted out of current list
    resp_c = client.post(
        reverse("pricing:decide", args=[pi_c.pk]),
        {"decision": "accept", "item_id": "1"},
    )
    assert resp_c.status_code == 200
    assert resp_c.context["estimate"]["count"] == 3
    assert resp_c.context["estimate"]["mean"] == Decimal("30.00")

    page_two_out = client.get(reverse("pricing:screening", args=[1]))
    assert page_two_out.context["estimate"] == resp_c.context["estimate"]
    assert "2 aceitos fora da lista atual" in page_two_out.content.decode()


def test_get_screening_candidates_allows_retry_after_empty_pncp_response(monkeypatch):
    """N2: Empty PNCP response does not cache failure; next view retries and succeeds."""
    from django.core.cache import cache
    from django.utils import timezone

    import ingestion.client
    from ingestion.models import PublicItem, RawRecord
    from semantic_index.search import ScoredPublicItem

    today = datetime.date.today()
    raw_items = RawRecord.objects.create(
        endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/7201/itens",
        params={"pagina": 1},
        fetched_at=timezone.now(),
        payload=[{"numeroItem": 1, "temResultado": True}],
        status_code=200,
    )
    pi = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=7201,
        item_number=1,
        description="Item com resultado publicado depois",
        unit="pacote",
        quantity=Decimal("10"),
        agency_name="Órgão Fictício",
        published_on=today,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("25.00"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )
    pi.raw_records.add(raw_items)
    cache.delete(f"pncp_fetch_failed_{pi.pk}")

    responses = [
        RawRecord(
            endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/7201/itens/1/resultados",
            params={},
            fetched_at=timezone.now(),
            payload=[],
            status_code=200,
        ),
        RawRecord(
            endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/7201/itens/1/resultados",
            params={},
            fetched_at=timezone.now(),
            payload=[
                {
                    "numeroItem": 1,
                    "situacaoCompraItemResultadoNome": "Informado",
                    "dataCancelamento": None,
                    "valorUnitarioHomologado": 19.50,
                }
            ],
            status_code=200,
        ),
    ]
    call_count = 0

    def fake_fetch_item_results(**kwargs):
        nonlocal call_count
        call_count += 1
        return responses[call_count - 1]

    monkeypatch.setattr(ingestion.client, "fetch_item_results", fake_fetch_item_results)
    item = get_item(1)

    first = views.get_screening_candidates(
        item,
        search_fn=lambda **kwargs: [ScoredPublicItem(item=pi, score=0.9)],
    )
    assert call_count == 1
    assert first[0].is_estimated is True
    assert cache.get(f"pncp_fetch_failed_{pi.pk}") is None

    pi.refresh_from_db()
    second = views.get_screening_candidates(
        item,
        search_fn=lambda **kwargs: [ScoredPublicItem(item=pi, score=0.9)],
    )
    assert call_count == 2
    assert second[0].is_estimated is False
    assert second[0].price == Decimal("19.5000")


@pytest.mark.parametrize("bad_item_id", ["abc", "2.5", "999999999999", "-1"])
def test_decide_rejects_malformed_or_nonexistent_item_id_with_404_and_writes_no_session(
    client, bad_item_id
):
    """N3: Non-integer or nonexistent item_id returns 404 (never 500) and leaves session clean."""
    from ingestion.models import PublicItem

    public_item = PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=83002,
        item_number=1,
        description="Item público para teste N3",
        unit="pacote",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("10.00"),
        agency_name="Órgão fictício",
        published_on=datetime.date(2026, 11, 24),
        modality=6,
        state="PA",
        item_kind="product",
    )

    response = client.post(
        reverse("pricing:decide", args=[public_item.pk]),
        {"decision": "accept", "item_id": bad_item_id},
    )

    assert response.status_code == 404
    assert "screening_decisions" not in client.session


def test_get_corpus_info_distinguishes_model_oserror_from_qdrant_error(client, monkeypatch):
    """N4: Model OSError sets model_error=True (not qdrant_error) with distinct notice."""
    from pricing.views import CorpusInfo

    monkeypatch.setattr(views, "search_function", views.default_search_function)
    monkeypatch.setattr(views, "_EMBEDDING_MODEL", None)

    def failing_model_loader():
        raise OSError("Cannot load model offline")

    monkeypatch.setattr(views, "get_embedding_model", failing_model_loader)

    info = views.get_corpus_info(client=MagicMock())
    assert info.model_error is True
    assert info.qdrant_error is False
    assert info.is_partial is True

    monkeypatch.setattr(views, "search_function", lambda **kwargs: [])
    monkeypatch.setattr(views, "corpus_info_function", lambda: info)
    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Modelo de busca semântica temporariamente indisponível." in html
    assert "Índice de busca semântica temporariamente indisponível." not in html

    qdrant_only_info = CorpusInfo(0, None, None, is_partial=True, qdrant_error=True)
    monkeypatch.setattr(views, "corpus_info_function", lambda: qdrant_only_info)
    qdrant_html = client.get(reverse("pricing:screening", args=[1])).content.decode()
    assert "Índice de busca semântica temporariamente indisponível." in qdrant_html
    assert "Modelo de busca semântica temporariamente indisponível." not in qdrant_html


def test_max_screening_candidates_constant_is_pinned_at_20(client, monkeypatch):
    """N6: MAX_SCREENING_CANDIDATES = 20 is a recorded decision; capping and view limit obey it."""
    from pricing.candidates import Candidate

    assert views.MAX_SCREENING_CANDIDATES == 20

    many_candidates = [
        Candidate(
            id=30000 + i,
            description=f"Candidato {i}",
            unit="pacote",
            quantity=Decimal("1"),
            agency="Órgão fictício",
            date=datetime.date(2026, 11, 24),
            awarded_unit_price=Decimal("10.00"),
            similarity=0.9,
            item_id=1,
        )
        for i in range(50)
    ]
    recorded_limits = []

    def fake_search(**kwargs):
        recorded_limits.append(kwargs.get("limit"))
        return many_candidates

    result = views.get_screening_candidates(get_item(1), search_fn=fake_search, limit=50)
    assert recorded_limits == [20]
    assert len(result) == 20

    recorded_limits.clear()
    monkeypatch.setattr(views, "search_function", fake_search)
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(0, None, None, is_partial=False),
    )
    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    assert recorded_limits == [20]
    assert len(response.context["candidates"]) == 20


def test_get_screening_candidates_passes_2s_per_candidate_timeout(monkeypatch):
    """N6: On-demand fetch inside get_screening_candidates uses 2.0 s per-candidate timeout."""
    from django.core.cache import cache
    from django.utils import timezone

    import ingestion.client
    from ingestion.models import PublicItem, RawRecord
    from semantic_index.search import ScoredPublicItem

    assert views.ON_DEMAND_FETCH_TIMEOUT_SECONDS == 2.0

    today = datetime.date.today()
    raw_items = RawRecord.objects.create(
        endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/7301/itens",
        params={"pagina": 1},
        fetched_at=timezone.now(),
        payload=[{"numeroItem": 1, "temResultado": True}],
        status_code=200,
    )
    pi = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=7301,
        item_number=1,
        description="Item para checar timeout de 2s",
        unit="pacote",
        quantity=Decimal("1"),
        agency_name="Órgão Fictício",
        published_on=today,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("10.00"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )
    pi.raw_records.add(raw_items)
    cache.delete(f"pncp_fetch_failed_{pi.pk}")

    recorded_timeouts = []

    def fake_fetch_item_results(**kwargs):
        transport = kwargs.get("transport")
        if transport and hasattr(transport, "keywords"):
            recorded_timeouts.append(transport.keywords.get("timeout"))
        return None

    monkeypatch.setattr(ingestion.client, "fetch_item_results", fake_fetch_item_results)
    views.get_screening_candidates(
        get_item(1),
        search_fn=lambda **kwargs: [ScoredPublicItem(item=pi, score=0.9)],
    )

    assert recorded_timeouts == [2.0]


def test_get_corpus_info_does_not_load_model_when_search_function_is_injected(monkeypatch):
    """N6: Calling get_corpus_info directly must not call get_embedding_model if search is fake."""
    from django.core.cache import cache

    cache.delete("corpus_db_items_count")
    monkeypatch.setattr(views, "_EMBEDDING_MODEL", None)
    monkeypatch.setattr(views, "search_function", lambda **kwargs: [])

    def forbidden_loader():
        raise AssertionError("get_embedding_model must not be called when search_function injected")

    monkeypatch.setattr(views, "get_embedding_model", forbidden_loader)

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    info = views.get_corpus_info(client=mock_client)
    assert info.qdrant_error is False
    assert info.model_error is False


def test_decide_preserves_semantic_similarity_and_never_renders_zero_for_public_item(
    client, monkeypatch
):
    from ingestion.models import PublicItem
    from semantic_index.search import ScoredPublicItem

    today = datetime.date.today()
    pi = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=84001,
        item_number=1,
        description="Papel sulfite A4 branco para teste D1",
        unit="pacote",
        quantity=Decimal("50.0000"),
        agency_name="Prefeitura D1",
        published_on=today,
        awarded_unit_price=Decimal("41.1400"),
        estimated_unit_price=Decimal("45.0000"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )

    search_calls = 0

    def fake_search(**kwargs):
        nonlocal search_calls
        search_calls += 1
        return [ScoredPublicItem(item=pi, score=0.89414424)]

    monkeypatch.setattr(views, "search_function", fake_search)
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(1, today, today, is_partial=False, db_items_count=1),
    )

    get_resp = client.get(reverse("pricing:screening", args=[1]))
    assert get_resp.status_code == 200
    get_html = get_resp.content.decode()
    assert "0,89414424" in get_html
    assert f'hx-target="#candidate-{pi.pk}-decision"' in get_html
    assert search_calls == 1

    # POST accept (including forged similarity/score parameters that must be ignored)
    post_accept = client.post(
        reverse("pricing:decide", args=[pi.pk]),
        {
            "decision": "accept",
            "item_id": "1",
            "similarity": "0.1234",
            "score": "0.1234",
        },
    )
    assert post_accept.status_code == 200
    assert search_calls == 1
    accept_html = post_accept.content.decode()
    assert accept_html.lstrip().startswith(f'<td id="candidate-{pi.pk}-decision">')
    assert "Aceito" in accept_html
    assert 'id="estimate-panel"' in accept_html
    assert 'hx-swap-oob="true"' in accept_html
    assert "<tr" not in accept_html
    assert "0,0" not in accept_html
    assert "0,1234" not in accept_html

    # POST reject
    post_reject = client.post(
        reverse("pricing:decide", args=[pi.pk]),
        {
            "decision": "reject",
            "item_id": "1",
            "similarity": "0.5",
            "score": "0.5",
        },
    )
    assert post_reject.status_code == 200
    assert search_calls == 1
    reject_html = post_reject.content.decode()
    assert reject_html.lstrip().startswith(f'<td id="candidate-{pi.pk}-decision">')
    assert "Descartado" in reject_html
    assert 'id="estimate-panel"' in reject_html
    assert "<tr" not in reject_html
    assert "0,0" not in reject_html

    # Subsequent GET preserves exact semantic similarity and saved decision
    get_after = client.get(reverse("pricing:screening", args=[1]))
    assert get_after.status_code == 200
    after_row = _row(get_after.content.decode(), pi.pk)
    assert "0,89414424" in after_row
    assert "Descartado" in after_row


def test_screening_formats_db_and_on_demand_prices_and_quantities_identically(client, monkeypatch):
    from django.core.cache import cache
    from django.utils import timezone

    import ingestion.client
    from ingestion.models import PublicItem, RawRecord
    from semantic_index.search import ScoredPublicItem

    today = datetime.date.today()
    pi_db = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=84002,
        item_number=1,
        description="Item com preço homologado no banco",
        unit="pacote",
        quantity=Decimal("50.0000"),
        agency_name="Órgão DB",
        published_on=today,
        awarded_unit_price=Decimal("17.5500"),
        estimated_unit_price=Decimal("20.0000"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )

    raw_items = RawRecord.objects.create(
        endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/84003/itens",
        params={"pagina": 1},
        fetched_at=timezone.now(),
        payload=[{"numeroItem": 1, "temResultado": True}],
        status_code=200,
    )
    pi_on_demand = PublicItem.objects.create(
        cnpj="00000000000007",
        year=today.year,
        purchase_sequence=84003,
        item_number=1,
        description="Item com preço homologado sob demanda",
        unit="pacote",
        quantity=Decimal("0.0450"),
        agency_name="Órgão Demanda",
        published_on=today,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("28.0000"),
        secret_budget=False,
        modality=6,
        state="PA",
        item_kind="product",
    )
    pi_on_demand.raw_records.add(raw_items)
    cache.delete(f"pncp_fetch_failed_{pi_on_demand.pk}")

    def fake_fetch_item_results(**kwargs):
        return RawRecord(
            endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/84003/itens/1/resultados",
            params={},
            fetched_at=timezone.now(),
            payload=[
                {
                    "numeroItem": 1,
                    "situacaoCompraItemResultadoNome": "Informado",
                    "dataCancelamento": None,
                    "valorUnitarioHomologado": 17.55,
                }
            ],
            status_code=200,
        )

    monkeypatch.setattr(ingestion.client, "fetch_item_results", fake_fetch_item_results)
    monkeypatch.setattr(
        views,
        "search_function",
        lambda **kwargs: [
            ScoredPublicItem(item=pi_db, score=0.89414424),
            ScoredPublicItem(item=pi_on_demand, score=0.81234567),
        ],
    )
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(2, today, today, is_partial=False, db_items_count=2),
    )

    response = client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    html = response.content.decode()

    row_db = _row(html, pi_db.pk)
    row_demand = _row(html, pi_on_demand.pk)

    assert "<td>50</td>" in row_db
    assert "50,0000" not in row_db
    assert "<td>17,55</td>" in row_db
    assert "17,5500" not in row_db
    assert "<td>0,89414424</td>" in row_db

    assert "<td>0,0450</td>" in row_demand
    assert "<td>17,55</td>" in row_demand
    assert "<td>0,81234567</td>" in row_demand
