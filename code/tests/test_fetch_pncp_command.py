import io
import json
import urllib.error
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ingestion.client import PncpResponseError
from ingestion.management.commands.fetch_pncp import (
    RetryingTransport,
    create_retrying_transport,
)
from ingestion.models import RawRecord

PNCP_RESPONSES_DIR = Path(__file__).resolve().parent / "api_responses" / "pncp"
ENVELOPE = {"totalPaginas": 1, "numeroPagina": 1, "paginasRestantes": 0}


def publication(i: int) -> dict:
    return {
        "numeroControlePNCP": f"DEMO-{i}",
        "anoCompra": 2026,
        "sequencialCompra": i,
        "orgaoEntidade": {"cnpj": "00000000000000"},
    }


def _read_json(filename: str):
    return json.loads((PNCP_RESPONSES_DIR / filename).read_text(encoding="utf-8"))


def test_retrying_transport_succeeds_on_first_try():
    calls = []

    def mock_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        return 200, {"data": []}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=mock_transport,
        max_attempts=3,
        backoff_factor=1.0,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", {"p": 1})
    assert status == 200
    assert data == {"data": []}
    assert len(calls) == 1
    assert sleep_calls == []


def test_retrying_transport_retries_on_5xx_and_succeeds():
    calls = []

    def failing_then_success_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if len(calls) < 3:
            return 503, {"message": "Unavailable"}
        return 200, {"data": "ok"}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=failing_then_success_transport,
        max_attempts=5,
        backoff_factor=0.5,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 200
    assert data == {"data": "ok"}
    assert len(calls) == 3
    # Attempt 1 failed -> sleep 0.5 * 2^0 = 0.5; Attempt 2 failed -> sleep 0.5 * 2^1 = 1.0
    assert sleep_calls == [0.5, 1.0]


def test_retrying_transport_exhausts_retries_on_5xx():
    calls = []

    def server_error_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        return 500, {"message": "Server Error"}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=server_error_transport,
        max_attempts=3,
        backoff_factor=1.0,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 500
    assert len(calls) == 3
    assert len(sleep_calls) == 2


def test_retrying_transport_does_not_retry_4xx():
    calls = []

    def not_found_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        return 404, {"message": "Not Found"}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=not_found_transport,
        max_attempts=5,
        backoff_factor=1.0,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 404
    assert len(calls) == 1
    assert sleep_calls == []


def test_retrying_transport_retries_on_timeout_or_connection_error():
    calls = []

    def timeout_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if len(calls) == 1:
            raise TimeoutError("timed out")
        return 200, {"result": "recovered"}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=timeout_transport,
        max_attempts=3,
        backoff_factor=0.1,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 200
    assert data == {"result": "recovered"}
    assert len(calls) == 2
    assert sleep_calls == [0.1]


def test_retrying_transport_does_not_retry_pncp_response_error_with_4xx():
    calls = []

    def client_error_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        raise PncpResponseError("Bad Request", status=400)

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=client_error_transport,
        max_attempts=5,
        backoff_factor=1.0,
        sleep_func=sleep_calls.append,
    )

    with pytest.raises(PncpResponseError) as exc_info:
        transport("https://example.test", None)

    assert exc_info.value.status == 400
    assert len(calls) == 1
    assert sleep_calls == []


def test_retrying_transport_retries_pncp_response_error_with_5xx():
    calls = []

    def gateway_error_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if len(calls) < 2:
            raise PncpResponseError("Bad Gateway", status=502)
        return 200, {"recovered": True}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=gateway_error_transport,
        max_attempts=3,
        backoff_factor=0.2,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 200
    assert data == {"recovered": True}
    assert len(calls) == 2
    assert sleep_calls == [0.2]


def test_retrying_transport_retries_urllib_url_error():
    calls = []

    def network_error_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if len(calls) < 2:
            raise urllib.error.URLError("Connection refused")
        return 200, {"online": True}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=network_error_transport,
        max_attempts=3,
        backoff_factor=0.2,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 200
    assert data == {"online": True}
    assert len(calls) == 2
    assert sleep_calls == [0.2]


def test_the_backoff_doubles_with_every_attempt():
    sleeps = []
    transport = RetryingTransport(
        base_transport=lambda url, params: (503, {}),
        max_attempts=5,
        backoff_factor=1.0,
        sleep_func=sleeps.append,
    )
    transport("https://example.test", None)
    assert sleeps == [1.0, 2.0, 4.0, 8.0]


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("timed out"),
        urllib.error.URLError("refused"),
        PncpResponseError("bad gateway", status=502),
    ],
)
def test_a_failure_that_does_not_go_away_is_raised_after_max_attempts(error):
    calls, sleeps = [], []

    def always_failing(url, params):
        calls.append(1)
        if len(calls) > 20:
            pytest.fail("still retrying after 20 attempts")
        raise error

    transport = RetryingTransport(
        base_transport=always_failing,
        max_attempts=3,
        backoff_factor=1.0,
        sleep_func=sleeps.append,
    )
    with pytest.raises(type(error)):
        transport("https://example.test", None)
    assert len(calls) == 3
    assert sleeps == [1.0, 2.0]


def test_fetch_pncp_command_requires_valid_dates():
    out = io.StringIO()
    with pytest.raises(CommandError) as exc_info:
        call_command("fetch_pncp", start="invalid-date", end="2026-11-05", stdout=out)
    assert "YYYY-MM-DD" in str(exc_info.value)


def test_fetch_pncp_command_handles_empty_window_204():
    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        transport=lambda u, p: (204, None),
        stdout=out,
    )
    output = out.getvalue()
    assert "Publications: 0" in output
    assert "Item pages: 0" in output
    assert "Items: 0" in output
    assert "Failures: 0" in output


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_command_runs_pipeline_and_prints_summary():
    page_1 = _read_json("publications_page_1.json")  # 2 publications
    page_2 = _read_json("publications_page_2.json")  # 2 publications
    items_p1 = _read_json("items_page_1.json")  # 3 items
    items_p2 = _read_json("items_page_2.json")  # 3 items
    quantity = _read_json("items_quantity.json")  # 6

    def mock_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            p = params.get("pagina", 1) if params else 1
            if p == 1:
                return 200, page_1
            return 200, page_2
        if url.endswith("/quantidade"):
            return 200, quantity
        if "/itens" in url:
            p = params.get("pagina", 1) if params else 1
            if p == 1:
                return 200, items_p1
            return 200, items_p2
        return 404, {}

    retrying_transport = create_retrying_transport(
        base_transport=mock_transport,
        max_attempts=2,
        backoff_factor=0.0,
        sleep_func=lambda s: None,
    )

    out = io.StringIO()
    initial_records = RawRecord.objects.count()

    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-02",
        uf="PA",
        modality=6,
        transport=retrying_transport,
        stdout=out,
    )

    output = out.getvalue()
    # 2 publication pages (total 4 publications)
    # Each publication fetches 1 quantity + 2 item pages = 2 RawRecords for items per publication
    # 4 publications * 2 item pages = 8 item page records
    # Total new records = 2 (pub pages) + 8 (item pages) = 10 RawRecords
    assert "Publications: 4" in output
    assert "Item pages: 8" in output
    assert "Items: 24" in output  # 4 * 6 items
    assert "Failures: 0" in output
    assert "Elapsed:" in output

    assert RawRecord.objects.count() == initial_records + 10


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_skips_publication_on_item_failure_and_counts_it():
    page_1 = _read_json("publications_page_1.json")
    single_pub_envelope = dict(page_1)
    single_pub_envelope["data"] = [page_1["data"][0]]
    single_pub_envelope["totalRegistros"] = 1
    single_pub_envelope["totalPaginas"] = 1
    single_pub_envelope["numeroPagina"] = 1
    single_pub_envelope["paginasRestantes"] = 0

    def mock_failing_items_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub_envelope
        if url.endswith("/quantidade"):
            # Continuous 500 error for items quantity
            return 500, {"message": "Items unavailable"}
        return 404, {}

    retrying_transport = create_retrying_transport(
        base_transport=mock_failing_items_transport,
        max_attempts=2,
        backoff_factor=0.0,
        sleep_func=lambda s: None,
    )

    out = io.StringIO()
    err = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        transport=retrying_transport,
        stdout=out,
        stderr=err,
    )

    output = out.getvalue()
    assert "Publications: 1" in output
    assert "Item pages: 0" in output
    assert "Items: 0" in output
    assert "Failures: 1" in output
    assert "Skipping publication" in err.getvalue() or "Skipping publication" in output


@pytest.mark.integration
@pytest.mark.django_db
def test_the_command_sends_the_window_the_uf_and_the_modality():
    seen = []

    def transport(url, params=None):
        seen.append((url, dict(params)))
        return 200, {"data": [], "totalRegistros": 0, **ENVELOPE}

    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-03",
        uf="MA",
        modality=8,
        base_url="https://example.test",
        transport=transport,
        stdout=io.StringIO(),
    )
    url, params = seen[0]
    assert url == "https://example.test/api/consulta/v1/contratacoes/publicacao"
    assert params["dataInicial"] == "20261101"
    assert params["dataFinal"] == "20261103"
    assert params["uf"] == "MA"
    assert params["codigoModalidadeContratacao"] == 8


@pytest.mark.integration
@pytest.mark.django_db
def test_the_command_defaults_are_pa_and_pregao_eletronico():
    seen = []

    def transport(url, params=None):
        seen.append(dict(params))
        return 200, {"data": [], "totalRegistros": 0, **ENVELOPE}

    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        transport=transport,
        stdout=io.StringIO(),
    )
    assert seen[0]["uf"] == "PA"
    assert seen[0]["codigoModalidadeContratacao"] == 6


@pytest.mark.integration
@pytest.mark.django_db
def test_one_failing_publication_does_not_stop_the_others():
    def transport(url, params=None):
        if "/contratacoes/publicacao" in url:
            return 200, {
                "data": [publication(1), publication(2), publication(3)],
                "totalRegistros": 3,
                **ENVELOPE,
            }
        if "/compras/2026/2/" in url:
            return 500, {"message": "unavailable"}
        if url.endswith("/quantidade"):
            return 200, 2
        return 200, [{"numeroItem": 1}, {"numeroItem": 2}]

    out, err = io.StringIO(), io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        transport=transport,
        stdout=out,
        stderr=err,
    )
    assert "Publications: 3" in out.getvalue()
    assert "Item pages: 2" in out.getvalue()
    assert "Items: 4" in out.getvalue()
    assert "Failures: 1" in out.getvalue()
    assert RawRecord.objects.filter(endpoint__endswith="/itens").count() == 2


@pytest.mark.integration
@pytest.mark.django_db
def test_a_failure_to_fetch_the_publications_is_fatal_and_saves_nothing():
    with pytest.raises(CommandError):
        call_command(
            "fetch_pncp",
            start="2026-11-01",
            end="2026-11-01",
            transport=lambda url, params=None: (500, {"message": "down"}),
            stdout=io.StringIO(),
        )
    assert RawRecord.objects.count() == 0
