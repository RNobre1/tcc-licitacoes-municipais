import pytest
from django.utils import timezone

from ingestion.models import RawRecord


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
