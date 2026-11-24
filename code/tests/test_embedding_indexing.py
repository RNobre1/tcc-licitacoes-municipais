from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from qdrant_client.models import Distance, VectorParams

from semantic_index import (
    EmbeddingModel,
    SentenceTransformerEmbeddingModel,
    collection_name_for_model,
    index_public_items,
)
from tests.fake_embedding_model import FakeEmbeddingModel


class FakeQdrantIndexingClient:
    """In-memory fake client for testing index_public_items without network calls."""

    def __init__(self):
        self.collections: dict[str, VectorParams] = {}
        self.points: dict[str, list[Any]] = {}

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.collections

    def create_collection(self, collection_name: str, vectors_config: VectorParams) -> bool:
        self.collections[collection_name] = vectors_config
        self.points[collection_name] = []
        return True

    def get_collection(self, collection_name: str) -> Any:
        return SimpleNamespace(
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=self.collections[collection_name],
                )
            )
        )

    def upsert(self, collection_name: str, points: list[Any]) -> Any:
        if collection_name not in self.points:
            self.points[collection_name] = []
        self.points[collection_name].extend(points)
        return SimpleNamespace(status="completed")


def test_fake_embedding_model_implements_embedding_model_protocol():
    model = FakeEmbeddingModel(name="test-fake", revision="rev-1", dimension=16)
    assert isinstance(model, EmbeddingModel)
    assert model.name == "test-fake"
    assert model.revision == "rev-1"
    assert model.dimension == 16

    queries = ["caneta azul", "papel sulfite"]
    query_embeddings = model.embed_queries(queries)
    assert len(query_embeddings) == 2
    assert len(query_embeddings[0]) == 16

    passages = ["Caneta esferográfica azul 1.0mm", "Resma papel A4 75g"]
    passage_embeddings = model.embed_passages(passages)
    assert len(passage_embeddings) == 2
    assert len(passage_embeddings[0]) == 16


def test_collection_name_for_model_is_unique_per_model_and_revision():
    m1 = FakeEmbeddingModel(name="intfloat/multilingual-e5-base", revision="rev1")
    m2 = FakeEmbeddingModel(name="intfloat/multilingual-e5-base", revision="rev2")
    m3 = FakeEmbeddingModel(name="sentence-transformers/all-MiniLM-L6-v2", revision="rev1")

    name1 = collection_name_for_model(m1)
    name2 = collection_name_for_model(m2)
    name3 = collection_name_for_model(m3)

    assert name1 != name2
    assert name1 != name3
    assert name2 != name3

    # Clean alphanumeric identifiers with underscore
    assert "/" not in name1 and "-" not in name1
    assert "multilingual_e5_base" in name1
    assert "rev1" in name1


def test_sentence_transformer_embedding_model_pins_revision_and_applies_e5_prefixes():
    mock_st_instance = MagicMock()
    mock_st_instance.get_sentence_embedding_dimension.return_value = 768
    mock_st_instance.encode.side_effect = lambda texts, **kwargs: [[0.1] * 768 for _ in texts]

    with patch(
        "sentence_transformers.SentenceTransformer", return_value=mock_st_instance
    ) as mock_st_cls:
        model = SentenceTransformerEmbeddingModel(
            model_name="intfloat/multilingual-e5-base",
            revision="e4ce9877abf3ed52277057f97ab5083a31c50494",
        )

        mock_st_cls.assert_called_once_with(
            "intfloat/multilingual-e5-base",
            revision="e4ce9877abf3ed52277057f97ab5083a31c50494",
        )

        assert model.name == "intfloat/multilingual-e5-base"
        assert model.revision == "e4ce9877abf3ed52277057f97ab5083a31c50494"
        assert model.dimension == 768

        # Embed queries -> query: prefix
        queries = ["cadeira escritório"]
        q_vectors = model.embed_queries(queries)
        assert len(q_vectors) == 1
        assert len(q_vectors[0]) == 768
        mock_st_instance.encode.assert_called_with(
            ["query: cadeira escritório"], normalize_embeddings=True
        )

        # Embed passages -> passage: prefix
        passages = ["Cadeira giratória com braços"]
        p_vectors = model.embed_passages(passages)
        assert len(p_vectors) == 1
        assert len(p_vectors[0]) == 768
        mock_st_instance.encode.assert_called_with(
            ["passage: Cadeira giratória com braços"], normalize_embeddings=True
        )


def test_index_public_items_indexes_points_with_structured_filter_payload():
    client = FakeQdrantIndexingClient()
    model = FakeEmbeddingModel(dimension=16)

    # Simple objects with PublicItem interface
    item1 = SimpleNamespace(
        pk=101,
        description="DEMO-Papel A4 75g",
        unit=" Caixa com 10 resmas ",
        state="PA",
        published_on=date(2026, 10, 26),
        item_kind="product",
    )
    item2 = SimpleNamespace(
        pk=102,
        description="DEMO-Serviço de limpeza predial",
        unit="Mês",
        state="MA",
        published_on=date(2026, 10, 28),
        item_kind="service",
    )

    count = index_public_items(model=model, items=[item1, item2], client=client)
    assert count == 2

    coll_name = collection_name_for_model(model)
    assert client.collection_exists(coll_name)
    assert (
        client.collections[coll_name].size == 16
        and client.collections[coll_name].distance == Distance.COSINE
    )

    points = client.points[coll_name]
    assert len(points) == 2

    # Point 1: check id, vector dimension, and payload normalization
    p1 = points[0]
    assert p1.id == 101
    assert len(p1.vector) == 16
    assert p1.payload["unit"] == "caixa com 10 resmas"  # stripped and casefolded
    assert p1.payload["state"] == "PA"
    assert p1.payload["published_on"] == "2026-10-26"  # ISO sortable string
    assert p1.payload["item_kind"] == "product"

    # Point 2
    p2 = points[1]
    assert p2.id == 102
    assert len(p2.vector) == 16
    assert p2.payload["unit"] == "mês"  # stripped and casefolded
    assert p2.payload["state"] == "MA"
    assert p2.payload["published_on"] == "2026-10-28"
    assert p2.payload["item_kind"] == "service"
