from typing import Any

from django import template

register = template.Library()


@register.filter
def lookup(mapping: dict[Any, Any] | None, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None
    return mapping.get(key)
