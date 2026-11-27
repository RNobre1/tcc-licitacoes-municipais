import math
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


def format_decimal(value: Any) -> str:
    """Format a decimal price or quantity with Brazilian comma rules and no rounding."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)

    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        d = Decimal(str(value))
    else:
        try:
            d = Decimal(str(value).strip())
        except InvalidOperation, ValueError:
            return str(value)

    if not d.is_finite():
        return str(value)

    with localcontext() as ctx:
        ctx.prec = max(28, len(d.as_tuple().digits) + 2)
        norm = d.normalize()

    if norm == 0:
        return "0"

    exponent = norm.as_tuple().exponent
    frac_digits = max(0, -int(exponent))
    if frac_digits == 0:
        target_places = 0
    elif frac_digits <= 2:
        target_places = 2
    elif frac_digits <= 4:
        target_places = 4
    else:
        target_places = frac_digits

    return f"{norm:.{target_places}f}".replace(".", ",")


def format_similarity(value: Any) -> str:
    """Format a semantic similarity score to two decimal places with Brazilian comma."""
    raise NotImplementedError("format_similarity is not implemented yet")
