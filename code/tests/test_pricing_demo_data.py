import datetime
import re
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from pricing.demo_data import (
    PriceCandidate,
    candidates_for,
    get_candidate,
)
from procurement.demo_data import UNITS, list_procurements


def _all_items():
    return [item for procurement in list_procurements() for item in procurement.items]


def _all_candidates():
    candidates = []
    for item in _all_items():
        candidates.extend(candidates_for(item.id))
    return candidates


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2}


def _is_service(text: str) -> bool:
    return "serviço" in text.lower()


def test_dataclass_fields_match_the_frozen_contract():
    expected_fields = [
        "id",
        "item_id",
        "description",
        "unit",
        "quantity",
        "agency",
        "date",
        "source",
        "price",
        "similarity",
        "provenance",
    ]
    assert [f.name for f in fields(PriceCandidate)] == expected_fields


def test_candidates_dataclass_is_frozen():
    candidate = get_candidate(1)
    assert candidate is not None
    with pytest.raises(FrozenInstanceError):
        candidate.price = Decimal("100.00")  # type: ignore[misc]


def test_contract_types_hold_for_every_record():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert isinstance(c.id, int)
        assert isinstance(c.item_id, int)
        assert isinstance(c.description, str)
        assert isinstance(c.unit, str)
        assert isinstance(c.quantity, Decimal)
        assert isinstance(c.agency, str)
        assert isinstance(c.date, datetime.date)
        assert isinstance(c.source, str)
        assert isinstance(c.price, Decimal)
        assert isinstance(c.similarity, float)
        assert isinstance(c.provenance, str)


def test_every_candidate_is_found_by_its_own_id():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert get_candidate(c.id) is c


def test_candidates_for_returns_declaration_order():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for item in _all_items():
        item_candidates = candidates_for(item.id)
        assert len(item_candidates) >= 3
        expected_subset = [c for c in all_candidates if c.item_id == item.id]
        assert item_candidates == expected_subset


def test_candidate_count_per_requested_item_between_three_and_six():
    items = _all_items()
    assert len(items) > 0
    for item in items:
        item_candidates = candidates_for(item.id)
        assert 3 <= len(item_candidates) <= 6


def test_candidate_ids_are_unique():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    ids = [c.id for c in all_candidates]
    assert len(ids) == len(set(ids))


def test_candidate_item_ids_exist_in_procurement_demo_data():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    valid_item_ids = {item.id for item in _all_items()}
    for c in all_candidates:
        assert c.item_id in valid_item_ids


def test_candidate_similarity_between_zero_and_one():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert 0.0 <= c.similarity <= 1.0


def test_candidate_prices_and_quantities_are_positive():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert isinstance(c.price, Decimal)
        assert c.price > Decimal(0)
        assert isinstance(c.quantity, Decimal)
        assert c.quantity > Decimal(0)


def test_candidate_text_fields_are_filled_in():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert c.description.strip()
        assert c.unit.strip()
        assert c.agency.strip()
        assert c.source.strip()
        assert c.provenance.strip()


def test_candidate_units_belong_to_vocabulary():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert c.unit in UNITS


def test_candidate_provenance_is_fictitious_and_marked():
    all_candidates = _all_candidates()
    assert len(all_candidates) > 0
    for c in all_candidates:
        assert "fictíci" in c.agency.lower()
        assert c.source.startswith("Fonte Fictícia")
        assert c.provenance.startswith("DEMO-")


def test_hard_case_keyword_match_service_is_present():
    item = {i.id: i for i in _all_items()}
    hits = []
    for c in _all_candidates():
        it = item[c.item_id]
        if (
            _is_service(c.description)
            and not _is_service(it.description)
            and len(_tokens(c.description) & _tokens(it.description)) >= 2
        ):
            hits.append(c)
    assert hits


def test_hard_case_incompatible_unit_is_present():
    item = {i.id: i for i in _all_items()}
    hits = []
    for c in _all_candidates():
        it = item[c.item_id]
        if (
            c.unit != it.unit
            and not _is_service(c.description)
            and len(_tokens(c.description) & _tokens(it.description)) >= 3
        ):
            hits.append(c)
    assert hits


def test_hard_case_terse_description_names_the_product_but_not_its_specification():
    item = {i.id: i for i in _all_items()}
    hits = []
    for c in _all_candidates():
        wanted, got = _tokens(item[c.item_id].description), _tokens(c.description)
        if len(c.description.split()) <= 2 and got & wanted and len(wanted - got) >= 3:
            hits.append(c)
    assert hits


def test_hard_case_outlier_price_among_comparable_candidates():
    hits = []
    for item in _all_items():
        comparable = [
            c
            for c in candidates_for(item.id)
            if c.unit == item.unit and not _is_service(c.description)
        ]
        for c in comparable:
            others = [o.price for o in comparable if o is not c]
            if len(others) >= 2 and c.price >= 5 * max(others):
                hits.append(c)
    assert hits


def test_get_candidate_unknown_id_returns_none():
    assert get_candidate(99999) is None


def test_candidates_for_unknown_item_returns_empty_list():
    assert candidates_for(99999) == []
