import datetime
from decimal import Decimal

import pytest

from pricing.demo_data import PriceCandidate
from pricing.ranking import (
    BAND_HIGH_MIN,
    BAND_MEDIUM_MIN,
    compute_proximity,
    format_proximity,
    rank_candidates,
)


def _make_candidate(
    candidate_id: int,
    similarity: float,
    price: str,
    unit: str = "pacote",
    description: str = "Candidate description",
) -> PriceCandidate:
    return PriceCandidate(
        id=candidate_id,
        item_id=1,
        description=description,
        unit=unit,
        quantity=Decimal("10"),
        agency="Prefeitura Fictícia A",
        date=datetime.date(2026, 3, 12),
        source="Fonte Fictícia 1",
        price=Decimal(price),
        similarity=similarity,
        provenance="DEMO-001",
    )


# --- 1. Band Constants ---


def test_band_thresholds_are_declared_as_constants():
    assert BAND_HIGH_MIN == 0.80
    assert BAND_MEDIUM_MIN == 0.60


# --- 2. Proximity Computation & Formatting ---


def test_compute_proximity_symmetry_for_double_and_half():
    # If e=10.00, p=20.00 -> ln(2) approx 0.6931
    # p=5.00 -> |ln(0.5)| = ln(2) approx 0.6931
    e = Decimal("10.00")
    d_double = compute_proximity(Decimal("20.00"), e, candidate_unit="pacote", item_unit="pacote")
    d_half = compute_proximity(Decimal("5.00"), e, candidate_unit="pacote", item_unit="pacote")

    assert d_double is not None
    assert d_half is not None
    assert pytest.approx(d_double, rel=1e-5) == d_half


def test_compute_proximity_zero_distance_when_prices_equal():
    e = Decimal("15.50")
    d = compute_proximity(Decimal("15.50"), e, candidate_unit="pacote", item_unit="pacote")
    assert d == 0.0


def test_compute_proximity_undefined_when_units_mismatch():
    d = compute_proximity(
        Decimal("10.00"),
        Decimal("10.00"),
        candidate_unit="unidade",
        item_unit="pacote",
    )
    assert d is None


def test_compute_proximity_undefined_when_price_non_positive():
    assert (
        compute_proximity(Decimal("0.00"), Decimal("10.00"), candidate_unit="kg", item_unit="kg")
        is None
    )
    assert (
        compute_proximity(Decimal("-5.00"), Decimal("10.00"), candidate_unit="kg", item_unit="kg")
        is None
    )


def test_compute_proximity_undefined_when_no_expected_price():
    assert compute_proximity(Decimal("10.00"), None, candidate_unit="kg", item_unit="kg") is None


def test_format_proximity_display():
    e = Decimal("10.00")
    # p=13.50 -> 1.35x acima
    d_above = compute_proximity(Decimal("13.50"), e, "kg", "kg")
    assert format_proximity(Decimal("13.50"), e, d_above, "kg", "kg") == "1,35× acima"

    # p=7.41 -> approx 1.35x abaixo (10 / 7.4074 approx 1.35)
    d_below = compute_proximity(Decimal("7.4074"), e, "kg", "kg")
    assert format_proximity(Decimal("7.4074"), e, d_below, "kg", "kg") == "1,35× abaixo"

    # Equal prices -> "1,00×"
    d_equal = compute_proximity(Decimal("10.00"), e, "kg", "kg")
    assert "1,00×" in format_proximity(Decimal("10.00"), e, d_equal, "kg", "kg")

    # Undefined due to unit mismatch
    assert format_proximity(Decimal("10.00"), e, None, "unidade", "kg") == "unidade diferente"

    # Undefined due to p <= 0
    assert format_proximity(Decimal("0.00"), e, None, "kg", "kg") == "preço inválido"

    # No expected price
    assert format_proximity(Decimal("10.00"), None, None, "kg", "kg") == "—"
    assert format_proximity(Decimal("10.00"), None, None, "unidade", "pacote") == "—"


# --- 3. Ranking Order Rules (Option A) ---


def test_ranking_empty_list():
    assert rank_candidates([], Decimal("10.00"), "pacote") == []


def test_ranking_band_order_beats_proximity():
    # Candidate A: High band (sim 0.85), price farther (p=30, e=10)
    # Candidate B: Medium band (sim 0.70), price closer (p=11, e=10)
    cand_a = _make_candidate(1, similarity=0.85, price="30.00")
    cand_b = _make_candidate(2, similarity=0.70, price="11.00")

    ranked = rank_candidates([cand_b, cand_a], expected_price=Decimal("10.00"), item_unit="pacote")
    assert [c.id for c in ranked] == [1, 2]


def test_ranking_proximity_orders_inside_band():
    # Both High band:
    # cand 1: p=11.00 (d = |ln(1.1)| approx 0.095)
    # cand 2: p=15.00 (d = |ln(1.5)| approx 0.405)
    cand_1 = _make_candidate(1, similarity=0.85, price="11.00")
    cand_2 = _make_candidate(2, similarity=0.85, price="15.00")

    ranked = rank_candidates([cand_2, cand_1], expected_price=Decimal("10.00"), item_unit="pacote")
    assert [c.id for c in ranked] == [1, 2]


def test_ranking_without_expected_price_orders_by_band_then_similarity():
    # Without expected price: order is band desc, similarity desc, id asc
    cand_1 = _make_candidate(1, similarity=0.82, price="50.00")
    cand_2 = _make_candidate(2, similarity=0.88, price="10.00")
    cand_3 = _make_candidate(3, similarity=0.65, price="12.00")

    ranked = rank_candidates([cand_1, cand_3, cand_2], expected_price=None, item_unit="pacote")
    assert [c.id for c in ranked] == [2, 1, 3]


def test_ranking_without_expected_price_keeps_unit_mismatched_candidate_in_similarity_order():
    # Without expected price, unit mismatch is NOT sent to end of band:
    # Order is strictly band desc, similarity desc, id asc.
    cand_1 = _make_candidate(1, similarity=0.75, price="10.00", unit="unidade")  # mismatch
    cand_2 = _make_candidate(2, similarity=0.70, price="10.00", unit="pacote")  # matches item unit

    ranked = rank_candidates([cand_2, cand_1], expected_price=None, item_unit="pacote")
    assert [c.id for c in ranked] == [1, 2]


def test_ranking_unit_mismatch_goes_to_end_of_band():
    # All Medium band (sim 0.70)
    # cand 1: unit matches, p=20 (d approx 0.693)
    # cand 2: unit mismatch -> goes to end of Medium band
    # cand 3: unit matches, p=11 (d approx 0.095)
    cand_1 = _make_candidate(1, similarity=0.70, price="20.00", unit="pacote")
    cand_2 = _make_candidate(2, similarity=0.70, price="10.00", unit="unidade")
    cand_3 = _make_candidate(3, similarity=0.70, price="11.00", unit="pacote")

    ranked = rank_candidates(
        [cand_2, cand_1, cand_3],
        expected_price=Decimal("10.00"),
        item_unit="pacote",
    )
    assert [c.id for c in ranked] == [3, 1, 2]


def test_ranking_ties_broken_by_similarity_descending_then_id_ascending():
    # Same band, same price proximity (both p=10, e=10 -> d=0)
    # cand 1: sim 0.85, id 10
    # cand 2: sim 0.90, id 20 -> higher similarity beats cand 1
    # cand 3: sim 0.85, id 5  -> same similarity as cand 1, but lower id beats cand 1
    cand_1 = _make_candidate(10, similarity=0.85, price="10.00")
    cand_2 = _make_candidate(20, similarity=0.90, price="10.00")
    cand_3 = _make_candidate(5, similarity=0.85, price="10.00")

    ranked = rank_candidates(
        [cand_1, cand_2, cand_3],
        expected_price=Decimal("10.00"),
        item_unit="pacote",
    )
    assert [c.id for c in ranked] == [20, 5, 10]


def test_ranking_band_boundaries_exact_080_and_060():
    # 0.80 is High band; 0.799 is Medium band
    # 0.60 is Medium band; 0.599 is Low band
    c_high = _make_candidate(1, similarity=0.80, price="100.00")
    c_med_top = _make_candidate(2, similarity=0.799, price="10.00")
    c_med_bottom = _make_candidate(3, similarity=0.60, price="100.00")
    c_low = _make_candidate(4, similarity=0.599, price="10.00")

    ranked = rank_candidates(
        [c_low, c_med_bottom, c_med_top, c_high],
        expected_price=Decimal("10.00"),
        item_unit="pacote",
    )
    assert [c.id for c in ranked] == [1, 2, 3, 4]
