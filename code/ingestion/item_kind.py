"""Procurement item kind mapping between PNCP raw values and domain values."""


def map_item_kind(value: str | None) -> str:
    """Map PNCP materialOuServico to domain item_kind ('product' or 'service').

    Rule: 'S' is service, anything else is product.
    """
    if value is not None:
        v = str(value).strip().upper()
        if v == "S" or v.startswith("SERVI"):
            return "service"
    return "product"
