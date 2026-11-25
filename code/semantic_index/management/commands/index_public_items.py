import time
from datetime import date, datetime

from django.core.management.base import BaseCommand

from ingestion.models import PublicItem
from semantic_index.embedding import SentenceTransformerEmbeddingModel
from semantic_index.indexing import index_public_items

DEFAULT_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_REVISION = "d13f1b27baf31030b7fd040960d60d909913633f"


def _parse_command_date(val: str | None) -> date | None:
    if not val:
        return None
    val_str = val.strip()
    if not val_str:
        return None
    if len(val_str) == 8 and val_str.isdigit():
        return datetime.strptime(val_str, "%Y%m%d").date()
    return date.fromisoformat(val_str[:10])


class Command(BaseCommand):
    help = "Index every PublicItem into a Qdrant collection named from model and pinned revision."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            default=DEFAULT_MODEL,
            help=f"Embedding model name on Hugging Face hub (default: {DEFAULT_MODEL})",
        )
        parser.add_argument(
            "--revision",
            default=DEFAULT_REVISION,
            help=(
                f"Pinned model commit revision from Hugging Face hub (default: {DEFAULT_REVISION})"
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=256,
            help="Batch size for embedding and indexing (default: 256)",
        )
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
        model_name = options["model"]
        revision = options["revision"]
        batch_size = options["batch_size"]
        start_d = _parse_command_date(options.get("start"))
        end_d = _parse_command_date(options.get("end"))

        self.stdout.write(f"Loading embedding model '{model_name}' (revision: {revision})...")
        model = SentenceTransformerEmbeddingModel(
            model_name=model_name,
            revision=revision,
        )

        items = PublicItem.objects.all().order_by("pk")
        if start_d is not None:
            items = items.filter(published_on__gte=start_d)
        if end_d is not None:
            items = items.filter(published_on__lte=end_d)

        total_count = items.count()
        self.stdout.write(f"Indexing {total_count} PublicItems into Qdrant...")

        start_time = time.monotonic()
        indexed_count = index_public_items(
            model=model,
            items=items,
            batch_size=batch_size,
        )
        elapsed = time.monotonic() - start_time

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {indexed_count} public items into Qdrant collection in {elapsed:.2f}s."
            )
        )
