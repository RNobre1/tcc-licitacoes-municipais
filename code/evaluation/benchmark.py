"""Benchmark harness, evaluation metrics and paired statistical tests."""

from collections.abc import Sequence
from typing import Any


def compute_recall_at_k(ranked_ids: Sequence[Any], ground_truth_ids: set[Any], k: int) -> float:
    raise NotImplementedError


def compute_mrr_at_k(ranked_ids: Sequence[Any], ground_truth_ids: set[Any], k: int = 20) -> float:
    raise NotImplementedError


def bootstrap_paired_difference(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    alpha: float = 0.05,
    n_resamples: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float]:
    raise NotImplementedError


def permutation_test_paired(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 1000,
    seed: int = 42,
) -> float:
    raise NotImplementedError
