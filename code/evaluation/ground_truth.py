"""Resolution and normalization of ground-truth records in PNCP."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ingestion.client import fetch_items
from ingestion.models import RawRecord


@dataclass(frozen=True)
class ResolvedGroundTruthItem:
    cnpj: str
    ano: int
    sequencial: int
    numero_item: int
    found: bool
    description: str | None = None
    item_kind: str | None = None  # "product" or "service"
    unit: str | None = None
    quantity: Decimal | None = None
    estimated_unit_price: Decimal | None = None
    awarded_unit_price: Decimal | None = None
    has_result: bool | None = None
    secret_budget: bool | None = None
    failure_cause: str | None = None


def resolve_purchase_items(
    cnpj: str,
    ano: int,
    sequencial: int,
    transport: Any = None,
    save: bool = True,
) -> list[RawRecord]:
    """Fetch purchase items via existing ingestion client."""
    return fetch_items(
        cnpj=cnpj,
        ano=ano,
        sequencial=sequencial,
        transport=transport,
        save=save,
    )


def match_ground_truth_item(
    cnpj: str,
    ano: int,
    sequencial: int,
    numero_item: int,
    records: list[RawRecord],
) -> ResolvedGroundTruthItem:
    """Find specific item in fetched purchase raw records."""
    raise NotImplementedError
