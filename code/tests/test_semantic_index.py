from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from semantic_index import (
    CollectionConfigurationMismatchError,
    check_health,
    create_collection,
    get_qdrant_client,
)


def response(status: int, text: str = "") -> UnexpectedResponse:
    body = ('{"status":{"error":"' + text + '"},"time":0.0}').encode()
    return UnexpectedResponse(status, "reason", body, httpx.Headers())


class FakeQdrantClient:
    """In-memory fake QdrantClient for unit tests without network dependency."""

    def __init__(self, healthy: bool = True):
        self.healthy = healthy
        self.collections: dict[str, VectorParams] = {}

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
        vectors_config: VectorParams,
    ) -> bool:
        if not self.healthy:
            raise ConnectionError("Connection refused by fake Qdrant service")
        if collection_name in self.collections:
            raise response(409, f"Collection `{collection_name}` already exists!")
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


class RejectingClient(FakeQdrantClient):
    """Client where create_collection always raises configured error."""

    error: Exception = RuntimeError("Default rejection")

    def create_collection(self, collection_name: str, vectors_config: VectorParams) -> bool:
        raise self.error


class RacingClient(FakeQdrantClient):
    """Client simulating another process creating collection between check and create."""

    created_as = VectorParams(size=128, distance=Distance.COSINE)

    def collection_exists(self, collection_name: str) -> bool:
        return False

    def create_collection(self, collection_name: str, vectors_config: VectorParams) -> bool:
        self.collections[collection_name] = self.created_as
        raise response(409, "Collection already exists")


class TestSemanticIndexHealthUnit:
    """Unit tests for semantic_index health check using fake client."""

    def test_check_health_returns_true_when_healthy(self):
        client = FakeQdrantClient(healthy=True)
        assert check_health(client) is True

    def test_check_health_returns_false_when_unhealthy(self):
        client = FakeQdrantClient(healthy=False)
        assert check_health(client) is False


class TestSemanticIndexCollectionUnit:
    """Unit tests for collection management, idempotency, and error handling."""

    @pytest.mark.parametrize(
        ("size", "distance"),
        [
            (64, Distance.DOT),
            (384, Distance.EUCLID),
            (1024, Distance.COSINE),
        ],
    )
    def test_vector_size_and_distance_are_the_ones_given(self, size, distance):
        client = FakeQdrantClient()
        assert create_collection(client, "items", vector_size=size, distance=distance) is True
        vectors = client.get_collection("items").config.params.vectors
        assert (vectors.size, vectors.distance) == (size, distance)

    def test_create_collection_is_idempotent_when_called_twice_with_same_configuration(self):
        client = FakeQdrantClient()
        res1 = create_collection(
            client=client,
            collection_name="items",
            vector_size=128,
            distance=Distance.COSINE,
        )
        res2 = create_collection(
            client=client,
            collection_name="items",
            vector_size=128,
            distance=Distance.COSINE,
        )
        assert res1 is True
        assert res2 is True
        assert client.collection_exists("items")

    @pytest.mark.parametrize(
        ("size", "distance"),
        [
            (256, Distance.COSINE),
            (128, Distance.DOT),
            (256, Distance.DOT),
        ],
    )
    def test_existing_collection_with_another_configuration_is_an_error(self, size, distance):
        client = FakeQdrantClient()
        create_collection(client, "items", vector_size=128, distance=Distance.COSINE)
        with pytest.raises(CollectionConfigurationMismatchError) as exc_info:
            create_collection(client, "items", vector_size=size, distance=distance)

        msg = str(exc_info.value)
        assert "items" in msg
        assert "128" in msg and str(Distance.COSINE) in msg
        assert str(size) in msg and str(distance) in msg

        vectors = client.get_collection("items").config.params.vectors
        assert (vectors.size, vectors.distance) == (128, Distance.COSINE)

    @pytest.mark.parametrize(
        "error",
        [
            response(422, "Validation error: vectors.size value 409600 invalid"),
            response(500, "internal"),
            ConnectionError("lost the connection"),
        ],
    )
    def test_a_failed_creation_is_never_reported_as_success(self, error):
        client = RejectingClient()
        client.error = error
        with pytest.raises(type(error)):
            create_collection(client, "items", vector_size=128, distance=Distance.COSINE)
        assert not client.collection_exists("items")

    def test_losing_a_creation_race_with_the_same_configuration_is_success(self):
        assert create_collection(RacingClient(), "items", 128, Distance.COSINE) is True

    def test_losing_a_creation_race_to_another_configuration_is_an_error(self):
        client = RacingClient()
        client.created_as = VectorParams(size=256, distance=Distance.DOT)
        with pytest.raises(CollectionConfigurationMismatchError) as exc_info:
            create_collection(client, "items", 128, Distance.COSINE)

        msg = str(exc_info.value)
        assert "items" in msg
        assert "256" in msg and str(Distance.DOT) in msg
        assert "128" in msg and str(Distance.COSINE) in msg

    def test_create_collection_requires_explicit_vector_size_and_distance(self):
        client = FakeQdrantClient()
        with pytest.raises(TypeError):
            create_collection(client=client, collection_name="items")  # type: ignore[call-arg]


class TestGetQdrantClientUnit:
    """Unit tests for get_qdrant_client configuration resolution."""

    def test_get_qdrant_client_uses_explicit_url(self):
        client = get_qdrant_client(url="http://custom-qdrant:6333")
        assert "custom-qdrant:6333" in str(client._client.rest_uri)

    def test_get_qdrant_client_reads_qdrant_url_from_env(self, monkeypatch):
        monkeypatch.setenv("QDRANT_URL", "http://env-qdrant:6333")
        client = get_qdrant_client()
        assert "env-qdrant:6333" in str(client._client.rest_uri)

    def test_get_qdrant_client_defaults_to_localhost_when_unset(self, monkeypatch):
        monkeypatch.delenv("QDRANT_URL", raising=False)
        client = get_qdrant_client()
        assert "127.0.0.1:6333" in str(client._client.rest_uri)
