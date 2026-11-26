from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
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

    pinned_rev = "d13f1b27baf31030b7fd040960d60d909913633f"
    with patch(
        "sentence_transformers.SentenceTransformer", return_value=mock_st_instance
    ) as mock_st_cls:
        model = SentenceTransformerEmbeddingModel(
            model_name="intfloat/multilingual-e5-base",
            revision=pinned_rev,
        )

        mock_st_cls.assert_called_once_with(
            "intfloat/multilingual-e5-base",
            revision=pinned_rev,
        )

        assert model.name == "intfloat/multilingual-e5-base"
        assert model.revision == pinned_rev
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
        unit_normalized="caixa com 10 resmas",
        state="PA",
        published_on=date(2026, 10, 26),
        item_kind="product",
        modality=6,
    )
    item2 = SimpleNamespace(
        pk=102,
        description="DEMO-Serviço de limpeza predial",
        unit="Mês",
        unit_normalized="mês",
        state="MA",
        published_on=date(2026, 10, 28),
        item_kind="service",
        modality=8,
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
    assert p1.payload["modality"] == 6

    # Point 2
    p2 = points[1]
    assert p2.id == 102
    assert len(p2.vector) == 16
    assert p2.payload["unit"] == "mês"  # stripped and casefolded
    assert p2.payload["state"] == "MA"
    assert p2.payload["published_on"] == "2026-10-28"
    assert p2.payload["item_kind"] == "service"
    assert p2.payload["modality"] == 8


def test_index_public_items_uses_the_stored_normalized_unit():
    client = FakeQdrantIndexingClient()
    model = FakeEmbeddingModel(dimension=16)
    item = SimpleNamespace(
        pk=103,
        description="DEMO-Item com unidade pré-calculada",
        unit="Raw source unit",
        unit_normalized="stored canonical value",
        state="PA",
        published_on=date(2026, 10, 29),
        item_kind="product",
        modality=6,
    )

    assert index_public_items(model=model, items=[item], client=client) == 1

    collection_name = collection_name_for_model(model)
    assert client.points[collection_name][0].payload["unit"] == "stored canonical value"


def test_index_public_items_refuses_non_blank_unit_with_blank_unit_normalized():
    client = FakeQdrantIndexingClient()
    model = FakeEmbeddingModel(dimension=16)

    valid_item = SimpleNamespace(
        pk=1,
        description="DEMO-Caneta",
        unit="KG",
        unit_normalized="kg",
        state="PA",
        published_on=date(2026, 10, 29),
        item_kind="product",
        modality=6,
    )
    blank_item = SimpleNamespace(
        pk=2,
        description="DEMO-Sem unidade",
        unit="   ",
        unit_normalized="",
        state="PA",
        published_on=date(2026, 10, 29),
        item_kind="product",
        modality=6,
    )
    bad_item_1 = SimpleNamespace(
        pk=3,
        description="DEMO-Caixa sem normalizacao",
        unit="Caixa ",
        unit_normalized="",
        state="PA",
        published_on=date(2026, 10, 29),
        item_kind="product",
        modality=6,
    )
    bad_item_2 = SimpleNamespace(
        pk=4,
        description="DEMO-Resma sem normalizacao",
        unit="RESMA",
        unit_normalized="   ",
        state="PA",
        published_on=date(2026, 10, 29),
        item_kind="product",
        modality=6,
    )

    with pytest.raises(ValueError, match=r"\b2\b"):
        index_public_items(
            model=model,
            items=[valid_item, blank_item, bad_item_1, bad_item_2],
            client=client,
        )

    assert not client.collection_exists(collection_name_for_model(model))


@pytest.mark.integration
@pytest.mark.django_db
def test_index_public_items_queryset_refuses_unnormalized_rows_and_reports_count():
    from decimal import Decimal

    from ingestion.models import PublicItem

    PublicItem.objects.create(
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="DEMO-Old row without normalized unit",
        unit="Caixa ",
        unit_normalized="",
        quantity=Decimal("1.0000"),
        estimated_unit_price=Decimal("10.0000"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 10, 29),
        agency_name="Prefeitura Teste",
        agency_cnpj="00000000000001",
        state="PA",
        modality=6,
        item_kind="product",
    )

    client = FakeQdrantIndexingClient()
    model = FakeEmbeddingModel(dimension=16)

    with pytest.raises(ValueError, match=r"\b1\b"):
        index_public_items(model=model, items=PublicItem.objects.all(), client=client)

    assert not client.collection_exists(collection_name_for_model(model))
