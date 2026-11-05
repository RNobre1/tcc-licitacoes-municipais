import http.server
import json
import threading
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.client import (
    ItemCountMismatchError,
    PncpClient,
    PncpResponseError,
    fetch_items,
    fetch_publications,
    urllib_transport,
)

PNCP_RESPONSES_DIR = Path(__file__).resolve().parent / "api_responses" / "pncp"
CNPJ = "00000000000000"


def _read_json(filename: str):
    return json.loads((PNCP_RESPONSES_DIR / filename).read_text(encoding="utf-8"))


def items_transport(quantity, pages):
    def transport(url, params=None):
        if url.endswith("/quantidade"):
            return 200, quantity
        return 200, pages.get(params["pagina"], [])

    return transport


def test_fetch_publications_walks_pages_until_paginas_restantes_zero():
    page_1 = _read_json("publications_page_1.json")
    page_2 = _read_json("publications_page_2.json")

    calls = []

    def mock_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if params and params.get("pagina") == 1:
            return 200, page_1
        if params and params.get("pagina") == 2:
            return 200, page_2
        return 404, {"message": "Not found"}

    records = fetch_publications(
        params={"dataInicial": "20261101", "dataFinal": "20261102", "uf": "PA"},
        transport=mock_transport,
        save=False,
    )

    assert len(records) == 2
    assert len(calls) == 2

    assert calls[0][1]["pagina"] == 1
    assert calls[0][1]["tamanhoPagina"] == 50
    assert calls[1][1]["pagina"] == 2
    assert calls[1][1]["tamanhoPagina"] == 50

    # B4: endpoint stored as full path including API prefix, without host
    assert records[0].endpoint == "/api/consulta/v1/contratacoes/publicacao"
    assert records[0].params["pagina"] == 1
    assert records[0].params["tamanhoPagina"] == 50
    assert records[0].payload == page_1
    assert records[0].status_code == 200

    assert records[1].endpoint == "/api/consulta/v1/contratacoes/publicacao"
    assert records[1].params["pagina"] == 2
    assert records[1].params["tamanhoPagina"] == 50
    assert records[1].payload == page_2
    assert records[1].status_code == 200


def test_fetch_publications_raises_on_non_200_status():
    def error_transport(url: str, params: dict | None = None):
        return 500, {"message": "PNCP API temporarily unavailable"}

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_publications(
            params={"dataInicial": "20261101", "dataFinal": "20261102"},
            transport=error_transport,
            save=False,
        )

    assert "500" in str(exc_info.value)
    assert exc_info.value.status == 500


def test_fetch_publications_raises_on_null_or_invalid_payload():
    def null_transport(url: str, params: dict | None = None):
        return 200, None

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_publications(
            params={"dataInicial": "20261101"},
            transport=null_transport,
            save=False,
        )
    assert "payload" in str(exc_info.value).lower()


def test_fetch_items_reads_quantidade_and_walks_pages():
    items_p1 = _read_json("items_page_1.json")
    items_p2 = _read_json("items_page_2.json")
    quantity = _read_json("items_quantity.json")

    calls = []

    def mock_transport(url: str, params: dict | None = None):
        calls.append((url, params))
        if url.endswith("/quantidade"):
            return 200, quantity
        if params and params.get("pagina") == 1:
            return 200, items_p1
        if params and params.get("pagina") == 2:
            return 200, items_p2
        return 200, []

    records = fetch_items(
        cnpj=CNPJ,
        ano=2026,
        sequencial=1,
        transport=mock_transport,
        save=False,
    )

    assert len(records) == 2
    assert len(calls) == 3  # 1 for quantidade, 2 for pages

    assert calls[0][0].endswith("/compras/2026/1/itens/quantidade")
    assert calls[1][1]["pagina"] == 1
    assert calls[1][1]["tamanhoPagina"] == 500
    assert calls[2][1]["pagina"] == 2
    assert calls[2][1]["tamanhoPagina"] == 500

    # B4: endpoint stored as full path including API prefix, without host
    assert records[0].endpoint == f"/api/pncp/v1/orgaos/{CNPJ}/compras/2026/1/itens"
    assert records[0].params["tamanhoPagina"] == 500
    assert records[0].payload == items_p1
    assert records[1].endpoint == f"/api/pncp/v1/orgaos/{CNPJ}/compras/2026/1/itens"
    assert records[1].params["tamanhoPagina"] == 500
    assert records[1].payload == items_p2

    total_items = sum(len(r.payload) for r in records)
    assert total_items == quantity


def test_fetch_items_raises_when_short_of_quantidade():
    items_p1 = _read_json("items_page_1.json")  # 3 items
    quantity = _read_json("items_quantity.json")  # 6 items

    def short_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        if params and params.get("pagina") == 1:
            return 200, items_p1
        # Truncated: page 2 returns empty list, reaching only 3 of 6 items
        return 200, []

    with pytest.raises(ItemCountMismatchError) as exc_info:
        fetch_items(
            cnpj=CNPJ,
            ano=2026,
            sequencial=1,
            transport=short_transport,
            save=False,
        )

    err_msg = str(exc_info.value).lower()
    assert "collected 3" in err_msg
    assert "expected 6" in err_msg


def test_items_over_long_is_an_error():
    page = [{"numeroItem": 1}, {"numeroItem": 2}, {"numeroItem": 3}]
    with pytest.raises(ItemCountMismatchError) as caught:
        fetch_items(CNPJ, 2026, 1, transport=items_transport(4, {1: page, 2: page}), save=False)
    assert "collected 6" in str(caught.value) and "expected 4" in str(caught.value)


def test_the_endpoint_names_the_api_that_answered():
    pub = fetch_publications(
        transport=lambda url, params: (200, {"data": [], "paginasRestantes": 0}), save=False
    )
    assert pub[0].endpoint == "/api/consulta/v1/contratacoes/publicacao"
    items = fetch_items(
        CNPJ, 2026, 1, transport=items_transport(1, {1: [{"numeroItem": 1}]}), save=False
    )
    assert items[0].endpoint == f"/api/pncp/v1/orgaos/{CNPJ}/compras/2026/1/itens"


def test_a_body_without_the_envelope_is_an_error_not_a_complete_walk():
    with pytest.raises(PncpResponseError):
        fetch_publications(transport=lambda url, params: (200, {"message": "other"}), save=False)


def test_a_walk_that_never_advances_is_stopped():
    calls = []

    def stuck(url, params):
        calls.append(params["pagina"])
        if len(calls) > 20:
            pytest.fail("still walking after 20 requests")
        return 200, {"data": [], "totalPaginas": 2, "numeroPagina": 1, "paginasRestantes": 1}

    with pytest.raises(PncpResponseError):
        fetch_publications(transport=stuck, save=False)
    assert len(calls) <= 3


def test_fetch_publications_raises_on_count_mismatch_with_total_registros():
    def mismatch_transport(url, params):
        return 200, {
            "data": [{"numeroControlePNCP": "00000000000000-1-000001/2026"}],
            "totalRegistros": 4,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        }

    with pytest.raises(PncpResponseError) as caught:
        fetch_publications(transport=mismatch_transport, save=False)
    assert "count mismatch" in str(caught.value).lower()


def test_fetch_items_raises_on_duplicate_item_numbers():
    page = [{"numeroItem": 1}, {"numeroItem": 2}, {"numeroItem": 3}]
    with pytest.raises(PncpResponseError) as caught:
        fetch_items(CNPJ, 2026, 1, transport=items_transport(6, {1: page, 2: page}), save=False)
    assert "duplicate" in str(caught.value).lower()


def test_fetch_items_raises_on_non_200_quantity():
    def error_transport(url: str, params: dict | None = None):
        return 503, {"message": "Service Unavailable"}

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj=CNPJ,
            ano=2026,
            sequencial=1,
            transport=error_transport,
            save=False,
        )

    assert "503" in str(exc_info.value)
    assert exc_info.value.status == 503


def test_fetch_items_raises_on_non_200_items_page():
    quantity = _read_json("items_quantity.json")

    def error_on_page_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        return 500, {"message": "Internal Server Error"}

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj=CNPJ,
            ano=2026,
            sequencial=1,
            transport=error_on_page_transport,
            save=False,
        )

    assert "500" in str(exc_info.value)
    assert exc_info.value.status == 500


def test_fetch_items_raises_on_null_or_invalid_items_page():
    quantity = _read_json("items_quantity.json")

    def null_items_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        return 200, None

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj=CNPJ,
            ano=2026,
            sequencial=1,
            transport=null_items_transport,
            save=False,
        )

    assert "payload" in str(exc_info.value).lower()


def test_pncp_client_instance_and_injected_transport():
    mock_transport = MagicMock(return_value=(200, {"data": [], "paginasRestantes": 0}))
    client = PncpClient(base_url="https://example.test", transport=mock_transport)

    records = client.fetch_publications(params={"pagina": 1}, save=False)
    assert len(records) == 1
    mock_transport.assert_called_once_with(
        "https://example.test/api/consulta/v1/contratacoes/publicacao",
        {"pagina": 1, "tamanhoPagina": 50},
    )


def test_pncp_response_error_carries_status():
    err = PncpResponseError("Gateway timeout", status=504)
    assert err.status == 504


def test_urllib_transport_success():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'{"success": true}'
    fake_response.__enter__.return_value = fake_response

    with patch("urllib.request.urlopen", return_value=fake_response):
        status, data = urllib_transport("https://pncp.gov.br/api/test", {"key": "value"})
        assert status == 200
        assert data == {"success": True}


def test_urllib_transport_http_error():
    fake_error = urllib.error.HTTPError(
        url="https://pncp.gov.br/api/test",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"error": "not found"}'),
    )

    with patch("urllib.request.urlopen", side_effect=fake_error):
        status, data = urllib_transport("https://pncp.gov.br/api/test")
        assert status == 404
        assert data == {"error": "not found"}


def test_urllib_transport_non_json_body():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b"<html>Bad Gateway</html>"
    fake_response.__enter__.return_value = fake_response

    with patch("urllib.request.urlopen", return_value=fake_response):
        with pytest.raises(PncpResponseError) as exc_info:
            urllib_transport("https://pncp.gov.br/api/test")
        assert "valid json" in str(exc_info.value).lower()


def test_urllib_transport_sends_the_path_the_query_and_the_accept_header():
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append((self.path, self.headers.get("Accept")))
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/consulta/v1/x"
        assert urllib_transport(url, {"pagina": 2, "uf": "PA"}) == (200, {"ok": True})
    finally:
        server.shutdown()
    assert seen == [("/api/consulta/v1/x?pagina=2&uf=PA", "application/json")]


def test_urllib_transport_times_out():
    class HangingHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            import time

            time.sleep(1.0)
            self.send_response(200)
            self.end_headers()

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), HangingHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/timeout"
        with pytest.raises((TimeoutError, urllib.error.URLError)):
            urllib_transport(url, timeout=0.05)
    finally:
        server.shutdown()
