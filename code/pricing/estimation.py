import statistics
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from .candidates import Candidate


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
    """Return the awarded prices usable for calculation from Candidate objects.

    Duck-typed objects and bare Decimals raise TypeError. Zero prices,
    estimated prices, and secret-budget items are excluded.
    """
    usable: list[Decimal] = []
    for candidate in candidates:
        if not isinstance(candidate, Candidate):
            raise TypeError(f"Expected Candidate, got {type(candidate).__name__}")
        price = candidate.usable_calculation_price
        if price is not None and price > Decimal("0.00"):
            usable.append(price)
    return usable
