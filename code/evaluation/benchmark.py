"""Benchmark harness, evaluation metrics and paired statistical tests."""

import hashlib
import json
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
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


def compute_success_at_k(ranked_ids: Sequence[Any], ground_truth_ids: set[Any], k: int) -> float:
    """Compute Success@k (1.0 if at least one ground truth item is in top k, else 0.0).

    Descriptive metric only.
    """
    if not ground_truth_ids or k <= 0:
        return 0.0

    top_k = set(ranked_ids[:k])
    return 1.0 if bool(top_k.intersection(ground_truth_ids)) else 0.0


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
    n_resamples: int = 10000,
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
    n_resamples: int = 10000,
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
        perm_diff = sum(d if rng.random() < 0.5 else -d for d in diffs) / n
        if abs(perm_diff) >= obs_diff:
            extreme_count += 1

    return extreme_count / n_resamples


@dataclass(frozen=True)
class DatasetSplit:
    tuning_items: tuple[str, ...]
    measurement_items: tuple[str, ...]
    sha256_hash: str


def _compute_split_hash(tuning_items: Sequence[str], measurement_items: Sequence[str]) -> str:
    content = json.dumps(
        {
            "tuning_items": list(tuning_items),
            "measurement_items": list(measurement_items),
        },
        sort_keys=True,
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def create_dataset_split(
    items: Sequence[dict[str, Any]],
    tuning_fraction: float = 0.4,
    seed: int = 42,
) -> DatasetSplit:
    """Stratified split by report_id and item_kind with fixed seed."""
    groups: dict[tuple[str, str], list[str]] = {}
    for it in items:
        rep = str(it.get("report_id", ""))
        kind = str(it.get("item_kind", ""))
        item_id = str(it.get("item_id", ""))
        groups.setdefault((rep, kind), []).append(item_id)

    rng = random.Random(seed)
    tuning_list: list[str] = []
    measurement_list: list[str] = []

    for key in sorted(groups.keys()):
        item_ids = list(groups[key])
        item_ids.sort()
        rng.shuffle(item_ids)

        n_tune = int(round(len(item_ids) * tuning_fraction))
        tuning_list.extend(item_ids[:n_tune])
        measurement_list.extend(item_ids[n_tune:])

    tuning_list.sort()
    measurement_list.sort()

    sha256_hash = _compute_split_hash(tuning_list, measurement_list)

    return DatasetSplit(
        tuning_items=tuple(tuning_list),
        measurement_items=tuple(measurement_list),
        sha256_hash=sha256_hash,
    )


def verify_split_hash(
    tuning_items: Sequence[str],
    measurement_items: Sequence[str],
    expected_hash: str,
) -> bool:
    """Verify SHA-256 hash of dataset split items."""
    computed = _compute_split_hash(tuning_items, measurement_items)
    return computed == expected_hash


def check_thresholds_note_guard(note_path: Path) -> bool:
    """Check that thresholds note exists and resides under TCC/decisões/."""
    path = Path(note_path).resolve()
    if not path.exists():
        raise ValueError(f"Thresholds note file does not exist: {note_path}")

    # Check path contains 'TCC/decisões' or resolved path is under repo's TCC/decisões
    parts = path.parts
    if "TCC" not in parts or "decisões" not in parts:
        raise ValueError(f"Thresholds note must point to a file in TCC/decisões/: {note_path}")

    return True


@dataclass(frozen=True)
class PriceCandidateSim:
    id: int
    price: Decimal
    similarity: float
    unit: str = "UNIDADE"


def generate_anchor_prices(
    chosen_prices: Sequence[Decimal | float],
    sigmas: Sequence[float],
    n_draws: int = 200,
    seed: int = 42,
) -> dict[float, list[float]]:
    """Generate anchor prices using log-normal noise.

    Anchor = exp(mean(ln(p)) + sigma * Z), with Z ~ N(0, 1).
    Reuses the same Z across levels for each draw.
    sigma = 0 is labeled 'upper bound (oracle)'.
    """
    valid_prices = [float(p) for p in chosen_prices if float(p) > 0]
    if not valid_prices:
        raise ValueError("At least one positive price required")

    mean_ln = sum(math.log(p) for p in valid_prices) / len(valid_prices)

    rng = random.Random(seed)
    z_draws = [rng.gauss(0.0, 1.0) for _ in range(n_draws)]

    anchors_by_sigma: dict[float, list[float]] = {}
    for sigma in sigmas:
        sigma_val = float(sigma)
        anchors_by_sigma[sigma_val] = [math.exp(mean_ln + sigma_val * z) for z in z_draws]

    return anchors_by_sigma


def rank_by_price_only(
    candidates: Sequence[Any],
    anchor: Decimal | float,
) -> list[Any]:
    """Rank candidates by |ln(price / anchor)| asc, breaking ties by candidate id."""
    anchor_f = float(anchor)
    if anchor_f <= 0:
        raise ValueError("Anchor price must be positive")

    def sort_key(candidate: Any) -> tuple[float, Any]:
        p = getattr(candidate, "price", None)
        p_val = float(p) if p is not None else 0.0
        if p_val <= 0:
            return (float("inf"), candidate.id)
        dist = abs(math.log(p_val / anchor_f))
        return (round(dist, 9), candidate.id)

    return sorted(candidates, key=sort_key)


def classify_easy_hard_items(
    candidates: Sequence[Any],
    anchor: Decimal | float,
    ground_truth_ids: set[Any],
    k: int = 10,
) -> bool:
    """Classify an item as easy if price-only baseline puts a relevant item in top k."""
    if not ground_truth_ids or not candidates:
        return False
    ranked = rank_by_price_only(candidates, anchor=anchor)
    top_k_ids = set(c.id for c in ranked[:k])
    return bool(top_k_ids.intersection(ground_truth_ids))


def evaluate_r1_acceptance(
    diff_mean: float,
    ci_95_lower: float,
    ci_95_upper: float,
    ci_90_lower: float,
    ci_90_upper: float,
) -> dict[str, Any]:
    """Evaluate R1 acceptance rules.

    - Accept if lower bound of 95% CI of paired difference > 0.05.
    - Declare a tie only if 90% CI lies entirely within (-0.08, +0.08).
    - Otherwise call it inconclusive.
    """
    if ci_95_lower > 0.05:
        outcome = "accepted"
    elif ci_90_lower > -0.08 and ci_90_upper < 0.08:
        outcome = "tie"
    else:
        outcome = "inconclusive"

    return {
        "outcome": outcome,
        "diff_mean": diff_mean,
        "ci_95": (ci_95_lower, ci_95_upper),
        "ci_90": (ci_90_lower, ci_90_upper),
    }


def evaluate_r2_acceptance(
    r1_result: dict[str, Any],
    sigma_025_ci: tuple[float, float, float],
    hard_gain_ci: tuple[float, float, float],
) -> bool:
    """Evaluate R2 acceptance rules.

    Accepted when all three hold:
    (a) R1 is accepted;
    (b) at sigma=0.25, system beats price-only with lower 95% CI > 0;
    (c) finalist gain over BM25 persists on hard items with lower 95% CI > 0.
    """
    if r1_result.get("outcome") != "accepted":
        return False
    if sigma_025_ci[1] <= 0:
        return False
    return hard_gain_ci[1] > 0


def resolve_candidate_price(
    item: Any,
    prefer_awarded: bool = True,
) -> Decimal | None:
    """Resolve candidate item price for R2 anchor and price-only ranking.

    The candidate price is the awarded price when stored and positive,
    otherwise the estimated price when positive.
    Secret-budget items have no price, and a price of zero is never a price.
    Note: The specific price metric used in measured R2 remains configurable.
    """
    if getattr(item, "secret_budget", False):
        return None

    awarded = getattr(item, "awarded_unit_price", None)
    estimated = getattr(item, "estimated_unit_price", None)

    if prefer_awarded:
        if awarded is not None and awarded > Decimal("0"):
            return awarded
        if estimated is not None and estimated > Decimal("0"):
            return estimated
    else:
        if estimated is not None and estimated > Decimal("0"):
            return estimated
        if awarded is not None and awarded > Decimal("0"):
            return awarded
    return None


@dataclass(frozen=True)
class PublicItemSim:
    id: Any
    published_on: Any = None
    modality: int | None = None
    state: str = ""
    awarded_unit_price: Decimal | None = None
    estimated_unit_price: Decimal | None = None
    secret_budget: bool = False
    unit: str = "UNIDADE"

    @property
    def price(self) -> Decimal | None:
        return resolve_candidate_price(self)


def filter_candidate_corpus(
    items: Sequence[Any],
    survey_date: date,
    allowed_modalities: tuple[int, ...] = (6, 7, 8),
) -> list[Any]:
    """Filter candidate items to define C(q).

    RN07 window: 12 months up to survey date (report date).
    Allowed modalities: 6, 7, 8 (all states included).
    """
    try:
        start_date = survey_date.replace(year=survey_date.year - 1)
    except ValueError:
        start_date = survey_date.replace(year=survey_date.year - 1, day=28)

    filtered = []
    for it in items:
        pub = getattr(it, "published_on", None)
        mod = getattr(it, "modality", None)
        if pub is None or mod is None:
            continue
        if start_date <= pub <= survey_date and mod in allowed_modalities:
            filtered.append(it)
    return filtered
