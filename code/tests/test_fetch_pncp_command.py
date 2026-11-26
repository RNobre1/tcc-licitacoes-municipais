import http.client
import io
import json
import urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from ingestion.client import PncpResponseError
from ingestion.management.commands.fetch_pncp import (
    RateLimiter,
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


@pytest.mark.django_db
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
        end="2026-11-01",
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
    with pytest.raises(CommandError):
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
    # S7: Walks day by day (3 days: 20261101, 20261102, 20261103)
    assert len(seen) == 3
    assert seen[0][0] == "https://example.test/api/consulta/v1/contratacoes/publicacao"
    assert seen[0][1]["dataInicial"] == "20261101"
    assert seen[0][1]["dataFinal"] == "20261101"
    assert seen[0][1]["uf"] == "MA"
    assert seen[0][1]["codigoModalidadeContratacao"] == 8

    assert seen[1][1]["dataInicial"] == "20261102"
    assert seen[1][1]["dataFinal"] == "20261102"

    assert seen[2][1]["dataInicial"] == "20261103"
    assert seen[2][1]["dataFinal"] == "20261103"


@pytest.mark.integration
@pytest.mark.django_db
def test_the_command_defaults_are_national_and_three_modalities():
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
    # S7: National default: no uf filter
    assert all("uf" not in s for s in seen)
    # S7: Three modalities by default: 6 (pregão eletrônico), 8 (dispensa), 7 (pregão presencial)
    assert len(seen) == 3
    assert [s["codigoModalidadeContratacao"] for s in seen] == [6, 8, 7]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_is_resumable_and_skips_already_stored_purchases():
    t0 = timezone.now()
    RawRecord.objects.create(
        endpoint="/api/pncp/v1/orgaos/00000000000000/compras/2026/1/itens",
        params={"pagina": 1},
        fetched_at=t0,
        payload=[{"numeroItem": 1}],
        status_code=200,
    )

    item_calls = []

    def transport(url, params=None):
        if "/contratacoes/publicacao" in url:
            return 200, {
                "data": [publication(1), publication(2)],
                "totalRegistros": 2,
                **ENVELOPE,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        if "/itens" in url:
            item_calls.append(url)
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )
    # Publication 1 is already in DB, so its items should NOT be fetched again
    assert not any("/compras/2026/1/itens" in u for u in item_calls)
    assert any("/compras/2026/2/itens" in u for u in item_calls)
    assert "Skipped already stored: 1" in out.getvalue()


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
    with pytest.raises(CommandError):
        call_command(
            "fetch_pncp",
            start="2026-11-01",
            end="2026-11-01",
            modality=6,
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
            modality=6,
            transport=lambda url, params=None: (500, {"message": "down"}),
            stdout=io.StringIO(),
        )
    assert RawRecord.objects.count() == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_with_results_flag_fetches_item_results_for_items_with_tem_resultado():
    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]  # 1 publication
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    # items 1 and 3 have temResultado=True, item 2 has False
    items_p1 = _read_json("items_page_1.json")
    results = _read_json("item_results.json")
    quantity = len(items_p1)

    calls = []

    def mock_transport(url: str, params: dict | None = None):
        calls.append(url)
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub
        if url.endswith("/quantidade"):
            return 200, quantity
        if url.endswith("/itens"):
            return 200, items_p1
        if "/resultados" in url:
            return 200, results
        return 404, {}

    out = io.StringIO()
    initial_records = RawRecord.objects.count()

    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        with_results=True,
        transport=mock_transport,
        stdout=out,
    )

    output = out.getvalue()
    assert "Publications: 1" in output
    assert "Item pages: 1" in output
    assert "Items: 3" in output
    assert "Item results: 2" in output
    assert "Failures: 0" in output

    # Calls should include /resultados for item 1 and item 3, but not item 2
    resultado_calls = [c for c in calls if "/resultados" in c]
    assert len(resultado_calls) == 2
    assert any("/itens/1/resultados" in c for c in resultado_calls)
    assert any("/itens/3/resultados" in c for c in resultado_calls)
    assert not any("/itens/2/resultados" in c for c in resultado_calls)

    # 1 pub page + 1 item page + 2 results = 4 RawRecords
    assert RawRecord.objects.count() == initial_records + 4


def test_rate_limiter_enforces_interval():
    current_time = 100.0

    def fake_time():
        return current_time

    sleep_calls = []
    limiter = RateLimiter(
        requests_per_second=2.0,
        time_func=fake_time,
        sleep_func=sleep_calls.append,
    )

    w1 = limiter.wait()
    assert w1 == 0.0
    assert sleep_calls == []

    w2 = limiter.wait()
    assert w2 == 0.5
    assert sleep_calls == [0.5]

    w3 = limiter.wait()
    assert w3 == 1.0
    assert sleep_calls == [0.5, 1.0]

    current_time = 102.0
    w4 = limiter.wait()
    assert w4 == 0.0
    assert sleep_calls == [0.5, 1.0]


def test_retrying_transport_retries_429_with_and_without_retry_after():
    calls = []

    def fake_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if len(calls) == 1:
            return 429, {"error": "Too Many Requests", "retry_after": 15.0}
        if len(calls) == 2:
            return 429, {"error": "Too Many Requests"}
        return 200, {"data": "ok"}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=fake_transport,
        rate_limit_initial_wait=30.0,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test/api/endpoint", None)
    assert status == 200
    assert data == {"data": "ok"}
    assert len(calls) == 3
    assert sleep_calls == [15.0, 30.0]


@pytest.mark.parametrize(
    "network_error",
    [
        ConnectionResetError("Connection reset by peer"),
        http.client.RemoteDisconnected("Remote end closed connection without response"),
        http.client.IncompleteRead(b"partial"),
    ],
)
def test_retrying_transport_retries_network_read_errors(network_error):
    calls = []

    def flaking_transport(url: str, params: dict | None = None):
        calls.append(url)
        if len(calls) == 1:
            raise network_error
        return 200, {"recovered": True}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=flaking_transport,
        max_attempts=3,
        backoff_factor=0.1,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test", None)
    assert status == 200
    assert data == {"recovered": True}
    assert len(calls) == 2
    assert sleep_calls == [0.1]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_walk_recovers_from_429_on_publications_and_completes():
    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    pub_attempts = 0
    sleep_calls = []

    def mock_transport(url: str, params: dict | None = None):
        nonlocal pub_attempts
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            pub_attempts += 1
            if pub_attempts == 1:
                return 429, {"retry_after": 15.0, "error": "Too Many Requests"}
            if pub_attempts == 2:
                return 429, {"error": "Too Many Requests"}
            return 200, single_pub
        if url.endswith("/quantidade"):
            return 200, 1
        if url.endswith("/itens"):
            return 200, [{"numeroItem": 1}]
        return 404, {}

    retrying_transport = create_retrying_transport(
        base_transport=mock_transport,
        rate_limit_initial_wait=30.0,
        rate_limit=0.0,
        sleep_func=sleep_calls.append,
    )

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        transport=retrying_transport,
        stdout=out,
    )

    output = out.getvalue()
    assert "Publications: 1" in output
    assert "Item pages: 1" in output
    assert "Items: 1" in output
    assert "Failures: 0" in output
    assert sleep_calls == [15.0, 30.0]


def test_retrying_transport_does_not_retry_envelope_or_completeness_violations():
    calls = []

    def envelope_violation_transport(url: str, params: dict | None = None):
        calls.append(url)
        raise PncpResponseError("Missing paginasRestantes in payload", status=None)

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=envelope_violation_transport,
        max_attempts=5,
        sleep_func=sleep_calls.append,
    )

    with pytest.raises(PncpResponseError) as exc_info:
        transport("https://example.test", None)

    assert "Missing paginasRestantes" in str(exc_info.value)
    assert len(calls) == 1
    assert sleep_calls == []


def test_rate_limiter_enforces_interval_across_concurrent_threads():
    import concurrent.futures
    import time

    def slow_fake_time():
        time.sleep(0.002)
        return 100.0

    sleep_calls = []
    limiter = RateLimiter(
        requests_per_second=2.0,
        time_func=slow_fake_time,
        sleep_func=sleep_calls.append,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        waits = list(executor.map(lambda _: limiter.wait(), range(12)))

    # With lock held during schedule calculation, each call gets a unique 0.5s slot
    assert sorted(waits) == [0.5 * i for i in range(12)]


def test_create_retrying_transport_shares_single_rate_limiter_across_calls():
    current_time = 100.0
    sleep_calls = []

    def fake_time():
        return current_time

    limiter = RateLimiter(
        requests_per_second=2.0,
        time_func=fake_time,
        sleep_func=sleep_calls.append,
    )
    transport = create_retrying_transport(
        base_transport=lambda url, params=None: (200, {}),
        rate_limiter=limiter,
        sleep_func=sleep_calls.append,
    )

    transport("https://example.test/1", None)
    transport("https://example.test/2", None)
    transport("https://example.test/3", None)
    assert sleep_calls == [0.5, 1.0]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_shares_one_rate_limiter_across_worker_threads():
    import time
    from unittest.mock import patch

    call_times = []

    def fake_urllib(url, params=None):
        call_times.append(time.monotonic())
        if "/contratacoes/publicacao" in url:
            return 200, {
                "data": [publication(1), publication(2), publication(3), publication(4)],
                "totalRegistros": 4,
                **ENVELOPE,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        return 200, [{"numeroItem": 1}]

    out = io.StringIO()
    with patch(
        "ingestion.management.commands.fetch_pncp.urllib_transport",
        side_effect=fake_urllib,
    ):
        call_command(
            "fetch_pncp",
            start="2026-11-01",
            end="2026-11-01",
            modality=6,
            concurrency=3,
            rate_limit=100.0,
            stdout=out,
        )

    # 1 pub call + 4 * 2 item calls = 9 calls; at 100 req/s (10ms interval), span >= 80ms
    assert len(call_times) == 9
    call_times.sort()
    assert (call_times[-1] - call_times[0]) >= 0.07


def test_rate_limiter_shared_pause_blocks_subsequent_wait_calls():
    current_time = 100.0

    def fake_time():
        return current_time

    sleep_calls = []
    limiter = RateLimiter(
        requests_per_second=2.0,
        time_func=fake_time,
        sleep_func=sleep_calls.append,
    )

    assert limiter.wait() == 0.0

    limiter.pause(30.0)

    current_time = 100.1
    w = limiter.wait()
    assert abs(w - 29.9) < 0.001
    assert any(abs(s - 29.9) < 0.001 for s in sleep_calls)


def test_retrying_transport_pauses_shared_rate_limiter_on_429():
    calls = []

    def fake_transport(url: str, params: dict | None = None):
        calls.append(url)
        if len(calls) == 1:
            return 429, {"error": "Too Many Requests", "retry_after": 25.0}
        return 200, {"ok": True}

    current_time = 100.0
    sleep_calls = []
    limiter = RateLimiter(
        requests_per_second=2.0,
        time_func=lambda: current_time,
        sleep_func=sleep_calls.append,
    )

    transport = RetryingTransport(
        base_transport=fake_transport,
        rate_limiter=limiter,
        sleep_func=sleep_calls.append,
    )

    status, data = transport("https://example.test/api/endpoint", None)
    assert status == 200
    assert limiter._paused_until >= 125.0


def test_retrying_transport_429_backoff_caps_at_600s():
    sleep_calls = []
    transport = RetryingTransport(
        base_transport=lambda url, params=None: (429, {"error": "Too Many Requests"}),
        sleep_func=sleep_calls.append,
    )

    status, _ = transport("https://example.test/api/429", None)
    assert status == 429
    assert sleep_calls == [30.0, 60.0, 120.0, 240.0, 480.0, 600.0, 600.0, 600.0, 600.0]

    # Retry-After above 600s in dict is also capped, and inf falls back to backoff
    sleep_calls_2 = []
    responses = [
        (429, {"retry_after": 1200.0}),
        (429, {"retry_after": float("inf")}),
        (200, {"ok": True}),
    ]
    transport2 = RetryingTransport(
        base_transport=lambda url, params=None: responses.pop(0),
        sleep_func=sleep_calls_2.append,
    )
    status2, _ = transport2("https://example.test/api/429-cap", None)
    assert status2 == 200
    assert sleep_calls_2 == [600.0, 30.0]


def test_retrying_transport_5xx_and_network_errors_use_long_backoff():
    calls = []

    def flaky_503_transport(url: str, params: dict | None = None):
        calls.append(url)
        if len(calls) == 1:
            return 503, {"error": "Service Unavailable"}
        return 200, {"recovered": True}

    sleep_calls = []
    transport = RetryingTransport(
        base_transport=flaky_503_transport,
        sleep_func=sleep_calls.append,
    )

    status, _ = transport("https://example.test/api/503", None)
    assert status == 200
    assert len(calls) == 2
    assert sleep_calls == [30.0]

    # Exhausting 503 uses full 10-attempt long backoff capped at 600s
    sleep_503 = []
    transport_503 = RetryingTransport(
        base_transport=lambda url, params=None: (503, {"error": "Service Unavailable"}),
        sleep_func=sleep_503.append,
    )
    status_503, _ = transport_503("https://example.test/api/503-exhaust", None)
    assert status_503 == 503
    assert sleep_503 == [30.0, 60.0, 120.0, 240.0, 480.0, 600.0, 600.0, 600.0, 600.0]

    # Network errors also use the same long backoff
    sleep_net = []

    def always_reset(url, params=None):
        raise ConnectionResetError("reset")

    transport_net = RetryingTransport(
        base_transport=always_reset,
        sleep_func=sleep_net.append,
    )
    with pytest.raises(ConnectionResetError):
        transport_net("https://example.test/api/net-exhaust", None)
    assert sleep_net == [30.0, 60.0, 120.0, 240.0, 480.0, 600.0, 600.0, 600.0, 600.0]


def test_retrying_transport_logs_backoff_wait_and_increments_count():
    calls = []

    def flaky_transport(url: str, params: dict | None = None):
        calls.append(url)
        if len(calls) == 1:
            return 429, {"error": "Too Many Requests", "retry_after": 10.0}
        return 200, {"ok": True}

    logs = []
    sleep_calls = []
    transport = RetryingTransport(
        base_transport=flaky_transport,
        sleep_func=sleep_calls.append,
        log_func=logs.append,
    )

    status, _ = transport("https://example.test/api/call", None)
    assert status == 200
    assert transport.backoff_waits_count == 1
    assert len(logs) == 1
    assert "[backoff]" in logs[0]
    assert "https://example.test/api/call" in logs[0]
    assert "10.0s" in logs[0]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_prints_progress_line_per_day_and_modality():
    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    def mock_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub
        if url.endswith("/quantidade"):
            return 200, 1
        if url.endswith("/itens"):
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        transport=mock_transport,
        stdout=out,
    )
    output = out.getvalue()
    assert "[2026-11-01 modality 6] seen: 1, fetched: 1, skipped: 0, failed: 0" in output
    assert "Backoff waits: 0" in output


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_records_permanent_404_as_raw_record_and_skips_on_resumption():
    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    calls_to_items = []

    def mock_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub
        if url.endswith("/quantidade"):
            calls_to_items.append(url)
            return 404, {"message": "Contratação não cadastrada"}
        return 404, {}

    out = io.StringIO()
    err = io.StringIO()

    with pytest.raises(CommandError):
        call_command(
            "fetch_pncp",
            start="2026-11-01",
            end="2026-11-01",
            uf="PA",
            modality=6,
            transport=mock_transport,
            stdout=out,
            stderr=err,
        )

    assert len(calls_to_items) == 1
    rec_404 = RawRecord.objects.filter(endpoint__endswith="/itens", status_code=404).first()
    assert rec_404 is not None

    out2 = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        uf="PA",
        modality=6,
        transport=mock_transport,
        stdout=out2,
    )
    assert len(calls_to_items) == 1
    assert "Skipped already stored: 1" in out2.getvalue()
    assert "Failures: 0" in out2.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_writes_failed_purchases_to_file_and_raises_command_error(tmp_path):
    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    def failing_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub
        if url.endswith("/quantidade"):
            return 500, {"message": "fatal internal server error"}
        return 404, {}

    failed_file = tmp_path / "test_failed.jsonl"
    out = io.StringIO()
    err = io.StringIO()

    with pytest.raises(CommandError) as exc_info:
        call_command(
            "fetch_pncp",
            start="2026-11-01",
            end="2026-11-01",
            uf="PA",
            modality=6,
            transport=failing_transport,
            failed_purchases_file=str(failed_file),
            stdout=out,
            stderr=err,
        )

    assert "1 failure" in str(exc_info.value)
    assert "Failures: 1" in out.getvalue()
    assert failed_file.exists()
    lines = failed_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["purchase_key"] == ["00000000000000", 2026, 1]
    assert "error" in record


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_deduplicates_duplicate_publications_in_same_listing():
    item_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            return 200, {
                "data": [publication(1), publication(1)],
                "totalRegistros": 2,
                **ENVELOPE,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        if "/itens" in url:
            item_calls.append(url)
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert len(item_calls) == 1
    assert RawRecord.objects.filter(endpoint__endswith="/itens").count() == 1
    output = out.getvalue()
    assert "[2026-11-01 modality 6] seen: 2, fetched: 1, skipped: 1, failed: 0" in output


def _seed_listing_page(
    *,
    day: str = "20261101",
    modality: int = 6,
    pagina: int = 1,
    total_paginas: int = 1,
    publications: list[dict] | None = None,
    uf: str | None = None,
    fetched_at=None,
) -> RawRecord:
    pubs = publications if publications is not None else []
    params = {
        "dataInicial": day,
        "dataFinal": day,
        "codigoModalidadeContratacao": modality,
        "tamanhoPagina": 50,
        "pagina": pagina,
    }
    if uf is not None:
        params["uf"] = uf
    return RawRecord.objects.create(
        endpoint="/api/consulta/v1/contratacoes/publicacao",
        params=params,
        fetched_at=fetched_at or timezone.now(),
        payload={
            "data": pubs,
            "totalRegistros": len(pubs),
            "totalPaginas": total_paginas,
            "numeroPagina": pagina,
            "paginasRestantes": max(0, total_paginas - pagina),
        },
        status_code=200,
    )


def _seed_purchase_items(seq: int, cnpj: str = "00000000000000", status_code: int = 200) -> None:
    RawRecord.objects.create(
        endpoint=f"/api/pncp/v1/orgaos/{cnpj}/compras/2026/{seq}/itens",
        params={"pagina": 1},
        fetched_at=timezone.now(),
        payload=[{"numeroItem": 1}] if status_code == 200 else {"status": status_code},
        status_code=status_code,
    )


AFTER_20261101_END = datetime(2026, 11, 2, 0, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_complete_day_makes_zero_http_calls():
    _seed_listing_page(
        pagina=1, total_paginas=2, publications=[publication(1)], fetched_at=AFTER_20261101_END
    )
    _seed_listing_page(
        pagina=2, total_paginas=2, publications=[publication(2)], fetched_at=AFTER_20261101_END
    )
    _seed_purchase_items(1)
    _seed_purchase_items(2)

    calls = []

    def transport(url: str, params: dict | None = None):
        calls.append((url, params))
        raise AssertionError("No HTTP call should be made for a complete day")

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert calls == []
    output = out.getvalue()
    assert "[2026-11-01 modality 6] seen: 2, fetched: 0, skipped: 2, failed: 0" in output
    assert "Publications: 2" in output
    assert "Skipped already stored: 2" in output
    assert "Failures: 0" in output


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_rewalks_day_missing_a_listing_page():
    # totalPaginas=2, but only page 1 is stored in DB
    _seed_listing_page(
        pagina=1, total_paginas=2, publications=[publication(1)], fetched_at=AFTER_20261101_END
    )
    _seed_purchase_items(1)

    listing_calls = []
    item_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            page = (params or {}).get("pagina", 1)
            listing_calls.append(page)
            if page == 1:
                return 200, {
                    "data": [publication(1)],
                    "totalRegistros": 2,
                    "totalPaginas": 2,
                    "numeroPagina": 1,
                    "paginasRestantes": 1,
                }
            return 200, {
                "data": [publication(2)],
                "totalRegistros": 2,
                "totalPaginas": 2,
                "numeroPagina": 2,
                "paginasRestantes": 0,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        if "/itens" in url:
            item_calls.append(url)
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert listing_calls == [1, 2]
    assert len(item_calls) == 1
    assert "/compras/2026/2/itens" in item_calls[0]
    assert "[2026-11-01 modality 6] seen: 2, fetched: 1, skipped: 1, failed: 0" in out.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_rewalks_day_missing_a_purchase_items():
    _seed_listing_page(
        pagina=1, total_paginas=2, publications=[publication(1)], fetched_at=AFTER_20261101_END
    )
    _seed_listing_page(
        pagina=2, total_paginas=2, publications=[publication(2)], fetched_at=AFTER_20261101_END
    )
    # Purchase 1 has items, purchase 2 is missing items
    _seed_purchase_items(1)

    listing_calls = []
    item_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            page = (params or {}).get("pagina", 1)
            listing_calls.append(page)
            if page == 1:
                return 200, {
                    "data": [publication(1)],
                    "totalRegistros": 2,
                    "totalPaginas": 2,
                    "numeroPagina": 1,
                    "paginasRestantes": 1,
                }
            return 200, {
                "data": [publication(2)],
                "totalRegistros": 2,
                "totalPaginas": 2,
                "numeroPagina": 2,
                "paginasRestantes": 0,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        if "/itens" in url:
            item_calls.append(url)
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert listing_calls == [1, 2]
    assert len(item_calls) == 1
    assert "/compras/2026/2/itens" in item_calls[0]


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_refetch_listings_forces_rewalk_even_when_complete():
    _seed_listing_page(
        pagina=1, total_paginas=1, publications=[publication(1)], fetched_at=AFTER_20261101_END
    )
    _seed_purchase_items(1)

    listing_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            listing_calls.append((params or {}).get("pagina", 1))
            return 200, {
                "data": [publication(1)],
                "totalRegistros": 1,
                "totalPaginas": 1,
                "numeroPagina": 1,
                "paginasRestantes": 0,
            }
        raise AssertionError(f"Unexpected call: {url}")

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        refetch_listings=True,
        transport=transport,
        stdout=out,
    )

    assert listing_calls == [1]
    assert "Skipped already stored: 1" in out.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_rewalks_day_listed_before_day_end_brt():
    """B1: day D listed at 10:00 BRT on D is open and must be re-listed on 2nd pass."""
    open_day_fetched_at = datetime(2026, 11, 1, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    _seed_listing_page(
        day="20261101",
        pagina=1,
        total_paginas=1,
        publications=[publication(1), publication(2)],
        fetched_at=open_day_fetched_at,
    )
    _seed_purchase_items(1)
    _seed_purchase_items(2)

    listing_calls = []
    item_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            listing_calls.append((params or {}).get("pagina", 1))
            return 200, {
                "data": [publication(1), publication(2), publication(3)],
                "totalRegistros": 3,
                "totalPaginas": 1,
                "numeroPagina": 1,
                "paginasRestantes": 0,
            }
        if url.endswith("/quantidade"):
            return 200, 1
        if "/itens" in url:
            item_calls.append(url)
            return 200, [{"numeroItem": 1}]
        return 404, {}

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert listing_calls == [1]
    assert len(item_calls) == 1
    assert "/compras/2026/3/itens" in item_calls[0]
    assert "[2026-11-01 modality 6] seen: 3, fetched: 1, skipped: 2, failed: 0" in out.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_rewalks_multipage_day_if_any_page_fetched_before_day_end_brt():
    """B1: min(fetched_at) across all pages must be >= (day + 1) 00:00 BRT."""
    after_end = datetime(2026, 11, 2, 0, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))
    before_end = datetime(2026, 11, 1, 23, 59, tzinfo=ZoneInfo("America/Sao_Paulo"))
    _seed_listing_page(
        day="20261101",
        pagina=1,
        total_paginas=2,
        publications=[publication(1)],
        fetched_at=after_end,
    )
    _seed_listing_page(
        day="20261101",
        pagina=2,
        total_paginas=2,
        publications=[publication(2)],
        fetched_at=before_end,
    )
    _seed_purchase_items(1)
    _seed_purchase_items(2)

    listing_calls = []

    def transport(url: str, params: dict | None = None):
        if "/contratacoes/publicacao" in url:
            page = (params or {}).get("pagina", 1)
            listing_calls.append(page)
            if page == 1:
                return 200, {
                    "data": [publication(1)],
                    "totalRegistros": 2,
                    "totalPaginas": 2,
                    "numeroPagina": 1,
                    "paginasRestantes": 1,
                }
            return 200, {
                "data": [publication(2)],
                "totalRegistros": 2,
                "totalPaginas": 2,
                "numeroPagina": 2,
                "paginasRestantes": 0,
            }
        raise AssertionError(f"Unexpected call: {url}")

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert listing_calls == [1, 2]
    assert "[2026-11-01 modality 6] seen: 2, fetched: 0, skipped: 2, failed: 0" in out.getvalue()


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_skips_day_listed_after_day_end_brt():
    """B1 counter-proof: day D listed at 00:30 BRT on D+1 is closed and skipped."""
    closed_day_fetched_at = datetime(2026, 11, 2, 0, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))
    _seed_listing_page(
        day="20261101",
        pagina=1,
        total_paginas=1,
        publications=[publication(1), publication(2)],
        fetched_at=closed_day_fetched_at,
    )
    _seed_purchase_items(1)
    _seed_purchase_items(2)

    calls = []

    def transport(url: str, params: dict | None = None):
        calls.append((url, params))
        raise AssertionError("No HTTP call should be made when listed after day end BRT")

    out = io.StringIO()
    call_command(
        "fetch_pncp",
        start="2026-11-01",
        end="2026-11-01",
        modality=6,
        transport=transport,
        stdout=out,
    )

    assert calls == []
    assert (
        "[2026-11-01 modality 6] seen: 2, fetched: 0, skipped: 2, failed: 0 (complete)"
        in out.getvalue()
    )


def test_fetch_pncp_default_failed_purchases_file_is_outside_repository():
    from ingestion.management.commands.fetch_pncp import Command

    parser = Command().create_parser("manage.py", "fetch_pncp")
    default_path = Path(parser.get_default("failed_purchases_file")).resolve()
    repo_root = Path(__file__).resolve().parents[2]
    assert not default_path.is_relative_to(repo_root)
    assert default_path.name == "fetch_failed_purchases.jsonl"
    assert default_path.parent.name == "preparatory-phase-support"


@pytest.mark.integration
@pytest.mark.django_db
def test_fetch_pncp_resolves_relative_failed_purchases_file_under_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    code_dir = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(code_dir)

    page_1 = _read_json("publications_page_1.json")
    single_pub = dict(page_1)
    single_pub["data"] = [page_1["data"][0]]
    single_pub["totalRegistros"] = 1
    single_pub["totalPaginas"] = 1
    single_pub["numeroPagina"] = 1
    single_pub["paginasRestantes"] = 0

    def failing_transport(url: str, params: dict | None = None):
        if "/api/consulta/v1/contratacoes/publicacao" in url:
            return 200, single_pub
        if url.endswith("/quantidade"):
            return 500, {"message": "fatal internal server error"}
        return 404, {}

    rel_name = "relative_fetch_failed.jsonl"
    stray_in_code = code_dir / rel_name
    try:
        with pytest.raises(CommandError):
            call_command(
                "fetch_pncp",
                start="2026-11-01",
                end="2026-11-01",
                uf="PA",
                modality=6,
                transport=failing_transport,
                failed_purchases_file=rel_name,
                stdout=io.StringIO(),
                stderr=io.StringIO(),
            )

        assert not stray_in_code.exists()
        expected = tmp_path / ".local" / "state" / "preparatory-phase-support" / rel_name
        assert expected.exists()
        lines = expected.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["purchase_key"] == ["00000000000000", 2026, 1]
    finally:
        stray_in_code.unlink(missing_ok=True)


@pytest.mark.django_db
def test_fetch_pncp_rejects_failed_purchases_file_inside_repository():
    code_dir = Path(__file__).resolve().parents[1]
    inside_repo = code_dir / "should_not_be_created.jsonl"
    try:
        with pytest.raises(CommandError, match="repository"):
            call_command(
                "fetch_pncp",
                start="2026-11-01",
                end="2026-11-01",
                uf="PA",
                modality=6,
                transport=lambda u, p: (204, None),
                failed_purchases_file=str(inside_repo),
                stdout=io.StringIO(),
                stderr=io.StringIO(),
            )
        assert not inside_repo.exists()
    finally:
        inside_repo.unlink(missing_ok=True)
