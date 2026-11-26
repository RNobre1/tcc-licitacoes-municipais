"""Behavioral tests for C17 (ties in evaluation + addendum) and Q1/Q2 guards."""

import hashlib
import inspect
import itertools
import json
import random
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from qdrant_client import models

import evaluation.benchmark as benchmark_module
from evaluation.benchmark import (
    ALLOWED_MODALITIES,
    BenchmarkOrchestrator,
    BM25SearchMethod,
    FakeDeterministicEmbeddingModel,
    PriceCandidateSim,
    PublicItemSim,
    SemanticSearchMethod,
    check_collection_coverage,
    classify_easy_hard_items,
    compute_expected_mrr_at_k,
    compute_expected_recall_at_k,
    compute_expected_success_at_k,
    compute_mrr_at_k,
    compute_recall_at_k,
    compute_success_at_k,
    compute_tie_sensitivity,
    create_dataset_split,
    group_tied_scored_ids,
    shuffle_tied_groups,
)
from semantic_index.search import ScoredPublicItem, StructuredFilter, semantic_search


def _brute_force_expected_metrics(
    groups: list[list[int]], gt_ids: set[int], k: int
) -> tuple[float, float, float]:
    """Enumerate cartesian product of permutations within tied groups (small cases only)."""
    group_perms = [list(itertools.permutations(group)) for group in groups]
    recall_sum = 0.0
    success_sum = 0.0
    mrr_sum = 0.0
    total = 0
    for choice in itertools.product(*group_perms):
        flat = [item for part in choice for item in part]
        recall_sum += compute_recall_at_k(flat, gt_ids, k=k)
        success_sum += compute_success_at_k(flat, gt_ids, k=k)
        mrr_sum += compute_mrr_at_k(flat, gt_ids, k=k)
        total += 1
    return recall_sum / total, success_sum / total, mrr_sum / total


def test_c17_closed_forms_match_brute_force_enumeration_on_small_cases():
    cases = [
        # (score_groups, gt_ids, k)
        ([[1, 2, 3], [4, 5], [6]], {2, 4}, 4),
        ([[1, 2, 3, 4], [5, 6]], {2, 3}, 2),
        ([[1], [2, 3, 4, 5], [6, 7]], {3, 5, 7}, 3),
        ([[1, 2], [3, 4, 5, 6]], {4, 5}, 4),
        ([[1, 2, 3]], {1, 2, 3}, 2),
        ([[1, 2, 3, 4, 5]], {5}, 3),
        ([[1, 2], [3, 4], [5, 6]], {6}, 4),
    ]
    for groups, gt_ids, k in cases:
        ranked_scored = [
            (doc_id, float(len(groups) - g_idx))
            for g_idx, grp in enumerate(groups)
            for doc_id in grp
        ]
        bf_recall, bf_success, bf_mrr = _brute_force_expected_metrics(groups, gt_ids, k=k)
        assert compute_expected_recall_at_k(ranked_scored, gt_ids, k=k) == pytest.approx(
            bf_recall, abs=1e-12
        )
        assert compute_expected_success_at_k(ranked_scored, gt_ids, k=k) == pytest.approx(
            bf_success, abs=1e-12
        )
        assert compute_expected_mrr_at_k(ranked_scored, gt_ids, k=k) == pytest.approx(
            bf_mrr, abs=1e-12
        )


def test_c17_closed_forms_handle_100_tied_items_at_rank_5_with_3_relevant():
    # Group 1: ranks 1..4 (offset 0, size 4), no relevant
    # Group 2: starts at rank 5 (offset 4), size 100, 3 relevant
    ranked_scored = [(i, 0.9) for i in range(1, 5)] + [(i, 0.5) for i in range(5, 105)]
    gt_ids = {10, 50, 104}

    # Recall@10: 6 slots in [5..10] of 100 -> expected hits = 3 * 6 / 100 = 0.18 -> / 3 = 0.06
    exp_recall_10 = compute_expected_recall_at_k(ranked_scored, gt_ids, k=10)
    assert exp_recall_10 == pytest.approx(0.06, abs=1e-12)

    # Success@10: 1 - C(97, 6) / C(100, 6) = 1 - (97*96*95*94*93*92)/(100*99*98*97*96*95)
    prob_no_hit = (94 * 93 * 92) / (100 * 99 * 98)
    assert compute_expected_success_at_k(ranked_scored, gt_ids, k=10) == pytest.approx(
        1.0 - prob_no_hit, abs=1e-12
    )

    # MRR@20: first group with relevant starts at offset 4, m=100, r=3, t=16 slots in top 20
    # Verify exact recurrence against independent combinatorial probability of first relevant at j
    expected_mrr = 0.0
    m, r, offset = 100, 3, 4
    for j in range(1, 17):
        # P(first relevant at position j in group) = C(m - r, j - 1) / C(m, j - 1) * r / (m - j + 1)
        p_j = r / (m - j + 1)
        for prev in range(j - 1):
            p_j *= (m - r - prev) / (m - prev)
        expected_mrr += p_j / (offset + j)

    assert compute_expected_mrr_at_k(ranked_scored, gt_ids, k=20) == pytest.approx(
        expected_mrr, abs=1e-12
    )


def test_c17_exact_score_equality_groups_ties_and_takes_full_list():
    # Near-equal floats must NOT tie; exact identical floats DO tie
    ranked_scored = [
        (1, 0.5000001),
        (2, 0.5),
        (3, 0.5),
    ]
    groups = group_tied_scored_ids(ranked_scored)
    assert groups == [(0.5000001, [1]), (0.5, [2, 3])]

    # Full list metrics include relevant items ranked past top_n (k=20 vs top_n=5)
    full_25 = [(i, 1.0 - 0.01 * i) for i in range(1, 26)]
    assert compute_expected_recall_at_k(full_25, {15}, k=20) == 1.0
    assert compute_expected_mrr_at_k(full_25, {15}, k=20) == pytest.approx(1.0 / 15.0)


def test_c17_r1_eliminates_id_tie_bias_when_scores_tie():
    # Probe from C17 context: when all 15 candidates tie on score (0 overlap with query),
    # a relevant item at id=1 vs id=15 must get IDENTICAL expected R1 metrics (2/3 = 0.6667 @10).
    corpus = [
        PublicItemSim(
            id=i,
            description="item totalmente generico",
            price=Decimal("10.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 16)
    ]

    class AllTiedCandidate:
        name = "all_tied"

        def rank(self, query, candidates):
            return [(c, 0.5) for c in candidates]

    orch = BenchmarkOrchestrator(n_noise_draws=5, n_bootstrap_resamples=10, seed=42)
    base_item = {
        "item_id": "probe",
        "description": "consulta sem correspondencia",
        "chosen_prices": [Decimal("10.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    res_low_id = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {1}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[AllTiedCandidate()],
        baseline_method=BM25SearchMethod(),
        top_n=5,
    )
    res_high_id = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {15}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[AllTiedCandidate()],
        baseline_method=BM25SearchMethod(),
        top_n=5,
    )

    for metric_key in (
        "recall_at_1",
        "recall_at_5",
        "recall_at_10",
        "recall_at_20",
        "success_at_10",
        "mrr_at_20",
    ):
        for method_name in ("bm25", "all_tied"):
            assert res_low_id["methods"][method_name]["metrics"][metric_key] == pytest.approx(
                res_high_id["methods"][method_name]["metrics"][metric_key], abs=1e-12
            )

    # Recall@10 over 15 tied items with 1 relevant = 10/15; Recall@20 = 1.0 even with top_n=5.
    assert res_high_id["methods"]["all_tied"]["metrics"]["recall_at_10"] == pytest.approx(
        10.0 / 15.0, abs=1e-12
    )
    assert res_high_id["methods"]["all_tied"]["metrics"]["recall_at_20"] == pytest.approx(
        1.0, abs=1e-12
    )


def test_c17_r2_shuffles_tied_groups_before_top_n_cut_and_breaks_rf23_final_tie_by_draw():
    # Setup: 15 candidates all inside top_n=15 with identical similarity=0.85 and price=25.0.
    # Without per-draw random rank replacing id in RF23 and price-only tie reshuffling,
    # gt={1} gets sys=1.0 and gt={15} gets sys=0.0 across all draws.
    # RF23 orders top 10 of 15. Without per-draw random rank replacing id inside RF23,
    # ground_truth={1} ALWAYS gets 1.0 and ground_truth={15} ALWAYS gets 0.0 across all draws!
    corpus_15 = [
        PublicItemSim(
            id=i,
            description=f"item {i}",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 16)
    ]

    class TiedSimilarityMethod:
        name = "tied_sim"

        def rank(self, query, candidates):
            return [(c, 0.85) for c in candidates]

    orch = BenchmarkOrchestrator(n_noise_draws=200, n_bootstrap_resamples=10, seed=42)
    base_item = {
        "item_id": "rf23_tie",
        "description": "papel sulfite",
        "chosen_prices": [Decimal("25.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    res_low = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {1}}],
        corpus=corpus_15,
        split_name="tuning",
        candidate_methods=[TiedSimilarityMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=15,
    )
    res_high = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {15}}],
        corpus=corpus_15,
        split_name="tuning",
        candidate_methods=[TiedSimilarityMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=15,
    )

    # Seed recorded and does not depend on ground truth
    assert "r2_tie_break_seed" in res_low["constants"]
    assert res_low["constants"]["r2_tie_break_seed"] == res_high["constants"]["r2_tie_break_seed"]

    # With 200 draws, equal-price reshuffling keeps price_only_baseline near 10/15 (~0.667)
    # for both lowest and highest ID, and RF23 random rank keeps g_sigma["0.0"] near 0.0.
    assert 0.45 < res_low["r2"]["price_only_baseline"] < 0.88
    assert 0.45 < res_high["r2"]["price_only_baseline"] < 0.88
    assert abs(res_low["r2"]["g_sigma"]["0.0"]) < 0.15
    assert abs(res_high["r2"]["g_sigma"]["0.0"]) < 0.15
    # Also verify pre-cut shuffle: 25 identical-score items with top_n=10 and gt={25}.
    corpus_25 = [
        PublicItemSim(
            id=i,
            description=f"item {i}",
            price=Decimal("25.0") if i == 25 else Decimal("999.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 26)
    ]
    res_precut = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {25}}],
        corpus=corpus_25,
        split_name="tuning",
        candidate_methods=[TiedSimilarityMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=10,
    )
    # Without pre-cut shuffle on full list, id=25 never enters top_n=10 -> sys=0, g=-1.0.
    # With pre-cut shuffle (10/25 = 0.40 chance of id=25 entering top_n=10), g > -0.80.
    assert res_precut["r2"]["g_sigma"]["0.25"] > -0.80


def test_c17_addendum_easy_hard_uses_expected_success_at_10_over_equal_price_groups():
    # Addendum #3:
    # - exact geometric mean anchor (sigma = 0)
    # - remove misleading sigma = 0.25 comment in benchmark.py
    # - p = expected Success@10 of price-only over equal-price groups
    # - EASY if p > 0, HARD if p = 0.
    benchmark_source = Path(inspect.getsourcefile(benchmark_module)).read_text(encoding="utf-8")
    assert "Classify easy/hard on sigma=0.25" not in benchmark_source

    # Tie group of 15 items all at exact price 25.0 crossing rank 10, with 1 relevant at id=15
    candidates = [
        PriceCandidateSim(id=i, price=Decimal("25.0"), similarity=0.5) for i in range(1, 16)
    ]
    assert (
        classify_easy_hard_items(candidates, anchor=Decimal("25.0"), ground_truth_ids={15}, k=10)
        is True
    )

    # Strictly 10 cheaper/closer distractors before relevant -> p = 0.0 -> HARD
    candidates_hard = [
        PriceCandidateSim(id=i, price=Decimal("25.0"), similarity=0.5) for i in range(1, 11)
    ] + [PriceCandidateSim(id=11, price=Decimal("50.0"), similarity=0.5)]
    assert (
        classify_easy_hard_items(
            candidates_hard, anchor=Decimal("25.0"), ground_truth_ids={11}, k=10
        )
        is False
    )


def test_c17_tie_sensitivity_exact_rules():
    # Recall@10: group crossing rank 10 with >=1 relevant AND >=1 non-relevant (0 < r < m)
    # Crossing group has offsets 8..11 (m=4):
    # - mixed (r=2): recall_at_10=True, r2_pool=False (no group crosses 20)
    mixed_recall = [(i, 0.9) for i in range(1, 9)] + [(i, 0.5) for i in range(9, 13)]
    assert compute_tie_sensitivity(mixed_recall, {9, 10}, top_n=20) == {
        "recall_at_10": True,
        "mrr_at_20": True,  # first group with relevant is the tied group [9..12] (m=4, r=2 < m)
        "r2_pool": False,
    }

    # Crossing group all relevant (r == m): recall_at_10=False, mrr_at_20=False!
    all_rel_cross_10 = [(i, 0.9) for i in range(1, 9)] + [(i, 0.5) for i in range(9, 13)]
    assert compute_tie_sensitivity(all_rel_cross_10, {9, 10, 11, 12}, top_n=20) == {
        "recall_at_10": False,
        "mrr_at_20": False,
        "r2_pool": False,
    }

    # Crossing group has zero relevant (r==0) & earlier singleton relevant -> both False
    zero_rel_cross_10 = [(i, 0.9) for i in range(1, 9)] + [(i, 0.5) for i in range(9, 13)]
    assert compute_tie_sensitivity(zero_rel_cross_10, {1}, top_n=20) == {
        "recall_at_10": False,
        "mrr_at_20": False,
        "r2_pool": False,
    }

    # Group crossing rank 20 (offsets 18..22, m=5) -> r2_pool=True
    cross_20 = [(i, 1.0 - 0.01 * i) for i in range(1, 19)] + [(i, 0.5) for i in range(19, 24)]
    assert compute_tie_sensitivity(cross_20, {1}, top_n=20) == {
        "recall_at_10": False,
        "mrr_at_20": False,
        "r2_pool": True,
    }

    # Orchestrator result reports tie_sensitivity per method and at top level
    corpus = [
        PublicItemSim(
            id=i,
            description=f"doc {i}",
            price=Decimal("10.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 25)
    ]

    class TiedEverywhere:
        name = "tied"

        def rank(self, query, candidates):
            return [(c, 0.7) for c in candidates]

    res = BenchmarkOrchestrator(n_noise_draws=2, n_bootstrap_resamples=5, seed=42).run_benchmark(
        items=[
            {
                "item_id": "ts1",
                "description": "query",
                "ground_truth": {5},
                "chosen_prices": [Decimal("10.0")],
                "unit": "UNIDADE",
                "survey_date": date(2026, 6, 1),
            }
        ],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[TiedEverywhere()],
        baseline_method=BM25SearchMethod(),
        top_n=20,
    )
    assert res["tie_sensitivity"] == {"recall_at_10": 1.0, "mrr_at_20": 1.0, "r2_pool": 1.0}
    assert res["methods"]["tied"]["tie_sensitivity"] == {
        "recall_at_10": 1.0,
        "mrr_at_20": 1.0,
        "r2_pool": 1.0,
    }


def test_c17_shuffle_tied_groups_preserves_group_boundaries_and_shuffles_members():
    pairs = [("a1", 0.9), ("a2", 0.9), ("b1", 0.5), ("b2", 0.5), ("b3", 0.5)]
    seen_orders = set()
    for s in range(30):
        shuffled = shuffle_tied_groups(pairs, random.Random(s))
        assert [score for _, score in shuffled] == [0.9, 0.9, 0.5, 0.5, 0.5]
        assert {doc for doc, _ in shuffled[:2]} == {"a1", "a2"}
        assert {doc for doc, _ in shuffled[2:]} == {"b1", "b2", "b3"}
        seen_orders.add(tuple(doc for doc, _ in shuffled))
    assert len(seen_orders) > 2


def test_c17_metamorphic_sentinel_covers_tie_groups_and_scores():
    corpus = [
        PublicItemSim(
            id=i,
            description="papel sulfite pautado" if i in (2, 3, 4) else f"outro item {i}",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 6)
    ]

    bm25 = BM25SearchMethod(name="bm25")
    semantic = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="semantic")
    orch = BenchmarkOrchestrator(n_noise_draws=2, n_bootstrap_resamples=5, seed=42)

    base_item = {
        "item_id": "grp_meta",
        "description": "papel sulfite pautado",
        "chosen_prices": [Decimal("25.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    res_real_gt = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {2}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[semantic],
        baseline_method=bm25,
        include_full_rankings=True,
    )
    res_nonexistent_gt = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {999999}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[semantic],
        baseline_method=bm25,
        include_full_rankings=True,
    )

    for method_name in ("bm25", "semantic"):
        assert (
            res_real_gt["full_ranked_groups_by_method"][method_name]["grp_meta"]
            == res_nonexistent_gt["full_ranked_groups_by_method"][method_name]["grp_meta"]
        )


def test_c17_semantic_search_supports_exact_flag():
    model = FakeDeterministicEmbeddingModel()
    mock_client = SimpleNamespace(
        collection_exists=lambda name: True,
        get_collection=lambda name: SimpleNamespace(
            payload_schema={"modality": SimpleNamespace(data_type=models.PayloadSchemaType.INTEGER)}
        ),
        count=lambda **kw: SimpleNamespace(count=0),
        query_points_calls=[],
    )

    def fake_query_points(**kwargs):
        mock_client.query_points_calls.append(kwargs)
        return SimpleNamespace(points=[])

    mock_client.query_points = fake_query_points

    semantic_search(
        model=model,
        query="papel sulfite",
        structured_filter=StructuredFilter(
            date_window=(date(2026, 1, 1), date(2026, 6, 1)),
            modality=list(ALLOWED_MODALITIES),
        ),
        limit=50,
        client=mock_client,
        exact=True,
    )

    assert len(mock_client.query_points_calls) == 1
    search_params = mock_client.query_points_calls[0].get("search_params")
    assert isinstance(search_params, models.SearchParams)
    assert search_params.exact is True


@pytest.mark.django_db
def test_c17_semantic_method_db_path_uses_exact_limit_and_modality_filter(monkeypatch):
    from ingestion.models import PublicItem

    items = [
        PublicItem.objects.create(
            cnpj="11111111000111",
            year=2026,
            purchase_sequence=100 + idx,
            item_number=1,
            description=f"Papel sulfite {idx}",
            unit="UNIDADE",
            quantity=Decimal("1"),
            estimated_unit_price=Decimal("25"),
            awarded_unit_price=Decimal("25"),
            secret_budget=False,
            published_on=date(2026, 5, 1),
            agency_name="Prefeitura Fictícia",
            agency_cnpj="11111111000111",
            state="PA",
            modality=6,
            item_kind="product",
        )
        for idx in range(3)
    ]

    recorded = []

    def fake_semantic_search(model, query, structured_filter, limit, client=None, exact=False):
        recorded.append((structured_filter, limit, exact))
        return [ScoredPublicItem(item=item, score=0.8) for item in items]

    monkeypatch.setattr("semantic_index.search.semantic_search", fake_semantic_search)

    SemanticSearchMethod(model=FakeDeterministicEmbeddingModel()).rank("Papel sulfite", items)

    assert len(recorded) == 1
    sf, limit, exact = recorded[0]
    assert exact is True
    assert limit >= len(items)
    assert list(sf.modality) == list(ALLOWED_MODALITIES)


@pytest.mark.django_db
def test_q1_and_q2_n1d_anti_forge_tuning_lock_and_sha256_stdout(monkeypatch, tmp_path, capsys):
    from ingestion.models import PublicItem

    eval_dir = tmp_path / "avaliacao"
    eval_dir.mkdir(parents=True)
    split = create_dataset_split(
        [
            {"item_id": "rep_1", "report_id": "rep", "item_kind": "product"},
            {"item_id": "rep_2", "report_id": "rep", "item_kind": "product"},
        ],
        tuning_fraction=0.5,
        seed=42,
    )
    (eval_dir / "dataset_split.json").write_text(
        json.dumps(
            {
                "tuning_items": list(split.tuning_items),
                "measurement_items": list(split.measurement_items),
                "sha256_hash": split.sha256_hash,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "ground_truth_resolved.json").write_text(
        json.dumps(
            {
                "resolved_items": {
                    "rep_it1_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                    "rep_it2_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "rep.report.json").write_text(
        json.dumps(
            {
                "report_id": "rep",
                "survey_end": "15/06/2026",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                    {
                        "item_number": 2,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite A4",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    monkeypatch.setattr(
        "evaluation.management.commands.run_benchmark.check_thresholds_note_guard",
        lambda note_path, split_hash=None: "accepted",
    )
    monkeypatch.setattr(
        "pricing.views.get_embedding_model",
        lambda: FakeDeterministicEmbeddingModel(),
    )
    fake_qdrant = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: fake_qdrant)
    monkeypatch.setattr(
        "semantic_index.search.semantic_search",
        lambda *a, **kw: [],
    )

    valid_base = {
        "split": "tuning",
        "synthetic": False,
        "items_count": len(split.tuning_items),
        "split_hash": split.sha256_hash,
        "finalist": "semantic",
        "methods": {
            "bm25": {"metrics": {"recall_at_10": 0.4, "mrr_at_20": 0.3}},
            "semantic": {"metrics": {"recall_at_10": 0.8, "mrr_at_20": 0.7}},
        },
    }
    tuning_file = eval_dir / "benchmark_tuning_results.json"

    # N1-d: missing 'split' or wrong 'split' rejected
    for bad_split in (
        {k: v for k, v in valid_base.items() if k != "split"},
        {**valid_base, "split": "measurement"},
    ):
        tuning_file.write_text(json.dumps(bad_split), encoding="utf-8")
        with pytest.raises(CommandError, match="tuning"):
            call_command(
                "run_benchmark",
                split="measurement",
                thresholds_note="note.md",
                eval_dir=str(eval_dir),
                pattern="*.report.json",
                allow_real_data=True,
            )

    # Q1: synthetic=True tuning file rejected in real measurement mode
    tuning_file.write_text(json.dumps({**valid_base, "synthetic": True}), encoding="utf-8")
    with pytest.raises(CommandError, match="synthetic"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # Q1: mismatched items_count rejected
    tuning_file.write_text(json.dumps({**valid_base, "items_count": 99}), encoding="utf-8")
    with pytest.raises(CommandError, match="items_count"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # Q1: forged finalist that disagrees with select_finalist(methods) rejected
    forged = {
        **valid_base,
        "finalist": "other_cand",
        "methods": {
            "bm25": {"metrics": {"recall_at_10": 0.4, "mrr_at_20": 0.3}},
            "semantic": {"metrics": {"recall_at_10": 0.9, "mrr_at_20": 0.8}},
            "other_cand": {"metrics": {"recall_at_10": 0.2, "mrr_at_20": 0.1}},
        },
    }
    tuning_file.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(CommandError, match="recomputed finalist"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # Q1: --tuning-output outside eval_dir rejected
    outside_tuning = tmp_path / "escaped_tuning.json"
    outside_tuning.write_text(json.dumps(valid_base), encoding="utf-8")
    with pytest.raises(CommandError, match="eval directory"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            eval_dir=str(eval_dir),
            tuning_output=str(outside_tuning),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # Q1: stdout prints SHA-256 of written tuning output file
    syn_out = tmp_path / "syn_tuning.json"
    capsys.readouterr()
    call_command("run_benchmark", split="tuning", output=str(syn_out), synthetic=True)
    captured = capsys.readouterr().out
    expected_sha256 = hashlib.sha256(syn_out.read_bytes()).hexdigest()
    assert expected_sha256 in captured


def test_q2_n4b_check_collection_coverage_across_multiple_batches():
    ids = list(range(1, 1206))  # > 2 * 500 -> 3 batches (500, 500, 205)
    batch_sizes_seen = []

    class MultiBatchQdrantClient:
        def collection_exists(self, collection_name):
            return True

        def retrieve(self, collection_name, ids, with_payload=False, with_vectors=False):
            batch_sizes_seen.append(len(ids))
            return [SimpleNamespace(id=pk) for pk in ids]

    coverage = check_collection_coverage(
        FakeDeterministicEmbeddingModel(),
        ids,
        client=MultiBatchQdrantClient(),
        batch_size=500,
    )
    assert batch_sizes_seen == [500, 500, 205]
    assert coverage["expected_count"] == 1205
    assert coverage["present_count"] == 1205
    assert coverage["missing_count"] == 0
    assert coverage["coverage_ratio"] == 1.0


@pytest.mark.django_db
def test_q2_n6b_and_n6c_run_benchmark_refuses_missing_or_zero_chosen_prices_with_count(
    monkeypatch, tmp_path
):
    from ingestion.models import PublicItem

    eval_dir = tmp_path / "avaliacao"
    eval_dir.mkdir(parents=True)
    split = create_dataset_split(
        [
            {"item_id": "rep_1", "report_id": "rep", "item_kind": "product"},
            {"item_id": "rep_2", "report_id": "rep", "item_kind": "product"},
        ],
        tuning_fraction=1.0,
        seed=42,
    )
    (eval_dir / "dataset_split.json").write_text(
        json.dumps(
            {
                "tuning_items": list(split.tuning_items),
                "measurement_items": list(split.measurement_items),
                "sha256_hash": split.sha256_hash,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "ground_truth_resolved.json").write_text(
        json.dumps(
            {
                "resolved_items": {
                    "rep_it1_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                    "rep_it2_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite A4",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    monkeypatch.setattr(
        "evaluation.management.commands.run_benchmark.check_thresholds_note_guard",
        lambda note_path, split_hash=None: "accepted",
    )

    # N6-b: one item with chosen_prices=None and one with missing key -> 2 item(s) refused
    (eval_dir / "rep.report.json").write_text(
        json.dumps(
            {
                "report_id": "rep",
                "survey_end": "15/06/2026",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": None,
                    },
                    {
                        "item_number": 2,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="2 tuning item\\(s\\) have no chosen price"):
        call_command(
            "run_benchmark",
            split="tuning",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # N6-c: zero chosen prices -> counted CommandError, never ZeroDivisionError
    (eval_dir / "rep.report.json").write_text(
        json.dumps(
            {
                "report_id": "rep",
                "survey_end": "15/06/2026",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "0.00"}],
                    },
                    {
                        "item_number": 2,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": 0}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="2 tuning item\\(s\\) have no chosen price"):
        call_command(
            "run_benchmark",
            split="tuning",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )
