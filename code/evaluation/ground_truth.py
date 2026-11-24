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
    found_item: dict[str, Any] | None = None

    for record in records:
        payload = record.payload
        if isinstance(payload, list):
            for it in payload:
                if isinstance(it, dict) and it.get("numeroItem") == numero_item:
                    found_item = it
                    break
        elif isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                for it in data:
                    if isinstance(it, dict) and it.get("numeroItem") == numero_item:
                        found_item = it
                        break
        if found_item is not None:
            break

    if found_item is None:
        return ResolvedGroundTruthItem(
            cnpj=cnpj,
            ano=ano,
            sequencial=sequencial,
            numero_item=numero_item,
            found=False,
            failure_cause="item_not_found_in_purchase",
        )

    # Map materialOuServico to item_kind ("product" or "service")
    mat_serv = str(found_item.get("materialOuServico") or "").strip().upper()
    if mat_serv.startswith("M"):
        item_kind = "product"
    elif mat_serv.startswith("S"):
        item_kind = "service"
    else:
        item_kind = None

    # Quantity
    raw_qty = found_item.get("quantidade")
    qty = Decimal(str(raw_qty)) if raw_qty is not None else None

    # Estimated unit price
    raw_est = found_item.get("valorUnitarioEstimado")
    est_price = Decimal(str(raw_est)) if raw_est is not None else None

    # Awarded unit price
    raw_awarded = found_item.get("valorUnitarioHomologado")
    awarded_price = Decimal(str(raw_awarded)) if raw_awarded is not None else None

    return ResolvedGroundTruthItem(
        cnpj=cnpj,
        ano=ano,
        sequencial=sequencial,
        numero_item=numero_item,
        found=True,
        description=found_item.get("descricao"),
        item_kind=item_kind,
        unit=found_item.get("unidadeMedida"),
        quantity=qty,
        estimated_unit_price=est_price,
        awarded_unit_price=awarded_price,
        has_result=found_item.get("temResultado"),
        secret_budget=found_item.get("orcamentoSigiloso"),
        failure_cause=None,
    )
