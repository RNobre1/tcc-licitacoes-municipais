"""Benchmark harness, evaluation metrics and paired statistical tests."""

import random
from collections.abc import Sequence
from typing import Any


def compute_recall_at_k(ranked_ids: Sequence[Any], ground_truth_ids: set[Any], k: int) -> float:
    """Compute Recall@k for a single item.

    If ground_truth_ids is empty, returns 0.0.
    """
    if not ground_truth_ids or k <= 0:
        return 0.0

    top_k = set(ranked_ids[:k])
    hits = len(top_k.intersection(ground_truth_ids))
    return hits / len(ground_truth_ids)


def compute_mrr_at_k(ranked_ids: Sequence[Any], ground_truth_ids: set[Any], k: int = 20) -> float:
    """Compute MRR@k (reciprocal rank of first relevant item in top k).

    If no relevant item is found in top k, returns 0.0.
    """
    if not ground_truth_ids or k <= 0:
        return 0.0

    for rank, item_id in enumerate(ranked_ids[:k], start=1):
        if item_id in ground_truth_ids:
            return 1.0 / rank

    return 0.0


def bootstrap_paired_difference(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    alpha: float = 0.05,
    n_resamples: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Percentile bootstrap over items for paired difference (A - B).

    Returns (mean_diff, ci_lower, ci_upper) at (1 - alpha) confidence.
    """
    if len(scores_a) != len(scores_b):
        raise ValueError("scores_a and scores_b must have the same length")
    n = len(scores_a)
    if n == 0:
        return 0.0, 0.0, 0.0

    diffs = [a - b for a, b in zip(scores_a, scores_b, strict=False)]
    mean_diff = sum(diffs) / n

    rng = random.Random(seed)
    bootstrap_means: list[float] = []

    for _ in range(n_resamples):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        bootstrap_means.append(sum(sample) / n)

    bootstrap_means.sort()
    lower_idx = int((alpha / 2.0) * n_resamples)
    upper_idx = int((1.0 - alpha / 2.0) * n_resamples)
    upper_idx = min(upper_idx, n_resamples - 1)

    ci_lower = bootstrap_means[lower_idx]
    ci_upper = bootstrap_means[upper_idx]

    return mean_diff, ci_lower, ci_upper


def permutation_test_paired(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 1000,
    seed: int = 42,
) -> float:
    """Two-sided paired permutation test on difference of means."""
    if len(scores_a) != len(scores_b):
        raise ValueError("scores_a and scores_b must have the same length")
    n = len(scores_a)
    if n == 0:
        return 1.0

    diffs = [a - b for a, b in zip(scores_a, scores_b, strict=False)]
    obs_diff = abs(sum(diffs) / n)

    rng = random.Random(seed)
    extreme_count = 0

    for _ in range(n_resamples):
        # random sign flip for each pair
        perm_diff = sum(d if rng.random() < 0.5 else -d for d in diffs) / n
        if abs(perm_diff) >= obs_diff:
            extreme_count += 1

    return extreme_count / n_resamples


class DatasetSplit:
    pass


def create_dataset_split(items, tuning_fraction: float = 0.4, seed: int = 42):
    raise NotImplementedError


def verify_split_hash(tuning_items, measurement_items, expected_hash: str) -> bool:
    raise NotImplementedError


def check_thresholds_note_guard(note_path) -> bool:
    raise NotImplementedError
