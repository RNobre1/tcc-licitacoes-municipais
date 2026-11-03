from decimal import Decimal
from typing import Sequence


def calculate_mean(prices: Sequence[Decimal]) -> Decimal:
    """Compute the arithmetic mean of a sequence of prices (IN 65/2021, Art. 6 caput)."""
    raise NotImplementedError


def calculate_median(prices: Sequence[Decimal]) -> Decimal:
    """Compute the median of a sequence of prices (IN 65/2021, Art. 6 caput)."""
    raise NotImplementedError


def calculate_min(prices: Sequence[Decimal]) -> Decimal:
    """Compute the lowest price in a sequence (IN 65/2021, Art. 6 caput)."""
    raise NotImplementedError


def requires_justification(prices: Sequence[Decimal]) -> bool:
    """Check whether estimation requires justification due to fewer than 3 prices (IN 65/2021, Art. 6 § 5, RN06)."""
    raise NotImplementedError
