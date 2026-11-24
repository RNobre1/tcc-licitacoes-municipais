"""Management command to resolve ground-truth records in PNCP."""

import json
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from evaluation.ground_truth import match_ground_truth_item, resolve_purchase_items
from ingestion.client import ItemCountMismatchError, PncpResponseError
from ingestion.models import RawRecord


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = "Resolve ground-truth chosen prices in PNCP via ingestion client."

    def add_arguments(self, parser):
        parser.add_argument(
            "--eval-dir",
            type=str,
            default="/Users/rnobre/Documents/UFOPA/Projetos Codigo/TCC/dados-dominio/avaliacao/",
            help="Directory containing the parsed evaluation JSON files.",
        )
        parser.add_argument(
            "--skip-fetch",
            action="store_true",
            help="Skip fetching and resolve only from existing database RawRecords.",
        )

    def handle(self, *args, **options):
        eval_dir = Path(options["eval_dir"])
        skip_fetch = options["skip_fetch"]

        report_files = sorted(eval_dir.glob("105588_Cotacao_*.json"))
        if not report_files:
            # check for any other json if test environment
            report_files = sorted(
                f for f in eval_dir.glob("*.json") if f.name != "ground_truth_resolved.json"
            )

        self.stdout.write(f"Found {len(report_files)} report JSON file(s).")

        # Collect all PNCP keys across reports
        # purchase_key: (cnpj, ano, sequencial) -> list of reference dicts
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
                        p_key = (k["cnpj"], k["ano"], k["sequencial"])
                        purchases.setdefault(p_key, []).append(
                            {
                                "report_id": report_id,
                                "requested_item_number": item_number,
                                "price_number": price["price_number"],
                                "numero_item": k["numero_item"],
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

        for idx, ((cnpj, ano, sequencial), refs) in enumerate(purchases.items(), start=1):
            endpoint = f"/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
            records = list(RawRecord.objects.filter(endpoint=endpoint))

            if not records and not skip_fetch:
                self.stdout.write(
                    f"[{idx}/{len(purchases)}] Fetching PNCP items for {cnpj}/{ano}/{sequencial}..."
                )
                try:
                    records = resolve_purchase_items(cnpj, ano, sequencial, save=True)
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
                            "ano": ano,
                            "sequencial": sequencial,
                            "numero_item": ref["numero_item"],
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
                            "ano": ano,
                            "sequencial": sequencial,
                            "numero_item": ref["numero_item"],
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
                        "ano": ano,
                        "sequencial": sequencial,
                        "numero_item": ref["numero_item"],
                        "found": False,
                        "failure_cause": cause,
                    }
                continue

            for ref in refs:
                res = match_ground_truth_item(
                    cnpj=cnpj,
                    ano=ano,
                    sequencial=sequencial,
                    numero_item=ref["numero_item"],
                    records=records,
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
