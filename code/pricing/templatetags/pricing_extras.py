from typing import Any

from django import template

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
