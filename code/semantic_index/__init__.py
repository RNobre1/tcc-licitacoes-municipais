"""Semantic index client and collection management for Qdrant."""

import os
from typing import Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse


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


def create_collection(
    client: Any,
    collection_name: str,
    vector_size: int,
    distance: models.Distance,
) -> bool:
    """Create a collection idempotently. Calling twice produces the same effect as once."""
    if client.collection_exists(collection_name):
        _assert_matching_configuration(client, collection_name, vector_size, distance)
        return True

    vectors_config = models.VectorParams(size=vector_size, distance=distance)
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )
        return True
    except UnexpectedResponse as exc:
        if exc.status_code == 409:
            _assert_matching_configuration(client, collection_name, vector_size, distance)
            return True
        raise
