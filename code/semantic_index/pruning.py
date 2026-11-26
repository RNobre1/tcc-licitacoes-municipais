"""Removal of orphan points: Qdrant points whose PublicItem no longer exists in PostgreSQL."""

from dataclasses import dataclass
from typing import Any

from qdrant_client import models

DEFAULT_PRUNE_BATCH_SIZE = 1000


@dataclass(frozen=True)
class PruneResult:
    """Counts from one pruning pass over a collection."""

    collection_name: str
    scanned: int
    orphans: int
    deleted: int
    dry_run: bool


def prune_orphan_points(
    client: Any,
    collection_name: str,
    *,
    batch_size: int = DEFAULT_PRUNE_BATCH_SIZE,
    dry_run: bool = False,
) -> PruneResult:
    """Delete every point of the collection whose id is not a PublicItem primary key."""
    if isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError(f"batch_size must be a positive integer, got {batch_size!r}")

    if not client.collection_exists(collection_name):
        raise ValueError(f"Collection '{collection_name}' does not exist")

    from ingestion.models import PublicItem

    scanned = 0
    orphans = 0
    deleted = 0
    offset: Any = None

    while True:
        records, next_offset = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        if not records:
            break

        batch_ids = [record.id for record in records]
        int_ids = [
            point_id
            for point_id in batch_ids
            if isinstance(point_id, int) and not isinstance(point_id, bool)
        ]
        existing_pks = (
            set(PublicItem.objects.filter(pk__in=int_ids).values_list("pk", flat=True))
            if int_ids
            else set()
        )
        batch_orphans = [point_id for point_id in batch_ids if point_id not in existing_pks]

        scanned += len(batch_ids)
        orphans += len(batch_orphans)

        if batch_orphans and not dry_run:
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=batch_orphans),
                wait=True,
            )
            deleted += len(batch_orphans)

        if next_offset is None:
            break
        offset = next_offset

    return PruneResult(
        collection_name=collection_name,
        scanned=scanned,
        orphans=orphans,
        deleted=deleted,
        dry_run=dry_run,
    )
