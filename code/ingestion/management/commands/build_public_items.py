import time

from django.core.management.base import BaseCommand

from ingestion.builder import build_public_items


class Command(BaseCommand):
    help = "Build or update PublicItem records from the latest RawRecords idempotently."

    def handle(self, *args, **options):
        start_time = time.monotonic()
        self.stdout.write("Building public items from latest raw records...")

        result = build_public_items()
        elapsed = time.monotonic() - start_time

        self.stdout.write(
            f"Successfully built or updated {result.built_count} public items "
            f"(skipped {result.skipped_without_publication} without publication metadata) "
            f"in {elapsed:.2f}s."
        )
