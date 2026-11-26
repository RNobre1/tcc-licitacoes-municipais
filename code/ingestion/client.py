import datetime
import email.utils
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from django.db import transaction
from django.utils import timezone

from ingestion.models import RawRecord

DEFAULT_PNCP_BASE_URL = "https://pncp.gov.br"
MAX_PUBLICATIONS_PAGES = 10000
MAX_RETRY_AFTER_SECONDS = 600.0

TransportCallable = Callable[..., tuple[int, Any]]


def parse_retry_after(
    value: str | None,
    *,
    now: datetime.datetime | None = None,
) -> float | None:
    """Parse Retry-After header as seconds or HTTP date, returning seconds capped at 600s."""
    if not value:
        return None
    val_str = str(value).strip()
    try:
        sec = float(val_str)
        if not math.isfinite(sec) or sec < 0:
            return None
        return min(MAX_RETRY_AFTER_SECONDS, sec)
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(val_str)
        if dt is None or dt.tzinfo is None:
            return None
        ref_now = now if now is not None else datetime.datetime.now(datetime.UTC)
        diff = (dt - ref_now).total_seconds()
        if not math.isfinite(diff):
            return None
        if diff < 0:
            return 0.0
        return min(MAX_RETRY_AFTER_SECONDS, diff)
    except Exception:
        return None


class PncpError(Exception):
    """Base exception for PNCP client errors."""


class PncpResponseError(PncpError):
    """Raised when PNCP API returns a non-200 status or invalid response."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        headers: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.headers = headers or {}
        self.retry_after = retry_after


class ItemCountMismatchError(PncpError):
    """Raised when the number of collected items differs from expected quantidade."""


def urllib_transport(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, Any]:
    """Default HTTP transport using standard library urllib with timeout."""
    if params:
        query_string = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}{query_string}"
    else:
        full_url = url

    req = urllib.request.Request(full_url, headers={"Accept": "application/json"})
    headers: dict[str, str] = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            body = resp.read()
            if hasattr(resp, "headers") and resp.headers:
                headers = {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read()
        if hasattr(exc, "headers") and exc.headers:
            headers = {k.lower(): v for k, v in exc.headers.items()}

    if status == 204:
        return 204, None

    if status == 429:
        retry_after = parse_retry_after(headers.get("retry-after"))
        return 429, {
            "error": "Too Many Requests",
            "retry_after": retry_after,
            "headers": headers,
        }

    if status >= 400:
        try:
            decoded = body.decode("utf-8") if isinstance(body, bytes) else str(body)
            data = json.loads(decoded)
        except Exception:
            decoded_text = (
                body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            )
            data = {"error": f"HTTP {status}", "body": decoded_text[:1000]}
        return status, data

    try:
        decoded = body.decode("utf-8") if isinstance(body, bytes) else str(body)
        data = json.loads(decoded)
    except Exception as exc:
        raise PncpResponseError(
            f"Failed to decode response as valid JSON from {url} (status {status}): {exc}",
            status=status,
            headers=headers,
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
        endpoint = "/api/consulta/v1/contratacoes/publicacao"
        url = f"{self.base_url}{endpoint}"

        query_params = dict(params or {})
        query_params.pop("pagina", None)
        query_params.setdefault("tamanhoPagina", 50)

        records: list[RawRecord] = []
        pagina = 1
        expected_total_registros: int | None = None

        while True:
            if pagina > MAX_PUBLICATIONS_PAGES:
                raise PncpResponseError(
                    f"Publications walk exceeded hard page cap ({MAX_PUBLICATIONS_PAGES})"
                )

            current_params = dict(query_params)
            current_params["pagina"] = pagina

            status, payload = self.transport(url, current_params)

            if pagina == 1 and status == 204:
                return []

            if status != 200:
                raise PncpResponseError(
                    f"PNCP publications request failed with status {status}: {payload}",
                    status=status,
                )

            if payload is None or not isinstance(payload, dict):
                raise PncpResponseError(
                    f"PNCP publications request returned invalid payload: {payload}",
                    status=status,
                )

            data = payload.get("data")
            if data is not None and not isinstance(data, list):
                raise PncpResponseError(
                    f"PNCP publications request returned non-list data: {payload}",
                    status=status,
                )

            paginas_restantes = payload.get("paginasRestantes")
            if (
                paginas_restantes is None
                or not isinstance(paginas_restantes, int)
                or isinstance(paginas_restantes, bool)
            ):
                raise PncpResponseError(
                    f"Missing or invalid paginasRestantes in payload: {payload}",
                    status=status,
                )

            numero_pagina = payload.get("numeroPagina")
            if (
                numero_pagina is None
                or not isinstance(numero_pagina, int)
                or isinstance(numero_pagina, bool)
            ):
                raise PncpResponseError(
                    f"Missing or invalid numeroPagina in payload: {payload}",
                    status=status,
                )
            if numero_pagina != pagina:
                raise PncpResponseError(
                    f"API returned numeroPagina {numero_pagina} but requested {pagina}",
                    status=status,
                )

            total_paginas = payload.get("totalPaginas")
            if (
                total_paginas is None
                or not isinstance(total_paginas, int)
                or isinstance(total_paginas, bool)
            ):
                raise PncpResponseError(
                    f"Missing or invalid totalPaginas in payload: {payload}",
                    status=status,
                )
            if pagina > total_paginas:
                raise PncpResponseError(
                    f"Current page {pagina} exceeds totalPaginas {total_paginas}",
                    status=status,
                )

            if "totalRegistros" in payload and isinstance(payload["totalRegistros"], int):
                expected_total_registros = payload["totalRegistros"]

            record = RawRecord(
                endpoint=endpoint,
                params=current_params,
                fetched_at=timezone.now(),
                payload=payload,
                status_code=status,
            )
            records.append(record)

            if paginas_restantes == 0:
                break
            pagina += 1

        if expected_total_registros is not None:
            total_publications = sum(
                len(r.payload.get("data", []))
                for r in records
                if isinstance(r.payload.get("data"), list)
            )
            if total_publications != expected_total_registros:
                raise PncpResponseError(
                    f"Publication count mismatch: collected {total_publications} items, "
                    f"expected {expected_total_registros}",
                    status=status,
                )

        if save and records:
            with transaction.atomic():
                RawRecord.objects.bulk_create(records)

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
        endpoint_base = f"/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
        quantity_url = f"{self.base_url}{endpoint_base}/quantidade"
        items_url = f"{self.base_url}{endpoint_base}"

        q_status, q_payload = self.transport(quantity_url, None)
        if q_status != 200:
            raise PncpResponseError(
                f"PNCP items quantity request failed with status {q_status}: {q_payload}",
                status=q_status,
            )
        if q_payload is None or not isinstance(q_payload, int) or isinstance(q_payload, bool):
            raise PncpResponseError(
                f"PNCP items quantity request returned invalid payload: {q_payload}",
                status=q_status,
            )
        expected_quantity = q_payload

        query_params = dict(params or {})
        query_params.pop("pagina", None)
        query_params.setdefault("tamanhoPagina", 500)

        records: list[RawRecord] = []
        collected_items_count = 0
        seen_item_numbers: set[Any] = set()
        pagina = 1

        while True:
            current_params = dict(query_params)
            current_params["pagina"] = pagina

            status, payload = self.transport(items_url, current_params)

            if status != 200:
                raise PncpResponseError(
                    f"PNCP items request failed with status {status}: {payload}",
                    status=status,
                )

            if payload is None or not isinstance(payload, list):
                raise PncpResponseError(
                    f"PNCP items request returned invalid payload: {payload}",
                    status=status,
                )

            for item in payload:
                if not isinstance(item, dict):
                    raise PncpResponseError(
                        f"PNCP item is not a dictionary: {item}",
                        status=status,
                    )
                item_num = item.get("numeroItem")
                if item_num is not None:
                    seen_item_numbers.add(item_num)

            record = RawRecord(
                endpoint=endpoint_base,
                params=current_params,
                fetched_at=timezone.now(),
                payload=payload,
                status_code=status,
            )
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

        if len(seen_item_numbers) != collected_items_count:
            raise PncpResponseError(
                f"Duplicate numeroItem found across pages: {len(seen_item_numbers)} "
                f"unique items for {collected_items_count} total items",
                status=status,
            )

        if save and records:
            with transaction.atomic():
                RawRecord.objects.bulk_create(records)

        return records

    def fetch_item_results(
        self,
        cnpj: str,
        ano: int,
        sequencial: int,
        numero_item: int,
        *,
        save: bool = True,
    ) -> RawRecord:
        """Fetch item results (awarded price and winner) for a specific item."""
        endpoint_base = f"/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
        endpoint = f"{endpoint_base}/{numero_item}/resultados"
        url = f"{self.base_url}{endpoint}"

        status, payload = self.transport(url, None)

        if status == 204:
            payload = []
        elif status != 200:
            raise PncpResponseError(
                f"PNCP item results request failed with status {status}: {payload}",
                status=status,
            )
        elif not isinstance(payload, list):
            raise PncpResponseError(
                f"PNCP item results request returned invalid payload: {payload}",
                status=status,
            )

        record = RawRecord(
            endpoint=endpoint,
            params={},
            fetched_at=timezone.now(),
            payload=payload,
            status_code=status,
        )

        if save:
            with transaction.atomic():
                record.save()

        return record

    def fetch_purchase(
        self,
        cnpj: str,
        ano: int,
        sequencial: int,
        *,
        save: bool = True,
    ) -> RawRecord:
        """Fetch single purchase header metadata by its key."""
        endpoint = f"/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}"
        url = f"{self.base_url}{endpoint}"

        status, payload = self.transport(url, None)

        if status != 200:
            raise PncpResponseError(
                f"PNCP purchase request failed with status {status}: {payload}",
                status=status,
            )
        if not isinstance(payload, dict):
            raise PncpResponseError(
                f"PNCP purchase request returned invalid payload: {payload}",
                status=status,
            )

        record = RawRecord(
            endpoint=endpoint,
            params={},
            fetched_at=timezone.now(),
            payload=payload,
            status_code=status,
        )

        if save:
            with transaction.atomic():
                record.save()

        return record


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


def fetch_item_results(
    cnpj: str,
    ano: int,
    sequencial: int,
    numero_item: int,
    transport: TransportCallable | None = None,
    base_url: str = DEFAULT_PNCP_BASE_URL,
    *,
    save: bool = True,
) -> RawRecord:
    """Convenience functional wrapper for PncpClient.fetch_item_results."""
    client = PncpClient(base_url=base_url, transport=transport)
    return client.fetch_item_results(
        cnpj=cnpj,
        ano=ano,
        sequencial=sequencial,
        numero_item=numero_item,
        save=save,
    )


def fetch_purchase(
    cnpj: str,
    ano: int,
    sequencial: int,
    transport: TransportCallable | None = None,
    base_url: str = DEFAULT_PNCP_BASE_URL,
    *,
    save: bool = True,
) -> RawRecord:
    """Convenience functional wrapper for PncpClient.fetch_purchase."""
    client = PncpClient(base_url=base_url, transport=transport)
    return client.fetch_purchase(
        cnpj=cnpj,
        ano=ano,
        sequencial=sequencial,
        save=save,
    )
