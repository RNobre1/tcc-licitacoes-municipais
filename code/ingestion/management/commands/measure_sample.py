import json
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from ingestion.metrics import (
    distinct_units,
    median_description_length,
    missing_share,
    volume_per_day,
)
from ingestion.models import RawRecord


def _deduplicate_records(records: list[RawRecord]) -> list[RawRecord]:
    """Keep the record with latest fetched_at for each (endpoint, canonical_params)."""
    latest_by_key: dict[tuple[str, str], RawRecord] = {}
    for r in records:
        canonical_params = json.dumps(r.params, sort_keys=True) if r.params is not None else ""
        key = (r.endpoint, canonical_params)
        if key not in latest_by_key or r.fetched_at > latest_by_key[key].fetched_at:
            latest_by_key[key] = r
    return list(latest_by_key.values())


class Command(BaseCommand):
    help = "Measure exploratory metrics on ingested PNCP sample."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            required=True,
            help="Start date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--end",
            required=True,
            help="End date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--uf",
            default="PA",
            help="Federative Unit code (default: PA)",
        )
        parser.add_argument(
            "--modality",
            type=int,
            default=6,
            help="Procurement modality code (default: 6 for Pregão Eletrônico)",
        )

    def handle(self, *args, **options):
        start_str = options["start"]
        end_str = options["end"]

        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError as exc:
            raise CommandError("Dates must be in YYYY-MM-DD format") from exc

        if start_dt > end_dt:
            raise CommandError("Start date cannot be after end date")

        data_inicial = start_dt.strftime("%Y%m%d")
        data_final = end_dt.strftime("%Y%m%d")
        uf = options.get("uf")
        modality = options.get("modality")

        # 1. Filter publication records matching the window
        all_pub_records = list(
            RawRecord.objects.filter(endpoint="/api/consulta/v1/contratacoes/publicacao")
        )

        matched_pub_records: list[RawRecord] = []
        for r in all_pub_records:
            params = r.params or {}
            if (
                params.get("dataInicial") == data_inicial
                and params.get("dataFinal") == data_final
                and (uf is None or params.get("uf") == uf)
                and (
                    modality is None
                    or str(params.get("codigoModalidadeContratacao")) == str(modality)
                )
            ):
                matched_pub_records.append(r)

        # Deduplicate publication pages (one per page: latest fetched_at)
        dedup_pub_records = _deduplicate_records(matched_pub_records)
        dedup_pub_records.sort(key=lambda r: (r.params or {}).get("pagina", 1))

        # 2. Extract publications and build item endpoint targets
        publications: list[dict[str, Any]] = []
        target_item_endpoints: set[str] = set()

        for page in dedup_pub_records:
            data = page.payload.get("data", []) if isinstance(page.payload, dict) else []
            if isinstance(data, list):
                for pub in data:
                    if isinstance(pub, dict):
                        publications.append(pub)
                        cnpj = pub.get("orgaoEntidade", {}).get("cnpj")
                        ano = pub.get("anoCompra")
                        seq = pub.get("sequencialCompra")
                        if cnpj and ano and seq is not None:
                            target_item_endpoints.add(
                                f"/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens"
                            )

        # 3. Filter item records matching the target endpoints
        matched_item_records = list(RawRecord.objects.filter(endpoint__in=target_item_endpoints))
        dedup_item_records = _deduplicate_records(matched_item_records)
        dedup_item_records.sort(key=lambda r: (r.endpoint, (r.params or {}).get("pagina", 1)))

        # 4. Extract items
        items: list[dict[str, Any]] = []
        for page in dedup_item_records:
            if isinstance(page.payload, list):
                for item in page.payload:
                    if isinstance(item, dict):
                        items.append(item)

        # 5. Calculate metrics
        vol_per_day = volume_per_day(publications)

        fields_to_check = [
            "descricao",
            "quantidade",
            "unidadeMedida",
            "valorUnitarioEstimado",
        ]
        missing_shares = {field: missing_share(items, field) for field in fields_to_check}
        med_desc_len = median_description_length(items)
        dist_units = distinct_units(items)

        # 6. Fetch time range across selected records
        all_selected_records = dedup_pub_records + dedup_item_records
        if all_selected_records:
            min_fetched_at = min(r.fetched_at for r in all_selected_records).isoformat()
            max_fetched_at = max(r.fetched_at for r in all_selected_records).isoformat()
            if min_fetched_at == max_fetched_at:
                fetch_time_str = min_fetched_at
            else:
                fetch_time_str = f"{min_fetched_at} to {max_fetched_at}"
        else:
            fetch_time_str = "N/A"

        # 7. Print deterministic report
        self.stdout.write("=== Sample Measurement Report ===")
        self.stdout.write(f"Window: {start_str} to {end_str}")
        self.stdout.write(f"UF: {uf}")
        self.stdout.write(f"Modality: {modality}")
        self.stdout.write(f"Fetch time: {fetch_time_str}\n")

        self.stdout.write("Counts:")
        self.stdout.write(f"  Publications: {len(publications)}")
        self.stdout.write(f"  Item pages: {len(dedup_item_records)}")
        self.stdout.write(f"  Items: {len(items)}\n")

        self.stdout.write("Volume per day:")
        for dt, count in sorted(vol_per_day.items()):
            self.stdout.write(f"  {dt.isoformat()}: {count}")
        if not vol_per_day:
            self.stdout.write("  (none)")
        self.stdout.write("")

        self.stdout.write("Missing share:")
        for field in sorted(missing_shares.keys()):
            share = missing_shares[field]
            share_str = f"{share:.4f}" if share is not None else "N/A"
            self.stdout.write(f"  {field}: {share_str}")
        self.stdout.write("")

        self.stdout.write("Item metrics:")
        med_str = f"{med_desc_len:.1f}" if med_desc_len is not None else "N/A"
        self.stdout.write(f"  Median description length: {med_str}")
        self.stdout.write(f"  Distinct units: {dist_units}")
