"""Tests for evaluation benchmark metrics and bootstrap comparison."""

import pytest

from evaluation.benchmark import (
    bootstrap_paired_difference,
    compute_mrr_at_k,
    compute_recall_at_k,
    permutation_test_paired,
)


def test_compute_recall_at_k():
    # Ground truth items: 10, 20
    # Ranked items: [10, 30, 40, 50]
    gt = {10, 20}
    ranked = [10, 30, 40, 50]

    assert compute_recall_at_k(ranked, gt, k=1) == 0.5
    assert compute_recall_at_k(ranked, gt, k=2) == 0.5
    assert compute_recall_at_k(ranked, gt, k=5) == 0.5

    # With empty ground truth, return 0.0
    assert compute_recall_at_k(ranked, set(), k=5) == 0.0

    # With full recall
    assert compute_recall_at_k([10, 20], gt, k=2) == 1.0


def test_compute_mrr_at_k():
    gt = {20, 30}
    # First relevant at rank 2 (index 1) -> MRR = 1/2 = 0.5
    ranked = [10, 20, 30, 40]
    assert compute_mrr_at_k(ranked, gt, k=20) == 0.5

    # First relevant at rank 1 -> 1.0
    assert compute_mrr_at_k([20, 10], gt, k=20) == 1.0

    # No relevant in top k -> 0.0
    assert compute_mrr_at_k([10, 40, 50], gt, k=20) == 0.0


def test_bootstrap_paired_difference():
    # Method A is consistently better than Method B by 0.1
    scores_a = [0.8, 0.9, 0.7, 0.85, 0.9] * 10
    scores_b = [0.7, 0.8, 0.6, 0.75, 0.8] * 10

    diff_mean, ci_lower, ci_upper = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.05, n_resamples=1000, seed=42
    )

    assert pytest.approx(diff_mean, abs=1e-4) == 0.1
    assert ci_lower > 0.05
    assert ci_upper < 0.15


def test_bootstrap_paired_vs_unpaired_mutant():
    # Kill mutant: bootstrap without pairing
    # Heterogeneous item scores with strictly constant paired difference (+0.05)
    scores_b = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7] * 10
    scores_a = [b + 0.05 for b in scores_b]

    diff_mean, ci_lower, ci_upper = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.05, n_resamples=1000, seed=42
    )
    # Under paired bootstrap, difference is constant 0.05 for every resample
    assert pytest.approx(diff_mean, abs=1e-6) == 0.05
    assert pytest.approx(ci_lower, abs=1e-6) == 0.05
    assert pytest.approx(ci_upper, abs=1e-6) == 0.05
    assert (ci_upper - ci_lower) < 1e-5


def test_bootstrap_seed_determinism_and_alpha_percentiles_mutants():
    # Kill mutants: bootstrap without seed, and wrong percentile indices
    scores_a = [0.8, 0.6, 0.9, 0.7, 0.5] * 10
    scores_b = [0.7, 0.6, 0.8, 0.6, 0.4] * 10

    res1 = bootstrap_paired_difference(scores_a, scores_b, alpha=0.05, n_resamples=500, seed=42)
    res2 = bootstrap_paired_difference(scores_a, scores_b, alpha=0.05, n_resamples=500, seed=42)
    res3 = bootstrap_paired_difference(scores_a, scores_b, alpha=0.05, n_resamples=500, seed=99)

    assert res1 == res2
    assert res1 != res3

    # Alpha 0.10 (90% CI) must be strictly narrower than alpha 0.05 (95% CI)
    _, ci_90_l, ci_90_u = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.10, n_resamples=1000, seed=42
    )
    _, ci_95_l, ci_95_u = bootstrap_paired_difference(
        scores_a, scores_b, alpha=0.05, n_resamples=1000, seed=42
    )
    assert ci_90_l >= ci_95_l
    assert ci_90_u <= ci_95_u


def test_permutation_test_paired_seed_and_identical_n8():
    # Kill mutants: permutation without seed, and permutation returning 0 for identical
    scores_a = [0.8, 0.9, 0.7, 0.85, 0.9] * 10
    scores_b = [0.7, 0.8, 0.6, 0.75, 0.8] * 10

    p1 = permutation_test_paired(scores_a, scores_b, n_resamples=500, seed=42)
    p2 = permutation_test_paired(scores_a, scores_b, n_resamples=500, seed=42)
    p3 = permutation_test_paired(scores_a, scores_b, n_resamples=500, seed=99)

    assert p1 == p2
    assert p1 != p3
    # N8: Monte Carlo p-value is strictly > 0 (at minimum 1 / (n + 1))
    assert p1 > 0.0
    assert p1 == pytest.approx(1.0 / 501.0, abs=0.01)

    # Identical scores should yield p = 1.0 (extreme_count = n_resamples -> (n+1)/(n+1) = 1.0)
    p_identical = permutation_test_paired(scores_a, scores_a, n_resamples=500, seed=42)
    assert p_identical == 1.0
