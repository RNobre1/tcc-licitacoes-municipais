import datetime
import re
from dataclasses import dataclass
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory

from pricing.templatetags.pricing_extras import lookup


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
        },
        request=request,
    )


def _render_candidate_fragment(
    candidate: CandidateStub,
    decision: str | None = None,
    proximity: str | None = None,
) -> str:
    request = RequestFactory().get("/")
    return render_to_string(
        "pricing/_candidate.html",
        {
            "candidate": candidate,
            "decision": decision,
            "proximity": proximity,
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
