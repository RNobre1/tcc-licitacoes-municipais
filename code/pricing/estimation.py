import statistics
from collections.abc import Sequence
from decimal import Decimal


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
