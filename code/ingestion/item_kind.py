"""Procurement item kind mapping between PNCP raw values and domain values."""


def map_item_kind(code: object, name: object) -> str:
    """Map PNCP material/service fields to a domain item_kind."""
    raise NotImplementedError("Item kind mapping is not implemented")
