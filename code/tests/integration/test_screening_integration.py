from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from ingestion.models import PublicItem, RawRecord
from ingestion.units import normalize_unit
from pricing import views
from semantic_index import (
    ScoredPublicItem,
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
            unit_normalized=normalize_unit("pacote"),
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
            unit_normalized=normalize_unit("pacote"),
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


def _client_backend_connections() -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity "
            "WHERE datname = current_database() AND backend_type = 'client backend'"
        )
        return int(cursor.fetchone()[0])


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_screening_parallel_on_demand_fetch_does_not_leak_db_connections(monkeypatch):
    import ingestion.client

    today = date.today()
    items = []
    for i in range(20):
        raw_rec = RawRecord.objects.create(
            endpoint=f"/api/pncp/v1/orgaos/00000000000007/compras/{today.year}/900/itens",
            params={"pagina": 1},
            fetched_at=timezone.now(),
            payload=[{"numeroItem": i + 1, "temResultado": True}],
            status_code=200,
        )
        pi = PublicItem.objects.create(
            cnpj="00000000000007",
            year=today.year,
            purchase_sequence=900,
            item_number=i + 1,
            description=f"Item sintético para triagem {i}",
            unit="pacote",
            quantity=Decimal("10"),
            agency_name="Órgão Fictício",
            published_on=today - timedelta(days=5),
            awarded_unit_price=None,
            estimated_unit_price=Decimal("25.00"),
            secret_budget=False,
            modality=6,
            state="PA",
            item_kind="product",
        )
        pi.raw_records.add(raw_rec)
        items.append(pi)
        cache.delete(f"pncp_fetch_failed_{pi.pk}")

    def failing_fetch(**kwargs):
        raise TimeoutError("Simulated PNCP failure")

    monkeypatch.setattr(ingestion.client, "fetch_item_results", failing_fetch)
    monkeypatch.setattr(
        views,
        "search_function",
        lambda **kwargs: [ScoredPublicItem(item=pi, score=0.9) for pi in items],
    )
    monkeypatch.setattr(
        views,
        "corpus_info_function",
        lambda: views.CorpusInfo(20, today, today, is_partial=False, db_items_count=20),
    )

    django_client = Client()
    connections_before = _client_backend_connections()

    response = django_client.get(reverse("pricing:screening", args=[1]))
    assert response.status_code == 200
    assert len(response.context["candidates"]) == 20

    connections_after = _client_backend_connections()
    assert connections_after == connections_before


@pytest.mark.integration
@pytest.mark.django_db
def test_screening_and_decide_preserve_similarity_and_format_decimals_end_to_end(monkeypatch):
    client = get_qdrant_client()
    unique_rev = f"test_d1_d2_{uuid4().hex[:8]}"
    model = FakeEmbeddingModel(name="integration-d1-d2", revision=unique_rev, dimension=16)
    coll_name = collection_name_for_model(model)

    try:
        today = date.today()
        item = PublicItem.objects.create(
            cnpj="00000000000007",
            year=today.year,
            purchase_sequence=942,
            item_number=1,
            description="Papel sulfite A4 branco, resma com 500 folhas",
            unit="pacote",
            unit_normalized=normalize_unit("pacote"),
            quantity=Decimal("50.0000"),
            agency_name="Prefeitura D1D2",
            published_on=today - timedelta(days=10),
            awarded_unit_price=Decimal("41.1400"),
            estimated_unit_price=Decimal("45.0000"),
            secret_budget=False,
            modality=6,
            state="PA",
            item_kind="product",
        )
        indexed = index_public_items(model=model, items=[item], client=client)
        assert indexed == 1

        monkeypatch.setattr(views, "get_embedding_model", lambda: model)
        monkeypatch.setattr(views, "search_function", views.default_search_function)

        django_client = Client()
        screening_url = reverse("pricing:screening", args=[1])
        get_resp = django_client.get(screening_url)
        assert get_resp.status_code == 200
        get_html = get_resp.content.decode()

        assert "<td>50</td>" in get_html
        assert "50,0000" not in get_html
        assert "<td>41,14</td>" in get_html
        assert "41,1400" not in get_html
        assert f'hx-target="#candidate-{item.pk}-decision"' in get_html

        candidate = get_resp.context["candidates"][0]
        assert candidate.similarity != 0.0

        post_accept = django_client.post(
            reverse("pricing:decide", args=[item.pk]),
            {"decision": "accept", "item_id": "1"},
        )
        assert post_accept.status_code == 200
        accept_html = post_accept.content.decode()
        assert accept_html.lstrip().startswith(f'<td id="candidate-{item.pk}-decision">')
        assert "Aceito" in accept_html
        assert "<tr" not in accept_html
        assert "0,0" not in accept_html
        assert 'id="estimate-panel"' in accept_html

        post_reject = django_client.post(
            reverse("pricing:decide", args=[item.pk]),
            {"decision": "reject", "item_id": "1"},
        )
        assert post_reject.status_code == 200
        reject_html = post_reject.content.decode()
        assert reject_html.lstrip().startswith(f'<td id="candidate-{item.pk}-decision">')
        assert "Descartado" in reject_html
        assert "<tr" not in reject_html
        assert "0,0" not in reject_html

        get_after = django_client.get(screening_url)
        assert get_after.status_code == 200
        assert get_after.context["candidates"][0].similarity == candidate.similarity
        assert "Descartado" in get_after.content.decode()
    finally:
        if client.collection_exists(coll_name):
            client.delete_collection(coll_name)
