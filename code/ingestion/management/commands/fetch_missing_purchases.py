from django.core.management.base import BaseCommand

from ingestion.client import fetch_purchase  # noqa: F401


class Command(BaseCommand):
    help = "Fetch header metadata for purchases that have item pages but no publication record."

    def handle(self, *args, **options):
        raise NotImplementedError
