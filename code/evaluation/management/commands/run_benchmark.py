"""Management command to run evaluation benchmarks."""

import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    check_thresholds_note_guard,
    create_dataset_split,
    verify_split_hash,
)


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

    def handle(self, *args, **options):
        split_name = options["split"]
        eval_dir = Path(options["eval_dir"])
        thresholds_note = options["thresholds_note"]
        output_path = options.get("output")
        synthetic = options["synthetic"]

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
            self._handle_synthetic(split_name, output_path)
        else:
            self._handle_real(split_name, eval_dir, output_path, thresholds_note)

    def _handle_synthetic(self, split_name: str, output_path: str | None):
        self.stdout.write(f"Running benchmark on synthetic data ({split_name} split)...")

        synthetic_corpus = [
            {
                "id": 1,
                "description": "Papel Sulfite A4 75g",
                "price": Decimal("25.0"),
                "unit": "UNIDADE",
            },
            {
                "id": 2,
                "description": "Caneta Esferográfica Azul 1.0mm",
                "price": Decimal("1.5"),
                "unit": "UNIDADE",
            },
            {
                "id": 3,
                "description": "Papel A4 Reciclado 500 folhas",
                "price": Decimal("22.0"),
                "unit": "UNIDADE",
            },
            {
                "id": 4,
                "description": "Lápis Preto Grafite HB",
                "price": Decimal("0.8"),
                "unit": "UNIDADE",
            },
            {
                "id": 5,
                "description": "Borracha Branca Escolar",
                "price": Decimal("1.0"),
                "unit": "UNIDADE",
            },
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
            },
            {
                "item_id": "syn_2",
                "report_id": "rep_demo",
                "item_kind": "product",
                "description": "Caneta azul ponta média",
                "ground_truth": {2},
                "chosen_prices": [Decimal("1.5")],
                "unit": "UNIDADE",
            },
        ]

        split = create_dataset_split(synthetic_items, tuning_fraction=0.5, seed=42)
        active_ids = (
            set(split.tuning_items) if split_name == "tuning" else set(split.measurement_items)
        )

        orch = BenchmarkOrchestrator(n_noise_draws=200, n_bootstrap_resamples=10000, seed=42)
        results = orch.run_benchmark(
            items=synthetic_items,
            corpus=synthetic_corpus,
            split_name=split_name,
            active_item_ids=active_ids,
            synthetic=True,
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
    ):
        eval_dir.mkdir(parents=True, exist_ok=True)
        split_file = eval_dir / "dataset_split.json"
        if not split_file.exists():
            raise CommandError(
                f"Split file {split_file} does not exist. "
                "Split must be generated via generate_dataset_split before running benchmark."
            )

        split_data = json.loads(split_file.read_text(encoding="utf-8"))
        if not verify_split_hash(
            split_data["tuning_items"],
            split_data["measurement_items"],
            split_data["sha256_hash"],
        ):
            raise CommandError("Dataset split file failed SHA-256 verification!")

        if split_name == "measurement" and thresholds_note:
            try:
                check_thresholds_note_guard(
                    Path(thresholds_note), split_hash=split_data["sha256_hash"]
                )
            except ValueError as exc:
                raise CommandError(str(exc)) from exc

        self.stdout.write(
            f"Dataset split verified (SHA-256: {split_data['sha256_hash'][:16]}...). "
            "Corpus benchmark awaits E5 indexing completion."
        )
