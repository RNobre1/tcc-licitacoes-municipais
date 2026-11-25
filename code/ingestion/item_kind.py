"""Procurement item kind mapping between PNCP raw values and domain values."""


def map_item_kind(code: object, name: object) -> str:
    """Map PNCP material/service fields to a domain item_kind."""
    material_or_service = str(code or "").upper()
    material_or_service_name = str(name or "").lower()
    if material_or_service == "S" or "serviço" in material_or_service_name:
        return "service"
    return "product"
