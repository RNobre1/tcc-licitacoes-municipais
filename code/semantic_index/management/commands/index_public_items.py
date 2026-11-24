import time

from django.core.management.base import BaseCommand

from ingestion.models import PublicItem
from semantic_index.embedding import SentenceTransformerEmbeddingModel
from semantic_index.indexing import index_public_items

DEFAULT_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_REVISION = "d13f1b27baf31030b7fd040960d60d909913633f"


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
                "Pinned model commit revision from Hugging Face hub "
                f"(default: {DEFAULT_REVISION}, evaluated on MTEB benchmark)"
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=256,
            help="Batch size for embedding and indexing (default: 256)",
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        revision = options["revision"]
        batch_size = options["batch_size"]

        self.stdout.write(f"Loading embedding model '{model_name}' (revision: {revision})...")
        model = SentenceTransformerEmbeddingModel(
            model_name=model_name,
            revision=revision,
        )

        items = PublicItem.objects.all().order_by("pk")
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
