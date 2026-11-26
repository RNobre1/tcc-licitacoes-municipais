"""Pruning orphan points from the semantic index.

An orphan point is a Qdrant point whose id is not the primary key of any
PublicItem. Rebuilding public items can remove rows, and the index keeps their
points: search already discards them, but they inflate the indexed count and
waste space. These tests use an in-memory stand-in for the Qdrant client and
the test database; the real Qdrant path is covered in tests/integration.
"""

import math
from datetime import date
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ingestion.models import PublicItem
from ingestion.units import normalize_unit
from semantic_index.embedding import collection_name_for_model
from semantic_index.pruning import DEFAULT_PRUNE_BATCH_SIZE, PruneResult, prune_orphan_points


class InMemoryQdrant:
    """Minimal stand-in for the three QdrantClient calls that pruning needs."""

    def __init__(self, collections: dict[str, list[int]]) -> None:
        self.points = {name: sorted(ids) for name, ids in collections.items()}
        self.scroll_calls: list[dict] = []
        self.deleted: list[int] = []
        self.delete_calls = 0

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.points

    def scroll(
        self,
        collection_name,
        limit=10,
        offset=None,
        with_payload=True,
        with_vectors=False,
        **kwargs,
    ):
        self.scroll_calls.append(
            {
                "limit": limit,
                "offset": offset,
                "with_payload": with_payload,
                "with_vectors": with_vectors,
            }
        )
        ids = self.points[collection_name]
        remaining = [i for i in ids if offset is None or i >= offset]
        page = remaining[:limit]
        next_offset = remaining[limit] if len(remaining) > limit else None
        return [SimpleNamespace(id=i, payload=None, vector=None) for i in page], next_offset

    def delete(self, collection_name, points_selector, wait=True, **kwargs):
        self.delete_calls += 1
        ids = list(getattr(points_selector, "points", points_selector))
        self.deleted.extend(ids)
        self.points[collection_name] = [i for i in self.points[collection_name] if i not in ids]


def _create_item(number: int) -> PublicItem:
    return PublicItem.objects.create(
        cnpj="00000000000007",
        year=2026,
        purchase_sequence=1,
        item_number=number,
        description=f"Item fictício DEMO-{number}",
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


def _orphan_ids(count: int) -> list[int]:
    top = PublicItem.objects.order_by("-pk").values_list("pk", flat=True).first() or 0
    return [top + 1000 + i for i in range(count)]


COLLECTION = "items_test_prune"


@pytest.mark.django_db
def test_dry_run_counts_orphans_and_deletes_nothing():
    live = [_create_item(n).pk for n in range(1, 4)]
    orphans = _orphan_ids(2)
    client = InMemoryQdrant({COLLECTION: live + orphans})

    result = prune_orphan_points(client, COLLECTION, dry_run=True)

    assert result == PruneResult(
        collection_name=COLLECTION, scanned=5, orphans=2, deleted=0, dry_run=True
    )
    assert client.deleted == []
    assert client.delete_calls == 0
    assert client.points[COLLECTION] == sorted(live + orphans)


@pytest.mark.django_db
def test_prune_deletes_only_orphans_and_keeps_every_live_point():
    live = [_create_item(n).pk for n in range(1, 4)]
    orphans = _orphan_ids(2)
    client = InMemoryQdrant({COLLECTION: live + orphans})

    result = prune_orphan_points(client, COLLECTION)

    assert result == PruneResult(
        collection_name=COLLECTION, scanned=5, orphans=2, deleted=2, dry_run=False
    )
    assert sorted(client.deleted) == sorted(orphans)
    assert client.points[COLLECTION] == sorted(live)


@pytest.mark.django_db
def test_prune_is_idempotent():
    live = [_create_item(n).pk for n in range(1, 3)]
    client = InMemoryQdrant({COLLECTION: live + _orphan_ids(3)})

    prune_orphan_points(client, COLLECTION)
    second = prune_orphan_points(client, COLLECTION)

    assert second == PruneResult(
        collection_name=COLLECTION, scanned=2, orphans=0, deleted=0, dry_run=False
    )
    assert client.points[COLLECTION] == sorted(live)


@pytest.mark.django_db
def test_prune_with_no_orphans_never_calls_delete():
    live = [_create_item(n).pk for n in range(1, 4)]
    client = InMemoryQdrant({COLLECTION: live})

    result = prune_orphan_points(client, COLLECTION)

    assert result.orphans == 0
    assert result.deleted == 0
    assert client.delete_calls == 0


@pytest.mark.django_db
def test_prune_scrolls_in_batches_without_vectors_or_payload():
    live = [_create_item(n).pk for n in range(1, 21)]
    orphans = _orphan_ids(5)
    client = InMemoryQdrant({COLLECTION: live + orphans})

    result = prune_orphan_points(client, COLLECTION, batch_size=10)

    assert result.scanned == 25
    assert result.deleted == 5
    assert len(client.scroll_calls) == math.ceil(25 / 10)
    assert all(call["limit"] == 10 for call in client.scroll_calls)
    assert all(call["with_vectors"] is False for call in client.scroll_calls)
    assert all(call["with_payload"] is False for call in client.scroll_calls)
    assert client.points[COLLECTION] == sorted(live)


@pytest.mark.django_db
def test_prune_issues_one_database_query_per_batch(django_assert_num_queries):
    live = [_create_item(n).pk for n in range(1, 21)]
    client = InMemoryQdrant({COLLECTION: live + _orphan_ids(5)})

    with django_assert_num_queries(math.ceil(25 / 10)):
        prune_orphan_points(client, COLLECTION, batch_size=10)


@pytest.mark.django_db
def test_prune_of_empty_collection_scans_nothing():
    client = InMemoryQdrant({COLLECTION: []})

    result = prune_orphan_points(client, COLLECTION)

    assert result == PruneResult(
        collection_name=COLLECTION, scanned=0, orphans=0, deleted=0, dry_run=False
    )
    assert client.delete_calls == 0


@pytest.mark.django_db
def test_prune_refuses_a_missing_collection():
    client = InMemoryQdrant({})

    with pytest.raises(ValueError, match="does not exist"):
        prune_orphan_points(client, "items_missing_collection")

    assert client.scroll_calls == []
    assert client.delete_calls == 0


@pytest.mark.parametrize("bad_batch_size", [0, -1])
def test_prune_rejects_a_non_positive_batch_size(bad_batch_size):
    client = InMemoryQdrant({COLLECTION: []})

    with pytest.raises(ValueError, match="batch_size"):
        prune_orphan_points(client, COLLECTION, batch_size=bad_batch_size)


def test_default_batch_size_is_one_thousand():
    assert DEFAULT_PRUNE_BATCH_SIZE == 1000


def _command_collection(model: str, revision: str) -> str:
    return collection_name_for_model(SimpleNamespace(name=model, revision=revision))


@pytest.fixture
def command_module(monkeypatch):
    """Load the command module and forbid any real model load or real Qdrant client."""
    import sentence_transformers

    def _no_model_load(*args, **kwargs):
        raise AssertionError("prune_index must never load an embedding model")

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", _no_model_load)
    from semantic_index.management.commands import prune_index

    return prune_index


@pytest.mark.django_db
def test_command_dry_run_reports_counts_and_deletes_nothing(command_module, monkeypatch):
    live = [_create_item(n).pk for n in range(1, 4)]
    orphans = _orphan_ids(2)
    name = _command_collection("fake/model-a", "rev-1")
    client = InMemoryQdrant({name: live + orphans})
    monkeypatch.setattr(command_module, "get_qdrant_client", lambda *a, **k: client)
    out = StringIO()

    call_command(
        "prune_index", "--model", "fake/model-a", "--revision", "rev-1", "--dry-run", stdout=out
    )

    text = out.getvalue()
    assert f"Collection: {name}" in text
    assert "Scanned: 5" in text
    assert "Orphans: 2" in text
    assert "Deleted: 0" in text
    assert "Dry run" in text
    assert client.delete_calls == 0


@pytest.mark.django_db
def test_command_deletes_orphans_and_reports_counts(command_module, monkeypatch):
    live = [_create_item(n).pk for n in range(1, 4)]
    orphans = _orphan_ids(2)
    name = _command_collection("fake/model-b", "rev-2")
    client = InMemoryQdrant({name: live + orphans})
    monkeypatch.setattr(command_module, "get_qdrant_client", lambda *a, **k: client)
    out = StringIO()

    call_command(
        "prune_index",
        "--model",
        "fake/model-b",
        "--revision",
        "rev-2",
        "--batch-size",
        "2",
        stdout=out,
    )

    text = out.getvalue()
    assert "Scanned: 5" in text
    assert "Orphans: 2" in text
    assert "Deleted: 2" in text
    assert "Dry run" not in text
    assert client.points[name] == sorted(live)
    assert all(call["limit"] == 2 for call in client.scroll_calls)


@pytest.mark.django_db
def test_command_refuses_a_missing_collection(command_module, monkeypatch):
    client = InMemoryQdrant({})
    monkeypatch.setattr(command_module, "get_qdrant_client", lambda *a, **k: client)

    with pytest.raises(CommandError, match="does not exist"):
        call_command("prune_index", "--model", "fake/model-c", "--revision", "rev-3")


def test_command_defaults_match_the_index_command(command_module):
    from semantic_index.management.commands import index_public_items

    assert command_module.DEFAULT_MODEL == index_public_items.DEFAULT_MODEL
    assert command_module.DEFAULT_REVISION == index_public_items.DEFAULT_REVISION
