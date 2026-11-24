from dataclasses import dataclass
from datetime import date
from typing import Any

from ingestion.models import PublicItem
from semantic_index.embedding import EmbeddingModel


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
    raise NotImplementedError
