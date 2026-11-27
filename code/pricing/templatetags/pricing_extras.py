from typing import Any

from django import template

from pricing.formatting import format_decimal as _format_decimal
from pricing.formatting import format_similarity as _format_similarity

register = template.Library()


@register.filter
def lookup(mapping: dict[Any, Any] | None, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(key)


@register.filter
def units_match(unit_a: Any, unit_b: Any) -> bool:
    from ingestion.units import normalize_unit

    return normalize_unit(unit_a) == normalize_unit(unit_b)


@register.filter
def format_decimal(value: Any) -> str:
    return _format_decimal(value)


@register.filter
def format_similarity(value: Any) -> str:
    return _format_similarity(value)
