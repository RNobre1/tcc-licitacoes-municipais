"""Utilities for querying and deduplicating RawRecord models."""

import json
from collections.abc import Iterable, Sequence

from ingestion.models import RawRecord


def latest_copies(records: Sequence[RawRecord] | Iterable[RawRecord]) -> list[RawRecord]:
    """Keep the newest RawRecord for each (endpoint, canonical_params).

    Deterministically resolves duplicates by comparing (fetched_at, id).
    """
    latest: dict[tuple[str, str], RawRecord] = {}
    for r in records:
        params_key = json.dumps(r.params, sort_keys=True) if r.params is not None else ""
        key = (r.endpoint, params_key)
        if key not in latest:
            latest[key] = r
        else:
            prev = latest[key]
            if (r.fetched_at, r.id or 0) > (prev.fetched_at, prev.id or 0):
                latest[key] = r
    return list(latest.values())
