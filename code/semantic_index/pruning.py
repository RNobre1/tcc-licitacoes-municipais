"""Removal of orphan points: Qdrant points whose PublicItem no longer exists in PostgreSQL."""

from dataclasses import dataclass
from typing import Any

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
    raise NotImplementedError
