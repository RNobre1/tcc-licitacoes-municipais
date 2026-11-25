"""Procurement item awarded result processing and validation."""

from collections.abc import Iterable
from decimal import Decimal, DecimalException
from typing import Any


def select_valid_result(
    results: Iterable[dict[str, Any]] | Any,
) -> dict[str, Any] | None:
    """Select the valid awarded result from PNCP /resultados payload.

    Picks the first informed, non-cancelled result with a positive readable
    valorUnitarioHomologado. Returns None if no valid result is found.
    """
    if not results or not isinstance(results, (list, tuple, Iterable)):
        return None

    for res in results:
        if not isinstance(res, dict):
            continue
        situacao = res.get("situacaoCompraItemResultadoNome")
        cancelado = res.get("dataCancelamento")
        if situacao != "Informado" or cancelado:
            continue

        try:
            awarded_price = Decimal(str(res.get("valorUnitarioHomologado")))
        except DecimalException, TypeError, ValueError:
            continue
        if awarded_price.is_finite() and awarded_price > 0:
            return res

    return None
