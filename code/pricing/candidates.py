from __future__ import annotations

import contextlib
import functools
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

FETCH_FAILURE_CACHE_TIMEOUT_SECONDS = 300


def build_provenance_url(cnpj: str, year: int, purchase_sequence: int) -> str:
    """Build the public PNCP purchase page URL from PNCP key components."""
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{purchase_sequence}"


@dataclass(frozen=True)
class Candidate:
    """A price candidate built from a normalized PublicItem."""

    id: int
    description: str
    unit: str
    quantity: Decimal
    agency: str
    date: date
    source: str = "PNCP"
    provenance: str = ""
    similarity: float = 0.0
    awarded_unit_price: Decimal | None = None
    estimated_unit_price: Decimal | None = None
    secret_budget: bool = False
    item_id: int | None = None

    @property
    def published_on(self) -> date:
        return self.date

    @property
    def price(self) -> Decimal | None:
        """Display price: awarded when present, else estimated if not secret budget."""
        if self.secret_budget:
            return None
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return self.awarded_unit_price
        if self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00"):
            return self.estimated_unit_price
        return None

    @property
    def is_estimated(self) -> bool:
        """Return True when displaying estimated price instead of awarded."""
        if self.secret_budget:
            return False
        has_awarded = self.awarded_unit_price is not None and self.awarded_unit_price > Decimal(
            "0.00"
        )
        has_estimated = (
            self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00")
        )
        return not has_awarded and has_estimated

    @property
    def price_kind(self) -> str:
        """Price classification: 'awarded', 'estimated', 'secret_budget', or 'no_price'."""
        if self.secret_budget:
            return "secret_budget"
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return "awarded"
        if self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00"):
            return "estimated"
        return "no_price"

    @property
    def usable_calculation_price(self) -> Decimal | None:
        """Price usable for estimation calculation: awarded prices only.

        Estimated prices, zero prices, and secret budget items return None
        and never enter calculation.
        """
        if self.secret_budget or self.is_estimated:
            return None
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return self.awarded_unit_price
        return None

    @property
    def has_usable_calculation_price(self) -> bool:
        return self.usable_calculation_price is not None


def candidate_from_public_item(
    public_item: Any,
    similarity: float = 0.0,
    item_id: int | None = None,
) -> Candidate:
    """Build a Candidate instance from a PublicItem and search score."""
    provenance = build_provenance_url(
        cnpj=public_item.cnpj,
        year=public_item.year,
        purchase_sequence=public_item.purchase_sequence,
    )
    return Candidate(
        id=public_item.pk,
        description=public_item.description,
        unit=public_item.unit,
        quantity=public_item.quantity,
        agency=public_item.agency_name,
        date=public_item.published_on,
        source="PNCP",
        provenance=provenance,
        similarity=float(similarity),
        awarded_unit_price=public_item.awarded_unit_price,
        estimated_unit_price=public_item.estimated_unit_price,
        secret_budget=public_item.secret_budget,
        item_id=item_id,
    )


def _failure_cache_key(public_item: Any) -> str | None:
    item_pk = getattr(public_item, "pk", None)
    if isinstance(item_pk, (int, str)) and str(item_pk).isalnum():
        return f"pncp_fetch_failed_{item_pk}"
    return None


def is_fetch_failure_cached(public_item: Any) -> bool:
    """Return True if a recent on-demand PNCP fetch failed for this item."""
    from django.core.cache import cache

    cache_key = _failure_cache_key(public_item)
    if not cache_key:
        return False
    try:
        return bool(cache.get(cache_key))
    except Exception:
        # A cache outage must not turn an optional lookup into a page error.
        return False


def record_fetch_failure(public_item: Any) -> None:
    """Remember a failed PNCP fetch for 5 minutes to prevent retry storms."""
    from django.core.cache import cache

    cache_key = _failure_cache_key(public_item)
    if not cache_key:
        return
    with contextlib.suppress(Exception):
        cache.set(cache_key, True, timeout=FETCH_FAILURE_CACHE_TIMEOUT_SECONDS)


def has_pending_result(public_item: Any) -> bool:
    """Return True if public_item has no awarded price yet and temResultado is True."""
    from ingestion.models import PublicItem

    if getattr(public_item, "awarded_unit_price", None) is not None:
        return False

    if isinstance(public_item, PublicItem) and public_item._state.adding:
        return False

    raw_records = getattr(public_item, "raw_records", None)
    if raw_records is None:
        return False

    for r in raw_records.all():
        endpoint = getattr(r, "endpoint", "")
        if "itens" in endpoint and not endpoint.endswith("resultados"):
            payload = getattr(r, "payload", None)
            if isinstance(payload, list):
                for it in payload:
                    if (
                        isinstance(it, dict)
                        and it.get("numeroItem") == getattr(public_item, "item_number", None)
                        and it.get("temResultado") is True
                    ):
                        return True
    return False


def fetch_item_results_network(
    public_item: Any,
    timeout: float = 2.0,
    fetch_fn: Any = None,
) -> Any:
    """Execute only the network lookup for PNCP item results without touching the DB."""
    if fetch_fn is not None:
        return fetch_fn(
            cnpj=public_item.cnpj,
            ano=public_item.year,
            sequencial=public_item.purchase_sequence,
            numero_item=public_item.item_number,
        )

    from ingestion.client import fetch_item_results, urllib_transport

    transport = functools.partial(urllib_transport, timeout=timeout)
    return fetch_item_results(
        cnpj=str(public_item.cnpj),
        ano=int(public_item.year),
        sequencial=int(public_item.purchase_sequence),
        numero_item=int(public_item.item_number),
        transport=transport,
        save=False,
    )


def apply_fetched_item_result_record(public_item: Any, record: Any) -> None:
    """Persist fetched RawRecord and awarded price on the main thread."""
    from django.db import transaction

    from ingestion.models import RawRecord
    from ingestion.results import select_valid_result

    if isinstance(record, RawRecord) and record.pk is None:
        with transaction.atomic():
            record.save()

    if record and isinstance(getattr(record, "payload", None), list) and record.payload:
        valid_res = select_valid_result(record.payload)
        if valid_res and isinstance(valid_res, dict):
            val = valid_res.get("valorUnitarioHomologado")
            if val is not None:
                public_item.awarded_unit_price = Decimal(str(val))
                if hasattr(public_item, "save"):
                    public_item.save(update_fields=["awarded_unit_price"])
                if hasattr(public_item.raw_records, "add"):
                    public_item.raw_records.add(record)


def fetch_awarded_price_on_demand(
    public_item: Any,
    timeout: float = 2.0,
    fetch_fn: Any = None,
) -> None:
    """Fetch awarded price on demand when a displayed item has a result in PNCP.

    Uses ingestion fetch_item_results with short timeout. If the fetch fails,
    records the failure briefly in cache and leaves the candidate as estimado.
    """
    if not has_pending_result(public_item):
        return
    if is_fetch_failure_cached(public_item):
        return

    try:
        record = fetch_item_results_network(public_item, timeout=timeout, fetch_fn=fetch_fn)
    except Exception:
        record_fetch_failure(public_item)
        return

    try:
        apply_fetched_item_result_record(public_item, record)
    except Exception:
        # Persistence failures leave the candidate as estimado so the page still renders.
        return
