"""Management command to parse quotation reports into evaluation JSON files."""

import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from evaluation.parser import extract_pdf_layout_text, parse_quotation_report_text


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = "Parse quotation reports from PDF into JSON evaluation files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            type=str,
            default="/Users/rnobre/Documents/UFOPA/Projetos Codigo/TCC/dados-dominio/",
            help="Directory containing the quotation report PDF files.",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="/Users/rnobre/Documents/UFOPA/Projetos Codigo/TCC/dados-dominio/avaliacao/",
            help="Directory where parsed JSON files will be written.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"])
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_files = sorted(input_dir.glob("105588_Cotacao_*.pdf"))
        self.stdout.write(f"Found {len(pdf_files)} quotation report PDF(s) in {input_dir}")

        total_items = 0
        total_chosen_prices = 0
        total_pncp_keys = 0
        items_with_pncp = 0

        for pdf_path in pdf_files:
            report_id = pdf_path.stem
            self.stdout.write(f"Parsing {pdf_path.name}...")
            text = extract_pdf_layout_text(pdf_path)
            report = parse_quotation_report_text(text, report_id=report_id)

            report_dict = asdict(report)
            out_file = output_dir / f"{report_id}.json"
            out_file.write_text(
                json.dumps(report_dict, indent=2, ensure_ascii=False, cls=DecimalEncoder),
                encoding="utf-8",
            )

            rep_items = len(report.items)
            rep_prices = sum(len(it.chosen_prices) for it in report.items)
            rep_pncp = sum(
                1 for it in report.items for p in it.chosen_prices if p.pncp_key is not None
            )
            rep_items_with_pncp = sum(
                1 for it in report.items if any(p.pncp_key is not None for p in it.chosen_prices)
            )

            total_items += rep_items
            total_chosen_prices += rep_prices
            total_pncp_keys += rep_pncp
            items_with_pncp += rep_items_with_pncp

            self.stdout.write(
                f"  -> {report_id}: {rep_items} items, {rep_prices} chosen prices, "
                f"{rep_pncp} with PNCP key ({rep_items_with_pncp} items with >= 1 PNCP key)"
            )

        self.stdout.write(
            f"Total: {total_items} items, {total_chosen_prices} chosen prices, "
            f"{total_pncp_keys} with PNCP key, {items_with_pncp} items with >= 1 PNCP key"
        )
