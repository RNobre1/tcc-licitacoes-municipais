from django.core.management.base import BaseCommand

from semantic_index.embedding import (  # noqa: F401
    SentenceTransformerEmbeddingModel,
)
from semantic_index.indexing import index_public_items  # noqa: F401

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
        raise NotImplementedError
