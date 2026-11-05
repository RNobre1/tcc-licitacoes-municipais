from collections.abc import Iterable, Sequence
from datetime import date, datetime
from statistics import median
from typing import Any


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _parse_publication_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        if len(cleaned) >= 10 and cleaned[4] == "-" and cleaned[7] == "-":
            try:
                return date.fromisoformat(cleaned[:10])
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(cleaned).date()
        except ValueError:
            return None
    return None


def volume_per_day(
    publications: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> dict[date, int]:
    """Count publications by the date part of dataPublicacaoPncp."""
    counts: dict[date, int] = {}
    for pub in publications:
        raw_date = pub.get("dataPublicacaoPncp")
        if raw_date is None:
            continue
        parsed_date = _parse_publication_date(raw_date)
        if parsed_date is not None:
            counts[parsed_date] = counts.get(parsed_date, 0) + 1
    return counts


def missing_share(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
    field: str,
) -> float | None:
    """Calculate the share of items where field is absent, None, or empty after strip."""
    items_list = list(items) if not isinstance(items, (list, tuple)) else items
    if not items_list:
        return None
    missing_count = sum(1 for item in items_list if field not in item or _is_missing(item[field]))
    return missing_count / len(items_list)


def median_description_length(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> float | None:
    """Calculate the median length of non-missing descriptions after strip."""
    lengths: list[int] = []
    for item in items:
        val = item.get("descricao")
        if _is_missing(val):
            continue
        lengths.append(len(val.strip()))
    if not lengths:
        return None
    return float(median(lengths))


def distinct_units(
    items: Sequence[dict[str, Any]] | Iterable[dict[str, Any]],
) -> int:
    """Count distinct unidadeMedida values after strip and casefold, ignoring missing."""
    units: set[str] = set()
    for item in items:
        val = item.get("unidadeMedida")
        if _is_missing(val) or not isinstance(val, str):
            continue
        units.add(val.strip().casefold())
    return len(units)
