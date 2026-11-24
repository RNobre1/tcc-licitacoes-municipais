"""Procurement item awarded result processing and validation."""

from collections.abc import Iterable
from typing import Any


def select_valid_result(
    results: Iterable[dict[str, Any]] | Any,
) -> dict[str, Any] | None:
    """Select the valid awarded result from PNCP /resultados payload.

    Picks the first result with situacaoCompraItemResultadoNome == 'Informado'
    and no dataCancelamento. Returns None if no valid result is found.
    """
    if not results or not isinstance(results, (list, tuple, Iterable)):
        return None

    for res in results:
        if not isinstance(res, dict):
            continue
        situacao = res.get("situacaoCompraItemResultadoNome")
        cancelado = res.get("dataCancelamento")
        if situacao == "Informado" and not cancelado:
            return res

    return None
