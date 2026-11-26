"""Tests to kill the surviving mutants identified in review:
1. Bootstrap without seed.
2. Percentile at alpha instead of alpha/2.
3. Finalist sorted by MRR before Recall@10.
4. Finalist being BM25 (contrasting baseline with itself).
5. R1 comparing the finalist with itself.
"""

from datetime import date
from random import Random as BaseRandom

import pytest

import evaluation.benchmark as benchmark_module
from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    bootstrap_paired_difference,
    select_finalist,
)


def test_mutant_bootstrap_seed_determinism_and_variation(monkeypatch):
    # 1. Bootstrap must pass the configured seed to its random generator.
    scores_a = [0.8, 0.6, 0.9, 0.4, 0.7, 0.5, 0.85, 0.65]
    scores_b = [0.5, 0.5, 0.6, 0.3, 0.4, 0.5, 0.60, 0.50]

    seeds = []

    class RecordingRandom:
        def __init__(self, seed):
            seeds.append(seed)
            self.delegate = BaseRandom(seed)

        def randrange(self, stop):
            return self.delegate.randrange(stop)

    monkeypatch.setattr(benchmark_module.random, "Random", RecordingRandom)

    res1 = bootstrap_paired_difference(scores_a, scores_b, seed=42, n_resamples=500)
    res2 = bootstrap_paired_difference(scores_a, scores_b, seed=42, n_resamples=500)
    res3 = bootstrap_paired_difference(scores_a, scores_b, seed=999, n_resamples=500)

    assert res1 == res2
    assert res1[1] != res3[1] or res1[2] != res3[2]
    assert seeds == [42, 42, 999]


def test_mutant_bootstrap_alpha_percentiles_two_sided():
    # 2. Must use alpha/2 and (1 - alpha/2) for two-sided (1 - alpha) CI
    # With 20 resamples and alpha=0.10, the correct indices are 1 and 19;
    # using alpha directly would choose 2 and 18.
    _, ci_lower_90, ci_upper_90 = bootstrap_paired_difference(
        [0.1, 0.2, 0.3, 0.4, 0.5], [0.0] * 5, alpha=0.10, n_resamples=20, seed=2
    )
    assert ci_lower_90 == 0.2
    assert ci_upper_90 == 0.5


def test_mutant_finalist_sorted_by_recall_before_mrr():
    # 3. Finalist rule: Recall@10 is the primary criterion, MRR@20 is tiebreaker only.
    # Method A has higher Recall@10 (0.80 vs 0.70) but lower MRR@20 (0.20 vs 0.90).
    # Method A MUST be selected.
    metrics = {
        "model_higher_recall": {"recall_at_10": 0.80, "mrr_at_20": 0.20},
        "model_higher_mrr": {"recall_at_10": 0.70, "mrr_at_20": 0.90},
    }
    assert select_finalist(metrics) == "model_higher_recall"


def test_mutant_finalist_cannot_be_bm25_and_r1_cannot_contrast_with_itself():
    # 4. BM25 is the baseline, NOT a finalist candidate.
    # Even if BM25 has higher Recall@10, it cannot be chosen as finalist.
    metrics = {
        "bm25": {"recall_at_10": 0.99, "mrr_at_20": 0.99},
        "candidate_model": {"recall_at_10": 0.80, "mrr_at_20": 0.40},
    }
    assert select_finalist(metrics) == "candidate_model"

    # If only BM25 is present, selecting finalist must fail
    with pytest.raises(ValueError, match="baseline"):
        select_finalist({"bm25": {"recall_at_10": 0.90, "mrr_at_20": 0.50}})


def test_orchestrator_finalist_uses_recall_before_mrr():
    # 5. End-to-end selection must use Recall@10 first, even when another method
    # has the higher MRR@20 on tuning.
    class RankingMethod:
        def __init__(self, name, preferred_rank):
            self.name = name
            self.preferred_rank = preferred_rank

        def rank(self, query, candidates):
            query_index = int(query.removeprefix("query-"))
            relevant = next(
                candidate
                for candidate in candidates
                if f"query-{query_index}" in candidate["description"]
            )
            distractors = [candidate for candidate in candidates if candidate is not relevant]
            relevant_rank = self.preferred_rank(query_index)
            ranked = distractors[: relevant_rank - 1] + [relevant]
            ranked.extend(distractors[relevant_rank - 1 :])
            return [(candidate, float(len(ranked) - idx)) for idx, candidate in enumerate(ranked)]

    high_recall = RankingMethod("high_recall", lambda item_index: 10 if item_index < 8 else 11)
    high_mrr = RankingMethod("high_mrr", lambda item_index: 1 if item_index < 7 else 11)

    items = [
        {
            "item_id": f"item-{index}",
            "description": f"query-{index}",
            "ground_truth": {index},
            "chosen_prices": [10.0],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
        for index in range(10)
    ]
    corpus = [
        {
            "id": index,
            "description": f"candidate query-{index}",
            "price": 10.0,
            "unit": "UNIDADE",
            "published_on": date(2026, 5, 1),
            "modality": 6,
        }
        for index in range(10)
    ]
    corpus.append(
        {
            "id": 99,
            "description": "unrelated distractor",
            "price": 10.0,
            "unit": "UNIDADE",
            "published_on": date(2026, 5, 1),
            "modality": 6,
        }
    )

    results = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5).run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[high_recall, high_mrr],
        baseline_method=BM25SearchMethod(),
    )

    assert results["methods"]["high_recall"]["metrics"]["recall_at_10"] == 0.8
    assert results["methods"]["high_mrr"]["metrics"]["recall_at_10"] == 0.7
    assert (
        results["methods"]["high_mrr"]["metrics"]["mrr_at_20"]
        > results["methods"]["high_recall"]["metrics"]["mrr_at_20"]
    )
    assert results["finalist"] == "high_recall"
