import json
import logging
import re
from collections import defaultdict
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone

from ingestion.item_kind import map_item_kind
from ingestion.models import PublicItem, RawRecord
from ingestion.raw_records import latest_copies
from ingestion.results import select_valid_result
from ingestion.units import normalize_unit

PUB_ENDPOINT = "/api/consulta/v1/contratacoes/publicacao"
PURCHASE_ENDPOINT_PATTERN = re.compile(
    r"^/api/consulta/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)$"
)
ITEM_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens$"
)
RESULT_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens/(?P<item>\d+)/resultados$"
)
PURCHASE_KEY_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens(?:/(?P<item>\d+)/resultados)?$"
)
RAW_ITEM_PREFIX = "/api/pncp/v1/orgaos/"
DEFAULT_FAILED_PURCHASES_FILE = (
    Path.home() / ".local" / "state" / "preparatory-phase-support" / "build_failed_purchases.jsonl"
)

logger = logging.getLogger(__name__)


class BuildResult(int):
    """Integer subclass carrying build metadata counts."""

    built_count: int
    skipped_without_publication: int
    failed_count: int
    failed_purchases_file: str | None

    def __new__(
        cls,
        built_count: int,
        skipped_without_publication: int = 0,
        failed_count: int = 0,
        failed_purchases_file: str | None = None,
    ):
        obj = super().__new__(cls, built_count)
        obj.built_count = built_count
        obj.skipped_without_publication = skipped_without_publication
        obj.failed_count = failed_count
        obj.failed_purchases_file = failed_purchases_file
        return obj


@dataclass(slots=True)
class _PubMetadata:
    published_on: date
    agency_name: str
    agency_cnpj: str
    state: str
    modality: int
    raw_record_id: int
    fetched_at: datetime


def _parse_date(val: date | str | None) -> date | None:
    if val is None or isinstance(val, date):
        return val
    val_str = str(val).strip()
    if not val_str:
        return None
    if len(val_str) == 8 and val_str.isdigit():
        return datetime.strptime(val_str, "%Y%m%d").date()
    return date.fromisoformat(val_str[:10])


def build_public_items(
    start: date | str | None = None,
    end: date | str | None = None,
    *,
    failed_purchases_file: str | Path | None = DEFAULT_FAILED_PURCHASES_FILE,
    on_error: Callable[[str], None] | None = None,
) -> BuildResult:
    """Build or update PublicItem records from latest RawRecords idempotently in streaming mode."""
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    has_date_filter = start_date is not None or end_date is not None

    pub_lookup: dict[tuple[str, int, int], _PubMetadata] = {}

    # 1. Deduplicate publication records and index by (cnpj, ano, seq)
    pub_qs = (
        RawRecord.objects.filter(endpoint__startswith=PUB_ENDPOINT)
        .values_list("id", "fetched_at", "payload")
        .iterator(chunk_size=500)
    )
    for rec_id, fetched_at, payload in pub_qs:
        if not isinstance(payload, dict):
            continue
        data = payload.get("data", [])
        if not isinstance(data, list):
            continue
        for pub in data:
            if not isinstance(pub, dict):
                continue
            orgao = pub.get("orgaoEntidade") or {}
            cnpj = orgao.get("cnpj") if isinstance(orgao, dict) else None
            ano = pub.get("anoCompra")
            seq = pub.get("sequencialCompra")
            if not cnpj or ano is None or seq is None:
                continue
            key = (str(cnpj), int(ano), int(seq))
            pub_date_str = pub.get("dataPublicacaoPncp")
            if not pub_date_str:
                continue
            try:
                pub_date = datetime.fromisoformat(str(pub_date_str)[:10]).date()
            except Exception:
                continue

            if start_date and pub_date < start_date:
                continue
            if end_date and pub_date > end_date:
                continue

            agency_name = (orgao.get("razaoSocial") or "") if isinstance(orgao, dict) else ""
            agency_cnpj = str(cnpj)
            unidade = pub.get("unidadeOrgao") or {}
            state = str(unidade.get("ufSigla") or "").strip() if isinstance(unidade, dict) else ""
            try:
                modality = int(pub.get("modalidadeId", 0) or 0)
            except Exception:
                modality = 0
            if not state or modality <= 0:
                continue

            prev = pub_lookup.get(key)
            if prev is None or (fetched_at, rec_id) > (prev.fetched_at, prev.raw_record_id):
                pub_lookup[key] = _PubMetadata(
                    pub_date, agency_name, agency_cnpj, state, modality, rec_id, fetched_at
                )

    # 1b. Support single purchase endpoint records: /orgaos/{cnpj}/compras/{ano}/{seq}
    single_pub_qs = (
        RawRecord.objects.filter(endpoint__startswith="/api/consulta/v1/orgaos/")
        .values_list("id", "endpoint", "fetched_at", "payload")
        .iterator(chunk_size=500)
    )
    for rec_id, endpoint, fetched_at, payload in single_pub_qs:
        m = PURCHASE_ENDPOINT_PATTERN.match(endpoint)
        if not m:
            continue
        if not isinstance(payload, dict):
            continue
        key = (str(m.group("cnpj")), int(m.group("ano")), int(m.group("seq")))
        pub_date_str = payload.get("dataPublicacaoPncp")
        if not pub_date_str:
            continue
        try:
            pub_date = datetime.fromisoformat(str(pub_date_str)[:10]).date()
        except Exception:
            continue

        if start_date and pub_date < start_date:
            continue
        if end_date and pub_date > end_date:
            continue

        orgao = payload.get("orgaoEntidade") or {}
        agency_name = (orgao.get("razaoSocial") or "") if isinstance(orgao, dict) else ""
        agency_cnpj = str(key[0])
        unidade = payload.get("unidadeOrgao") or {}
        state = str(unidade.get("ufSigla") or "").strip() if isinstance(unidade, dict) else ""
        try:
            modality = int(payload.get("modalidadeId", 0) or 0)
        except Exception:
            modality = 0
        if not state or modality <= 0:
            continue

        prev = pub_lookup.get(key)
        if prev is None or (fetched_at, rec_id) > (prev.fetched_at, prev.raw_record_id):
            pub_lookup[key] = _PubMetadata(
                pub_date, agency_name, agency_cnpj, state, modality, rec_id, fetched_at
            )

    built_count = 0
    skipped_without_publication = 0
    failed_count = 0
    failed_path = Path(failed_purchases_file) if failed_purchases_file else None
    failed_handle = None

    def _process_single_purchase(
        purchase_key: tuple[str, int, int],
        p_item_records: list[RawRecord],
        p_result_records: list[tuple[int, RawRecord]],
    ):
        nonlocal built_count, skipped_without_publication

        pub = pub_lookup.get(purchase_key)
        if pub is None:
            if has_date_filter:
                return
            deduped_items = latest_copies(p_item_records)
            total_skipped = sum(
                len(r.payload) for r in deduped_items if isinstance(r.payload, list)
            )
            skipped_without_publication += total_skipped
            return

        cnpj, ano, seq = purchase_key
        deduped_item_records = latest_copies(p_item_records)

        results_by_item: dict[int, list[RawRecord]] = defaultdict(list)
        for item_num, res_rec in p_result_records:
            results_by_item[item_num].append(res_rec)

        result_lookup: dict[int, tuple[Decimal | None, RawRecord]] = {}
        for item_num, recs in results_by_item.items():
            deduped_res = latest_copies(recs)
            if not deduped_res:
                continue
            res_rec = deduped_res[0]
            valid_res = select_valid_result(res_rec.payload)
            awarded_price = None
            if valid_res:
                val = valid_res.get("valorUnitarioHomologado")
                if val is not None:
                    with suppress(Exception):
                        awarded_price = Decimal(str(val))
            result_lookup[item_num] = (awarded_price, res_rec)

        parsed_items: dict[int, tuple[dict[str, Any], list[int]]] = {}
        for r in deduped_item_records:
            if not isinstance(r.payload, list):
                continue
            for item in r.payload:
                if not isinstance(item, dict):
                    continue
                num_raw = item.get("numeroItem")
                if num_raw is None:
                    continue
                try:
                    num_item = int(num_raw)
                except Exception:
                    continue

                description = str(item.get("descricao") or "")
                unit = str(item.get("unidadeMedida") or "")[:50]
                unit_normalized = normalize_unit(unit)
                try:
                    quantity = Decimal(str(item.get("quantidade") or 0))
                except Exception:
                    quantity = Decimal("0.0000")
                try:
                    estimated_price = Decimal(str(item.get("valorUnitarioEstimado") or 0))
                except Exception:
                    estimated_price = Decimal("0.0000")
                has_result = bool(item.get("temResultado", False))
                secret_budget = bool(item.get("orcamentoSigiloso", False))
                item_kind = map_item_kind(
                    item.get("materialOuServico"),
                    item.get("materialOuServicoNome"),
                )

                awarded_price, res_rec = result_lookup.get(num_item, (None, None))
                provenance_ids = [r.id, pub.raw_record_id]
                if res_rec is not None and res_rec.id:
                    provenance_ids.append(res_rec.id)

                defaults = {
                    "description": description,
                    "unit": unit,
                    "unit_normalized": unit_normalized,
                    "quantity": quantity,
                    "estimated_unit_price": estimated_price,
                    "awarded_unit_price": awarded_price,
                    "has_result": has_result,
                    "secret_budget": secret_budget,
                    "published_on": pub.published_on,
                    "agency_name": pub.agency_name,
                    "agency_cnpj": pub.agency_cnpj,
                    "state": pub.state,
                    "modality": pub.modality,
                    "item_kind": item_kind,
                }
                parsed_items[num_item] = (defaults, provenance_ids)

        if not parsed_items:
            with transaction.atomic():
                PublicItem.objects.filter(cnpj=cnpj, year=ano, purchase_sequence=seq).delete()
            return

        with transaction.atomic():
            existing = {
                it.item_number: it
                for it in PublicItem.objects.filter(cnpj=cnpj, year=ano, purchase_sequence=seq)
            }
            to_create: list[PublicItem] = []
            to_update: list[PublicItem] = []

            for num_item, (defaults, _) in parsed_items.items():
                if num_item in existing:
                    it = existing[num_item]
                    for field, val in defaults.items():
                        setattr(it, field, val)
                    to_update.append(it)
                else:
                    to_create.append(
                        PublicItem(
                            cnpj=cnpj,
                            year=ano,
                            purchase_sequence=seq,
                            item_number=num_item,
                            **defaults,
                        )
                    )

            if to_create:
                PublicItem.objects.bulk_create(to_create)
            if to_update:
                PublicItem.objects.bulk_update(
                    to_update,
                    fields=[
                        "description",
                        "unit",
                        "unit_normalized",
                        "quantity",
                        "estimated_unit_price",
                        "awarded_unit_price",
                        "has_result",
                        "secret_budget",
                        "published_on",
                        "agency_name",
                        "agency_cnpj",
                        "state",
                        "modality",
                        "item_kind",
                    ],
                )

            Through = PublicItem.raw_records.through
            all_items = to_create + to_update
            all_pks = [it.pk for it in all_items]
            Through.objects.filter(publicitem_id__in=all_pks).delete()

            through_rows = []
            for it in all_items:
                _, prov_ids = parsed_items[it.item_number]
                for raw_id in prov_ids:
                    through_rows.append(Through(publicitem_id=it.pk, rawrecord_id=raw_id))
            if through_rows:
                Through.objects.bulk_create(through_rows)

            stale_pks = [it.pk for num, it in existing.items() if num not in parsed_items]
            if stale_pks:
                PublicItem.objects.filter(pk__in=stale_pks).delete()

        built_count += len(parsed_items)

    def _run_purchase(
        purchase_key: tuple[str, int, int],
        p_item_records: list[RawRecord],
        p_result_records: list[tuple[int, RawRecord]],
    ) -> None:
        nonlocal failed_count, failed_handle

        try:
            _process_single_purchase(purchase_key, p_item_records, p_result_records)
        except Exception as exc:
            failed_count += 1
            cnpj, ano, seq = purchase_key
            pncp_key = f"{cnpj}/{ano}/{seq}"
            exc_name = exc.__class__.__name__
            msg = f"Failed building purchase {pncp_key} ({exc_name}): {exc}"
            logger.exception(msg)
            if on_error is not None:
                on_error(msg)
            if failed_path is not None:
                if failed_handle is None:
                    failed_path.parent.mkdir(parents=True, exist_ok=True)
                    failed_handle = failed_path.open("a", encoding="utf-8")
                failed_rec = {
                    "timestamp": timezone.now().isoformat(),
                    "purchase_key": [str(cnpj), int(ano), int(seq)],
                    "pncp_key": pncp_key,
                    "exception_class": exc_name,
                    "error": str(exc),
                }
                failed_handle.write(json.dumps(failed_rec) + "\n")
                failed_handle.flush()

    records_qs = (
        RawRecord.objects.filter(endpoint__startswith=RAW_ITEM_PREFIX)
        .order_by("endpoint")
        .iterator(chunk_size=1000)
    )

    current_key: tuple[str, int, int] | None = None
    current_item_records: list[RawRecord] = []
    current_result_records: list[tuple[int, RawRecord]] = []

    try:
        for r in records_qs:
            m = PURCHASE_KEY_PATTERN.match(r.endpoint)
            if not m:
                continue
            purchase_key = (str(m.group("cnpj")), int(m.group("ano")), int(m.group("seq")))
            if purchase_key != current_key:
                if current_key is not None:
                    _run_purchase(current_key, current_item_records, current_result_records)
                    current_item_records.clear()
                    current_result_records.clear()
                current_key = purchase_key

            item_str = m.group("item")
            if item_str is None:
                current_item_records.append(r)
            else:
                current_result_records.append((int(item_str), r))

        if current_key is not None:
            _run_purchase(current_key, current_item_records, current_result_records)
    finally:
        if failed_handle is not None:
            failed_handle.close()

    recorded_file = str(failed_path) if failed_count > 0 and failed_path is not None else None
    return BuildResult(
        built_count,
        skipped_without_publication,
        failed_count,
        recorded_file,
    )
