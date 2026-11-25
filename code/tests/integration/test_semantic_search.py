from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from qdrant_client import models

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
def test_semantic_search_validates_date_window():
    model = FakeEmbeddingModel(name="test-model", revision="rev1")

    # Missing date window
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

    # Inverted date window (start > end)
    with pytest.raises(ValueError, match="Inverted date_window"):
        semantic_search(
            model=model,
            query="cadeira",
            structured_filter=StructuredFilter(date_window=(date(2026, 12, 31), date(2026, 1, 1))),
        )

    # Date window exceeding 12 months (RN07)
    with pytest.raises(ValueError, match="date_window exceeds 12-month limit"):
        semantic_search(
            model=model,
            query="cadeira",
            structured_filter=StructuredFilter(date_window=(date(2024, 1, 1), date(2026, 1, 1))),
        )


@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search_raises_on_missing_collection():
    client = get_qdrant_client()
    model = FakeEmbeddingModel(name="missing-model", revision=f"rev_{uuid4().hex[:8]}")
    with pytest.raises(ValueError, match="does not exist"):
        semantic_search(
            model=model,
            query="cadeira",
            structured_filter=StructuredFilter(date_window=(date(2026, 1, 1), date(2026, 6, 1))),
            client=client,
        )


@pytest.mark.integration
def test_semantic_search_rejects_old_collection_without_modality_payload():
    client = get_qdrant_client()
    model = FakeEmbeddingModel(name="old-collection-model", revision=f"old_{uuid4().hex[:8]}")
    collection_name = collection_name_for_model(model)

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=16, distance=models.Distance.COSINE),
        )
        for field_name, field_schema in [
            ("published_on", models.PayloadSchemaType.DATETIME),
            ("state", models.PayloadSchemaType.KEYWORD),
            ("unit", models.PayloadSchemaType.KEYWORD),
            ("item_kind", models.PayloadSchemaType.KEYWORD),
        ]:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema,
            )
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=1,
                    vector=[0.0] * 16,
                    payload={
                        "published_on": "2026-04-01",
                        "state": "PA",
                        "unit": "unidade",
                        "item_kind": "product",
                    },
                )
            ],
        )

        with pytest.raises(ValueError, match="modality.*payload index"):
            semantic_search(
                model=model,
                query="cadeira",
                structured_filter=StructuredFilter(
                    date_window=(date(2026, 1, 1), date(2026, 6, 1)),
                    modality=[6],
                ),
                client=client,
            )
    finally:
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)


@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search_overfetches_so_dropped_ghosts_do_not_shrink_results():
    client = get_qdrant_client()
    unique_rev = f"ghost_{uuid4().hex[:8]}"
    model = FakeEmbeddingModel(name="ghost-model", revision=unique_rev, dimension=16)
    coll_name = collection_name_for_model(model)

    try:
        # Create 3 valid items
        item1 = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=1,
            description="Item ghost 1",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("10.0000"),
            awarded_unit_price=Decimal("10.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        item2 = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=2,
            description="Item ghost 2",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("20.0000"),
            awarded_unit_price=Decimal("20.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        item3 = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=3,
            description="Item ghost 3",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("30.0000"),
            awarded_unit_price=Decimal("30.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )

        index_public_items(model=model, items=[item1, item2, item3], client=client)

        # Delete item1 from Postgres so it becomes a ghost point in Qdrant
        ghost_pk = item1.pk
        item1.delete()

        # Search with limit=2. Even though item1 is a ghost, search should return 2 items
        # (item2 and item3)
        results = semantic_search(
            model=model,
            query="Item ghost",
            structured_filter=StructuredFilter(
                date_window=(date(2026, 1, 1), date(2026, 12, 31)),
            ),
            limit=2,
            client=client,
        )

        assert len(results) == 2
        pks = [r.item.pk for r in results]
        assert ghost_pk not in pks
        assert pks == [item2.pk, item3.pk]

    finally:
        if client.collection_exists(coll_name):
            client.delete_collection(coll_name)


@pytest.mark.integration
@pytest.mark.django_db
def test_semantic_search_end_to_end_integration():
    client = get_qdrant_client()
    unique_rev = f"test_{uuid4().hex[:8]}"
    model = FakeEmbeddingModel(name="integration-model", revision=unique_rev, dimension=16)
    coll_name = collection_name_for_model(model)

    try:
        # 1. Create PublicItem rows in the PostgreSQL test database
        # Base item matching all filters
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
        # Second item matching all filters
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
        # N1: Differs ONLY in unit ("caixa" vs "unidade")
        item_diff_unit_only = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=3,
            description="Cadeira embalagem coletiva",
            unit="CAIXA",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("1000.0000"),
            awarded_unit_price=Decimal("950.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # N1: Differs ONLY in item_kind ("service" vs "product", with same unit "unidade")
        item_diff_kind_only = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=1,
            item_number=4,
            description="Serviço de montagem de cadeira",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("50.0000"),
            awarded_unit_price=Decimal("50.0000"),
            secret_budget=False,
            published_on=date(2026, 6, 15),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="service",
        )
        # N1: Date window boundaries: window will be 2026-03-01 to 2026-08-31
        # start - 1 day (2026-02-28) -> excluded
        item_start_minus_1 = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=2,
            item_number=1,
            description="Cadeira antes da janela",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("100.0000"),
            awarded_unit_price=Decimal("100.0000"),
            secret_budget=False,
            published_on=date(2026, 2, 28),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # start boundary (2026-03-01) -> included
        item_at_start = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=2,
            item_number=2,
            description="Cadeira no início da janela",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("100.0000"),
            awarded_unit_price=Decimal("100.0000"),
            secret_budget=False,
            published_on=date(2026, 3, 1),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # end boundary (2026-08-31) -> included
        item_at_end = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=2,
            item_number=3,
            description="Cadeira no fim da janela",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("100.0000"),
            awarded_unit_price=Decimal("100.0000"),
            secret_budget=False,
            published_on=date(2026, 8, 31),
            agency_name="Prefeitura Teste",
            agency_cnpj="00000000000001",
            state="PA",
            modality=6,
            item_kind="product",
        )
        # end + 1 day (2026-09-01) -> excluded
        item_end_plus_1 = PublicItem.objects.create(
            cnpj="00000000000001",
            year=2026,
            purchase_sequence=2,
            item_number=4,
            description="Cadeira após a janela",
            unit="UNIDADE",
            quantity=Decimal("1.0000"),
            estimated_unit_price=Decimal("100.0000"),
            awarded_unit_price=Decimal("100.0000"),
            secret_budget=False,
            published_on=date(2026, 9, 1),
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
            item_diff_unit_only,
            item_diff_kind_only,
            item_start_minus_1,
            item_at_start,
            item_at_end,
            item_end_plus_1,
            item_diff_state,
            item_ghost,
        ]

        # 2. Index all items into Qdrant
        indexed_count = index_public_items(model=model, items=all_items, client=client)
        assert indexed_count == len(all_items)
        assert client.collection_exists(coll_name)

        # 3. Delete item_ghost from PostgreSQL to test ghost prevention
        ghost_pk = item_ghost.pk
        item_ghost.delete()
        assert not PublicItem.objects.filter(pk=ghost_pk).exists()

        # 4. Perform search under mandatory date window (2026-03-01 to 2026-08-31) and unnormalized
        # query unit "  UNIDADE  "
        date_filter = StructuredFilter(
            date_window=(date(2026, 3, 1), date(2026, 8, 31)),
            state="PA",
            unit="  UNIDADE  ",  # N1: unnormalized unit query
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
        # Matching items: item_a, item_b, item_at_start, item_at_end
        result_pks = [r.item.pk for r in results]
        expected_pks = {item_a.pk, item_b.pk, item_at_start.pk, item_at_end.pk}
        assert set(result_pks) == expected_pks

        # N1: item differing ONLY in unit is excluded
        assert item_diff_unit_only.pk not in result_pks
        # N1: item differing ONLY in item_kind is excluded
        assert item_diff_kind_only.pk not in result_pks
        # N1: Boundary start - 1 day is excluded
        assert item_start_minus_1.pk not in result_pks
        # N1: Boundary end + 1 day is excluded
        assert item_end_plus_1.pk not in result_pks
        # Different state is excluded
        assert item_diff_state.pk not in result_pks
        # Ghost item is excluded
        assert ghost_pk not in result_pks

        # Assert hydration and score ordering
        for scored in results:
            assert isinstance(scored, ScoredPublicItem)
            assert isinstance(scored.item, PublicItem)
            assert isinstance(scored.score, float)

        # Scores are in descending order
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    finally:
        # Drop the test collection so no trace is left behind
        if client.collection_exists(coll_name):
            client.delete_collection(coll_name)
        assert not client.collection_exists(coll_name)
