"""Tests for resolving ground-truth records from PNCP raw records."""

from datetime import datetime, timezone
from decimal import Decimal

from evaluation.ground_truth import (
    ResolvedGroundTruthItem,
    match_ground_truth_item,
)
from ingestion.models import RawRecord


def test_match_ground_truth_item_found_with_results():
    # Item record without awarded price (PNCP items API does not carry awarded price)
    item_record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        fetched_at=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Papel Sulfite A4 75g",
                "materialOuServico": "M",
                "materialOuServicoNome": "Material",
                "unidadeMedida": "PACOTE",
                "quantidade": 50.0,
                "valorUnitarioEstimado": 28.5,
                "valorUnitarioHomologado": 999.0,  # Should be ignored (N6: comes from results, never item)
                "temResultado": True,
                "orcamentoSigiloso": False,
            },
        ],
    )

    # Result record carrying awarded price (N6)
    result_record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens/1/resultados",
        params={},
        status_code=200,
        fetched_at=datetime(2026, 11, 1, 10, 5, tzinfo=timezone.utc),
        payload=[
            {
                "situacaoCompraItemResultadoNome": "Informado",
                "dataCancelamento": None,
                "valorUnitarioHomologado": 25.0,
            }
        ],
    )

    resolved = match_ground_truth_item(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        item_records=[item_record],
        result_records=[result_record],
    )

    assert isinstance(resolved, ResolvedGroundTruthItem)
    assert resolved.found is True
    assert resolved.item_number == 1
    assert resolved.description == "DEMO-Papel Sulfite A4 75g"
    assert resolved.item_kind == "product"
    assert resolved.unit == "PACOTE"
    assert resolved.quantity == Decimal("50.0")
    assert resolved.estimated_unit_price == Decimal("28.5")
    # N6: Awarded price must be 25.0 from result record, NOT 999.0 from item
    assert resolved.awarded_unit_price == Decimal("25.0")
    assert resolved.has_result is True
    assert resolved.secret_budget is False
    assert resolved.failure_cause is None


def test_match_ground_truth_item_ignores_awarded_price_on_item():
    # If no result records are provided, awarded price is None (never read from item payload)
    item_record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Item",
                "materialOuServico": "M",
                "quantidade": 10.0,
                "valorUnitarioEstimado": 10.0,
                "valorUnitarioHomologado": 8.0,  # Must be ignored
            }
        ],
    )

    resolved = match_ground_truth_item(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        item_records=[item_record],
        result_records=[],
    )

    assert resolved.found is True
    assert resolved.awarded_unit_price is None


def test_match_ground_truth_item_newest_copy_wins():
    # N7: older copy and newer copy of item record
    older_record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        fetched_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        payload=[
            {
                "numeroItem": 1,
                "descricao": "OLDER-DESCRIPTION",
                "materialOuServico": "M",
                "quantidade": 10.0,
            }
        ],
    )
    newer_record = RawRecord(
        endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
        params={"pagina": 1},
        status_code=200,
        fetched_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        payload=[
            {
                "numeroItem": 1,
                "descricao": "NEWER-DESCRIPTION",
                "materialOuServico": "M",
                "quantidade": 15.0,
            }
        ],
    )

    resolved = match_ground_truth_item(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        item_records=[older_record, newer_record],
    )

    assert resolved.found is True
    assert resolved.description == "NEWER-DESCRIPTION"
    assert resolved.quantity == Decimal("15.0")


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
        year=2026,
        purchase_sequence=100,
        item_number=99,
        item_records=[record],
    )

    assert resolved.found is False
    assert resolved.item_number == 99
    assert resolved.failure_cause == "item_not_found_in_purchase"
