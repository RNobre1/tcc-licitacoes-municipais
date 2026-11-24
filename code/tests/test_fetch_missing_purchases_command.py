from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from ingestion.models import RawRecord


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_missing_purchases_command_identifies_and_fetches_missing_purchases():
    t1 = timezone.now()
    # 1. Purchase with publication metadata
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={"pagina": 1},
        fetched_at=t1,
        payload={
            "data": [
                {
                    "orgaoEntidade": {"cnpj": "00000000000001"},
                    "anoCompra": 2026,
                    "sequencialCompra": 1,
                }
            ]
        },
        status_code=200,
    )
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000001/compras/2026/1/itens",
        params={"pagina": 1},
        fetched_at=t1,
        payload=[{"numeroItem": 1}],
        status_code=200,
    )

    # 2. Purchase WITHOUT publication metadata
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000002/compras/2026/99/itens",
        params={"pagina": 1},
        fetched_at=t1,
        payload=[{"numeroItem": 1}],
        status_code=200,
    )

    mock_record = RawRecord(
        endpoint="/api/consulta/v1/orgaos/00000000000002/compras/2026/99",
        params={},
        fetched_at=t1,
        payload={
            "orgaoEntidade": {"cnpj": "00000000000002", "razaoSocial": "Órgão 2"},
            "anoCompra": 2026,
            "sequencialCompra": 99,
            "dataPublicacaoPncp": "2026-10-26T10:00:00",
            "modalidadeId": 6,
            "unidadeOrgao": {"ufSigla": "PA"},
        },
        status_code=200,
    )

    with patch(
        "ingestion.management.commands.fetch_missing_purchases.fetch_purchase",
        return_value=mock_record,
    ) as mock_fetch:
        call_command("fetch_missing_purchases")

        mock_fetch.assert_called_once_with(
            cnpj="00000000000002",
            ano=2026,
            sequencial=99,
            transport=pytest.approx(mock_fetch.call_args[1]["transport"]),
            save=True,
        )
