import io
from datetime import UTC, datetime

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ingestion.models import RawRecord

PUBLICATIONS = "/api/consulta/v1/contratacoes/publicacao"
T1 = datetime(2026, 11, 3, 10, 0, tzinfo=UTC)
T2 = datetime(2026, 11, 3, 11, 0, tzinfo=UTC)
T3 = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


def window(**changes):
    params = {
        "dataInicial": "20261101",
        "dataFinal": "20261102",
        "uf": "PA",
        "codigoModalidadeContratacao": 6,
        "pagina": 1,
        "tamanhoPagina": 50,
    }
    return {**params, **changes}


def publication(seq, day="2026-11-01"):
    return {
        "orgaoEntidade": {"cnpj": "00000000000000"},
        "anoCompra": 2026,
        "sequencialCompra": seq,
        "dataPublicacaoPncp": f"{day}T10:00:00",
    }


def publication_page(publications, fetched_at=T2, **changes):
    RawRecord.objects.create(
        endpoint=PUBLICATIONS,
        params=window(**changes),
        fetched_at=fetched_at,
        status_code=200,
        payload={
            "data": publications,
            "totalRegistros": len(publications),
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        },
    )


def item_page(seq, items, page=1, fetched_at=T2):
    RawRecord.objects.create(
        endpoint=f"/api/pncp/v1/orgaos/00000000000000/compras/2026/{seq}/itens",
        params={"pagina": page, "tamanhoPagina": 500},
        fetched_at=fetched_at,
        status_code=200,
        payload=items,
    )


def item(number, description="item", unit="UN", quantity=1, value=1.0):
    return {
        "numeroItem": number,
        "descricao": description,
        "unidadeMedida": unit,
        "quantidade": quantity,
        "valorUnitarioEstimado": value,
    }


def measure(**options):
    out = io.StringIO()
    call_command(
        "measure_sample",
        start="2026-11-01",
        end="2026-11-02",
        uf="PA",
        modality=6,
        stdout=out,
        **options,
    )
    return out.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_measure_sample_deterministic_output_and_deduplication():
    # Synthetic publications
    # 2 publications: one on 2026-11-01, one on 2026-11-02
    pub_payload_1 = {
        "data": [
            {
                "orgaoEntidade": {"cnpj": "00000000000000"},
                "anoCompra": 2026,
                "sequencialCompra": 1,
                "dataPublicacaoPncp": "2026-11-01T10:00:00",
            },
            {
                "orgaoEntidade": {"cnpj": "00000000000000"},
                "anoCompra": 2026,
                "sequencialCompra": 2,
                "dataPublicacaoPncp": "2026-11-02T10:00:00",
            },
        ],
        "totalRegistros": 2,
        "totalPaginas": 1,
        "numeroPagina": 1,
        "paginasRestantes": 0,
    }

    t1 = datetime(2026, 11, 3, 10, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 11, 3, 11, 0, 0, tzinfo=UTC)

    # First fetch of publication page (older)
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={
            "dataInicial": "20261101",
            "dataFinal": "20261102",
            "uf": "PA",
            "codigoModalidadeContratacao": 6,
            "pagina": 1,
            "tamanhoPagina": 50,
        },
        payload=pub_payload_1,
        fetched_at=t1,
        status_code=200,
    )

    # Duplicate fetch of publication page (newer, same params)
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={
            "dataInicial": "20261101",
            "dataFinal": "20261102",
            "uf": "PA",
            "codigoModalidadeContratacao": 6,
            "pagina": 1,
            "tamanhoPagina": 50,
        },
        payload=pub_payload_1,
        fetched_at=t2,
        status_code=200,
    )

    # Publication outside window (should not be measured)
    RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params={
            "dataInicial": "20261201",
            "dataFinal": "20261202",
            "uf": "PA",
            "codigoModalidadeContratacao": 6,
            "pagina": 1,
            "tamanhoPagina": 50,
        },
        payload={
            "data": [
                {
                    "orgaoEntidade": {"cnpj": "99999999999999"},
                    "anoCompra": 2026,
                    "sequencialCompra": 99,
                    "dataPublicacaoPncp": "2026-12-01T10:00:00",
                }
            ],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        },
        fetched_at=t2,
        status_code=200,
    )

    # Synthetic items for purchase 1
    items_pub_1 = [
        {
            "numeroItem": 1,
            "descricao": "Caneta esferográfica azul",
            "unidadeMedida": "UN",
            "quantidade": 100,
            "valorUnitarioEstimado": 1.50,
        },
        {
            "numeroItem": 2,
            "descricao": "Bloco de papel",
            "unidadeMedida": "PCT",
            "quantidade": 50,
            "valorUnitarioEstimado": 10.00,
        },
    ]

    # Older duplicate of items page
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1, "tamanhoPagina": 500},
        payload=items_pub_1,
        fetched_at=t1,
        status_code=200,
    )
    # Newer duplicate of items page
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1, "tamanhoPagina": 500},
        payload=items_pub_1,
        fetched_at=t2,
        status_code=200,
    )

    # Items for purchase 2
    items_pub_2 = [
        {
            "numeroItem": 1,
            "descricao": "Caderno espiral",
            "unidadeMedida": "un",  # Should normalize with UN
            "quantidade": 20,
            "valorUnitarioEstimado": None,  # Missing
        }
    ]
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/2/itens",
        params={"pagina": 1, "tamanhoPagina": 500},
        payload=items_pub_2,
        fetched_at=t2,
        status_code=200,
    )

    # Items for unselected purchase 99 (outside window, should not be measured)
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/99999999999999/compras/2026/99/itens",
        params={"pagina": 1, "tamanhoPagina": 500},
        payload=[
            {
                "numeroItem": 1,
                "descricao": "Item ignorado",
                "unidadeMedida": "CX",
                "quantidade": 1,
                "valorUnitarioEstimado": 5.0,
            }
        ],
        fetched_at=t2,
        status_code=200,
    )

    # Run 1
    out1 = io.StringIO()
    call_command(
        "measure_sample",
        start="2026-11-01",
        end="2026-11-02",
        uf="PA",
        modality=6,
        stdout=out1,
    )
    report1 = out1.getvalue()

    # Run 2 on the exact same records
    out2 = io.StringIO()
    call_command(
        "measure_sample",
        start="2026-11-01",
        end="2026-11-02",
        uf="PA",
        modality=6,
        stdout=out2,
    )
    report2 = out2.getvalue()

    # Determinism test ("Done when: running it twice on the same sample gives the same numbers")
    assert report1 == report2

    # Verification of report contents
    assert "Window: 2026-11-01 to 2026-11-02" in report1
    assert "UF: PA" in report1
    assert "Modality: 6" in report1
    assert "Fetch time:" in report1

    # Counts
    assert "Publications: 2" in report1
    assert "Item pages: 2" in report1
    assert "Items: 3" in report1

    # Volume per day
    assert "2026-11-01: 1" in report1
    assert "2026-11-02: 1" in report1

    # Missing share
    # valorUnitarioEstimado is missing in 1 of 3 items = 0.3333
    assert "valorUnitarioEstimado: 0.3333" in report1
    assert "descricao: 0.0000" in report1

    # Distinct units: "UN" and "PCT" (un casefolded with UN) = 2 distinct units
    assert "Distinct units: 2" in report1


def test_measure_sample_requires_valid_dates():
    out = io.StringIO()
    with pytest.raises(CommandError) as exc_info:
        call_command("measure_sample", start="bad-date", end="2026-11-02", stdout=out)
    assert "YYYY-MM-DD" in str(exc_info.value)

    with pytest.raises(CommandError) as exc_info:
        call_command("measure_sample", start="2026-11-05", end="2026-11-01", stdout=out)
    assert "cannot be after" in str(exc_info.value).lower()


@pytest.mark.integration
@pytest.mark.django_db
def test_the_latest_copy_of_a_page_is_the_one_measured():
    publication_page([publication(1)])
    item_page(1, [item(1)], fetched_at=T1)  # older copy, inserted first: one item
    item_page(1, [item(1), item(2)], fetched_at=T2)  # newer copy: two items
    assert "Items: 2" in measure()


@pytest.mark.integration
@pytest.mark.django_db
def test_every_page_of_a_purchase_is_measured():
    publication_page([publication(1)])
    item_page(1, [item(1), item(2)], page=1)
    item_page(1, [item(3)], page=2)
    report = measure()
    assert "Item pages: 2" in report
    assert "Items: 3" in report


@pytest.mark.integration
@pytest.mark.django_db
def test_the_report_carries_every_value_in_a_fixed_order():
    publication_page(
        [publication(2, day="2026-11-02"), publication(1, day="2026-11-01")],
        fetched_at=T2,
    )
    item_page(
        1,
        [item(1, description="a" * 2, quantity=None), item(2, description="a" * 3)],
        fetched_at=T1,
    )
    item_page(2, [item(1, description="a" * 100, unit=None)], fetched_at=T3)
    report = measure()
    assert "Median description length: 3.0" in report  # the mean would be 35.0
    assert "quantidade: 0.3333" in report
    assert "unidadeMedida: 0.3333" in report
    assert "Distinct units: 1" in report
    assert "Fetch time: 2026-11-03T10:00:00+00:00 to 2026-11-03T12:00:00+00:00" in report
    assert report.index("2026-11-01: 1") < report.index("2026-11-02: 1")


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.parametrize(
    "difference",
    [
        {"dataInicial": "20261031"},
        {"dataFinal": "20261103"},
        {"uf": "MA"},
        {"codigoModalidadeContratacao": 8},
    ],
)
def test_only_the_window_the_uf_and_the_modality_asked_for_are_measured(difference):
    publication_page([publication(1)])
    item_page(1, [item(1)])
    publication_page([publication(2)], **difference)
    item_page(2, [item(1), item(2), item(3)])
    report = measure()
    assert "Publications: 1" in report
    assert "Items: 1" in report
