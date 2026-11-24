import json
import re
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db import transaction

from ingestion.models import PublicItem, RawRecord

PUB_ENDPOINT = "/api/consulta/v1/contratacoes/publicacao"
ITEM_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens$"
)
RESULT_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens/(?P<item>\d+)/resultados$"
)


def _deduplicate_raw_records(records: Sequence[RawRecord]) -> list[RawRecord]:
    """Keep the newest RawRecord for each (endpoint, canonical_params)."""
    latest: dict[tuple[str, str], RawRecord] = {}
    for r in records:
        params_key = json.dumps(r.params, sort_keys=True) if r.params is not None else ""
        key = (r.endpoint, params_key)
        if key not in latest:
            latest[key] = r
        else:
            prev = latest[key]
            if (r.fetched_at, r.id or 0) > (prev.fetched_at, prev.id or 0):
                latest[key] = r
    return list(latest.values())


def build_public_items() -> int:
    """Build or update PublicItem records from the latest RawRecords idempotently."""
    # 1. Deduplicate publication records and index by (cnpj, ano, seq)
    pub_records = _deduplicate_raw_records(
        list(RawRecord.objects.filter(endpoint__startswith=PUB_ENDPOINT))
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
                # Newest pub record wins
                if key not in pub_lookup:
                    pub_lookup[key] = (pub, r)
                else:
                    _, existing_rec = pub_lookup[key]
                    if (r.fetched_at, r.id or 0) > (existing_rec.fetched_at, existing_rec.id or 0):
                        pub_lookup[key] = (pub, r)

    # 2. Deduplicate results records and index by (cnpj, ano, seq, numero_item)
    all_result_raw = [
        r for r in RawRecord.objects.all() if RESULT_ENDPOINT_PATTERN.match(r.endpoint)
    ]
    res_records = _deduplicate_raw_records(all_result_raw)

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
        if isinstance(r.payload, list) and r.payload:
            first_res = r.payload[0]
            if isinstance(first_res, dict):
                val = first_res.get("valorUnitarioHomologado")
                if val is not None:
                    try:
                        awarded_price = Decimal(str(val))
                    except Exception:
                        awarded_price = None

        key = (cnpj, ano, seq, item_num)
        result_lookup[key] = (awarded_price, r)

    # 3. Deduplicate item page records
    all_item_raw = [r for r in RawRecord.objects.all() if ITEM_ENDPOINT_PATTERN.match(r.endpoint)]
    item_records = _deduplicate_raw_records(all_item_raw)

    built_count = 0

    with transaction.atomic():
        for r in item_records:
            match = ITEM_ENDPOINT_PATTERN.match(r.endpoint)
            if not match:
                continue
            cnpj = match.group("cnpj")
            ano = int(match.group("ano"))
            seq = int(match.group("seq"))

            if not isinstance(r.payload, list):
                continue

            pub_data, pub_rec = pub_lookup.get((cnpj, ano, seq), ({}, None))

            # Publication metadata
            published_on_date = date.today()
            pub_date_str = pub_data.get("dataPublicacaoPncp")
            if pub_date_str:
                try:
                    published_on_date = datetime.fromisoformat(str(pub_date_str)[:10]).date()
                except Exception:
                    published_on_date = date.today()

            agency_name = pub_data.get("orgaoEntidade", {}).get("razaoSocial", "")
            state = pub_data.get("unidadeOrgao", {}).get("ufSigla", "")
            try:
                modality = int(pub_data.get("modalidadeId", 0))
            except Exception:
                modality = 0

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

                description = str(item.get("descricao") or "")
                unit = str(item.get("unidadeMedida") or "")
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
                mat_serv = str(item.get("materialOuServico") or "").upper()
                mat_serv_nome = str(item.get("materialOuServicoNome") or "").lower()
                if mat_serv == "S" or "serviço" in mat_serv_nome:
                    item_kind = "service"
                else:
                    item_kind = "product"

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

    return built_count
