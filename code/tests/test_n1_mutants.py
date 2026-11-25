"""Tests to kill the 4 surviving mutants identified in review:
1. Bootstrap without seed.
2. Percentile at alpha instead of alpha/2.
3. Finalist sorted by MRR before Recall@10.
4. Finalist being BM25 (contrasting baseline with itself).
"""

import pytest

from evaluation.benchmark import (
    bootstrap_paired_difference,
    select_finalist,
)


def test_mutant_bootstrap_seed_determinism_and_variation():
    # 1. Bootstrap must use seed: same seed gives identical bounds, different seeds vary
    scores_a = [0.8, 0.6, 0.9, 0.4, 0.7, 0.5, 0.85, 0.65]
    scores_b = [0.5, 0.5, 0.6, 0.3, 0.4, 0.5, 0.60, 0.50]

    res1 = bootstrap_paired_difference(scores_a, scores_b, seed=42, n_resamples=500)
    res2 = bootstrap_paired_difference(scores_a, scores_b, seed=42, n_resamples=500)
    res3 = bootstrap_paired_difference(scores_a, scores_b, seed=999, n_resamples=500)

    # Deterministic with same seed
    assert res1 == res2
    # Seed actually changes the resamples
    assert res1[1] != res3[1] or res1[2] != res3[2]


def test_mutant_bootstrap_alpha_percentiles_two_sided():
    # 2. Must use alpha/2 and (1 - alpha/2) for two-sided (1 - alpha) CI
    # If alpha=0.10 is used directly instead of alpha/2=0.05,
    # lower_idx would be 100 instead of 50 (in 1000 resamples),
    # and upper_idx would be 900 instead of 950.
    scores_a = [float(i) for i in range(100)]
    scores_b = [0.0] * 100

    # With n_resamples=1000 and alpha=0.10:
    # 5th percentile index is 50, 10th percentile index is 100.
    _, ci_lower_90, ci_upper_90 = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.10, n_resamples=1000, seed=42
    )
    # The 90% CI (alpha=0.10) must be strictly wider than an 80% CI (alpha=0.20)
    _, ci_lower_80, ci_upper_80 = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.20, n_resamples=1000, seed=42
    )

    # Two-sided 90% CI must be wider than 80% CI:
    # lower_90 (5th pct) < lower_80 (10th pct)
    assert ci_lower_90 < ci_lower_80
    # upper_90 (95th pct) > upper_80 (90th pct)
    assert ci_upper_90 > ci_upper_80


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
