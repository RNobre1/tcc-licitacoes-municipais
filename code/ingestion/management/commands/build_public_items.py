import time

from django.core.management.base import BaseCommand

from ingestion.builder import build_public_items


class Command(BaseCommand):
    help = "Build or update PublicItem records from the latest RawRecords idempotently."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=str,
            default=None,
            help="Start date for publication slice (YYYY-MM-DD or YYYYMMDD)",
        )
        parser.add_argument(
            "--end",
            type=str,
            default=None,
            help="End date for publication slice (YYYY-MM-DD or YYYYMMDD)",
        )

    def handle(self, *args, **options):
        start_time = time.monotonic()
        start_date = options.get("start")
        end_date = options.get("end")

        slice_info = ""
        if start_date or end_date:
            slice_info = f" (date slice: {start_date or 'beginning'} to {end_date or 'latest'})"

        self.stdout.write(f"Building public items from latest raw records{slice_info}...")

        result = build_public_items(start=start_date, end=end_date)
        elapsed = time.monotonic() - start_time

        self.stdout.write(
            f"Successfully built or updated {result.built_count} public items "
            f"(skipped {result.skipped_without_publication} without publication metadata) "
            f"in {elapsed:.2f}s."
        )
