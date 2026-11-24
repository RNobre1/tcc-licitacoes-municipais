import statistics
from collections.abc import Sequence
from decimal import Decimal
from typing import Any


def calculate_mean(prices: Sequence[Decimal]) -> Decimal:
    """Compute the arithmetic mean of a sequence of prices (IN 65/2021, Art. 6 caput)."""
    if not prices:
        raise ValueError("At least one price is required")
    return statistics.mean(prices)


def calculate_median(prices: Sequence[Decimal]) -> Decimal:
    """Compute the median of a sequence of prices (IN 65/2021, Art. 6 caput)."""
    if not prices:
        raise ValueError("At least one price is required")
    return statistics.median(prices)


def calculate_min(prices: Sequence[Decimal]) -> Decimal:
    """Compute the lowest price in a sequence (IN 65/2021, Art. 6 caput)."""
    if not prices:
        raise ValueError("At least one price is required")
    return min(prices)


def requires_justification(prices: Sequence[Decimal]) -> bool:
    """Check whether estimation requires justification (IN 65/2021, Art. 6 § 5, RN06)."""
    return len(prices) < 3


def get_calculation_prices(candidates: Sequence[Any]) -> list[Decimal]:
    """Return the prices usable for calculation from a sequence of candidates.

    Only awarded prices are usable. Zero prices, estimated prices, and secret-budget
    items are excluded so they never reach calculation functions.
    """
    raise NotImplementedError
