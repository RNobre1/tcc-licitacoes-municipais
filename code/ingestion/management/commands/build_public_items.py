import time

from django.core.management.base import BaseCommand, CommandError

from ingestion.builder import DEFAULT_FAILED_PURCHASES_FILE, build_public_items


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
        parser.add_argument(
            "--failed-purchases-file",
            type=str,
            default=str(DEFAULT_FAILED_PURCHASES_FILE),
            help="JSONL path to record purchases that fail to build",
        )

    def handle(self, *args, **options):
        start_time = time.monotonic()
        start_date = options.get("start")
        end_date = options.get("end")
        failed_purchases_file = options.get("failed_purchases_file")

        slice_info = ""
        if start_date or end_date:
            slice_info = f" (date slice: {start_date or 'beginning'} to {end_date or 'latest'})"

        self.stdout.write(f"Building public items from latest raw records{slice_info}...")

        result = build_public_items(
            start=start_date,
            end=end_date,
            failed_purchases_file=failed_purchases_file,
            on_error=self.stderr.write,
        )
        elapsed = time.monotonic() - start_time

        self.stdout.write(
            f"Built or updated {result.built_count} public items "
            f"(skipped {result.skipped_without_publication} without publication metadata; "
            f"Failures: {result.failed_count}) "
            f"in {elapsed:.2f}s."
        )
        if result.failed_count > 0:
            if result.failed_purchases_file:
                self.stderr.write(f"Failed purchases written to {result.failed_purchases_file}")
            raise CommandError(
                f"build_public_items completed with {result.failed_count} failure(s)"
            )
