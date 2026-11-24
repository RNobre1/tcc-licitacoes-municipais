from collections.abc import Sequence
from typing import Any

from semantic_index.embedding import EmbeddingModel


def index_public_items(
    model: EmbeddingModel,
    items: Sequence[Any],
    client: Any = None,
) -> int:
    """Index public items into a Qdrant collection named for the given model and revision."""
    raise NotImplementedError
