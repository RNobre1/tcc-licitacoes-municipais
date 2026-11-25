"""Management command to generate reproducible dataset_split.json."""

import json
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from evaluation.benchmark import create_dataset_split


class Command(BaseCommand):
    help = "Generate reproducible dataset_split.json from ground_truth_resolved.json."

    def add_arguments(self, parser):
        default_eval_dir = os.environ.get("EVALUATION_DATA_DIR") or str(
            Path(settings.BASE_DIR).parent / "dados-dominio" / "avaliacao"
        )
        parser.add_argument(
            "--eval-dir",
            type=str,
            default=default_eval_dir,
            help="Directory containing ground_truth_resolved.json.",
        )
        parser.add_argument(
            "--tuning-fraction",
            type=float,
            default=0.4,
            help="Fraction of items allocated to tuning split (default: 0.4).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible stratification (default: 42).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force overwrite if split file already exists.",
        )

    def handle(self, *args, **options):
        eval_dir = Path(options["eval_dir"])
        tuning_fraction = options["tuning_fraction"]
        seed = options["seed"]

        gt_file = eval_dir / "ground_truth_resolved.json"
        if not gt_file.exists():
            raise FileNotFoundError(f"Ground truth file not found: {gt_file}")

        gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
        resolved_items = gt_data.get("resolved_items", {})

        # Group resolved items by item key: (report_id, item_number)
        items_map: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for ref_key, item_info in resolved_items.items():
            if not item_info.get("found"):
                continue
            # ref_key format: {report_id}_it{item_number}_p{price_number}
            parts = ref_key.split("_it")
            report_id = parts[0]
            item_num = int(parts[1].split("_p")[0])
            items_map.setdefault((report_id, item_num), []).append(item_info)

        # Build item dict list for create_dataset_split
        items_list = []
        for (report_id, item_num), recs in sorted(items_map.items()):
            kind = "service" if any(r.get("item_kind") == "service" for r in recs) else "product"
            items_list.append(
                {
                    "item_id": f"{report_id}_{item_num}",
                    "report_id": report_id,
                    "item_kind": kind,
                }
            )

        split = create_dataset_split(items_list, tuning_fraction=tuning_fraction, seed=seed)

        out_data = {
            "total_eligible_items": len(items_list),
            "tuning_count": len(split.tuning_items),
            "measurement_count": len(split.measurement_items),
            "sha256_hash": split.sha256_hash,
            "tuning_items": list(split.tuning_items),
            "measurement_items": list(split.measurement_items),
        }

        out_file = eval_dir / "dataset_split.json"
        if out_file.exists() and not options.get("force"):
            from django.core.management.base import CommandError

            raise CommandError(
                f"Split file already exists at {out_file}. Use --force to overwrite."
            )
        out_file.write_text(json.dumps(out_data, indent=2), encoding="utf-8")

        self.stdout.write(
            f"Generated dataset split for {len(items_list)} eligible items: "
            f"{len(split.tuning_items)} tuning, {len(split.measurement_items)} measurement.\n"
            f"SHA-256: {split.sha256_hash}\n"
            f"Written to: {out_file}"
        )
