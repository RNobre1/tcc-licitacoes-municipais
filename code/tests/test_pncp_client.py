import json
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

PNCP_RESPONSES_DIR = Path(__file__).parent / "api_responses" / "pncp"


def _read_json(filename: str):
    return json.loads((PNCP_RESPONSES_DIR / filename).read_text(encoding="utf-8"))


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
    assert calls[1][1]["pagina"] == 2

    # N5: endpoint stored as path only, with leading slash and no host
    assert records[0].endpoint == "/v1/contratacoes/publicacao"
    assert records[0].params["pagina"] == 1
    assert records[0].payload == page_1
    assert records[0].status_code == 200

    assert records[1].endpoint == "/v1/contratacoes/publicacao"
    assert records[1].params["pagina"] == 2
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
        cnpj="00000000000000",
        ano=2026,
        sequencial=1,
        transport=mock_transport,
        save=False,
    )

    assert len(records) == 2
    assert len(calls) == 3  # 1 for quantidade, 2 for pages

    assert calls[0][0].endswith("/compras/2026/1/itens/quantidade")
    assert calls[1][1]["pagina"] == 1
    assert calls[2][1]["pagina"] == 2

    # N5: endpoint stored as path only, with leading slash and no host
    assert records[0].endpoint == "/v1/orgaos/00000000000000/compras/2026/1/itens"
    assert records[0].payload == items_p1
    assert records[1].endpoint == "/v1/orgaos/00000000000000/compras/2026/1/itens"
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
            cnpj="00000000000000",
            ano=2026,
            sequencial=1,
            transport=short_transport,
            save=False,
        )

    err_msg = str(exc_info.value).lower()
    assert "collected 3" in err_msg
    assert "expected 6" in err_msg


def test_fetch_items_raises_on_non_200_quantity():
    def error_transport(url: str, params: dict | None = None):
        return 503, {"message": "Service Unavailable"}

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj="00000000000000",
            ano=2026,
            sequencial=1,
            transport=error_transport,
            save=False,
        )

    assert "503" in str(exc_info.value)


def test_fetch_items_raises_on_non_200_items_page():
    quantity = _read_json("items_quantity.json")

    def error_on_page_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        return 500, {"message": "Internal Server Error"}

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj="00000000000000",
            ano=2026,
            sequencial=1,
            transport=error_on_page_transport,
            save=False,
        )

    assert "500" in str(exc_info.value)


def test_fetch_items_raises_on_null_or_invalid_items_page():
    quantity = _read_json("items_quantity.json")

    def null_items_transport(url: str, params: dict | None = None):
        if url.endswith("/quantidade"):
            return 200, quantity
        return 200, None

    with pytest.raises(PncpResponseError) as exc_info:
        fetch_items(
            cnpj="00000000000000",
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
        {"pagina": 1},
    )


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
        hdrs={},  # noqa: C408
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
