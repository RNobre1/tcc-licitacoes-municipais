from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from qdrant_client import models
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

    def test_mismatch_error_is_subclass_of_value_error(self):
        """N8: CollectionConfigurationMismatchError must inherit from ValueError."""
        assert issubclass(CollectionConfigurationMismatchError, ValueError)

    @pytest.mark.parametrize(
        ("size", "distance"),
        [
            (64, Distance.DOT),
            (384, Distance.EUCLID),
            (1024, Distance.COSINE),
        ],
    )
    def test_create_collection_is_idempotent_when_configuration_matches(self, size, distance):
        client = FakeQdrantClient()
        assert (
            create_collection(
                client=client,
                collection_name="items",
                vector_size=size,
                distance=distance,
            )
            is True
        )
        assert (
            create_collection(
                client=client,
                collection_name="items",
                vector_size=size,
                distance=distance,
            )
            is True
        )

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
        # N9: Anchored pattern matching ensures configurations aren't swapped
        assert "Collection 'items' exists with configuration (128, Cosine)" in msg
        assert f"conflicting with requested ({size}, {distance.value})" in msg

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

    def test_payload_index_creation_errors_are_not_suppressed(self):
        client = FakeQdrantClient()
        client.create_payload_index = MagicMock(side_effect=RuntimeError("index unavailable"))

        with pytest.raises(RuntimeError, match="index unavailable"):
            create_collection(client, "items", vector_size=128, distance=Distance.COSINE)

    def test_losing_a_creation_race_with_the_same_configuration_is_success(self):
        assert create_collection(RacingClient(), "items", 128, Distance.COSINE) is True

    def test_losing_a_creation_race_to_another_configuration_is_an_error(self):
        client = RacingClient()
        client.created_as = VectorParams(size=256, distance=Distance.DOT)
        with pytest.raises(CollectionConfigurationMismatchError) as exc_info:
            create_collection(client, "items", 128, Distance.COSINE)

        msg = str(exc_info.value)
        assert "Collection 'items' exists with configuration (256, Dot)" in msg
        assert "conflicting with requested (128, Cosine)" in msg

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


class TestModalitySemanticIndex:
    """Tests for modality in Qdrant payload index and semantic search filtering."""

    @staticmethod
    def _search_client(payload_schema=None, missing_points=0):
        client = MagicMock()
        client.collection_exists.return_value = True
        client.get_collection.return_value = SimpleNamespace(payload_schema=payload_schema or {})
        client.count.return_value = SimpleNamespace(count=missing_points)
        client.query_points.return_value = SimpleNamespace(points=[])
        return client

    def test_modality_is_in_payload_index_fields(self):
        from semantic_index import PAYLOAD_INDEX_FIELDS

        assert ("modality", models.PayloadSchemaType.INTEGER) in PAYLOAD_INDEX_FIELDS

    def test_semantic_search_builds_modality_filter(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        mock_client = self._search_client(
            payload_schema={"modality": SimpleNamespace(data_type=models.PayloadSchemaType.INTEGER)}
        )

        model = FakeEmbeddingModel(dimension=16)
        s_filter = StructuredFilter(
            date_window=(date(2026, 1, 1), date(2026, 6, 1)),
            modality=["6", "7", "8"],  # type: ignore[list-item]
        )
        semantic_search(model=model, query="teste", structured_filter=s_filter, client=mock_client)

        call_args = mock_client.query_points.call_args
        query_filter = call_args.kwargs["query_filter"]
        cond = next(c for c in query_filter.must if getattr(c, "key", None) == "modality")
        assert isinstance(cond.match, models.MatchAny)
        assert cond.match.any == [6, 7, 8]
        assert mock_client.count.call_count == 1
        count_filter = mock_client.count.call_args.kwargs["count_filter"]
        empty_condition = count_filter.must[0]
        assert isinstance(empty_condition, models.IsEmptyCondition)
        assert empty_condition.is_empty.key == "modality"

        semantic_search(model=model, query="teste", structured_filter=s_filter, client=mock_client)
        assert mock_client.count.call_count == 1

    def test_semantic_search_rejects_a_collection_without_modality_index(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        client = self._search_client(
            payload_schema={
                "published_on": SimpleNamespace(data_type=models.PayloadSchemaType.DATETIME),
                "state": SimpleNamespace(data_type=models.PayloadSchemaType.KEYWORD),
                "unit": SimpleNamespace(data_type=models.PayloadSchemaType.KEYWORD),
                "item_kind": SimpleNamespace(data_type=models.PayloadSchemaType.KEYWORD),
            }
        )

        with pytest.raises(ValueError, match="modality.*payload index"):
            semantic_search(
                model=FakeEmbeddingModel(dimension=16),
                query="teste",
                structured_filter=StructuredFilter(
                    date_window=(date(2026, 1, 1), date(2026, 6, 1)),
                    modality=[6],
                ),
                client=client,
            )

        client.count.assert_not_called()
        client.query_points.assert_not_called()

    def test_semantic_search_rejects_points_missing_modality(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        client = self._search_client(
            payload_schema={
                "modality": SimpleNamespace(data_type=models.PayloadSchemaType.INTEGER)
            },
            missing_points=1,
        )

        with pytest.raises(ValueError, match="points.*modality"):
            semantic_search(
                model=FakeEmbeddingModel(dimension=16),
                query="teste",
                structured_filter=StructuredFilter(
                    date_window=(date(2026, 1, 1), date(2026, 6, 1)),
                    modality=[6],
                ),
                client=client,
            )

        client.count.assert_called_once()
        client.query_points.assert_not_called()

    def test_missing_modality_payload_count_is_cached_after_error(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        client = self._search_client(
            payload_schema={
                "modality": SimpleNamespace(data_type=models.PayloadSchemaType.INTEGER)
            },
            missing_points=1,
        )
        search_filter = StructuredFilter(
            date_window=(date(2026, 1, 1), date(2026, 6, 1)),
            modality=[6],
        )

        for _ in range(2):
            with pytest.raises(ValueError, match="points.*modality"):
                semantic_search(
                    model=FakeEmbeddingModel(dimension=16),
                    query="teste",
                    structured_filter=search_filter,
                    client=client,
                )

        client.count.assert_called_once()
        client.query_points.assert_not_called()

    def test_empty_modality_list_does_not_filter_or_check_collection_schema(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        client = self._search_client(payload_schema={})
        semantic_search(
            model=FakeEmbeddingModel(dimension=16),
            query="teste",
            structured_filter=StructuredFilter(
                date_window=(date(2026, 1, 1), date(2026, 6, 1)),
                modality=[],
            ),
            client=client,
        )

        query_filter = client.query_points.call_args.kwargs["query_filter"]
        assert all(getattr(condition, "key", None) != "modality" for condition in query_filter.must)
        client.get_collection.assert_not_called()
        client.count.assert_not_called()

    def test_semantic_search_rejects_invalid_modality_codes(self):
        from semantic_index import StructuredFilter, semantic_search
        from tests.fake_embedding_model import FakeEmbeddingModel

        with pytest.raises(ValueError, match="modality codes"):
            semantic_search(
                model=FakeEmbeddingModel(dimension=16),
                query="teste",
                structured_filter=StructuredFilter(
                    date_window=(date(2026, 1, 1), date(2026, 6, 1)),
                    modality=["not-a-code"],  # type: ignore[list-item]
                ),
                client=self._search_client(),
            )
