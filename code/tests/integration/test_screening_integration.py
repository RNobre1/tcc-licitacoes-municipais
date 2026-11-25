from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.test import Client
from django.urls import reverse

from ingestion.models import PublicItem
from pricing import views
from semantic_index import (
    collection_name_for_model,
    get_qdrant_client,
    index_public_items,
)
from tests.fake_embedding_model import FakeEmbeddingModel


@pytest.mark.integration
@pytest.mark.django_db
def test_screening_page_renders_with_real_semantic_search_pipeline(monkeypatch):
    client = get_qdrant_client()
    unique_rev = f"test_{uuid4().hex[:8]}"
    model = FakeEmbeddingModel(name="integration-model", revision=unique_rev, dimension=16)
    coll_name = collection_name_for_model(model)

    try:
        today = date.today()
        # Item within the last 12 months
        item_in_window = PublicItem.objects.create(
            cnpj="00000000000007",
            year=today.year,
            purchase_sequence=42,
            item_number=1,
            description="Papel sulfite A4 branco, resma com 500 folhas",
            unit="pacote",
            quantity=Decimal("100"),
            agency_name="Prefeitura Alpha",
            published_on=today - timedelta(days=30),
            awarded_unit_price=Decimal("25.50"),
            estimated_unit_price=Decimal("30.00"),
            secret_budget=False,
            modality=6,
            state="PA",
            item_kind="product",
        )
        # Item outside 12-month window (> 365 days ago)
        item_expired = PublicItem.objects.create(
            cnpj="00000000000007",
            year=today.year - 2,
            purchase_sequence=10,
            item_number=1,
            description="Papel sulfite A4 branco antigo",
            unit="pacote",
            quantity=Decimal("50"),
            agency_name="Prefeitura Beta",
            published_on=today - timedelta(days=400),
            awarded_unit_price=Decimal("18.00"),
            estimated_unit_price=Decimal("20.00"),
            secret_budget=False,
            modality=6,
            state="PA",
            item_kind="product",
        )

        indexed = index_public_items(
            model=model,
            items=[item_in_window, item_expired],
            client=client,
        )
        assert indexed == 2
        assert client.collection_exists(coll_name)

        monkeypatch.setattr(views, "get_embedding_model", lambda: model)
        # Ensure search_function is the default semantic search pipeline
        monkeypatch.setattr(views, "search_function", views.default_search_function)

        django_client = Client()
        url = reverse("pricing:screening", args=[1])
        response = django_client.get(url)

        assert response.status_code == 200
        html = response.content.decode()

        # Provenance URL rendered for candidate in window
        expected_provenance = (
            f"https://pncp.gov.br/app/editais/{item_in_window.cnpj}/{item_in_window.year}/"
            f"{item_in_window.purchase_sequence}"
        )
        assert expected_provenance in html
        assert "Prefeitura Alpha" in html
        assert "25,50" in html

        # Expired item outside date window must not appear in screening results
        assert "Prefeitura Beta" not in html
        assert "18,00" not in html

        # Partial corpus note is rendered end-to-end
        assert "Busca realizada em corpus parcial" in html
        assert "2 de 2 itens do banco indexados" in html
    finally:
        if client.collection_exists(coll_name):
            client.delete_collection(coll_name)
