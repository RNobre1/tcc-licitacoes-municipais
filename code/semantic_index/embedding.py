from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingModel(Protocol):
    """Protocol for embedding models used in semantic search."""

    name: str
    revision: str
    dimension: int

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        """Embed search queries into vectors."""
        ...

    def embed_passages(self, passages: Sequence[str]) -> list[list[float]]:
        """Embed item passages/descriptions into vectors."""
        ...


class SentenceTransformerEmbeddingModel:
    """Embedding model backed by sentence-transformers with pinned revision and prefixes."""

    def __init__(
        self,
        model_name: str,
        revision: str,
        query_prefix: str | None = None,
        passage_prefix: str | None = None,
    ) -> None:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def revision(self) -> str:
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_passages(self, passages: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError


def collection_name_for_model(model: EmbeddingModel) -> str:
    """Return a unique, clean Qdrant collection name for a model and revision."""
    raise NotImplementedError
