import json
from pathlib import Path

import pytest
from django.utils import timezone

from ingestion.client import fetch_items, fetch_publications
from ingestion.models import RawRecord

PNCP_RESPONSES_DIR = Path(__file__).resolve().parent.parent / "api_responses" / "pncp"


def _read_json(filename: str):
    return json.loads((PNCP_RESPONSES_DIR / filename).read_text(encoding="utf-8"))


@pytest.mark.integration
@pytest.mark.django_db
def test_save_and_filter_by_key_inside_payload():
    now = timezone.now()
    record = RawRecord.objects.create(
        endpoint="/v1/contratacoes/publicacao",
        params={"dataInicial": "20260101", "dataFinal": "20260131", "pagina": 1},
        fetched_at=now,
        payload={
            "numeroControlePNCP": "00000000000000-1-000001/2026",
            "detalhes": {"modalidade": "Pregão Eletrônico", "itensCount": 5},
            "itens": [{"numeroItem": 1, "descricao": "Item 1"}],
        },
        status_code=200,
    )

    # Filter by top-level key inside payload
    filtered = RawRecord.objects.filter(
        payload__numeroControlePNCP="00000000000000-1-000001/2026"
    ).first()
    assert filtered is not None
    assert filtered.pk == record.pk
    assert filtered.endpoint == "/v1/contratacoes/publicacao"
    assert filtered.params == {"dataInicial": "20260101", "dataFinal": "20260131", "pagina": 1}
    assert filtered.fetched_at == now
    assert filtered.status_code == 200

    # Filter by nested key inside payload
    nested_match = RawRecord.objects.filter(
        payload__detalhes__modalidade="Pregão Eletrônico"
    ).first()
    assert nested_match is not None
    assert nested_match.pk == record.pk

    # Filter for non-matching key inside payload returns empty
    assert not RawRecord.objects.filter(payload__numeroControlePNCP="inexistente").exists()


@pytest.mark.integration
@pytest.mark.django_db
def test_raw_record_status_code_is_optional():
    now = timezone.now()
    record = RawRecord.objects.create(
        endpoint="/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1},
        fetched_at=now,
        payload=[{"numeroItem": 1, "descricao": "Item 1"}],
    )
    assert record.status_code is None
    assert record.pk is not None
    assert record.payload == [{"numeroItem": 1, "descricao": "Item 1"}]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_publications_stores_raw_records_in_database():
    page_1 = _read_json("publications_page_1.json")
    page_2 = _read_json("publications_page_2.json")

    def mock_transport(url: str, params: dict | None = None):
        if params and params.get("pagina") == 1:
            return 200, page_1
        return 200, page_2

    initial_count = RawRecord.objects.count()
    records = fetch_publications(
        params={"dataInicial": "20261101", "dataFinal": "20261102"},
        transport=mock_transport,
        save=True,
    )

    assert len(records) == 2
    for record in records:
        assert record.pk is not None
        assert record.endpoint == "/v1/contratacoes/publicacao"
    assert RawRecord.objects.count() == initial_count + 2

    # Query key inside stored payload in PostgreSQL
    persisted = RawRecord.objects.filter(
        payload__data__0__numeroControlePNCP="00000000000000-1-000001/2026"
    ).first()
    assert persisted is not None


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_items_stores_raw_records_in_database():
    items_p1 = _read_json("items_page_1.json")
    items_p2 = _read_json("items_page_2.json")
    quantity = _read_json("items_quantity.json")

    def mock_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        if params and params.get("pagina") == 1:
            return 200, items_p1
        return 200, items_p2

    initial_count = RawRecord.objects.count()
    records = fetch_items(
        cnpj="00000000000000",
        ano=2026,
        sequencial=1,
        transport=mock_transport,
        save=True,
    )

    assert len(records) == 2
    for record in records:
        assert record.pk is not None
        assert record.endpoint == "/v1/orgaos/00000000000000/compras/2026/1/itens"
    assert RawRecord.objects.count() == initial_count + 2
