"""Tests for resolving ground-truth records from PNCP raw records."""

from decimal import Decimal

from evaluation.ground_truth import (
    ResolvedGroundTruthItem,
    match_ground_truth_item,
)
from ingestion.models import RawRecord


def test_match_ground_truth_item_found():
    record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Papel Sulfite A4 75g",
                "materialOuServico": "M",
                "unidadeMedida": "PACOTE",
                "quantidade": 50.0,
                "valorUnitarioEstimado": 28.5,
                "valorUnitarioHomologado": 25.0,
                "temResultado": True,
                "orcamentoSigiloso": False,
            },
            {
                "numeroItem": 2,
                "descricao": "DEMO-Caneta",
                "materialOuServico": "M",
                "unidadeMedida": "UNIDADE",
                "quantidade": 10.0,
                "valorUnitarioEstimado": 1.5,
                "valorUnitarioHomologado": 1.4,
                "temResultado": True,
                "orcamentoSigiloso": False,
            },
        ],
    )

    resolved = match_ground_truth_item(
        cnpj="11111111000111",
        ano=2026,
        sequencial=100,
        numero_item=1,
        records=[record],
    )

    assert isinstance(resolved, ResolvedGroundTruthItem)
    assert resolved.found is True
    assert resolved.numero_item == 1
    assert resolved.description == "DEMO-Papel Sulfite A4 75g"
    assert resolved.item_kind == "product"
    assert resolved.unit == "PACOTE"
    assert resolved.quantity == Decimal("50.0")
    assert resolved.estimated_unit_price == Decimal("28.5")
    assert resolved.awarded_unit_price == Decimal("25.0")
    assert resolved.has_result is True
    assert resolved.secret_budget is False
    assert resolved.failure_cause is None


def test_match_ground_truth_item_not_found():
    record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        payload=[
            {
                "numeroItem": 2,
                "descricao": "DEMO-Caneta",
                "materialOuServico": "M",
                "unidadeMedida": "UNIDADE",
                "quantidade": 10.0,
                "valorUnitarioEstimado": 1.5,
                "temResultado": True,
                "orcamentoSigiloso": False,
            }
        ],
    )

    resolved = match_ground_truth_item(
        cnpj="11111111000111",
        ano=2026,
        sequencial=100,
        numero_item=99,
        records=[record],
    )

    assert resolved.found is False
    assert resolved.numero_item == 99
    assert resolved.failure_cause == "item_not_found_in_purchase"
