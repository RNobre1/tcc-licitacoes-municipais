"""Management command to run evaluation benchmarks."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from rank_bm25 import BM25Okapi

from evaluation.benchmark import (
    check_thresholds_note_guard,
    compute_mrr_at_k,
    compute_recall_at_k,
    create_dataset_split,
    verify_split_hash,
)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in text.split() if t.strip()]


class Command(BaseCommand):
    help = "Run search benchmark against evaluation set."

    def add_arguments(self, parser):
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
            default="/Users/rnobre/Documents/UFOPA/Projetos Codigo/TCC/dados-dominio/avaliacao/",
            help="Evaluation directory containing JSON files.",
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
        synthetic = options["synthetic"]

        eval_dir.mkdir(parents=True, exist_ok=True)

        # Enforce code guard for measurement split
        if split_name == "measurement":
            if not thresholds_note:
                raise ValueError(
                    "Thresholds note must be provided via --thresholds-note for measurement split"
                )
            check_thresholds_note_guard(Path(thresholds_note))
            self.stdout.write(f"Guard passed: verified thresholds note at {thresholds_note}")

        if synthetic:
            self._handle_synthetic(split_name, eval_dir)
        else:
            self._handle_real(split_name, eval_dir)

    def _handle_synthetic(self, split_name: str, eval_dir: Path):
        self.stdout.write(f"Running benchmark on synthetic data ({split_name} split)...")

        # Synthetic corpus and evaluation queries
        synthetic_corpus = [
            {"id": 1, "description": "Papel Sulfite A4 75g", "price": Decimal("25.0")},
            {"id": 2, "description": "Caneta Esferográfica Azul 1.0mm", "price": Decimal("1.5")},
            {"id": 3, "description": "Papel A4 Reciclado 500 folhas", "price": Decimal("22.0")},
            {"id": 4, "description": "Lápis Preto Grafite HB", "price": Decimal("0.8")},
            {"id": 5, "description": "Borracha Branca Escolar", "price": Decimal("1.0")},
        ]

        synthetic_items = [
            {
                "item_id": "syn_1",
                "report_id": "rep_demo",
                "item_kind": "product",
                "description": "Papel sulfite A4 resma branca",
                "ground_truth": {1, 3},
                "chosen_prices": [Decimal("25.0")],
            },
            {
                "item_id": "syn_2",
                "report_id": "rep_demo",
                "item_kind": "product",
                "description": "Caneta azul ponta média",
                "ground_truth": {2},
                "chosen_prices": [Decimal("1.5")],
            },
        ]

        split = create_dataset_split(synthetic_items, tuning_fraction=0.5, seed=42)

        tokenized_corpus = [_tokenize(doc["description"]) for doc in synthetic_corpus]
        bm25 = BM25Okapi(tokenized_corpus)

        recalls_at_10: list[float] = []
        mrrs_at_20: list[float] = []

        active_item_ids = (
            set(split.tuning_items) if split_name == "tuning" else set(split.measurement_items)
        )

        for item in synthetic_items:
            if item["item_id"] not in active_item_ids:
                continue

            query_tokens = _tokenize(item["description"])
            scores = bm25.get_scores(query_tokens)

            # Rank candidates by BM25 score desc
            ranked_pairs = sorted(
                zip(synthetic_corpus, scores, strict=False),
                key=lambda x: x[1],
                reverse=True,
            )
            ranked_ids = [doc["id"] for doc, s in ranked_pairs]

            r10 = compute_recall_at_k(ranked_ids, item["ground_truth"], k=10)
            mrr = compute_mrr_at_k(ranked_ids, item["ground_truth"], k=20)

            recalls_at_10.append(r10)
            mrrs_at_20.append(mrr)

        avg_recall = sum(recalls_at_10) / len(recalls_at_10) if recalls_at_10 else 0.0
        avg_mrr = sum(mrrs_at_20) / len(mrrs_at_20) if mrrs_at_20 else 0.0

        results = {
            "split": split_name,
            "synthetic": True,
            "items_count": len(recalls_at_10),
            "metrics": {
                "recall_at_10": avg_recall,
                "mrr_at_20": avg_mrr,
            },
            "split_hash": split.sha256_hash,
        }

        out_file = eval_dir / f"benchmark_{split_name}_results.json"
        out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
        self.stdout.write(f"Synthetic benchmark completed. Results written to {out_file}")

    def _handle_real(self, split_name: str, eval_dir: Path):
        # Checks split hash file existence or creates split on first run
        split_file = eval_dir / "dataset_split.json"
        if not split_file.exists():
            raise FileNotFoundError(
                f"Split file {split_file} does not exist. "
                "Split must be generated before running benchmark."
            )

        split_data = json.loads(split_file.read_text(encoding="utf-8"))
        if not verify_split_hash(
            split_data["tuning_items"],
            split_data["measurement_items"],
            split_data["sha256_hash"],
        ):
            raise ValueError("Dataset split file failed SHA-256 verification!")

        self.stdout.write(
            f"Dataset split verified (SHA-256: {split_data['sha256_hash'][:16]}...). "
            f"Corpus benchmark awaits Wednesday corpus decision."
        )
