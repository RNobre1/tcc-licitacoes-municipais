"""Resolution and normalization of ground-truth records in PNCP."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ingestion.client import fetch_items
from ingestion.item_kind import map_item_kind
from ingestion.models import RawRecord
from ingestion.raw_records import latest_copies


@dataclass(frozen=True)
class ResolvedGroundTruthItem:
    cnpj: str
    year: int
    purchase_sequence: int
    item_number: int
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
    ano: int | None = None,
    sequencial: int | None = None,
    year: int | None = None,
    purchase_sequence: int | None = None,
    transport: Any = None,
    save: bool = True,
) -> list[RawRecord]:
    """Fetch purchase items via existing ingestion client."""
    y = year if year is not None else (ano or 0)
    seq = purchase_sequence if purchase_sequence is not None else (sequencial or 0)
    return fetch_items(
        cnpj=cnpj,
        ano=y,
        sequencial=seq,
        transport=transport,
        save=save,
    )


def match_ground_truth_item(
    cnpj: str,
    ano: int | None = None,
    sequencial: int | None = None,
    numero_item: int | None = None,
    year: int | None = None,
    purchase_sequence: int | None = None,
    item_number: int | None = None,
    records: Sequence[RawRecord] | None = None,
    item_records: Sequence[RawRecord] | None = None,
    result_records: Sequence[RawRecord] | None = None,
) -> ResolvedGroundTruthItem:
    """Find specific item in fetched purchase raw records.

    N5: Uses map_item_kind and (year, purchase_sequence, item_number) key.
    N6: Awarded price comes strictly from result records, never from the item payload.
    N7: The newest RawRecord copy wins.
    """
    y = year if year is not None else (ano or 0)
    seq = purchase_sequence if purchase_sequence is not None else (sequencial or 0)
    it_num = item_number if item_number is not None else (numero_item or 0)

    raw_items_input = item_records if item_records is not None else (records or [])
    deduped_item_records = latest_copies(raw_items_input)

    found_item: dict[str, Any] | None = None
    for record in deduped_item_records:
        payload = record.payload
        items_list = []
        if isinstance(payload, list):
            items_list = payload
        elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
            items_list = payload["data"]

        for it in items_list:
            if isinstance(it, dict) and it.get("numeroItem") == it_num:
                found_item = it
                break
        if found_item is not None:
            break

    if found_item is None:
        return ResolvedGroundTruthItem(
            cnpj=cnpj,
            year=y,
            purchase_sequence=seq,
            item_number=it_num,
            found=False,
            failure_cause="item_not_found_in_purchase",
        )

    item_kind = map_item_kind(
        found_item.get("materialOuServico"),
        found_item.get("materialOuServicoNome"),
    )

    raw_qty = found_item.get("quantidade")
    qty = Decimal(str(raw_qty)) if raw_qty is not None else None

    raw_est = found_item.get("valorUnitarioEstimado")
    est_price = Decimal(str(raw_est)) if raw_est is not None else None

    # N6: Awarded price comes strictly from result records, never from the item payload
    awarded_price: Decimal | None = None
    if result_records:
        deduped_results = latest_copies(result_records)
        for r in deduped_results:
            if not isinstance(r.payload, list):
                continue
            for res in r.payload:
                if not isinstance(res, dict):
                    continue
                situacao = res.get("situacaoCompraItemResultadoNome")
                cancelado = res.get("dataCancelamento")
                if situacao == "Informado" and not cancelado:
                    val = res.get("valorUnitarioHomologado")
                    if val is not None:
                        try:
                            awarded_price = Decimal(str(val))
                            break
                        except Exception:
                            pass
            if awarded_price is not None:
                break

    return ResolvedGroundTruthItem(
        cnpj=cnpj,
        year=y,
        purchase_sequence=seq,
        item_number=it_num,
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
