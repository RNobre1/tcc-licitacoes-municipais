"""Management command to run evaluation benchmarks."""

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    FakeDeterministicEmbeddingModel,
    PublicItemSim,
    SemanticSearchMethod,
    check_thresholds_note_guard,
    create_dataset_split,
    verify_split_hash,
)
from evaluation.parser import parse_date_br


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = "Run search benchmark against evaluation set."

    def add_arguments(self, parser):
        default_eval = os.environ.get("EVALUATION_DATA_DIR") or str(
            Path(settings.BASE_DIR).parent / "dados-dominio" / "avaliacao"
        )
        parser.add_argument(
            "--split",
            type=str,
            choices=["tuning", "measurement"],
            default="tuning",
            help="Dataset split to evaluate.",
        )
        parser.add_argument(
            "--thresholds-note",
            type=str,
            default=None,
            help="Path to decision note in TCC/decisões/ defining thresholds.",
        )
        parser.add_argument(
            "--eval-dir",
            type=str,
            default=default_eval,
            help="Evaluation directory containing JSON files.",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            default=None,
            help="Explicit filename glob pattern for parsed quotation report JSON files.",
        )
        parser.add_argument(
            "--finalist",
            type=str,
            default=None,
            help=(
                "Optional confirmation of pinned finalist method from tuning output "
                "(must match benchmark_tuning_results.json)."
            ),
        )
        parser.add_argument(
            "--tuning-output",
            type=str,
            default=None,
            help=(
                "Path to benchmark_tuning_results.json used to verify pinned finalist during "
                "measurement (defaults to <eval-dir>/benchmark_tuning_results.json)."
            ),
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Path to output JSON file.",
        )
        parser.add_argument(
            "--synthetic",
            action="store_true",
            help="Run benchmark over synthetic demo data.",
        )
        parser.add_argument(
            "--allow-real-data",
            "--go-real",
            dest="allow_real_data",
            action="store_true",
            help="Explicitly permit real benchmark execution.",
        )
        parser.add_argument(
            "-n",
            "--top-n",
            dest="top_n",
            type=int,
            default=20,
            help=(
                "Depth of screening page: number of top candidates per method to "
                "reorder with anchor (default: 20)."
            ),
        )

    def _resolve_measurement_finalist(
        self,
        eval_dir: Path,
        tuning_output: str | None,
        split_hash: str,
        cli_finalist: str | None,
    ) -> str:
        tuning_file = (
            Path(tuning_output) if tuning_output else (eval_dir / "benchmark_tuning_results.json")
        )
        if not tuning_file.is_file():
            raise CommandError(
                f"Measurement requires tuning output file (benchmark_tuning_results.json); "
                f"missing at {tuning_file}."
            )
        try:
            tuning_data = json.loads(tuning_file.read_text(encoding="utf-8"))
        except (TypeError, OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Tuning output file is invalid: {tuning_file}") from exc

        if not isinstance(tuning_data, dict):
            raise CommandError(f"Tuning output file must be a JSON object: {tuning_file}")

        if "split" in tuning_data and tuning_data.get("split") != "tuning":
            raise CommandError(f"Tuning output file must come from a tuning run: {tuning_file}")

        tuning_split_hash = tuning_data.get("split_hash")
        if not tuning_split_hash or tuning_split_hash != split_hash:
            raise CommandError(
                "Tuning output split_hash does not match the frozen dataset split hash."
            )

        tuning_finalist = tuning_data.get("finalist")
        if (
            not isinstance(tuning_finalist, str)
            or not tuning_finalist.strip()
            or tuning_finalist == "bm25"
        ):
            raise CommandError(
                f"Tuning output does not contain a valid finalist candidate: {tuning_file}"
            )

        if cli_finalist is not None and cli_finalist != tuning_finalist:
            raise CommandError(
                f"Requested --finalist '{cli_finalist}' does not match pinned tuning finalist "
                f"'{tuning_finalist}'."
            )

        return tuning_finalist

    def handle(self, *args, **options):
        split_name = options["split"]
        eval_dir = Path(options["eval_dir"])
        thresholds_note = options["thresholds_note"]
        output_path = options.get("output")
        finalist = options.get("finalist")
        tuning_output = options.get("tuning_output")
        report_pattern = options.get("pattern")
        synthetic = options["synthetic"]
        allow_real_data = options.get("allow_real_data", False)
        top_n = options.get("top_n", 20)

        # Enforce code guard for measurement split
        if split_name == "measurement":
            if not thresholds_note:
                raise CommandError(
                    "Thresholds note must be provided via --thresholds-note for measurement split"
                )
            try:
                check_thresholds_note_guard(Path(thresholds_note))
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(f"Guard passed: verified thresholds note at {thresholds_note}")

        if synthetic:
            self._handle_synthetic(
                split_name,
                eval_dir=eval_dir,
                output_path=output_path,
                finalist=finalist,
                tuning_output=tuning_output,
                top_n=top_n,
            )
        else:
            self._handle_real(
                split_name,
                eval_dir,
                output_path,
                thresholds_note,
                finalist,
                tuning_output=tuning_output,
                report_pattern=report_pattern,
                allow_real_data=allow_real_data,
                top_n=top_n,
            )

    def _handle_synthetic(
        self,
        split_name: str,
        eval_dir: Path,
        output_path: str | None,
        finalist: str | None,
        tuning_output: str | None = None,
        top_n: int = 20,
    ):
        self.stdout.write(f"Running benchmark on synthetic data ({split_name} split)...")

        synthetic_corpus = [
            PublicItemSim(
                id=1,
                description="Papel Sulfite A4 75g",
                price=Decimal("25.0"),
                unit="UNIDADE",
                published_on=date(2026, 5, 1),
                modality=6,
            ),
            PublicItemSim(
                id=2,
                description="Caneta Esferográfica Azul 1.0mm",
                price=Decimal("1.5"),
                unit="UNIDADE",
                published_on=date(2026, 5, 1),
                modality=6,
            ),
            PublicItemSim(
                id=3,
                description="Papel A4 Reciclado 500 folhas",
                price=Decimal("22.0"),
                unit="UNIDADE",
                published_on=date(2026, 5, 1),
                modality=6,
            ),
            PublicItemSim(
                id=4,
                description="Lápis Preto Grafite HB",
                price=Decimal("0.8"),
                unit="UNIDADE",
                published_on=date(2026, 5, 1),
                modality=6,
            ),
            PublicItemSim(
                id=5,
                description="Borracha Branca Escolar",
                price=Decimal("1.0"),
                unit="UNIDADE",
                published_on=date(2026, 5, 1),
                modality=6,
            ),
        ]

        synthetic_items = [
            {
                "item_id": "syn_1",
                "report_id": "rep_demo",
                "item_kind": "product",
                "description": "Papel sulfite A4 resma branca",
                "ground_truth": {1, 3},
                "chosen_prices": [Decimal("25.0")],
                "unit": "UNIDADE",
                "survey_date": date(2026, 6, 1),
            },
            {
                "item_id": "syn_2",
                "report_id": "rep_demo",
                "item_kind": "product",
                "description": "Caneta azul ponta média",
                "ground_truth": {2},
                "chosen_prices": [Decimal("1.5")],
                "unit": "UNIDADE",
                "survey_date": date(2026, 6, 1),
            },
        ]

        split = create_dataset_split(synthetic_items, tuning_fraction=0.5, seed=42)
        active_ids = (
            set(split.tuning_items) if split_name == "tuning" else set(split.measurement_items)
        )
        if split_name == "measurement":
            finalist = self._resolve_measurement_finalist(
                eval_dir=eval_dir,
                tuning_output=tuning_output,
                split_hash=split.sha256_hash,
                cli_finalist=finalist,
            )

        bm25 = BM25SearchMethod(name="bm25")
        semantic = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="semantic")

        orch = BenchmarkOrchestrator(
            n_noise_draws=200, n_bootstrap_resamples=10000, seed=42, top_n=top_n
        )
        results = orch.run_benchmark(
            items=synthetic_items,
            corpus=synthetic_corpus,
            split_name=split_name,
            active_item_ids=active_ids,
            finalist=finalist,
            candidate_methods=[semantic],
            baseline_method=bm25,
            synthetic=True,
            top_n=top_n,
        )
        results["split_hash"] = split.sha256_hash

        if output_path:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(results, indent=2, cls=DecimalEncoder), encoding="utf-8")
            self.stdout.write(f"Synthetic benchmark completed. Results written to {out_file}")
        else:
            self.stdout.write("Synthetic benchmark completed successfully.")

    def _handle_real(
        self,
        split_name: str,
        eval_dir: Path,
        output_path: str | None,
        thresholds_note: str | None,
        finalist: str | None,
        tuning_output: str | None,
        report_pattern: str | None,
        allow_real_data: bool,
        top_n: int = 20,
    ):
        if not allow_real_data:
            raise CommandError(
                "Real benchmark execution requires explicit --allow-real-data approval."
            )
        if split_name not in ("tuning", "measurement"):
            raise CommandError("Real benchmark supports only tuning or measurement split.")
        if not report_pattern:
            raise CommandError(
                "Parsed report filename pattern must be provided via --pattern for real "
                "benchmark execution."
            )

        split_file = eval_dir / "dataset_split.json"
        if not split_file.exists():
            raise CommandError("The frozen dataset split file is missing.")

        try:
            split_data = json.loads(split_file.read_text(encoding="utf-8"))
            tuning_items = split_data["tuning_items"]
            measurement_items = split_data["measurement_items"]
            split_hash = split_data["sha256_hash"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError("The frozen dataset split file is invalid.") from exc

        if not verify_split_hash(tuning_items, measurement_items, split_hash):
            raise CommandError("Dataset split file failed SHA-256 verification!")

        default_thresholds_note = (
            Path(settings.BASE_DIR).parent
            / "TCC"
            / "decisões"
            / "2026-11-24-limiares-de-aceitacao-r1-r2.md"
        )
        note_path = Path(thresholds_note) if thresholds_note else default_thresholds_note
        try:
            check_thresholds_note_guard(note_path, split_hash=split_hash)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if split_name == "measurement":
            finalist = self._resolve_measurement_finalist(
                eval_dir=eval_dir,
                tuning_output=tuning_output,
                split_hash=split_hash,
                cli_finalist=finalist,
            )

        ground_truth_path = eval_dir / "ground_truth_resolved.json"
        if not ground_truth_path.is_file():
            raise CommandError("The resolved ground-truth file is missing.")
        try:
            ground_truth_data = json.loads(ground_truth_path.read_text(encoding="utf-8"))
            resolved_items = ground_truth_data["resolved_items"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError("The resolved ground-truth file is invalid.") from exc

        target_items = tuning_items if split_name == "tuning" else measurement_items
        active_item_ids = {str(item_id) for item_id in target_items}
        if not active_item_ids:
            raise CommandError(f"The frozen {split_name} split contains no items.")

        parsed_items: dict[str, tuple[dict[str, Any], date]] = {}
        report_files = sorted(path for path in eval_dir.glob(report_pattern) if path.is_file())
        if not report_files:
            raise CommandError(
                f"No parsed report files matched pattern '{report_pattern}' in {eval_dir}."
            )
        for report_file in report_files:
            try:
                report_data = json.loads(report_file.read_text(encoding="utf-8"))
                report_id = str(report_data.get("report_id") or report_file.stem)
                survey_date = parse_date_br(report_data["survey_end"])
                report_items = report_data["items"]
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise CommandError(
                    "A parsed quotation report is invalid or has no survey date."
                ) from exc

            for report_item in report_items:
                try:
                    item_number = int(report_item["item_number"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise CommandError(
                        "A parsed quotation report contains an invalid item number."
                    ) from exc
                item_id = f"{report_id}_{item_number}"
                if item_id in active_item_ids:
                    parsed_items[item_id] = (report_item, survey_date)

        missing_parsed_items = active_item_ids.difference(parsed_items)
        if missing_parsed_items:
            raise CommandError(
                f"{len(missing_parsed_items)} {split_name} item(s) are missing from parsed reports."
            )

        ground_truth_keys_by_item: dict[str, set[tuple[str, int, int, int]]] = {}
        for reference, resolved_item in resolved_items.items():
            if not resolved_item.get("found"):
                continue
            report_id, separator, suffix = reference.rpartition("_it")
            if not separator or "_p" not in suffix:
                raise CommandError("The resolved ground-truth file has a malformed item reference.")
            item_number_text = suffix.split("_p", 1)[0]
            try:
                item_number = int(item_number_text)
                pncp_key = (
                    str(resolved_item["cnpj"]),
                    int(resolved_item["year"]),
                    int(resolved_item["purchase_sequence"]),
                    int(resolved_item["item_number"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise CommandError(
                    "The resolved ground-truth file has an invalid PNCP key."
                ) from exc
            item_id = f"{report_id}_{item_number}"
            if item_id in active_item_ids:
                ground_truth_keys_by_item.setdefault(item_id, set()).add(pncp_key)

        missing_ground_truth = active_item_ids.difference(ground_truth_keys_by_item)
        if missing_ground_truth:
            raise CommandError(
                f"{len(missing_ground_truth)} {split_name} item(s) have no resolved "
                "relevant records."
            )

        from django.db.models import Q

        from ingestion.models import PublicItem

        all_ground_truth_keys = set().union(*ground_truth_keys_by_item.values())
        key_query = Q(pk__in=[])
        for cnpj, year, purchase_sequence, item_number in all_ground_truth_keys:
            key_query |= Q(
                cnpj=cnpj,
                year=year,
                purchase_sequence=purchase_sequence,
                item_number=item_number,
            )
        public_items_by_key = {
            (item.cnpj, item.year, item.purchase_sequence, item.item_number): item.pk
            for item in PublicItem.objects.filter(key_query).only(
                "pk", "cnpj", "year", "purchase_sequence", "item_number"
            )
        }
        missing_public_items = {
            key
            for keys in ground_truth_keys_by_item.values()
            for key in keys
            if key not in public_items_by_key
        }
        if missing_public_items:
            raise CommandError(
                f"{len(missing_public_items)} resolved relevant record(s) are absent "
                "from PublicItem."
            )

        benchmark_items = []
        missing_chosen_price_count = 0
        for item_id in sorted(active_item_ids):
            report_item, survey_date = parsed_items[item_id]
            ground_truth_ids = {
                public_items_by_key[key] for key in ground_truth_keys_by_item[item_id]
            }
            chosen_prices = [
                Decimal(str(price["unit_price"])) for price in report_item.get("chosen_prices", [])
            ]
            if not [p for p in chosen_prices if p > 0]:
                missing_chosen_price_count += 1
                continue
            benchmark_items.append(
                {
                    "item_id": item_id,
                    "description": str(report_item.get("description", "")),
                    "unit": str(report_item.get("unit", "UNIDADE")),
                    "survey_date": survey_date,
                    "chosen_prices": chosen_prices,
                    "ground_truth": ground_truth_ids,
                }
            )

        if missing_chosen_price_count > 0:
            raise CommandError(
                f"{missing_chosen_price_count} {split_name} item(s) have no chosen price "
                "for the R2 anchor."
            )

        from pricing.views import get_embedding_model

        semantic_method = SemanticSearchMethod(model=get_embedding_model(), name="semantic")
        orchestrator = BenchmarkOrchestrator(
            n_noise_draws=200, n_bootstrap_resamples=10000, seed=42, top_n=top_n
        )
        try:
            results = orchestrator.run_benchmark(
                items=benchmark_items,
                corpus=PublicItem.objects.all(),
                split_name=split_name,
                active_item_ids=active_item_ids,
                finalist=finalist,
                candidate_methods=[semantic_method],
                baseline_method=BM25SearchMethod(name="bm25"),
                synthetic=False,
                top_n=top_n,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        results["split_hash"] = split_hash

        out_file = (
            Path(output_path) if output_path else eval_dir / f"benchmark_{split_name}_results.json"
        )
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(results, indent=2, cls=DecimalEncoder), encoding="utf-8")
        self.stdout.write(
            f"Real {split_name} benchmark completed for {results['items_count']} items; "
            f"split SHA-256: {split_hash}. Results written to {out_file.name}."
        )
