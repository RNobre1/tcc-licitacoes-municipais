"""Pruning orphan points against a real Qdrant and the test database."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from ingestion.models import PublicItem
from ingestion.units import normalize_unit
from semantic_index import collection_name_for_model, get_qdrant_client, index_public_items
from semantic_index.pruning import PruneResult, prune_orphan_points
from tests.fake_embedding_model import FakeEmbeddingModel


def _create_item(number: int) -> PublicItem:
    return PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=2,
        item_number=number,
        description=f"Item fictício DEMO-poda-{number}",
        unit="UNIDADE",
        unit_normalized=normalize_unit("UNIDADE"),
        quantity=Decimal("1.0000"),
        estimated_unit_price=Decimal("10.0000"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 6, 15),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="00000000000007",
        state="PA",
        modality=6,
        item_kind="product",
    )


def _point_ids(client, collection_name: str) -> list[int]:
    ids: list[int] = []
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        ids.extend(int(r.id) for r in records)
        if offset is None:
            return sorted(ids)


@pytest.mark.integration
@pytest.mark.django_db
def test_prune_removes_points_of_deleted_items_from_a_real_collection():
    client = get_qdrant_client()
    model = FakeEmbeddingModel(name="prune-model", revision=f"prune_{uuid4().hex[:8]}")
    name = collection_name_for_model(model)
    try:
        items = [_create_item(n) for n in range(1, 6)]
        index_public_items(model=model, items=items, client=client)
        deleted_pks = [items[0].pk, items[3].pk]
        PublicItem.objects.filter(pk__in=deleted_pks).delete()
        live_pks = sorted(it.pk for it in items if it.pk not in deleted_pks)

        dry = prune_orphan_points(client, name, batch_size=2, dry_run=True)
        assert dry == PruneResult(
            collection_name=name, scanned=5, orphans=2, deleted=0, dry_run=True
        )
        assert len(_point_ids(client, name)) == 5

        real = prune_orphan_points(client, name, batch_size=2)
        assert real == PruneResult(
            collection_name=name, scanned=5, orphans=2, deleted=2, dry_run=False
        )
        assert _point_ids(client, name) == live_pks

        again = prune_orphan_points(client, name, batch_size=2)
        assert again == PruneResult(
            collection_name=name, scanned=3, orphans=0, deleted=0, dry_run=False
        )
        assert _point_ids(client, name) == live_pks
    finally:
        if client.collection_exists(name):
            client.delete_collection(name)
        assert not client.collection_exists(name)


@pytest.mark.integration
@pytest.mark.django_db
def test_prune_refuses_a_missing_real_collection_without_creating_it():
    client = get_qdrant_client()
    name = f"items_missing_prune_{uuid4().hex[:8]}"

    with pytest.raises(ValueError, match="does not exist"):
        prune_orphan_points(client, name)

    assert not client.collection_exists(name)
