"""Management command to remove orphan points from a semantic index collection."""

from types import SimpleNamespace

from django.core.management.base import BaseCommand, CommandError

from semantic_index import get_qdrant_client
from semantic_index.embedding import collection_name_for_model
from semantic_index.management.commands.index_public_items import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
)
from semantic_index.pruning import DEFAULT_PRUNE_BATCH_SIZE, prune_orphan_points


class Command(BaseCommand):
    help = "Delete Qdrant points whose PublicItem no longer exists in PostgreSQL."

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
            default=DEFAULT_PRUNE_BATCH_SIZE,
            help=(
                "Batch size for scrolling and deleting points "
                f"(default: {DEFAULT_PRUNE_BATCH_SIZE})"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Count orphan points without deleting them from Qdrant",
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        revision = options["revision"]
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]

        collection_name = collection_name_for_model(
            SimpleNamespace(name=model_name, revision=revision)
        )
        client = get_qdrant_client()

        try:
            result = prune_orphan_points(
                client,
                collection_name,
                batch_size=batch_size,
                dry_run=dry_run,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"Collection: {result.collection_name}")
        self.stdout.write(f"Scanned: {result.scanned}")
        self.stdout.write(f"Orphans: {result.orphans}")
        self.stdout.write(f"Deleted: {result.deleted}")
        if result.dry_run:
            self.stdout.write("Dry run: no points were deleted.")
