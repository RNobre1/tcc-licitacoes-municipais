"""Semantic index client and collection management for Qdrant."""

import os
from typing import Any

from qdrant_client import QdrantClient, models


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


def create_collection(
    client: Any,
    collection_name: str,
    vector_size: int,
    distance: str | models.Distance,
) -> bool:
    """Create a collection idempotently. Calling twice produces the same effect as once."""
    if isinstance(distance, str):
        distance_enum = getattr(models.Distance, distance.upper(), None)
        if distance_enum is None:
            distance_enum = models.Distance(distance)
    else:
        distance_enum = distance

    if client.collection_exists(collection_name):
        return True

    vectors_config = models.VectorParams(size=vector_size, distance=distance_enum)
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )
        return True
    except Exception as exc:
        if "already exists" in str(exc) or "409" in str(exc):
            return True
        raise
