import io
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from ingestion.models import PublicItem
from semantic_index.management.commands.index_public_items import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    Command,
)
from tests.fake_embedding_model import FakeEmbeddingModel


def test_command_help_and_arguments_contain_pinned_revision():
    cmd = Command()
    parser = cmd.create_parser("manage.py", "index_public_items")
    help_text = parser.format_help()

    assert "--model" in help_text
    assert DEFAULT_MODEL in help_text
    assert "--revision" in help_text
    assert DEFAULT_REVISION in help_text
    assert "--start" in help_text
    assert "--end" in help_text


@pytest.mark.integration
@pytest.mark.django_db
def test_index_public_items_command_runs_with_injected_embedding_model():
    # Create test PublicItems
    PublicItem.objects.create(
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="DEMO-Item 1 para indexação",
        unit="UNIDADE",
        unit_normalized="unidade",
        quantity=Decimal("10.0000"),
        estimated_unit_price=Decimal("100.0000"),
        awarded_unit_price=Decimal("95.0000"),
        secret_budget=False,
        published_on=date(2026, 10, 26),
        agency_name="Prefeitura Teste",
        agency_cnpj="00000000000001",
        state="PA",
        modality=6,
        item_kind="product",
    )

    fake_model = FakeEmbeddingModel(name="test-model", revision="rev1", dimension=16)

    out = io.StringIO()
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False

    with (
        patch(
            "semantic_index.management.commands.index_public_items.SentenceTransformerEmbeddingModel",
            return_value=fake_model,
        ),
        patch("semantic_index.get_qdrant_client", return_value=mock_client),
    ):
        call_command(
            "index_public_items",
            model="test-model",
            revision="rev1",
            stdout=out,
        )

    output = out.getvalue()
    assert "Indexed 1 public items" in output


@pytest.mark.integration
@pytest.mark.django_db
def test_index_public_items_command_filters_by_start_and_end_date():
    PublicItem.objects.create(
        cnpj="00000000000001",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="DEMO-Item 1 para indexação",
        unit="UNIDADE",
        unit_normalized="unidade",
        quantity=Decimal("10.0000"),
        estimated_unit_price=Decimal("100.0000"),
        awarded_unit_price=Decimal("95.0000"),
        secret_budget=False,
        published_on=date(2026, 10, 26),
        agency_name="Prefeitura Teste 1",
        agency_cnpj="00000000000001",
        state="PA",
        modality=6,
        item_kind="product",
    )
    PublicItem.objects.create(
        cnpj="00000000000002",
        year=2026,
        purchase_sequence=2,
        item_number=1,
        description="DEMO-Item 2 para indexação",
        unit="UNIDADE",
        unit_normalized="unidade",
        quantity=Decimal("10.0000"),
        estimated_unit_price=Decimal("100.0000"),
        awarded_unit_price=Decimal("95.0000"),
        secret_budget=False,
        published_on=date(2026, 10, 27),
        agency_name="Prefeitura Teste 2",
        agency_cnpj="00000000000002",
        state="PA",
        modality=6,
        item_kind="product",
    )

    fake_model = FakeEmbeddingModel(name="test-model", revision="rev1", dimension=16)

    out = io.StringIO()
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False

    with (
        patch(
            "semantic_index.management.commands.index_public_items.SentenceTransformerEmbeddingModel",
            return_value=fake_model,
        ),
        patch("semantic_index.get_qdrant_client", return_value=mock_client),
    ):
        call_command(
            "index_public_items",
            model="test-model",
            revision="rev1",
            start="2026-10-27",
            end="2026-10-27",
            stdout=out,
        )

    output = out.getvalue()
    assert "Indexed 1 public items" in output
