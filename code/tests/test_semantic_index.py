from types import SimpleNamespace
from typing import Any

import pytest
from qdrant_client import models

from semantic_index import check_health, create_collection, get_qdrant_client


class FakeQdrantClient:
    """In-memory fake QdrantClient for unit tests without network dependency."""

    def __init__(self, healthy: bool = True):
        self.healthy = healthy
        self.collections: dict[str, models.VectorParams] = {}

    def get_collections(self) -> Any:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        collection_descriptions = [SimpleNamespace(name=name) for name in self.collections]
        return SimpleNamespace(collections=collection_descriptions)

    def collection_exists(self, collection_name: str) -> bool:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        return collection_name in self.collections

    def create_collection(
        self,
        collection_name: str,
        vectors_config: models.VectorParams,
    ) -> bool:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        if collection_name in self.collections:
            raise RuntimeError(f"Conflict 409: Collection `{collection_name}` already exists!")
        self.collections[collection_name] = vectors_config
        return True

    def get_collection(self, collection_name: str) -> Any:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        if collection_name not in self.collections:
            raise RuntimeError(f"Collection `{collection_name}` not found")
        vector_params = self.collections[collection_name]
        return SimpleNamespace(
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=vector_params,
                )
            )
        )

    def delete_collection(self, collection_name: str) -> bool:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        self.collections.pop(collection_name, None)
        return True


class TestSemanticIndexHealthUnit:
    """Unit tests for semantic_index health check using fake client."""

    def test_check_health_returns_true_when_healthy(self):
        client = FakeQdrantClient(healthy=True)
        assert check_health(client) is True

    def test_check_health_returns_false_when_unhealthy(self):
        client = FakeQdrantClient(healthy=False)
        assert check_health(client) is False


class TestSemanticIndexCollectionUnit:
    """Unit tests for collection management and idempotency."""

    def test_create_collection_creates_new_collection(self):
        client = FakeQdrantClient()
        res = create_collection(
            client=client,
            collection_name="items",
            vector_size=128,
            distance=models.Distance.COSINE,
        )
        assert res is True
        assert client.collection_exists("items")
        info = client.get_collection("items")
        assert info.config.params.vectors.size == 128
        assert info.config.params.vectors.distance == models.Distance.COSINE

    def test_create_collection_is_idempotent_when_called_twice(self):
        client = FakeQdrantClient()
        res1 = create_collection(
            client=client,
            collection_name="items",
            vector_size=128,
            distance=models.Distance.COSINE,
        )
        res2 = create_collection(
            client=client,
            collection_name="items",
            vector_size=128,
            distance=models.Distance.COSINE,
        )
        assert res1 is True
        assert res2 is True
        assert client.collection_exists("items")

    def test_create_collection_requires_explicit_vector_size_and_distance(self):
        client = FakeQdrantClient()
        # vector_size and distance cannot be omitted
        with pytest.raises(TypeError):
            create_collection(client=client, collection_name="items")  # type: ignore[call-arg]


class TestGetQdrantClientUnit:
    """Unit tests for get_qdrant_client configuration resolution."""

    def test_get_qdrant_client_uses_explicit_url(self):
        client = get_qdrant_client(url="http://custom-qdrant:6333")
        # In QdrantClient, init_options or rest_uri records the target url
        assert "custom-qdrant:6333" in str(client._client.rest_uri)

    def test_get_qdrant_client_reads_qdrant_url_from_env(self, monkeypatch):
        monkeypatch.setenv("QDRANT_URL", "http://env-qdrant:6333")
        client = get_qdrant_client()
        assert "env-qdrant:6333" in str(client._client.rest_uri)

    def test_get_qdrant_client_defaults_to_localhost_when_unset(self, monkeypatch):
        monkeypatch.delenv("QDRANT_URL", raising=False)
        client = get_qdrant_client()
        assert "127.0.0.1:6333" in str(client._client.rest_uri)
