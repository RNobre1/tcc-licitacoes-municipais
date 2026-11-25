"""Tests for B2 orchestrator overhaul:
- B2a: Search methods receive ONLY query and corpus (no ground truth / oracle).
       Deterministic fake embedding model used in tests.
       Refuses to run without candidate search methods.
       Sentinel test guarantees methods cannot reach ground truth.
- B2b: Finalist chosen only on tuning split and persisted.
       Measurement requires finalist from tuning and pins it (never recomputed).
       BM25 is baseline only and cannot be finalist.
- B2c: C(q) candidate corpus filtering applied per item.
"""

from datetime import date
from decimal import Decimal

import pytest

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    FakeDeterministicEmbeddingModel,
    PublicItemSim,
    SemanticSearchMethod,
)


def test_sentinel_method_cannot_reach_ground_truth():
    # B2a: Sentinel test. Ground truth must NOT influence ranking.
    # Item ground truth is doc 999 ("Caneta Azul"), but query is "Papel Sulfite A4".
    # Doc 1 is "Papel Sulfite A4".
    # An oracle method would put doc 999 at rank 1.
    # Real methods (BM25, Semantic) MUST put doc 1 at rank 1.
    corpus = [
        {"id": 1, "description": "Papel Sulfite A4 75g", "price": Decimal("25.0"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6},
        {"id": 999, "description": "Caneta Azul 1.0mm", "price": Decimal("1.5"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6},
    ]

    item = {
        "item_id": "item_1",
        "description": "Papel Sulfite A4",
        "ground_truth": {999},  # Hidden sentinel label
        "chosen_prices": [Decimal("25.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    bm25 = BM25SearchMethod()
    semantic = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())

    orch = BenchmarkOrchestrator(seed=42)
    results = orch.run_benchmark(
        items=[item],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[semantic],
        baseline_method=bm25,
        synthetic=True,
    )

    # In both BM25 and Semantic, doc 1 must rank first, NOT doc 999
    ranked_bm25 = results["ranked_ids_by_method"]["bm25"]["item_1"]
    ranked_sem = results["ranked_ids_by_method"]["semantic"]["item_1"]

    assert ranked_bm25[0] == 1
    assert ranked_sem[0] == 1
    assert ranked_bm25[0] != 999
    assert ranked_sem[0] != 999


def test_search_methods_receive_only_query_and_filtered_corpus():
    labels_read = False
    corpus = [
        {
            "id": 1,
            "description": "Papel Sulfite A4",
            "price": Decimal("25.0"),
            "unit": "UNIDADE",
            "published_on": date(2026, 5, 1),
            "modality": 6,
        }
    ]

    class TrackingItem(dict):
        def get(self, key, default=None):
            nonlocal labels_read
            if key == "ground_truth":
                labels_read = True
            return super().get(key, default)

    item = TrackingItem(
        item_id="item_1",
        description="Papel Sulfite A4",
        ground_truth={999},
        chosen_prices=[Decimal("25.0")],
        unit="UNIDADE",
        survey_date=date(2026, 6, 1),
    )

    class SentinelMethod:
        def __init__(self, name):
            self.name = name

        def rank(self, query, candidates):
            assert not labels_read
            assert query == item["description"]
            assert candidates == corpus
            assert all("ground_truth" not in candidate for candidate in candidates)
            return [(candidate, 1.0) for candidate in candidates]

    results = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5).run_benchmark(
        items=[item],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[SentinelMethod("candidate")],
        baseline_method=SentinelMethod("bm25"),
    )

    assert labels_read
    assert results["finalist"] == "candidate"


@pytest.mark.django_db
def test_semantic_method_uses_embedding_search_and_filters_modality_in_database(monkeypatch):
    from ingestion.models import PublicItem
    from semantic_index.search import ScoredPublicItem, StructuredFilter

    allowed = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    disallowed = PublicItem.objects.create(
        cnpj="22222222000122",
        year=2026,
        purchase_sequence=200,
        item_number=1,
        description="Papel sulfite em modalidade fora do espaço",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="22222222000122",
        state="AM",
        modality=99,
        item_kind="product",
    )

    calls = []
    model = FakeDeterministicEmbeddingModel()

    def fake_semantic_search(model_arg, query, structured_filter, limit, client=None):
        calls.append((model_arg, query, structured_filter, limit))
        return [
            ScoredPublicItem(item=disallowed, score=0.99),
            ScoredPublicItem(item=allowed, score=0.80),
        ]

    monkeypatch.setattr("semantic_index.search.semantic_search", fake_semantic_search)

    ranked = SemanticSearchMethod(model=model).rank(
        "Papel sulfite", [allowed, disallowed]
    )

    assert ranked == [(allowed, 0.80)]
    assert len(calls) == 1
    search_model, query, structured_filter, search_limit = calls[0]
    assert search_model is model
    assert query == "Papel sulfite"
    assert isinstance(structured_filter, StructuredFilter)
    assert structured_filter.date_window == (date(2026, 5, 1), date(2026, 5, 1))
    assert search_limit > 2


def test_orchestrator_refuses_without_candidate_methods():
    # B2a: If no real candidate method is provided, orchestrator refuses to run
    orch = BenchmarkOrchestrator(seed=42)
    with pytest.raises(ValueError, match="candidate search method"):
        orch.run_benchmark(
            items=[{"item_id": "1", "description": "test", "ground_truth": {1}, "chosen_prices": [Decimal("10.0")], "survey_date": date(2026, 6, 1)}],
            corpus=[{"id": 1, "description": "test", "price": Decimal("10.0"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6}],
            split_name="tuning",
            candidate_methods=[],
        )


def test_finalist_pinned_across_tuning_and_measurement():
    # B2b: Finalist chosen on tuning must be pinned on measurement, never recomputed.
    # On measurement, model_y would win if the orchestrator selected again.
    tuning_items = [
        {
            "item_id": "t1",
            "description": "Papel Sulfite A4",
            "ground_truth": {1},
            "chosen_prices": [Decimal("25.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]
    measurement_items = [
        {
            "item_id": "m1",
            "description": "Caneta Azul",
            "ground_truth": {2},
            "chosen_prices": [Decimal("1.5")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]
    corpus = [
        {"id": 1, "description": "Papel Sulfite A4 75g", "price": Decimal("25.0"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6},
        {"id": 2, "description": "Caneta Esferográfica Azul 1.0mm", "price": Decimal("1.5"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6},
    ]

    class PhraseRanker:
        def __init__(self, name, preferred_phrase):
            self.name = name
            self.preferred_phrase = preferred_phrase

        def rank(self, query, candidates):
            scored = [
                (candidate, float(self.preferred_phrase.lower() in candidate["description"].lower()))
                for candidate in candidates
            ]
            return sorted(scored, key=lambda pair: (-pair[1], pair[0]["id"]))

    model_x = PhraseRanker(name="model_x", preferred_phrase="Papel")
    model_y = PhraseRanker(name="model_y", preferred_phrase="Caneta")
    bm25 = BM25SearchMethod()

    orch = BenchmarkOrchestrator(seed=42)
    # Tuning run selects finalist (say model_x)
    tuning_results = orch.run_benchmark(
        items=tuning_items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[model_x, model_y],
        baseline_method=bm25,
    )
    chosen_finalist = tuning_results["finalist"]
    assert chosen_finalist in ["model_x", "model_y"]

    # Measurement run requires finalist passed from tuning
    measurement_results = orch.run_benchmark(
        items=measurement_items,
        corpus=corpus,
        split_name="measurement",
        candidate_methods=[model_x, model_y],
        baseline_method=bm25,
        finalist=chosen_finalist,
    )

    # Measurement output records the same finalist
    assert measurement_results["finalist"] == chosen_finalist
    assert chosen_finalist == "model_x"
    assert (
        measurement_results["methods"]["model_y"]["metrics"]["mrr_at_20"]
        > measurement_results["methods"]["model_x"]["metrics"]["mrr_at_20"]
    )


def test_r1_contrasts_finalist_against_bm25_baseline():
    class ReverseIdMethod:
        name = "candidate"

        def rank(self, query, candidates):
            return sorted(
                [(candidate, float(candidate["id"])) for candidate in candidates],
                key=lambda pair: pair[1],
                reverse=True,
            )

    corpus = [
        {
            "id": index,
            "description": "needle distractor",
            "price": Decimal("10"),
            "unit": "UNIDADE",
            "published_on": date(2026, 5, 1),
            "modality": 6,
        }
        for index in range(1, 11)
    ]
    corpus.append(
        {
            "id": 11,
            "description": "unrelated item",
            "price": Decimal("10"),
            "unit": "UNIDADE",
            "published_on": date(2026, 5, 1),
            "modality": 6,
        }
    )
    item = {
        "item_id": "item_1",
        "description": "needle",
        "ground_truth": {11},
        "chosen_prices": [Decimal("10")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    results = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5).run_benchmark(
        items=[item],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[ReverseIdMethod()],
        baseline_method=BM25SearchMethod(),
    )

    assert results["ranked_ids_by_method"]["candidate"]["item_1"][0] == 11
    assert results["ranked_ids_by_method"]["bm25"]["item_1"][0] != 11
    assert results["r1_acceptance"]["diff_mean"] == 1.0
    assert results["r1_acceptance"]["ci_95"] == (1.0, 1.0)


def test_measurement_refuses_without_finalist_or_when_finalist_is_bm25():
    # B2b: Measurement refuses without finalist, and refuses if finalist is bm25
    orch = BenchmarkOrchestrator(seed=42)
    model = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="model_sem")
    bm25 = BM25SearchMethod()

    items = [{"item_id": "m1", "description": "test", "ground_truth": {1}, "chosen_prices": [Decimal("10.0")], "survey_date": date(2026, 6, 1)}]
    corpus = [{"id": 1, "description": "test", "price": Decimal("10.0"), "unit": "UNIDADE", "published_on": date(2026, 5, 1), "modality": 6}]

    # Missing finalist on measurement
    with pytest.raises(ValueError, match="Finalist must be provided for measurement"):
        orch.run_benchmark(items=items, corpus=corpus, split_name="measurement", candidate_methods=[model], baseline_method=bm25, finalist=None)

    # Finalist cannot be bm25
    with pytest.raises(ValueError, match="Finalist cannot be the baseline method"):
        orch.run_benchmark(items=items, corpus=corpus, split_name="measurement", candidate_methods=[model], baseline_method=bm25, finalist="bm25")


def test_c_q_applied_per_item():
    # B2c: filter_candidate_corpus applied per item based on survey_date.
    items = [
        {
            "item_id": "it1",
            "description": "Papel A4",
            "ground_truth": {1},
            "chosen_prices": [Decimal("10.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
        {
            "item_id": "it2",
            "description": "Papel A4",
            "ground_truth": {1},
            "chosen_prices": [Decimal("10.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 2, 1),
        },
    ]

    corpus = [
        PublicItemSim(id=1, description="Papel A4 dentro da janela", price=Decimal("10.0"), published_on=date(2026, 1, 15), modality=6),
        PublicItemSim(id=2, description="Papel A4 publicado depois da pesquisa", price=Decimal("10.0"), published_on=date(2026, 6, 2), modality=6),
        PublicItemSim(id=3, description="Papel A4 modalidade invalida", price=Decimal("10.0"), published_on=date(2026, 1, 15), modality=99),
        PublicItemSim(id=4, description="Papel A4 antes da janela", price=Decimal("10.0"), published_on=date(2025, 5, 30), modality=6),
        PublicItemSim(id=5, description="Papel A4 após a pesquisa de it2", price=Decimal("10.0"), published_on=date(2026, 3, 1), modality=7, state="AM"),
        PublicItemSim(id=6, description="Papel A4 modalidade 8", price=Decimal("10.0"), published_on=date(2026, 1, 15), modality=8, state="SP"),
    ]

    bm25 = BM25SearchMethod()
    model = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="semantic")

    orch = BenchmarkOrchestrator(seed=42)
    results = orch.run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[model],
        baseline_method=bm25,
    )

    ranked_bm25_it1 = results["ranked_ids_by_method"]["bm25"]["it1"]
    ranked_sem_it1 = results["ranked_ids_by_method"]["semantic"]["it1"]
    ranked_bm25_it2 = results["ranked_ids_by_method"]["bm25"]["it2"]
    ranked_sem_it2 = results["ranked_ids_by_method"]["semantic"]["it2"]

    # id 5 belongs to it1's C(q), but was published after it2's survey date.
    # Modalities 6, 7 and 8 are included across all states; invalid candidates are excluded.
    assert set(ranked_bm25_it1) == {1, 5, 6}
    assert set(ranked_sem_it1) == {1, 5, 6}
    assert set(ranked_bm25_it2) == {1, 6}
    assert set(ranked_sem_it2) == {1, 6}


def test_c_q_corpus_provider_is_called_per_item():
    items = [
        {
            "item_id": "early",
            "description": "Papel A4",
            "ground_truth": {1},
            "chosen_prices": [Decimal("10.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 2, 1),
        },
        {
            "item_id": "late",
            "description": "Papel A4",
            "ground_truth": {1},
            "chosen_prices": [Decimal("10.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
    ]
    all_candidates = [
        PublicItemSim(
            id=1,
            description="Papel A4",
            price=Decimal("10.0"),
            published_on=date(2026, 1, 1),
            modality=6,
        ),
        PublicItemSim(
            id=2,
            description="Papel A4",
            price=Decimal("10.0"),
            published_on=date(2026, 3, 1),
            modality=7,
        ),
    ]
    requested_dates = []

    def corpus_provider(survey_date):
        requested_dates.append(survey_date)
        return all_candidates

    class CandidateMethod:
        name = "candidate"

        def rank(self, query, candidates):
            return [(candidate, 1.0) for candidate in candidates]

    results = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5).run_benchmark(
        items=items,
        corpus=corpus_provider,
        split_name="tuning",
        candidate_methods=[CandidateMethod()],
        baseline_method=BM25SearchMethod(),
    )

    assert requested_dates == [date(2026, 2, 1), date(2026, 6, 1)]
    assert results["ranked_ids_by_method"]["candidate"]["early"] == [1]
    assert results["ranked_ids_by_method"]["candidate"]["late"] == [1, 2]
