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
    BM25SearchMethod,
    BenchmarkOrchestrator,
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
    # B2b: Finalist chosen on tuning must be pinned on measurement, never recomputed
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

    model_x = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="model_x")
    model_y = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="model_y")
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
    # B2c: filter_candidate_corpus applied per item based on survey_date
    item = {
        "item_id": "it1",
        "description": "Papel A4",
        "ground_truth": {1},
        "chosen_prices": [Decimal("10.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),  # Window: 2025-06-01 to 2026-06-01
    }

    corpus = [
        PublicItemSim(id=1, description="Papel A4 dentro da janela", price=Decimal("10.0"), published_on=date(2026, 1, 15), modality=6),
        PublicItemSim(id=2, description="Papel A4 publicado depois da pesquisa", price=Decimal("10.0"), published_on=date(2026, 6, 2), modality=6),
        PublicItemSim(id=3, description="Papel A4 modalidade invalida", price=Decimal("10.0"), published_on=date(2026, 1, 15), modality=99),
        PublicItemSim(id=4, description="Papel A4 antes da janela", price=Decimal("10.0"), published_on=date(2025, 5, 30), modality=6),
    ]

    bm25 = BM25SearchMethod()
    model = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="semantic")

    orch = BenchmarkOrchestrator(seed=42)
    results = orch.run_benchmark(
        items=[item],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[model],
        baseline_method=bm25,
    )

    ranked_bm25 = results["ranked_ids_by_method"]["bm25"]["it1"]
    ranked_sem = results["ranked_ids_by_method"]["semantic"]["it1"]

    # Only doc 1 satisfies C(q). Docs 2, 3, 4 must NOT be in the results!
    assert ranked_bm25 == [1]
    assert ranked_sem == [1]
