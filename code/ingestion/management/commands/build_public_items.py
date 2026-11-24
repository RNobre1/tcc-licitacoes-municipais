import time

from django.core.management.base import BaseCommand

from ingestion.builder import build_public_items


class Command(BaseCommand):
    help = "Build or update PublicItem records from the latest RawRecords idempotently."

    def handle(self, *args, **options):
        start_time = time.monotonic()
        self.stdout.write("Building public items from latest raw records...")

        count = build_public_items()
        elapsed = time.monotonic() - start_time

        self.stdout.write(f"Successfully built or updated {count} public items in {elapsed:.2f}s.")
