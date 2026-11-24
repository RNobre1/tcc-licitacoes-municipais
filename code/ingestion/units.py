"""Procurement item measurement unit normalization."""


def normalize_unit(value: str | None) -> str:
    """Normalize procurement item measurement unit for indexing, search, and metrics.

    Applies strip and casefold to ensure consistent representation across all
    subsystems. If value is None, returns an empty string.
    """
    if value is None:
        return ""
    return str(value).strip().casefold()
