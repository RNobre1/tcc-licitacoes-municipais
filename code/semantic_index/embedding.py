import re
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
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._revision = revision
        self._st_model = SentenceTransformer(model_name, revision=revision)

        # Default prefix logic: E5 models require "query: " and "passage: "
        if query_prefix is not None:
            self._query_prefix = query_prefix
        elif "e5" in model_name.lower():
            self._query_prefix = "query: "
        else:
            self._query_prefix = ""

        if passage_prefix is not None:
            self._passage_prefix = passage_prefix
        elif "e5" in model_name.lower():
            self._passage_prefix = "passage: "
        else:
            self._passage_prefix = ""

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def revision(self) -> str:
        return self._revision

    @property
    def dimension(self) -> int:
        dim = getattr(self._st_model, "get_sentence_embedding_dimension", None)
        if callable(dim):
            return int(dim())
        return 768

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        prefixed = [f"{self._query_prefix}{q}" for q in queries]
        embeddings = self._st_model.encode(prefixed, normalize_embeddings=True)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(vec) for vec in embeddings]

    def embed_passages(self, passages: Sequence[str]) -> list[list[float]]:
        prefixed = [f"{self._passage_prefix}{p}" for p in passages]
        embeddings = self._st_model.encode(prefixed, normalize_embeddings=True)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(vec) for vec in embeddings]


def collection_name_for_model(model: EmbeddingModel) -> str:
    """Return a unique, clean Qdrant collection name for a model and revision."""
    clean_name = re.sub(r"[^a-zA-Z0-9]+", "_", model.name).strip("_").lower()
    clean_rev = re.sub(r"[^a-zA-Z0-9]+", "_", model.revision).strip("_").lower()
    return f"items_{clean_name}_{clean_rev}"
