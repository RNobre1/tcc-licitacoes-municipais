from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from ingestion.models import PublicItem
from semantic_index import (
    ScoredPublicItem,
    StructuredFilter,
    collection_name_for_model,
    get_qdrant_client,
    index_public_items,
    semantic_search,
)
from tests.fake_embedding_model import FakeEmbeddingModel


@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search_requires_mandatory_date_window():
    model = FakeEmbeddingModel(name="test-model", revision="rev1")
    with pytest.raises(ValueError, match="date_window is mandatory"):
        semantic_search(
            model=model,
            query="cadeira",
            structured_filter={},
        )

    with pytest.raises(ValueError, match="date_window is mandatory"):
        semantic_search(
            model=model,
            query="cadeira",
            structured_filter=StructuredFilter(date_window=None),  # type: ignore[arg-type]
        )


@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search_end_to_end_integration():
    client = get_qdrant_client()
    unique_rev = f"test_{uuid4().hex[:8]}"
    model = FakeEmbeddingModel(name="integration-model", revision=unique_rev, dimension=16)
    coll_name = collection_name_for_model(model)

    try:
        # 1. Create PublicItem rows in the PostgreSQL test database
        item_a = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=1,
            description="Cadeira giratória com braços ergonômica para escritório",
            unit="UNIDADE",
            quantity=Decimal("10.0000"),
            estimated_unit_price=Decimal("450.0000"),
            awarded_unit_price=Decimal("420.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        item_b = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=2,
            description="Cadeira executiva estofada",
            unit=" unidade ",
            quantity=Decimal("5.0000"),
            estimated_unit_price=Decimal("600.0000"),
            awarded_unit_price=Decimal("580.0000"),
            secret_budget=False,
            published_on=date(2026, 7, 20),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # Outside date window (2025)
        item_outside_date = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2025,
            purchase_sequence=2,
            item_number=1,
            description="Cadeira presidente preta",
            unit="UNIDADE",
            quantity=Decimal("2.0000"),
            estimated_unit_price=Decimal("800.0000"),
            awarded_unit_price=Decimal("750.0000"),
            secret_budget=False,
            published_on=date(2025, 1, 10),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # Different state (MA)
        item_diff_state = PublicItem.objects.create(
            cnpj="00000000000002",
            year=2026,
            purchase_sequence=1,
            item_number=1,
            description="Cadeira para escritório giratória",
            unit="UNIDADE",
            quantity=Decimal("8.0000"),
            estimated_unit_price=Decimal("400.0000"),
            awarded_unit_price=Decimal("380.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Outro Órgão",
            agency_cnpj="00000000000002",
            state="MA",
            modality=6,
            item_kind="product",
        )
        # Different item_kind (service)
        item_service = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=3,
            item_number=1,
            description="Manutenção preventiva de cadeiras de escritório",
            unit="SERVIÇO",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("1200.0000"),
            awarded_unit_price=None,
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="service",
        )
        # Ghost candidate: indexed in Qdrant but deleted from PostgreSQL
        item_ghost = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=4,
            item_number=1,
            description="Cadeira removida do banco relacional",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("300.0000"),
            awarded_unit_price=Decimal("290.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )

        all_items = [
            item_a,
            item_b,
            item_outside_date,
            item_diff_state,
            item_service,
            item_ghost,
        ]

        # 2. Index all items into Qdrant
        indexed_count = index_public_items(model=model, items=all_items, client=client)
        assert indexed_count == 6
        assert client.collection_exists(coll_name)

        # 3. Delete item_ghost from PostgreSQL to test ghost prevention
        ghost_pk = item_ghost.pk
        item_ghost.delete()
        assert not PublicItem.objects.filter(pk=ghost_pk).exists()

        # 4. Perform search under mandatory date window and optional filters
        date_filter = StructuredFilter(
            date_window=(date(2026, 1, 1), date(2026, 12, 31)),
            state="PA",
            unit="unidade",
            item_kind="product",
        )

        results = semantic_search(
            model=model,
            query="cadeira giratória de escritório",
            structured_filter=date_filter,
            limit=10,
            client=client,
        )

        # 5. Assert results
        # Only item_a and item_b match all filters (date 2026, PA, unit unidade, product)
        result_pks = [r.item.pk for r in results]
        assert set(result_pks) == {item_a.pk, item_b.pk}

        # Item outside date window is excluded
        assert item_outside_date.pk not in result_pks
        # Item with state MA is excluded
        assert item_diff_state.pk not in result_pks
        # Service item is excluded
        assert item_service.pk not in result_pks
        # Ghost item deleted from PostgreSQL is not returned
        assert ghost_pk not in result_pks

        # Assert hydration and score ordering
        for scored in results:
            assert isinstance(scored, ScoredPublicItem)
            assert isinstance(scored.item, PublicItem)
            assert isinstance(scored.score, float)

        # Scores are in descending order
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

        # Unpackable as tuple (item, score)
        first_item, first_score = results[0]
        assert first_item.pk in {item_a.pk, item_b.pk}
        assert isinstance(first_score, float)

    finally:
        # Drop the test collection so no trace is left behind
        if client.collection_exists(coll_name):
            client.delete_collection(coll_name)
        assert not client.collection_exists(coll_name)
