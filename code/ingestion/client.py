import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from django.utils import timezone

from ingestion.models import RawRecord

DEFAULT_PNCP_BASE_URL = "https://pncp.gov.br"

TransportCallable = Callable[[str, dict[str, Any] | None], tuple[int, Any]]


class PncpError(Exception):
    """Base exception for PNCP client errors."""


class PncpResponseError(PncpError):
    """Raised when PNCP API returns a non-200 status or invalid response."""


class ItemCountMismatchError(PncpError):
    """Raised when the number of collected items differs from expected quantidade."""


def urllib_transport(url: str, params: dict[str, Any] | None = None) -> tuple[int, Any]:
    """Default HTTP transport using standard library urllib."""
    if params:
        query_string = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}{query_string}"
    else:
        full_url = url

    req = urllib.request.Request(full_url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read()

    try:
        decoded = body.decode("utf-8") if isinstance(body, bytes) else str(body)
        data = json.loads(decoded)
    except Exception as exc:
        raise PncpResponseError(
            f"Failed to decode response as valid JSON from {url} (status {status}): {exc}"
        ) from exc

    return status, data


class PncpClient:
    """Client for fetching public procurement publications and items from PNCP."""

    def __init__(
        self,
        base_url: str = DEFAULT_PNCP_BASE_URL,
        transport: TransportCallable | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport or urllib_transport

    def fetch_publications(
        self,
        params: dict[str, Any] | None = None,
        *,
        save: bool = True,
    ) -> list[RawRecord]:
        """Fetch publications walking pages until paginasRestantes == 0."""
        endpoint = "/v1/contratacoes/publicacao"
        url = f"{self.base_url}/api/consulta{endpoint}"

        query_params = dict(params or {})
        pagina = int(query_params.get("pagina", 1))

        records: list[RawRecord] = []

        while True:
            current_params = dict(query_params)
            current_params["pagina"] = pagina

            status, payload = self.transport(url, current_params)

            if status != 200 or payload is None or not isinstance(payload, dict):
                raise PncpResponseError(
                    f"PNCP publications request failed with status {status} "
                    f"or invalid payload: {payload}"
                )

            record = RawRecord(
                endpoint=endpoint,
                params=current_params,
                fetched_at=timezone.now(),
                payload=payload,
                status_code=status,
            )
            if save:
                record.save()
            records.append(record)

            paginas_restantes = payload.get("paginasRestantes", 0)
            if paginas_restantes == 0:
                break
            pagina += 1

        return records

    def fetch_items(
        self,
        cnpj: str,
        ano: int,
        sequencial: int,
        params: dict[str, Any] | None = None,
        *,
        save: bool = True,
    ) -> list[RawRecord]:
        """Fetch items for a purchase after querying quantidade, validating completeness."""
        endpoint_base = f"/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
        quantity_url = f"{self.base_url}/api/pncp{endpoint_base}/quantidade"
        items_url = f"{self.base_url}/api/pncp{endpoint_base}"

        q_status, q_payload = self.transport(quantity_url, None)
        if q_status != 200 or q_payload is None or not isinstance(q_payload, int):
            raise PncpResponseError(
                f"PNCP items quantity request failed with status {q_status} "
                f"or invalid payload: {q_payload}"
            )
        expected_quantity = q_payload

        query_params = dict(params or {})
        pagina = int(query_params.get("pagina", 1))

        records: list[RawRecord] = []
        collected_items_count = 0

        while True:
            current_params = dict(query_params)
            current_params["pagina"] = pagina

            status, payload = self.transport(items_url, current_params)

            if status != 200 or payload is None or not isinstance(payload, list):
                raise PncpResponseError(
                    f"PNCP items request failed with status {status} or invalid payload: {payload}"
                )

            record = RawRecord(
                endpoint=endpoint_base,
                params=current_params,
                fetched_at=timezone.now(),
                payload=payload,
                status_code=status,
            )
            if save:
                record.save()
            records.append(record)

            page_items_count = len(payload)
            collected_items_count += page_items_count

            if page_items_count == 0 or collected_items_count >= expected_quantity:
                break
            pagina += 1

        if collected_items_count != expected_quantity:
            raise ItemCountMismatchError(
                f"Item count mismatch for {endpoint_base}: "
                f"collected {collected_items_count} items, expected {expected_quantity}"
            )

        return records


def fetch_publications(
    params: dict[str, Any] | None = None,
    transport: TransportCallable | None = None,
    base_url: str = DEFAULT_PNCP_BASE_URL,
    *,
    save: bool = True,
) -> list[RawRecord]:
    """Convenience functional wrapper for PncpClient.fetch_publications."""
    client = PncpClient(base_url=base_url, transport=transport)
    return client.fetch_publications(params=params, save=save)


def fetch_items(
    cnpj: str,
    ano: int,
    sequencial: int,
    params: dict[str, Any] | None = None,
    transport: TransportCallable | None = None,
    base_url: str = DEFAULT_PNCP_BASE_URL,
    *,
    save: bool = True,
) -> list[RawRecord]:
    """Convenience functional wrapper for PncpClient.fetch_items."""
    client = PncpClient(base_url=base_url, transport=transport)
    return client.fetch_items(cnpj=cnpj, ano=ano, sequencial=sequencial, params=params, save=save)
