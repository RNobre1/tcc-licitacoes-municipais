"""Management command to run evaluation benchmarks."""

from django.core.management.base import BaseCommand


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
        raise NotImplementedError
