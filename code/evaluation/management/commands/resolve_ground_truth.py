"""Management command to resolve ground-truth records in PNCP."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Resolve ground-truth chosen prices in PNCP via ingestion client."

    def add_arguments(self, parser):
        parser.add_argument(
            "--eval-dir",
            type=str,
            default="/Users/rnobre/Documents/UFOPA/Projetos Codigo/TCC/dados-dominio/avaliacao/",
            help="Directory containing the parsed evaluation JSON files.",
        )
        parser.add_argument(
            "--skip-fetch",
            action="store_true",
            help="Skip fetching and resolve only from existing database RawRecords.",
        )

    def handle(self, *args, **options):
        raise NotImplementedError
