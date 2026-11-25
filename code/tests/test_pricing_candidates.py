from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from pricing.candidates import (
    Candidate,
    build_provenance_url,
    candidate_from_public_item,
)
from pricing.estimation import get_calculation_prices


def test_build_provenance_url_matches_pncp_pattern():
    url = build_provenance_url("00000000000007", 2026, 42)
    assert url == "https://pncp.gov.br/app/editais/00000000000007/2026/42"


def test_candidate_with_awarded_price():
    candidate = Candidate(
        id=1,
        description="Papel sulfite A4",
        unit="pacote",
        quantity=Decimal("100"),
        agency="Prefeitura Municipal",
        date=date(2026, 11, 10),
        provenance="https://pncp.gov.br/app/editais/00000000000001/2026/1",
        similarity=0.92,
        awarded_unit_price=Decimal("25.50"),
        estimated_unit_price=Decimal("30.00"),
        secret_budget=False,
    )
    assert candidate.price == Decimal("25.50")
    assert candidate.is_estimated is False
    assert candidate.price_kind == "awarded"
    assert candidate.usable_calculation_price == Decimal("25.50")
    assert candidate.has_usable_calculation_price is True


def test_candidate_with_estimated_price_only():
    candidate = Candidate(
        id=2,
        description="Papel sulfite A4",
        unit="pacote",
        quantity=Decimal("50"),
        agency="Câmara Municipal",
        date=date(2026, 10, 15),
        provenance="https://pncp.gov.br/app/editais/00000000000002/2026/1",
        similarity=0.88,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("28.00"),
        secret_budget=False,
    )
    assert candidate.price == Decimal("28.00")
    assert candidate.is_estimated is True
    assert candidate.price_kind == "estimated"
    assert candidate.usable_calculation_price is None
    assert candidate.has_usable_calculation_price is False


def test_candidate_with_secret_budget():
    candidate = Candidate(
        id=3,
        description="Papel sulfite A4",
        unit="pacote",
        quantity=Decimal("200"),
        agency="Fundação Teste",
        date=date(2026, 9, 20),
        provenance="https://pncp.gov.br/app/editais/00000000000003/2026/1",
        similarity=0.85,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("0.00"),
        secret_budget=True,
    )
    assert candidate.price is None
    assert candidate.is_estimated is False
    assert candidate.price_kind == "secret_budget"
    assert candidate.usable_calculation_price is None
    assert candidate.has_usable_calculation_price is False


def test_candidate_from_public_item_builder():
    mock_item = MagicMock()
    mock_item.pk = 101
    mock_item.description = "Caneta esferográfica azul"
    mock_item.unit = "unidade"
    mock_item.quantity = Decimal("500")
    mock_item.agency_name = "Prefeitura Teste"
    mock_item.published_on = date(2026, 11, 1)
    mock_item.cnpj = "12345678000199"
    mock_item.year = 2026
    mock_item.purchase_sequence = 7
    mock_item.awarded_unit_price = Decimal("1.20")
    mock_item.estimated_unit_price = Decimal("1.50")
    mock_item.secret_budget = False

    candidate = candidate_from_public_item(mock_item, similarity=0.94, item_id=2)
    assert candidate.id == 101
    assert candidate.description == "Caneta esferográfica azul"
    assert candidate.unit == "unidade"
    assert candidate.quantity == Decimal("500")
    assert candidate.agency == "Prefeitura Teste"
    assert candidate.date == date(2026, 11, 1)
    assert candidate.source == "PNCP"
    assert candidate.provenance == "https://pncp.gov.br/app/editais/12345678000199/2026/7"
    assert candidate.similarity == 0.94
    assert candidate.price == Decimal("1.20")
    assert candidate.is_estimated is False
    assert candidate.price_kind == "awarded"
    assert candidate.item_id == 2


def test_get_calculation_prices_filters_out_estimated_and_secret_candidates():
    c_awarded = Candidate(
        id=1,
        description="Item A",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Org A",
        date=date(2026, 1, 1),
        awarded_unit_price=Decimal("10.00"),
    )
    c_estimated = Candidate(
        id=2,
        description="Item B",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Org B",
        date=date(2026, 1, 1),
        estimated_unit_price=Decimal("15.00"),
    )
    c_secret = Candidate(
        id=3,
        description="Item C",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Org C",
        date=date(2026, 1, 1),
        secret_budget=True,
    )
    assert get_calculation_prices([c_awarded, c_estimated, c_secret]) == [Decimal("10.00")]


def test_fetch_awarded_price_on_demand_success():
    from pricing.candidates import fetch_awarded_price_on_demand

    mock_item = MagicMock()
    mock_item.cnpj = "00000000000001"
    mock_item.year = 2026
    mock_item.purchase_sequence = 10
    mock_item.item_number = 3
    mock_item.awarded_unit_price = None

    raw_items_record = MagicMock()
    raw_items_record.endpoint = "/api/pncp/v1/orgaos/00000000000001/compras/2026/10/itens"
    raw_items_record.payload = [{"numeroItem": 3, "temResultado": True}]
    mock_item.raw_records.all.return_value = [raw_items_record]

    result_raw_record = MagicMock()
    result_raw_record.payload = [{"valorUnitarioHomologado": 45.50}]

    mock_fetch = MagicMock(return_value=result_raw_record)

    fetch_awarded_price_on_demand(mock_item, fetch_fn=mock_fetch)

    assert mock_fetch.called
    assert mock_item.awarded_unit_price == Decimal("45.50")
    mock_item.save.assert_called_once()
    mock_item.raw_records.add.assert_called_once_with(result_raw_record)


def test_fetch_awarded_price_on_demand_failure_leaves_candidate_estimated():
    from pricing.candidates import fetch_awarded_price_on_demand

    mock_item = MagicMock()
    mock_item.cnpj = "00000000000001"
    mock_item.year = 2026
    mock_item.purchase_sequence = 10
    mock_item.item_number = 3
    mock_item.awarded_unit_price = None
    mock_item.estimated_unit_price = Decimal("50.00")
    mock_item.secret_budget = False

    raw_items_record = MagicMock()
    raw_items_record.endpoint = "/api/pncp/v1/orgaos/00000000000001/compras/2026/10/itens"
    raw_items_record.payload = [{"numeroItem": 3, "temResultado": True}]
    mock_item.raw_records.all.return_value = [raw_items_record]

    mock_fetch = MagicMock(side_effect=TimeoutError("PNCP timed out"))

    # Should not raise exception
    fetch_awarded_price_on_demand(mock_item, fetch_fn=mock_fetch)

    assert mock_item.awarded_unit_price is None
    candidate = candidate_from_public_item(mock_item)
    assert candidate.is_estimated is True
    assert candidate.price == Decimal("50.00")


def test_fetch_awarded_price_on_demand_skips_when_no_result():
    from pricing.candidates import fetch_awarded_price_on_demand

    mock_item = MagicMock()
    mock_item.item_number = 1
    mock_item.awarded_unit_price = None

    raw_items_record = MagicMock()
    raw_items_record.endpoint = "/api/pncp/v1/orgaos/00000000000001/compras/2026/10/itens"
    raw_items_record.payload = [{"numeroItem": 1, "temResultado": False}]
    mock_item.raw_records.all.return_value = [raw_items_record]

    mock_fetch = MagicMock()
    fetch_awarded_price_on_demand(mock_item, fetch_fn=mock_fetch)
    assert not mock_fetch.called


def test_fetch_awarded_price_on_demand_skips_when_already_has_awarded_price():
    from pricing.candidates import fetch_awarded_price_on_demand

    mock_item = MagicMock()
    mock_item.awarded_unit_price = Decimal("20.00")

    mock_fetch = MagicMock()
    fetch_awarded_price_on_demand(mock_item, fetch_fn=mock_fetch)
    assert not mock_fetch.called

def test_candidate_price_respects_secret_budget_even_when_prices_present():
    """Mutant killer 1: Candidate.price must return None when secret_budget=True even if awarded/estimated prices exist."""
    cand = Candidate(
        id=99,
        description="Item sigiloso com preço",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Órgão",
        date=date.today(),
        awarded_unit_price=Decimal("50.00"),
        estimated_unit_price=Decimal("60.00"),
        secret_budget=True,
    )
    assert cand.price is None
    assert cand.price_kind == "secret_budget"
    assert cand.usable_calculation_price is None


def test_candidate_without_price_and_not_secret_budget_is_no_price():
    """N5: Any item without price that is not secret budget gets 'no_price' kind."""
    cand = Candidate(
        id=100,
        description="Item sem preço nenhum",
        unit="unidade",
        quantity=Decimal("1"),
        agency="Órgão",
        date=date.today(),
        awarded_unit_price=None,
        estimated_unit_price=None,
        secret_budget=False,
    )
    assert cand.price is None
    assert cand.price_kind == "no_price"
    assert cand.usable_calculation_price is None


def test_fetch_awarded_price_on_demand_uses_short_timeout(monkeypatch):
    """Mutant killer 4: fetch_awarded_price_on_demand passes timeout=2.0 (not 20.0)."""
    from ingestion.models import PublicItem
    from pricing.candidates import fetch_awarded_price_on_demand

    recorded_timeout = None

    def fake_fetch_item_results(**kwargs):
        nonlocal recorded_timeout
        transport = kwargs.get("transport")
        if transport and hasattr(transport, "keywords"):
            recorded_timeout = transport.keywords.get("timeout")
        return None

    import ingestion.client
    monkeypatch.setattr(ingestion.client, "fetch_item_results", fake_fetch_item_results)

    mock_pi = PublicItem(
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Test",
        unit="unidade",
        quantity=Decimal("1"),
        agency_name="Test",
        published_on=datetime.date.today(),
        awarded_unit_price=None,
        estimated_unit_price=Decimal("10.00"),
    )
    # Give mock_pi a raw_record with temResultado=True
    class MockRecord:
        endpoint = "/compras/2026/1/itens"
        payload = [{"numeroItem": 1, "temResultado": True}]

    class MockRawRecords:
        def all(self):
            return [MockRecord()]

    mock_pi.raw_records = MockRawRecords()

    fetch_awarded_price_on_demand(mock_pi)
    assert recorded_timeout == 2.0

def test_fetch_awarded_price_on_demand_selects_valid_result_skipping_cancelled():
    """B2: A cancelled result at 99 ahead of an informed one at 10 must store 10."""
    from pricing.candidates import fetch_awarded_price_on_demand

    mock_item = MagicMock()
    mock_item.cnpj = "00000000000001"
    mock_item.year = 2026
    mock_item.purchase_sequence = 1
    mock_item.item_number = 1
    mock_item.awarded_unit_price = None

    raw_rec = MagicMock()
    raw_rec.endpoint = "/compras/2026/1/itens"
    raw_rec.payload = [{"numeroItem": 1, "temResultado": True}]
    mock_item.raw_records.all.return_value = [raw_rec]

    cancelled_then_informed = [
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": "2026-05-01T10:00:00",
            "valorUnitarioHomologado": 99.00,
        },
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 10.00,
        },
    ]

    class FakeRecord:
        payload = cancelled_then_informed

    def fake_fetch(**kwargs):
        return FakeRecord()

    fetch_awarded_price_on_demand(mock_item, fetch_fn=fake_fetch)
    assert mock_item.awarded_unit_price == Decimal("10")
