import contextlib
import uuid

import pytest
from qdrant_client import models

from semantic_index import check_health, create_collection, get_qdrant_client


@pytest.fixture
def live_qdrant_client():
    """Fixture providing a connected Qdrant client or failing with a clear make up hint."""
    client = get_qdrant_client()
    failure = None
    try:
        client.get_collections()
    except Exception as exc:
        failure = str(exc)

    if failure:
        client.close()
        pytest.fail(
            f"Could not connect to Qdrant: {failure}\nStart the services with 'make up' in code/.",
            pytrace=False,
        )

    try:
        yield client
    finally:
        client.close()


@pytest.mark.integration
class TestQdrantIntegration:
    """Integration tests verifying connectivity and collection management on live Qdrant."""

    def test_qdrant_health_check(self, live_qdrant_client):
        """Integration: verifies check_health reports True against the running Qdrant instance."""
        assert check_health(live_qdrant_client) is True

    def test_create_collection_idempotent_with_explicit_vector_params(self, live_qdrant_client):
        """Integration: creates collection twice with same parameters, asserting idempotency."""
        collection_name = f"test_semantic_index_{uuid.uuid4().hex[:8]}"
        try:
            res1 = create_collection(
                live_qdrant_client,
                collection_name=collection_name,
                vector_size=128,
                distance=models.Distance.COSINE,
            )
            assert res1 is True

            # Second call with identical arguments must succeed with identical result
            res2 = create_collection(
                live_qdrant_client,
                collection_name=collection_name,
                vector_size=128,
                distance=models.Distance.COSINE,
            )
            assert res2 is True

            assert live_qdrant_client.collection_exists(collection_name)
            info = live_qdrant_client.get_collection(collection_name)
            assert info.config.params.vectors.size == 128
            assert info.config.params.vectors.distance == models.Distance.COSINE
        finally:
            with contextlib.suppress(Exception):
                live_qdrant_client.delete_collection(collection_name)

    def test_service_down_clean_failure_handling(self):
        """Integration: verifies unreachable Qdrant raises connection error for clean reporting."""
        client = get_qdrant_client(url="http://127.0.0.1:59999")
        failure = None
        try:
            client.get_collections()
        except Exception as exc:
            failure = str(exc)
        finally:
            client.close()

        assert failure is not None
        assert "connection" in failure.lower() or "refused" in failure.lower()
        # check_health against dead service returns False without unhandled crash
        assert check_health(client) is False
