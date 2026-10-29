"""Candidate ranking and price proximity calculations for RF23.

Note: BAND_HIGH_MIN and BAND_MEDIUM_MIN are provisional thresholds
for prototype display only, to be calibrated in backlog item C15
prior to empirical measurement.
"""

import math
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pricing.demo_data import PriceCandidate

BAND_HIGH_MIN = 0.80
BAND_MEDIUM_MIN = 0.60

EXPECTED_PRICE_MIN = Decimal("0.01")
EXPECTED_PRICE_MAX = Decimal("999999999.99")


def compute_proximity(price, expected_price, candidate_unit, item_unit) -> float | None:
    if price is None or expected_price is None or price <= 0 or expected_price <= 0:
        return None

    if candidate_unit is None or item_unit is None:
        return None

    if candidate_unit != item_unit:
        return None

    return abs(math.log(float(price) / float(expected_price)))


def format_proximity(price, expected_price, proximity, candidate_unit, item_unit) -> str:
    if expected_price is None:
        return "—"

    if price <= 0:
        return "preço inválido"

    if item_unit is None or candidate_unit is None:
        return "—"

    if item_unit != candidate_unit:
        return "unidade diferente"

    if proximity is not None:
        factor = math.exp(proximity)
        formatted = f"{factor:.2f}".replace(".", ",")

        if price > expected_price:
            return f"{formatted}× acima"
        if price < expected_price:
            return f"{formatted}× abaixo"
        if price == expected_price:
            return "1,00×"

    return "—"


def _band_rank(similarity: float) -> int:
    if similarity >= BAND_HIGH_MIN:
        return 0  # High band
    if similarity >= BAND_MEDIUM_MIN:
        return 1  # Medium band
    return 2  # Low band


def rank_candidates(candidates, expected_price=None, item_unit=None) -> list[PriceCandidate]:
    def sort_key(candidate):
        band = _band_rank(candidate.similarity)
        if expected_price is not None:
            prox = compute_proximity(
                candidate.price, expected_price, candidate.unit, item_unit or ""
            )
            # Undefined proximity (None) goes to the end of the band:
            # 0 comes before 1, so (0, prox) comes before (1, 0.0)
            has_no_prox = 1 if prox is None else 0
            distance = round(prox, 9) if prox is not None else 0.0
            return (band, has_no_prox, distance, -candidate.similarity, candidate.id)
        else:
            # When expected_price is None, order is strictly band, similarity desc, id asc
            return (band, -candidate.similarity, candidate.id)

    return sorted(candidates, key=sort_key)


def parse_expected_price(raw: str | None) -> Decimal | None:
    if raw is None or raw == "":
        return None

    cleaned = raw.strip().replace(",", ".")

    try:
        val = Decimal(cleaned)
        if not val.is_finite():
            return None
        if val < EXPECTED_PRICE_MIN or val > EXPECTED_PRICE_MAX:
            return None
        return val
    except InvalidOperation, TypeError:
        return None
