import datetime
import re
from dataclasses import dataclass
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse

from pricing.templatetags.pricing_extras import lookup

NO_PRICES = {
    "mean": None,
    "median": None,
    "min": None,
    "count": 0,
    "requires_justification": False,
}


@dataclass(frozen=True)
class ProcurementStub:
    id: int
    title: str = ""


@dataclass(frozen=True)
class ItemStub:
    id: int
    description: str
    quantity: Decimal
    unit: str
    requesting_department: str


@dataclass(frozen=True)
class CandidateStub:
    id: int
    description: str
    unit: str
    quantity: Decimal
    agency: str
    date: datetime.date
    source: str
    provenance: str
    price: Decimal
    similarity: float


pytestmark = pytest.mark.urls("tests.urls_pricing")


def _flat(html: str) -> str:
    return " ".join(html.split())


def _make_item(**kwargs) -> ItemStub:
    defaults = {
        "id": 1,
        "description": "Papel sulfite A4 branco",
        "quantity": Decimal("100"),
        "unit": "pacote",
        "requesting_department": "Secretaria Municipal de Administração",
    }
    defaults.update(kwargs)
    return ItemStub(**defaults)


def _make_candidate(**kwargs) -> CandidateStub:
    defaults = {
        "id": 1,
        "description": "Papel alcalino A4 multiúso 75g/m2, pacote com 500 folhas",
        "unit": "pacote",
        "quantity": Decimal("150"),
        "agency": "Câmara Fictícia B",
        "date": datetime.date(2026, 4, 18),
        "source": "Fonte Fictícia 1",
        "provenance": "DEMO-045/2026-01",
        "price": Decimal("24.80"),
        "similarity": 0.88,
    }
    defaults.update(kwargs)
    return CandidateStub(**defaults)


def _render_screening(
    item: ItemStub,
    candidates: list[CandidateStub],
    decisions: dict[int, str] | None = None,
    proximities: dict[int, str] | None = None,
    expected_price: Decimal | None = None,
    procurement: ProcurementStub | None = None,
) -> str:
    request = RequestFactory().get(f"/items/{item.id}/screening/")
    return render_to_string(
        "pricing/screening.html",
        {
            "item": item,
            "candidates": candidates,
            "decisions": decisions or {},
            "proximities": proximities or {},
            "expected_price": expected_price,
            "procurement": procurement,
        },
        request=request,
    )


def _render_candidate_fragment(
    candidate: CandidateStub,
    decision: str | None = None,
    proximity: str | None = None,
    expected_price: Decimal | None = None,
    item_unit: str | None = None,
) -> str:
    request = RequestFactory().get("/")
    return render_to_string(
        "pricing/_candidate.html",
        {
            "candidate": candidate,
            "decision": decision,
            "proximity": proximity,
            "expected_price": expected_price,
            "item_unit": item_unit,
        },
        request=request,
    )


def test_screening_extends_base_and_sets_the_page_title():
    item = _make_item()
    rendered = _render_screening(item, candidates=[])
    assert f"<title>Triagem — {settings.SYSTEM_NAME}</title>" in rendered


def test_screening_renders_item_fields():
    item = _make_item(
        description="Resma de papel A4",
        quantity=Decimal("50"),
        unit="pacote",
        requesting_department="Secretaria Municipal de Educação",
    )
    rendered = _render_screening(item, candidates=[])
    assert "Resma de papel A4" in rendered
    assert "50" in rendered
    assert "pacote" in rendered
    assert "Secretaria Municipal de Educação" in rendered


def test_screening_renders_candidates_in_given_order():
    item = _make_item()
    c4 = _make_candidate(id=4, description="Candidato quatro")
    c2 = _make_candidate(id=2, description="Candidato dois")
    c7 = _make_candidate(id=7, description="Candidato sete")
    rendered = _render_screening(item, candidates=[c4, c2, c7])

    pos_4 = rendered.find('id="candidate-4"')
    pos_2 = rendered.find('id="candidate-2"')
    pos_7 = rendered.find('id="candidate-7"')
    assert pos_4 != -1 and pos_2 != -1 and pos_7 != -1
    assert pos_4 < pos_2 < pos_7


def test_screening_renders_two_dimension_headers_separately():
    item = _make_item()
    rendered = _render_screening(item, candidates=[])
    assert "<th>Semelhança</th>" in rendered
    assert "<th>Proximidade de valor</th>" in rendered


def test_candidate_fragment_renders_proximity_string_when_given():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, proximity="1,35× acima")
    assert "<td>1,35× acima</td>" in rendered


def test_candidate_fragment_renders_dash_when_proximity_is_missing():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, proximity=None)
    assert "<td>—</td>" in rendered


def test_candidate_fragment_renders_decision_text_for_accept():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, decision="accept")
    assert "Aceito" in rendered


def test_candidate_fragment_renders_decision_text_for_reject():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, decision="reject")
    assert "Descartado" in rendered


def test_candidate_fragment_renders_decide_form_with_htmx_attributes_and_csrf():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate)
    assert f'id="candidate-{candidate.id}"' in rendered
    assert f'hx-post="/candidates/{candidate.id}/decision/"' in rendered
    assert f'hx-target="#candidate-{candidate.id}"' in rendered
    assert 'hx-swap="outerHTML"' in rendered
    assert 'name="csrfmiddlewaretoken"' in rendered
    assert '<button type="submit" name="decision" value="accept">Aceitar</button>' in rendered
    assert '<button type="submit" name="decision" value="reject">Descartar</button>' in rendered


def test_screening_pre_fills_expected_price_field_when_given():
    item = _make_item()
    rendered = _render_screening(item, candidates=[], expected_price=Decimal("12.50"))
    assert 'value="12.50"' in rendered


def test_screening_renders_empty_expected_price_field_when_missing():
    item = _make_item()
    rendered = _render_screening(item, candidates=[], expected_price=None)
    assert 'value=""' in rendered


def test_screening_renders_htmx_script_resolving_to_vendored_file():
    item = _make_item()
    rendered = _render_screening(item, candidates=[])
    match = re.search(r'<script\s+src="/static/([^"]+)"></script>', rendered)
    assert match, "screening.html has no HTMX <script> link under /static/"
    assert finders.find(match.group(1)), f"{match.group(1)} is not a static file"


def test_lookup_filter_returns_value_for_present_key():
    assert lookup({1: "accept", 2: "reject"}, 1) == "accept"


def test_lookup_filter_returns_none_for_missing_key():
    assert lookup({1: "accept"}, 99) is None


def test_lookup_filter_returns_none_for_none_mapping():
    assert lookup(None, 1) is None


def test_candidate_fragment_renders_every_evidence_field_in_column_order():
    candidate = _make_candidate(
        id=5,
        description="Descrição X",
        unit="caixa",
        quantity=Decimal("20"),
        agency="Prefeitura Fictícia A",
        date=datetime.date(2026, 3, 12),
        source="Fonte Fictícia 2",
        provenance="DEMO-007/2026-03",
        price=Decimal("24.80"),
        similarity=0.88,
    )
    flat = _flat(_render_candidate_fragment(candidate, proximity="1,35× acima"))
    assert (
        "<td>Descrição X</td> <td>caixa</td> <td>20</td> <td>Prefeitura Fictícia A</td> "
        "<td>12 de Março de 2026</td> <td>Fonte Fictícia 2</td> <td>DEMO-007/2026-03</td> "
        "<td>24,80</td> <td>0,88</td> <td>1,35× acima</td>"
    ) in flat


def test_screening_header_row_lists_every_column_in_the_fragment_order():
    flat = _flat(_render_screening(_make_item(), candidates=[]))
    assert (
        "<th>Descrição</th> <th>Unidade</th> <th>Quantidade</th> <th>Órgão</th> <th>Data</th> "
        "<th>Fonte</th> <th>Procedência</th> <th>Preço</th> <th>Semelhança</th> "
        "<th>Proximidade de valor</th> <th>Decisão</th> <th>Ações</th>"
    ) in flat


def test_screening_looks_decisions_and_proximities_up_by_candidate_id():
    cands = [_make_candidate(id=7), _make_candidate(id=3), _make_candidate(id=9)]
    rendered = _render_screening(
        _make_item(),
        candidates=cands,
        decisions={7: "accept", 9: "reject"},
        proximities={3: "2,00× acima", 9: "unidade diferente"},
    )
    rows = {
        int(i): row for i, row in re.findall(r'<tr id="candidate-(\d+)">(.*?)</tr>', rendered, re.S)
    }
    assert "Aceito" in rows[7] and "Descartado" not in rows[7]
    assert "<td>—</td>" in rows[7]
    assert "Aceito" not in rows[3] and "Descartado" not in rows[3]
    assert "<td>2,00× acima</td>" in rows[3]
    assert "Descartado" in rows[9] and "<td>unidade diferente</td>" in rows[9]


def test_screening_keeps_the_given_order_whatever_the_field_values_are():
    a = _make_candidate(
        id=4,
        description="m",
        unit="pacote",
        quantity=Decimal("20"),
        agency="Fictícia M",
        date=datetime.date(2026, 3, 1),
        source="Fonte M",
        provenance="DEMO-2",
        price=Decimal("25"),
        similarity=0.8,
    )
    b = _make_candidate(
        id=7,
        description="z",
        unit="unidade",
        quantity=Decimal("30"),
        agency="Fictícia Z",
        date=datetime.date(2026, 4, 1),
        source="Fonte Z",
        provenance="DEMO-3",
        price=Decimal("30"),
        similarity=0.9,
    )
    c = _make_candidate(
        id=2,
        description="a",
        unit="caixa",
        quantity=Decimal("10"),
        agency="Fictícia A",
        date=datetime.date(2026, 2, 1),
        source="Fonte A",
        provenance="DEMO-1",
        price=Decimal("20"),
        similarity=0.7,
    )
    rendered = _render_screening(_make_item(), candidates=[a, b, c])
    assert re.findall(r'<tr id="candidate-(\d+)">', rendered) == ["4", "7", "2"]


def test_candidate_fragment_form_posts_to_decide_for_its_own_candidate():
    flat = _flat(_render_candidate_fragment(_make_candidate(id=7)))
    assert (
        '<form method="post" action="/candidates/7/decision/" hx-post="/candidates/7/decision/" '
        'hx-target="#candidate-7" hx-swap="outerHTML">'
    ) in flat


def test_screening_get_form_has_one_expected_price_field_submitting_to_the_same_url():
    flat = _flat(
        _render_screening(_make_item(id=3), candidates=[], expected_price=Decimal("12.50"))
    )
    assert '<form method="get" action="/items/3/screening/">' in flat
    assert '<label for="expected_price">Preço esperado</label>' in flat
    assert '<input type="text" id="expected_price" name="expected_price" value="12.50">' in flat
    assert ">Atualizar</button>" in flat


def test_candidate_fragment_renders_hidden_expected_price_field():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, expected_price=Decimal("12.50"))
    assert '<input type="hidden" name="expected_price" value="12.50">' in rendered


def test_candidate_fragment_renders_empty_hidden_expected_price_when_none():
    candidate = _make_candidate(id=1)
    rendered = _render_candidate_fragment(candidate, expected_price=None)
    assert '<input type="hidden" name="expected_price" value="">' in rendered


def test_screening_passes_expected_price_to_candidate_fragments():
    item = _make_item()
    candidate = _make_candidate(id=1)
    rendered = _render_screening(item, candidates=[candidate], expected_price=Decimal("12.50"))
    assert '<input type="hidden" name="expected_price" value="12.50">' in rendered


def test_screening_renders_ignored_expected_price_notice_when_input_was_unusable():
    item = _make_item()
    rendered_notice = render_to_string(
        "pricing/screening.html",
        {
            "item": item,
            "candidates": [],
            "decisions": {},
            "proximities": {},
            "expected_price": None,
            "expected_price_ignored": True,
        },
        request=RequestFactory().get("/items/1/screening/?expected_price=1.234,50"),
    )
    assert "Preço esperado ignorado" in rendered_notice

    rendered_clean = render_to_string(
        "pricing/screening.html",
        {
            "item": item,
            "candidates": [],
            "decisions": {},
            "proximities": {},
            "expected_price": None,
            "expected_price_ignored": False,
        },
        request=RequestFactory().get("/items/1/screening/"),
    )
    assert "Preço esperado ignorado" not in rendered_clean


def test_the_panel_without_prices_shows_three_dashes_and_no_zero_value():
    rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": NO_PRICES})
    assert rendered.count("—") == 3 and "0,00" not in rendered
    assert re.search(r"Preços no cálculo:</strong>\s*0\s*</p>", rendered)
    assert "Menos de três preços" not in rendered


def test_the_panel_shows_how_many_prices_are_in_the_calculation():
    for count in (1, 2, 3, 7):
        estimate = {
            "mean": Decimal("10"),
            "median": Decimal("10"),
            "min": Decimal("10"),
            "count": count,
            "requires_justification": count < 3,
        }
        rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": estimate})
        assert re.search(rf"Preços no cálculo:</strong>\s*{count}\s*</p>", rendered)


def test_the_panel_prints_each_value_with_exactly_two_decimals():
    estimate = {
        "mean": Decimal("27.8"),
        "median": Decimal("27.9"),
        "min": Decimal("26.5"),
        "count": 3,
        "requires_justification": False,
    }
    rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": estimate})
    for value in ("27,80", "27,90", "26,50"):
        assert re.search(rf"R\$ {value}(?!\d)", rendered)


def test_estimate_panel_renders_wrapper_with_grid_class_and_aria_live():
    rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": NO_PRICES})
    assert 'aria-live="polite"' in rendered
    wrapper = re.search(r'<div class="([^"]*)">\s*<p>', rendered)
    assert wrapper and "grid" in wrapper.group(1).split()


def test_the_estimate_wrapper_carries_the_grid_class_as_a_token():
    rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": NO_PRICES})
    wrapper = re.search(r'<div class="([^"]*)">\s*<p>', rendered)
    assert wrapper and "grid" in wrapper.group(1).split()


def test_no_justification_notice_from_three_prices_on():
    for count in (3, 4, 7):
        estimate = {
            "mean": Decimal("10"),
            "median": Decimal("10"),
            "min": Decimal("10"),
            "count": count,
            "requires_justification": False,
        }
        rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": estimate})
        assert "Menos de três preços" not in rendered


def test_estimate_panel_renders_values_in_brazilian_currency_and_justification_notice():
    estimate = {
        "mean": Decimal("26.50"),
        "median": Decimal("26.50"),
        "min": Decimal("26.50"),
        "count": 1,
        "requires_justification": True,
    }
    rendered = render_to_string("pricing/_estimate_panel.html", {"estimate": estimate})
    assert re.search(r"R\$ 26,50(?!\d)", rendered)
    assert re.search(r"Preços no cálculo:</strong>\s*1\s*</p>", rendered)
    assert (
        "Menos de três preços: a pesquisa exige justificativa (IN 65/2021, art. 6º, § 5º; RN06)."
        in rendered
    )


def test_estimate_panel_renders_hx_swap_oob_attribute_when_flagged():
    rendered = render_to_string(
        "pricing/_estimate_panel.html", {"estimate": NO_PRICES, "hx_swap_oob": True}
    )
    assert 'id="estimate-panel"' in rendered
    assert 'hx-swap-oob="true"' in rendered


def test_candidate_fragment_renders_fora_do_calculo_when_accepted_with_unit_mismatch():
    candidate = _make_candidate(id=4, unit="unidade")
    rendered = _render_candidate_fragment(candidate, decision="accept", item_unit="pacote")
    assert "fora do cálculo: unidade diferente" in rendered
    assert "Aceito" not in rendered


def test_candidate_fragment_renders_aceito_when_accepted_with_matching_unit():
    candidate = _make_candidate(id=1, unit="pacote")
    rendered = _render_candidate_fragment(candidate, decision="accept", item_unit="pacote")
    assert "Aceito" in rendered
    assert "fora do cálculo: unidade diferente" not in rendered


def test_candidate_fragment_derives_decision_label_from_estimate_counted_ids():
    candidate = _make_candidate(id=1, unit="pacote")
    estimate_excluding = {"counted_candidate_ids": set()}
    rendered = render_to_string(
        "pricing/_candidate.html",
        {"candidate": candidate, "decision": "accept", "estimate": estimate_excluding},
    )
    assert "fora do cálculo: unidade diferente" in rendered
    assert "Aceito" not in rendered

    estimate_including = {"counted_candidate_ids": {1}}
    rendered_inc = render_to_string(
        "pricing/_candidate.html",
        {"candidate": candidate, "decision": "accept", "estimate": estimate_including},
    )
    assert "Aceito" in rendered_inc
    assert "fora do cálculo: unidade diferente" not in rendered_inc


def test_screening_renders_back_link_to_procurement():
    item = _make_item()
    procurement = ProcurementStub(id=7, title="Processo 7")
    rendered = _render_screening(item, candidates=[], procurement=procurement)
    detail_url = reverse("procurement:detail", args=[procurement.id])
    assert re.search(
        rf'<a\s+[^>]*href="{re.escape(detail_url)}"[^>]*>\s*Voltar para o processo\s*</a>',
        rendered,
    )


def test_screening_renders_no_back_link_when_procurement_is_none():
    item = _make_item()
    rendered = _render_screening(item, candidates=[], procurement=None)
    assert "Voltar para o processo" not in rendered
