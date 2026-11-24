import hashlib
import math
from collections.abc import Sequence


class FakeEmbeddingModel:
    """Deterministic fake embedding model for unit tests with zero network or download."""

    def __init__(
        self,
        name: str = "fake-model",
        revision: str = "v1-fake",
        dimension: int = 16,
    ) -> None:
        self.name = name
        self.revision = revision
        self.dimension = dimension
        self.embedded_queries: list[str] = []
        self.embedded_passages: list[str] = []

    def _embed(self, text: str) -> list[float]:
        # Hash text to dimension pseudo-random floats, normalized to unit L2 norm
        vec = []
        for i in range(self.dimension):
            h = hashlib.sha256(f"{text}-{i}".encode()).digest()
            val = int.from_bytes(h[:4], "big", signed=True) / (2**31)
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 6) for x in vec]

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        self.embedded_queries.extend(queries)
        return [self._embed(f"query: {q}") for q in queries]

    def embed_passages(self, passages: Sequence[str]) -> list[list[float]]:
        self.embedded_passages.extend(passages)
        return [self._embed(f"passage: {p}") for p in passages]
