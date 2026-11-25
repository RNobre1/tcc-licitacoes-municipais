"""Semantic index client, collection management, and embedding models for Qdrant."""

import contextlib
import os
from typing import Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from semantic_index.embedding import (
    EmbeddingModel,
    SentenceTransformerEmbeddingModel,
    collection_name_for_model,
)
from semantic_index.indexing import index_public_items
from semantic_index.search import ScoredPublicItem, StructuredFilter, semantic_search

__all__ = [
    "CollectionConfigurationMismatchError",
    "EmbeddingModel",
    "PAYLOAD_INDEX_FIELDS",
    "ScoredPublicItem",
    "SentenceTransformerEmbeddingModel",
    "StructuredFilter",
    "check_health",
    "collection_name_for_model",
    "create_collection",
    "get_qdrant_client",
    "index_public_items",
    "semantic_search",
]

PAYLOAD_INDEX_FIELDS = [
    ("published_on", models.PayloadSchemaType.DATETIME),
    ("state", models.PayloadSchemaType.KEYWORD),
    ("unit", models.PayloadSchemaType.KEYWORD),
    ("item_kind", models.PayloadSchemaType.KEYWORD),
    ("modality", models.PayloadSchemaType.INTEGER),
]


class CollectionConfigurationMismatchError(ValueError):
    """Raised when an existing collection has a different vector size or distance."""


def get_qdrant_client(url: str | None = None) -> QdrantClient:
    """Return a configured QdrantClient instance resolving URL from argument or environment."""
    target_url = url or os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    return QdrantClient(url=target_url, check_compatibility=False)


def check_health(client: Any) -> bool:
    """Check whether Qdrant service is reachable and healthy."""
    try:
        client.get_collections()
        return True
    except Exception:
        return False


def _assert_matching_configuration(
    client: Any,
    collection_name: str,
    vector_size: int,
    distance: models.Distance,
) -> None:
    info = client.get_collection(collection_name)
    existing_vectors = info.config.params.vectors
    if (existing_vectors.size, existing_vectors.distance) != (vector_size, distance):
        raise CollectionConfigurationMismatchError(
            f"Collection '{collection_name}' exists with configuration "
            f"({existing_vectors.size}, {existing_vectors.distance}), "
            f"conflicting with requested ({vector_size}, {distance})"
        )


def _ensure_payload_indexes(client: Any, collection_name: str) -> None:
    """Ensure payload indexes exist on filtered fields."""
    if not hasattr(client, "create_payload_index"):
        return
    for field_name, field_schema in PAYLOAD_INDEX_FIELDS:
        with contextlib.suppress(Exception):
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
            )


def create_collection(
    client: Any,
    collection_name: str,
    vector_size: int,
    distance: models.Distance,
) -> bool:
    """Create a collection idempotently with payload indexes on filtered fields."""
    if client.collection_exists(collection_name):
        _assert_matching_configuration(client, collection_name, vector_size, distance)
        _ensure_payload_indexes(client, collection_name)
        return True

    vectors_config = models.VectorParams(size=vector_size, distance=distance)
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )
        _ensure_payload_indexes(client, collection_name)
        return True
    except UnexpectedResponse as exc:
        if exc.status_code == 409:
            _assert_matching_configuration(client, collection_name, vector_size, distance)
            _ensure_payload_indexes(client, collection_name)
            return True
        raise
