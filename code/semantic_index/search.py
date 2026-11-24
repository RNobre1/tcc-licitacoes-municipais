from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

from qdrant_client import models

from semantic_index.embedding import EmbeddingModel, collection_name_for_model

if TYPE_CHECKING:
    from ingestion.models import PublicItem


@dataclass(frozen=True)
class StructuredFilter:
    """Structured filter for semantic search.

    The 12-month date window is mandatory (RN07, docs/requisitos/README.md).
    State, unit, and item_kind are optional.
    """

    date_window: tuple[date, date]
    state: str | None = None
    unit: str | None = None
    item_kind: str | None = None


@dataclass(frozen=True)
class ScoredPublicItem:
    """A PublicItem matched by semantic search, carrying its similarity score."""

    item: PublicItem
    score: float

    def __iter__(self):
        return iter((self.item, self.score))

    def __getitem__(self, index: int) -> Any:
        return (self.item, self.score)[index]


def semantic_search(
    model: EmbeddingModel,
    query: str,
    structured_filter: StructuredFilter | dict[str, Any],
    limit: int = 10,
    client: Any = None,
) -> list[ScoredPublicItem]:
    """Search PublicItems by vector similarity under mandatory structured filter."""
    from ingestion.models import PublicItem
    from semantic_index import get_qdrant_client

    # 1. Parse structured filter
    if isinstance(structured_filter, StructuredFilter):
        date_window = structured_filter.date_window
        state = structured_filter.state
        unit = structured_filter.unit
        item_kind = structured_filter.item_kind
    elif isinstance(structured_filter, dict):
        date_window = structured_filter.get("date_window")
        state = structured_filter.get("state")
        unit = structured_filter.get("unit")
        item_kind = structured_filter.get("item_kind")
    else:
        raise ValueError(f"Invalid structured_filter: {structured_filter}")

    # 2. Mandatory date window validation (RN07)
    if (
        not date_window
        or not isinstance(date_window, (tuple, list))
        or len(date_window) != 2
        or date_window[0] is None
        or date_window[1] is None
    ):
        raise ValueError("date_window is mandatory (RN07, 12-month window)")

    start_date, end_date = date_window
    if start_date > end_date:
        raise ValueError(
            f"Inverted date_window: start_date {start_date} is after end_date {end_date}"
        )
    if (end_date - start_date).days > 366:
        raise ValueError("date_window exceeds 12-month limit (RN07, docs/requisitos/README.md)")

    # 3. Build Qdrant filter
    must_conditions: list[models.Condition] = [
        models.FieldCondition(
            key="published_on",
            range=models.DatetimeRange(gte=start_date, lte=end_date),
        )
    ]

    if state:
        must_conditions.append(
            models.FieldCondition(
                key="state",
                match=models.MatchValue(value=str(state)),
            )
        )

    if unit:
        norm_unit = str(unit).strip().casefold()
        must_conditions.append(
            models.FieldCondition(
                key="unit",
                match=models.MatchValue(value=norm_unit),
            )
        )

    if item_kind:
        must_conditions.append(
            models.FieldCondition(
                key="item_kind",
                match=models.MatchValue(value=str(item_kind)),
            )
        )

    qdrant_filter = models.Filter(must=must_conditions)

    # 4. Embed query
    query_vectors = model.embed_queries([query])
    if not query_vectors:
        return []
    query_vector = query_vectors[0]

    # 5. Query Qdrant
    qdrant_client = client if client is not None else get_qdrant_client()
    collection_name = collection_name_for_model(model)

    if not qdrant_client.collection_exists(collection_name):
        raise ValueError(f"Collection '{collection_name}' does not exist")

    # Over-fetch from Qdrant so dropped ghosts never shrink the result below limit
    fetch_limit = max(limit * 2, limit + 20)
    response = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=fetch_limit,
    )

    scored_points = response.points
    if not scored_points:
        return []

    # 6. Hydrate from PostgreSQL in Qdrant's score order, preventing ghosts
    point_ids = [int(p.id) for p in scored_points]
    items_by_id = {item.pk: item for item in PublicItem.objects.filter(pk__in=point_ids)}

    results: list[ScoredPublicItem] = []
    for p in scored_points:
        item = items_by_id.get(int(p.id))
        if item is not None:
            results.append(ScoredPublicItem(item=item, score=float(p.score)))
            if len(results) >= limit:
                break

    return results
