from collections.abc import Iterable, Sequence
from datetime import date
from typing import Any


def volume_per_day(
    publications: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> dict[date, int]:
    """Count publications by the date part of dataPublicacaoPncp."""
    raise NotImplementedError


def missing_share(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
    field: str,
) -> float | None:
    """Calculate the share of items where field is absent, None, or empty after strip."""
    raise NotImplementedError


def median_description_length(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> float | None:
    """Calculate the median length of non-missing descriptions after strip."""
    raise NotImplementedError


def distinct_units(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> int:
    """Count distinct unidadeMedida values after strip and casefold, ignoring missing."""
    raise NotImplementedError
