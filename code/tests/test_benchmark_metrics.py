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


def test_permutation_test_paired():
    scores_a = [0.8, 0.9, 0.7, 0.85, 0.9] * 10
    scores_b = [0.7, 0.8, 0.6, 0.75, 0.8] * 10

    p_val = permutation_test_paired(scores_a, scores_b, n_resamples=1000, seed=42)
    assert p_val < 0.01
