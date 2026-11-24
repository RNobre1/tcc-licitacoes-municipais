from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from ingestion.builder import build_public_items
from ingestion.models import PublicItem, RawRecord
from pricing.estimation import calculate_mean, calculate_median, calculate_min


@pytest.mark.integration
@pytest.mark.django_db
def test_public_item_secret_budget_and_usable_price():
    secret_item = PublicItem.objects.create(
        cnpj="00000000000000",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Fictitious secret item",
        unit="UNIDADE",
        quantity=Decimal("10.0000"),
        estimated_unit_price=Decimal("0.0000"),
        awarded_unit_price=None,
        secret_budget=True,
        published_on=date(2026, 10, 26),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="00000000000000",
        state="PA",
        modality=6,
        item_kind="product",
    )

    assert secret_item.has_usable_estimated_price is False
    assert secret_item.usable_estimated_unit_price is None

    # An item with secret_budget must never reach calculation functions as a price
    usable_prices = [
        item.usable_estimated_unit_price
        for item in [secret_item]
        if item.usable_estimated_unit_price is not None
    ]
    assert usable_prices == []

    with pytest.raises(ValueError, match="At least one price is required"):
        calculate_mean(usable_prices)

    normal_item = PublicItem.objects.create(
        cnpj="00000000000000",
        year=2026,
        purchase_sequence=1,
        item_number=2,
        description="Fictitious normal item",
        unit="UNIDADE",
        quantity=Decimal("10.0000"),
        estimated_unit_price=Decimal("28.5000"),
        awarded_unit_price=Decimal("25.0000"),
        secret_budget=False,
        published_on=date(2026, 10, 26),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="00000000000000",
        state="PA",
        modality=6,
        item_kind="product",
    )

    assert normal_item.has_usable_estimated_price is True
    assert normal_item.usable_estimated_unit_price == Decimal("28.5000")

    active_prices = [
        item.usable_estimated_unit_price
        for item in [secret_item, normal_item]
        if item.usable_estimated_unit_price is not None
    ]
    assert active_prices == [Decimal("28.5000")]
    assert calculate_mean(active_prices) == Decimal("28.5000")
    assert calculate_median(active_prices) == Decimal("28.5000")
    assert calculate_min(active_prices) == Decimal("28.5000")


@pytest.mark.integration
@pytest.mark.django_db
def test_build_public_items_builds_items_with_provenance_and_results():
    t1 = timezone.now()

    pub_record = RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={"pagina": 1, "dataInicial": "20261026", "dataFinal": "20261030", "uf": "PA"},
        fetched_at=t1,
        payload={
            "data": [
                {
                    "orgaoEntidade": {
                        "cnpj": "00000000000000",
                        "razaoSocial": "Prefeitura Municipal Fictícia",
                    },
                    "anoCompra": 2026,
                    "sequencialCompra": 1,
                    "numeroControlePNCP": "00000000000000-1-000001/2026",
                    "dataPublicacaoPncp": "2026-10-26T08:00:00",
                    "modalidadeId": 6,
                    "unidadeOrgao": {"ufSigla": "PA"},
                }
            ]
        },
        status_code=200,
    )

    item_endpoint = "/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens"
    item_record = RawRecord.objects.create(
        endpoint=item_endpoint,
        params={"pagina": 1},
        fetched_at=t1,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Produto de escritório",
                "quantidade": 100.0,
                "unidadeMedida": "UNIDADE",
                "valorUnitarioEstimado": 28.5,
                "temResultado": True,
                "orcamentoSigiloso": False,
                "materialOuServico": "M",
            },
            {
                "numeroItem": 2,
                "descricao": "DEMO-Serviço de manutenção",
                "quantidade": 12.0,
                "unidadeMedida": "MÊS",
                "valorUnitarioEstimado": 1500.0,
                "temResultado": False,
                "orcamentoSigiloso": False,
                "materialOuServico": "S",
            },
        ],
        status_code=200,
    )

    result_endpoint = "/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens/1/resultados"
    res_record = RawRecord.objects.create(
        endpoint=result_endpoint,
        params={},
        fetched_at=t1,
        payload=[
            {
                "numeroItem": 1,
                "valorUnitarioHomologado": 27.8,
                "quantidadeHomologada": 100.0,
                "dataResultado": "2026-10-28",
                "nomeRazaoSocialFornecedor": "DEMO-Fornecedor Vencedor",
            }
        ],
        status_code=200,
    )

    count = build_public_items()
    assert count == 2
    assert PublicItem.objects.count() == 2

    item_1 = PublicItem.objects.get(
        cnpj="00000000000000", year=2026, purchase_sequence=1, item_number=1
    )
    assert item_1.pncp_key == ("00000000000000", 2026, 1, 1)
    assert item_1.description == "DEMO-Produto de escritório"
    assert item_1.unit == "UNIDADE"
    assert item_1.quantity == Decimal("100.0000")
    assert item_1.estimated_unit_price == Decimal("28.5000")
    assert item_1.awarded_unit_price == Decimal("27.8000")
    assert item_1.item_kind == "product"
    assert item_1.state == "PA"
    assert item_1.modality == 6
    assert item_1.published_on == date(2026, 10, 26)
    assert item_1.agency_name == "Prefeitura Municipal Fictícia"
    assert set(item_1.raw_records.all()) == {pub_record, item_record, res_record}

    item_2 = PublicItem.objects.get(
        cnpj="00000000000000", year=2026, purchase_sequence=1, item_number=2
    )
    assert item_2.pncp_key == ("00000000000000", 2026, 1, 2)
    assert item_2.awarded_unit_price is None
    assert item_2.item_kind == "service"
    assert set(item_2.raw_records.all()) == {pub_record, item_record}


@pytest.mark.integration
@pytest.mark.django_db
def test_build_public_items_is_idempotent():
    t1 = timezone.now()
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={"pagina": 1},
        fetched_at=t1,
        payload={
            "data": [
                {
                    "orgaoEntidade": {"cnpj": "00000000000000", "razaoSocial": "Prefeitura"},
                    "anoCompra": 2026,
                    "sequencialCompra": 1,
                    "dataPublicacaoPncp": "2026-10-26T08:00:00",
                    "modalidadeId": 6,
                    "unidadeOrgao": {"ufSigla": "PA"},
                }
            ]
        },
        status_code=200,
    )
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1},
        fetched_at=t1,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Item",
                "quantidade": 10.0,
                "unidadeMedida": "UNIDADE",
                "valorUnitarioEstimado": 50.0,
                "temResultado": False,
                "orcamentoSigiloso": False,
                "materialOuServico": "M",
            }
        ],
        status_code=200,
    )

    first_run = build_public_items()
    assert first_run == 1
    assert PublicItem.objects.count() == 1

    second_run = build_public_items()
    assert second_run == 1
    assert PublicItem.objects.count() == 1


@pytest.mark.integration
@pytest.mark.django_db
def test_build_public_items_newest_copy_wins_and_does_not_duplicate():
    t1 = timezone.now()
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={"pagina": 1},
        fetched_at=t1,
        payload={
            "data": [
                {
                    "orgaoEntidade": {"cnpj": "00000000000000", "razaoSocial": "Prefeitura"},
                    "anoCompra": 2026,
                    "sequencialCompra": 1,
                    "dataPublicacaoPncp": "2026-10-26T08:00:00",
                    "modalidadeId": 6,
                    "unidadeOrgao": {"ufSigla": "PA"},
                }
            ]
        },
        status_code=200,
    )

    item_endpoint = "/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens"
    rec1 = RawRecord.objects.create(
        endpoint=item_endpoint,
        params={"pagina": 1},
        fetched_at=t1,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "Old description",
                "quantidade": 10.0,
                "unidadeMedida": "UNIDADE",
                "valorUnitarioEstimado": 50.0,
                "temResultado": False,
                "orcamentoSigiloso": False,
                "materialOuServico": "M",
            }
        ],
        status_code=200,
    )
    build_public_items()
    assert PublicItem.objects.get().description == "Old description"

    # Second fetch of the same page at later time with updated description
    t2 = t1 + timezone.timedelta(hours=2)
    rec2 = RawRecord.objects.create(
        endpoint=item_endpoint,
        params={"pagina": 1},
        fetched_at=t2,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "New description updated",
                "quantidade": 10.0,
                "unidadeMedida": "UNIDADE",
                "valorUnitarioEstimado": 55.0,
                "temResultado": False,
                "orcamentoSigiloso": False,
                "materialOuServico": "M",
            }
        ],
        status_code=200,
    )

    build_public_items()
    assert PublicItem.objects.count() == 1
    updated_item = PublicItem.objects.get()
    assert updated_item.description == "New description updated"
    assert updated_item.estimated_unit_price == Decimal("55.0000")
    # Provenance links to the newest copy
    assert rec2 in updated_item.raw_records.all()
    assert rec1 not in updated_item.raw_records.all()


@pytest.mark.integration
@pytest.mark.django_db
def test_build_public_items_command():
    t1 = timezone.now()
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={"pagina": 1},
        fetched_at=t1,
        payload={
            "data": [
                {
                    "orgaoEntidade": {"cnpj": "00000000000000", "razaoSocial": "Prefeitura"},
                    "anoCompra": 2026,
                    "sequencialCompra": 1,
                    "dataPublicacaoPncp": "2026-10-26T08:00:00",
                    "modalidadeId": 6,
                    "unidadeOrgao": {"ufSigla": "PA"},
                }
            ]
        },
        status_code=200,
    )
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1},
        fetched_at=t1,
        payload=[
            {
                "numeroItem": 1,
                "descricao": "DEMO-Item",
                "quantidade": 10.0,
                "unidadeMedida": "UNIDADE",
                "valorUnitarioEstimado": 50.0,
                "temResultado": False,
                "orcamentoSigiloso": False,
                "materialOuServico": "M",
            }
        ],
        status_code=200,
    )
    call_command("build_public_items")
    assert PublicItem.objects.count() == 1
