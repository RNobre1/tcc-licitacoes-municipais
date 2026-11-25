import re
from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db import transaction

from ingestion.item_kind import map_item_kind
from ingestion.models import PublicItem, RawRecord
from ingestion.raw_records import latest_copies
from ingestion.results import select_valid_result

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


class BuildResult(int):
    """Integer subclass carrying build metadata counts."""

    built_count: int
    skipped_without_publication: int

    def __new__(cls, built_count: int, skipped_without_publication: int = 0):
        obj = super().__new__(cls, built_count)
        obj.built_count = built_count
        obj.skipped_without_publication = skipped_without_publication
        return obj


def build_public_items() -> BuildResult:
    """Build or update PublicItem records from latest RawRecords idempotently."""
    # 1. Deduplicate publication records and index by (cnpj, ano, seq)
    pub_records = latest_copies(
        list(RawRecord.objects.filter(endpoint__startswith=PUB_ENDPOINT).iterator(chunk_size=1000))
    )

    pub_lookup: dict[tuple[str, int, int], tuple[dict[str, Any], RawRecord]] = {}
    for r in pub_records:
        if not isinstance(r.payload, dict):
            continue
        data = r.payload.get("data", [])
        if not isinstance(data, list):
            continue
        for pub in data:
            if not isinstance(pub, dict):
                continue
            cnpj = pub.get("orgaoEntidade", {}).get("cnpj")
            ano = pub.get("anoCompra")
            seq = pub.get("sequencialCompra")
            if cnpj and ano is not None and seq is not None:
                key = (str(cnpj), int(ano), int(seq))
                if key not in pub_lookup:
                    pub_lookup[key] = (pub, r)
                else:
                    _, existing_rec = pub_lookup[key]
                    if (r.fetched_at, r.id or 0) > (existing_rec.fetched_at, existing_rec.id or 0):
                        pub_lookup[key] = (pub, r)

    # 1b. Support single purchase endpoint records: /orgaos/{cnpj}/compras/{ano}/{seq}
    single_purchase_raw = [
        r
        for r in RawRecord.objects.filter(endpoint__startswith="/api/consulta/v1/orgaos/").iterator(
            chunk_size=1000
        )
        if PURCHASE_ENDPOINT_PATTERN.match(r.endpoint)
    ]
    for r in latest_copies(single_purchase_raw):
        if not isinstance(r.payload, dict):
            continue
        m = PURCHASE_ENDPOINT_PATTERN.match(r.endpoint)
        if not m:
            continue
        cnpj = m.group("cnpj")
        ano = int(m.group("ano"))
        seq = int(m.group("seq"))
        key = (str(cnpj), ano, seq)
        if key not in pub_lookup:
            pub_lookup[key] = (r.payload, r)
        else:
            _, existing_rec = pub_lookup[key]
            if (r.fetched_at, r.id or 0) > (existing_rec.fetched_at, existing_rec.id or 0):
                pub_lookup[key] = (r.payload, r)

    # 2. Deduplicate results records and index by (cnpj, ano, seq, numero_item)
    all_result_raw = [
        r
        for r in RawRecord.objects.filter(endpoint__startswith="/api/pncp/v1/orgaos/").iterator(
            chunk_size=1000
        )
        if RESULT_ENDPOINT_PATTERN.match(r.endpoint)
    ]
    res_records = latest_copies(all_result_raw)

    result_lookup: dict[tuple[str, int, int, int], tuple[Decimal | None, RawRecord]] = {}
    for r in res_records:
        match = RESULT_ENDPOINT_PATTERN.match(r.endpoint)
        if not match:
            continue
        cnpj = match.group("cnpj")
        ano = int(match.group("ano"))
        seq = int(match.group("seq"))
        item_num = int(match.group("item"))

        awarded_price: Decimal | None = None
        valid_res = select_valid_result(r.payload)
        if valid_res:
            val = valid_res.get("valorUnitarioHomologado")
            if val is not None:
                with suppress(Exception):
                    awarded_price = Decimal(str(val))

        key = (cnpj, ano, seq, item_num)
        result_lookup[key] = (awarded_price, r)

    # 3. Deduplicate item page records and group by purchase
    all_item_raw = [
        r
        for r in RawRecord.objects.filter(endpoint__startswith="/api/pncp/v1/orgaos/").iterator(
            chunk_size=1000
        )
        if ITEM_ENDPOINT_PATTERN.match(r.endpoint)
    ]
    item_records = latest_copies(all_item_raw)

    records_by_purchase: dict[tuple[str, int, int], list[RawRecord]] = defaultdict(list)
    for r in item_records:
        match = ITEM_ENDPOINT_PATTERN.match(r.endpoint)
        if match:
            cnpj = match.group("cnpj")
            ano = int(match.group("ano"))
            seq = int(match.group("seq"))
            records_by_purchase[(cnpj, ano, seq)].append(r)

    built_count = 0
    skipped_without_publication = 0

    with transaction.atomic():
        for (cnpj, ano, seq), p_records in records_by_purchase.items():
            pub_data, pub_rec = pub_lookup.get((cnpj, ano, seq), (None, None))

            # B1: An item with no publication metadata is NEVER built
            if not pub_data or not isinstance(pub_data, dict):
                total_skipped = sum(
                    len(r.payload) for r in p_records if isinstance(r.payload, list)
                )
                skipped_without_publication += total_skipped
                continue

            pub_date_str = pub_data.get("dataPublicacaoPncp")
            if not pub_date_str:
                total_skipped = sum(
                    len(r.payload) for r in p_records if isinstance(r.payload, list)
                )
                skipped_without_publication += total_skipped
                continue

            try:
                published_on_date = datetime.fromisoformat(str(pub_date_str)[:10]).date()
            except Exception:
                total_skipped = sum(
                    len(r.payload) for r in p_records if isinstance(r.payload, list)
                )
                skipped_without_publication += total_skipped
                continue

            agency_name = pub_data.get("orgaoEntidade", {}).get("razaoSocial", "")
            state = pub_data.get("unidadeOrgao", {}).get("ufSigla", "")
            try:
                modality = int(pub_data.get("modalidadeId", 0))
            except Exception:
                modality = 0

            current_purchase_item_numbers: set[int] = set()

            for r in p_records:
                if not isinstance(r.payload, list):
                    continue

                for item in r.payload:
                    if not isinstance(item, dict):
                        continue
                    num_item_raw = item.get("numeroItem")
                    if num_item_raw is None:
                        continue
                    try:
                        num_item = int(num_item_raw)
                    except Exception:
                        continue

                    current_purchase_item_numbers.add(num_item)

                    description = str(item.get("descricao") or "")
                    # N9: truncate unit to 50 chars to survive long values gracefully
                    unit = str(item.get("unidadeMedida") or "")[:50]
                    try:
                        quantity = Decimal(str(item.get("quantidade") or 0))
                    except Exception:
                        quantity = Decimal("0.0000")

                    try:
                        estimated_price = Decimal(str(item.get("valorUnitarioEstimado") or 0))
                    except Exception:
                        estimated_price = Decimal("0.0000")

                    secret_budget = bool(item.get("orcamentoSigiloso", False))

                    # materialOuServico -> item_kind ("product" or "service")
                    item_kind = map_item_kind(
                        item.get("materialOuServico"),
                        item.get("materialOuServicoNome"),
                    )

                    # Check results
                    res_key = (cnpj, ano, seq, num_item)
                    awarded_price, res_rec = result_lookup.get(res_key, (None, None))

                    public_item, _ = PublicItem.objects.update_or_create(
                        cnpj=cnpj,
                        year=ano,
                        purchase_sequence=seq,
                        item_number=num_item,
                        defaults={
                            "description": description,
                            "unit": unit,
                            "quantity": quantity,
                            "estimated_unit_price": estimated_price,
                            "awarded_unit_price": awarded_price,
                            "secret_budget": secret_budget,
                            "published_on": published_on_date,
                            "agency_name": agency_name,
                            "agency_cnpj": cnpj,
                            "state": state,
                            "modality": modality,
                            "item_kind": item_kind,
                        },
                    )

                    provenance = [r]
                    if pub_rec is not None:
                        provenance.append(pub_rec)
                    if res_rec is not None:
                        provenance.append(res_rec)

                    public_item.raw_records.set(provenance)
                    built_count += 1

            # N2: Drop stale items that are no longer present in the newest pages of this purchase
            PublicItem.objects.filter(cnpj=cnpj, year=ano, purchase_sequence=seq).exclude(
                item_number__in=current_purchase_item_numbers
            ).delete()

    return BuildResult(built_count, skipped_without_publication)
