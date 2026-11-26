"""Management command to resolve ground-truth records in PNCP."""

import json
import os
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from evaluation.ground_truth import match_ground_truth_item, resolve_purchase_items
from ingestion.client import ItemCountMismatchError, PncpResponseError
from ingestion.models import RawRecord
from ingestion.raw_records import latest_copies


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = "Resolve ground-truth chosen prices in PNCP via ingestion client."

    def add_arguments(self, parser):
        default_eval_dir = os.environ.get("EVALUATION_DATA_DIR") or str(
            Path(settings.BASE_DIR).parent / "dados-dominio" / "avaliacao"
        )
        parser.add_argument(
            "--eval-dir",
            type=str,
            default=default_eval_dir,
            help="Directory containing the parsed evaluation JSON files.",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            required=True,
            help="Filename glob pattern for report JSON files.",
        )
        parser.add_argument(
            "--skip-fetch",
            action="store_true",
            help="Skip fetching and resolve only from existing database RawRecords.",
        )

    def handle(self, *args, **options):
        eval_dir = Path(options["eval_dir"])
        skip_fetch = options["skip_fetch"]
        pattern = options["pattern"]

        report_files = sorted(eval_dir.glob(pattern))
        if not report_files:
            # fallback for general test environment
            report_files = sorted(
                f for f in eval_dir.glob("*.json") if f.name != "ground_truth_resolved.json"
            )

        self.stdout.write(f"Found {len(report_files)} report JSON file(s).")

        # Collect all PNCP keys across reports
        # purchase_key: (cnpj, year, purchase_sequence) -> list of reference dicts
        purchases: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
        total_pncp_references = 0

        for r_file in report_files:
            data = json.loads(r_file.read_text(encoding="utf-8"))
            report_id = data.get("report_id", r_file.stem)
            for item in data.get("items", []):
                item_number = item["item_number"]
                for price in item.get("chosen_prices", []):
                    k = price.get("pncp_key")
                    if k:
                        total_pncp_references += 1
                        year_val = k.get("year", k.get("ano"))
                        seq_val = k.get("purchase_sequence", k.get("sequencial"))
                        item_num_val = k.get("item_number", k.get("numero_item"))
                        p_key = (str(k["cnpj"]), int(year_val), int(seq_val))
                        purchases.setdefault(p_key, []).append(
                            {
                                "report_id": report_id,
                                "requested_item_number": item_number,
                                "price_number": price["price_number"],
                                "item_number": int(item_num_val),
                            }
                        )

        self.stdout.write(
            f"Collected {total_pncp_references} PNCP price references across "
            f"{len(purchases)} distinct purchases."
        )

        resolved_records = 0
        failed_records = 0
        failures_by_cause: dict[str, int] = {}
        resolved_items_map: dict[str, Any] = {}

        for idx, ((cnpj, year, purchase_sequence), refs) in enumerate(purchases.items(), start=1):
            endpoint = f"/api/pncp/v1/orgaos/{cnpj}/compras/{year}/{purchase_sequence}/itens"
            records = list(RawRecord.objects.filter(endpoint=endpoint))

            if not records and not skip_fetch:
                self.stdout.write(
                    f"[{idx}/{len(purchases)}] Fetching PNCP items for "
                    f"{cnpj}/{year}/{purchase_sequence}..."
                )
                try:
                    records = resolve_purchase_items(
                        cnpj=cnpj,
                        year=year,
                        purchase_sequence=purchase_sequence,
                        save=True,
                    )
                except (PncpResponseError, ItemCountMismatchError) as err:
                    cause = f"fetch_error_{type(err).__name__}"
                    self.stderr.write(f"  Error fetching {endpoint}: {err}")
                    for ref in refs:
                        failed_records += 1
                        failures_by_cause[cause] = failures_by_cause.get(cause, 0) + 1
                        ref_key = (
                            f"{ref['report_id']}_it{ref['requested_item_number']}"
                            f"_p{ref['price_number']}"
                        )
                        resolved_items_map[ref_key] = {
                            "cnpj": cnpj,
                            "year": year,
                            "purchase_sequence": purchase_sequence,
                            "item_number": ref["item_number"],
                            "found": False,
                            "failure_cause": str(err),
                        }
                    continue
                except Exception as err:
                    cause = f"unexpected_error_{type(err).__name__}"
                    self.stderr.write(f"  Unexpected error for {endpoint}: {err}")
                    for ref in refs:
                        failed_records += 1
                        failures_by_cause[cause] = failures_by_cause.get(cause, 0) + 1
                        ref_key = (
                            f"{ref['report_id']}_it{ref['requested_item_number']}"
                            f"_p{ref['price_number']}"
                        )
                        resolved_items_map[ref_key] = {
                            "cnpj": cnpj,
                            "year": year,
                            "purchase_sequence": purchase_sequence,
                            "item_number": ref["item_number"],
                            "found": False,
                            "failure_cause": str(err),
                        }
                    continue

                # Be polite to public API
                time.sleep(0.05)

            if not records:
                cause = "purchase_not_in_database_and_skip_fetch_true"
                for ref in refs:
                    failed_records += 1
                    failures_by_cause[cause] = failures_by_cause.get(cause, 0) + 1
                    ref_key = (
                        f"{ref['report_id']}_it{ref['requested_item_number']}"
                        f"_p{ref['price_number']}"
                    )
                    resolved_items_map[ref_key] = {
                        "cnpj": cnpj,
                        "year": year,
                        "purchase_sequence": purchase_sequence,
                        "item_number": ref["item_number"],
                        "found": False,
                        "failure_cause": cause,
                    }
                continue

            deduped_records = latest_copies(records)

            for ref in refs:
                item_num = ref["item_number"]
                res_endpoint = (
                    f"/api/pncp/v1/orgaos/{cnpj}/compras/{year}/{purchase_sequence}"
                    f"/itens/{item_num}/resultados"
                )
                result_records = list(RawRecord.objects.filter(endpoint=res_endpoint))

                res = match_ground_truth_item(
                    cnpj=cnpj,
                    year=year,
                    purchase_sequence=purchase_sequence,
                    item_number=item_num,
                    item_records=deduped_records,
                    result_records=result_records,
                )
                ref_key = (
                    f"{ref['report_id']}_it{ref['requested_item_number']}_p{ref['price_number']}"
                )
                resolved_items_map[ref_key] = asdict(res)
                if res.found:
                    resolved_records += 1
                else:
                    failed_records += 1
                    cause = res.failure_cause or "unknown"
                    failures_by_cause[cause] = failures_by_cause.get(cause, 0) + 1

        summary = {
            "total_pncp_references": total_pncp_references,
            "resolved_records": resolved_records,
            "failed_records": failed_records,
            "failures_by_cause": failures_by_cause,
        }

        out_data = {
            "summary": summary,
            "resolved_items": resolved_items_map,
        }

        out_path = eval_dir / "ground_truth_resolved.json"
        out_path.write_text(
            json.dumps(out_data, indent=2, ensure_ascii=False, cls=DecimalEncoder),
            encoding="utf-8",
        )

        self.stdout.write(
            f"Ground truth resolution finished: {resolved_records} resolved, "
            f"{failed_records} failed. Written to {out_path}"
        )
        if failures_by_cause:
            self.stdout.write(f"Failures by cause: {failures_by_cause}")
