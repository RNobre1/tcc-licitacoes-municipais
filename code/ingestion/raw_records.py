"""Utilities for querying and deduplicating RawRecord models."""

from collections.abc import Iterable, Sequence

from ingestion.models import RawRecord


def latest_copies(records: Sequence[RawRecord] | Iterable[RawRecord]) -> list[RawRecord]:
    """Keep the newest RawRecord for each (endpoint, canonical_params).

    Deterministically resolves duplicates by comparing (fetched_at, id).
    """
    raise NotImplementedError
