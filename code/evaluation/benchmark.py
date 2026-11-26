"""Benchmark harness, evaluation metrics and paired statistical tests."""

import hashlib
import json
import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.db.models import QuerySet

from ingestion.units import normalize_unit
from semantic_index.embedding import EmbeddingModel

ALLOWED_MODALITIES = (6, 7, 8)


def _normalized_candidate_unit(doc: Any) -> str:
    if isinstance(doc, dict):
        norm = doc.get("unit_normalized")
        if norm:
            return str(norm)
        return normalize_unit(doc.get("unit", "UNIDADE"))
    norm = getattr(doc, "unit_normalized", "")
    if norm:
        return str(norm)
    return normalize_unit(getattr(doc, "unit", "UNIDADE"))


def check_collection_coverage(
    model: EmbeddingModel,
    candidate_ids: Sequence[Any],
    client: Any = None,
    batch_size: int = 500,
) -> dict[str, Any]:
    """Count how many C(q) PublicItem IDs exist in the model's Qdrant collection."""
    from semantic_index import get_qdrant_client
    from semantic_index.embedding import collection_name_for_model

    qdrant_client = client if client is not None else get_qdrant_client()
    collection_name = collection_name_for_model(model)

    if not qdrant_client.collection_exists(collection_name):
        raise ValueError(f"Semantic index collection '{collection_name}' does not exist")

    unique_ids = sorted({int(pk) for pk in candidate_ids})
    unique_id_set = set(unique_ids)
    present_ids: set[int] = set()

    for start in range(0, len(unique_ids), batch_size):
        batch = unique_ids[start : start + batch_size]
        records = qdrant_client.retrieve(
            collection_name=collection_name,
            ids=batch,
            with_payload=False,
            with_vectors=False,
        )
        for record in records:
            record_id = int(record.id)
            if record_id in unique_id_set:
                present_ids.add(record_id)

    expected_count = len(unique_ids)
    present_count = len(present_ids)
    missing_count = expected_count - present_count
    coverage_ratio = (present_count / expected_count) if expected_count else 1.0

    return {
        "collection": collection_name,
        "expected_count": expected_count,
        "present_count": present_count,
        "missing_count": missing_count,
        "coverage_ratio": coverage_ratio,
    }


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


def _extract_doc_id(doc: Any) -> Any:
    if isinstance(doc, dict):
        return doc.get("id")
    if hasattr(doc, "id"):
        return doc.id
    if hasattr(doc, "pk"):
        return doc.pk
    return doc


def group_tied_scored_ids(
    ranked_scored: Sequence[tuple[Any, Any]],
) -> list[tuple[float, list[Any]]]:
    """Group a full (doc_or_id, score) sequence into exact-score tie groups descending."""
    if not ranked_scored:
        return []

    ordered = sorted(
        ((_extract_doc_id(doc), float(score)) for doc, score in ranked_scored),
        key=lambda pair: pair[1],
        reverse=True,
    )
    groups: list[tuple[float, list[Any]]] = []
    current_score = ordered[0][1]
    current_ids: list[Any] = [ordered[0][0]]
    for doc_id, score in ordered[1:]:
        if score == current_score:
            current_ids.append(doc_id)
        else:
            groups.append((current_score, current_ids))
            current_score = score
            current_ids = [doc_id]
    groups.append((current_score, current_ids))
    return groups


def compute_expected_recall_at_k(
    ranked_scored: Sequence[tuple[Any, Any]],
    ground_truth_ids: set[Any],
    k: int,
) -> float:
    """Compute exact expected Recall@k over uniform random orderings within tied groups."""
    if not ground_truth_ids or k <= 0 or not ranked_scored:
        return 0.0

    groups = group_tied_scored_ids(ranked_scored)
    expected_hits = 0.0
    offset = 0
    for _score, group_ids in groups:
        if offset >= k:
            break
        m = len(group_ids)
        r = sum(1 for doc_id in group_ids if doc_id in ground_truth_ids)
        if offset + m <= k:
            expected_hits += float(r)
        else:
            t = k - offset
            expected_hits += r * (t / m)
        offset += m
    return expected_hits / len(ground_truth_ids)


def compute_expected_success_at_k(
    ranked_scored: Sequence[tuple[Any, Any]],
    ground_truth_ids: set[Any],
    k: int,
) -> float:
    """Compute exact expected Success@k over uniform random orderings within tied groups."""
    if not ground_truth_ids or k <= 0 or not ranked_scored:
        return 0.0

    groups = group_tied_scored_ids(ranked_scored)
    offset = 0
    for _score, group_ids in groups:
        if offset >= k:
            break
        m = len(group_ids)
        r = sum(1 for doc_id in group_ids if doc_id in ground_truth_ids)
        if r > 0:
            if offset + m <= k:
                return 1.0
            t = k - offset
            if r > m - t:
                return 1.0
            prob_no_hit = 1.0
            for i in range(t):
                prob_no_hit *= (m - r - i) / (m - i)
            return 1.0 - prob_no_hit
        offset += m
    return 0.0


def compute_expected_mrr_at_k(
    ranked_scored: Sequence[tuple[Any, Any]],
    ground_truth_ids: set[Any],
    k: int = 20,
) -> float:
    """Compute exact expected MRR@k over uniform random orderings within tied groups."""
    if not ground_truth_ids or k <= 0 or not ranked_scored:
        return 0.0

    groups = group_tied_scored_ids(ranked_scored)
    offset = 0
    for _score, group_ids in groups:
        if offset >= k:
            break
        m = len(group_ids)
        r = sum(1 for doc_id in group_ids if doc_id in ground_truth_ids)
        if r > 0:
            t = min(k - offset, m)
            max_j = min(t, m - r + 1)
            expected_rr = 0.0
            prob_first_at_j = r / m
            for j in range(1, max_j + 1):
                expected_rr += prob_first_at_j / (offset + j)
                if j < max_j:
                    prob_first_at_j *= (m - r - (j - 1)) / (m - j)
            return expected_rr
        offset += m
    return 0.0


def shuffle_tied_groups(
    ranked_scored: Sequence[tuple[Any, Any]],
    rng: random.Random,
) -> list[tuple[Any, float]]:
    """Shuffle item order strictly within each exact-score tie group."""
    if not ranked_scored:
        return []

    ordered = sorted(
        ((doc, float(score)) for doc, score in ranked_scored),
        key=lambda pair: pair[1],
        reverse=True,
    )
    result: list[tuple[Any, float]] = []
    idx = 0
    n = len(ordered)
    while idx < n:
        end = idx + 1
        current_score = ordered[idx][1]
        while end < n and ordered[end][1] == current_score:
            end += 1
        group = ordered[idx:end]
        if len(group) > 1:
            rng.shuffle(group)
        result.extend(group)
        idx = end
    return result


def compute_tie_sensitivity(
    ranked_scored: Sequence[tuple[Any, Any]],
    ground_truth_ids: set[Any],
    top_n: int = 20,
) -> dict[str, bool]:
    """Return tie-sensitivity flags for Recall@10, MRR@20, and R2 screening pool."""
    if not ranked_scored:
        return {"recall_at_10": False, "mrr_at_20": False, "r2_pool": False}

    groups = group_tied_scored_ids(ranked_scored)
    recall_sensitive = False
    mrr_sensitive = False
    r2_pool_sensitive = False
    found_first_rel_in_20 = False

    offset = 0
    for _score, group_ids in groups:
        m = len(group_ids)
        r = sum(1 for doc_id in group_ids if doc_id in ground_truth_ids) if ground_truth_ids else 0

        if offset < 10 < offset + m and 0 < r < m:
            recall_sensitive = True

        if not found_first_rel_in_20 and offset < 20 and r > 0:
            found_first_rel_in_20 = True
            if m > 1 and r < m:
                mrr_sensitive = True

        if offset < top_n < offset + m:
            r2_pool_sensitive = True

        offset += m

    return {
        "recall_at_10": recall_sensitive,
        "mrr_at_20": mrr_sensitive,
        "r2_pool": r2_pool_sensitive,
    }


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

    return (extreme_count + 1) / (n_resamples + 1)


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


def check_thresholds_note_guard(
    note_path: Path | str,
    split_hash: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Check that thresholds decision note exists, is valid, and matches split hash.

    Requirements:
    1. Regular file, not a directory.
    2. Resides strictly under repo's TCC/decisões/ (no symlink escape).
    3. Not empty.
    4. Has status: aceita.
    5. If split_hash provided, hash is present in the note.
    """
    path = Path(note_path).resolve()
    if not path.exists():
        raise ValueError(f"Thresholds note file does not exist: {note_path}")
    if not path.is_file():
        raise ValueError(f"Thresholds note must be a regular file, not a directory: {note_path}")

    import re

    from django.conf import settings

    root = (repo_root or Path(settings.BASE_DIR).parent).resolve()
    decisoes_dir = (root / "TCC" / "decisões").resolve()

    try:
        path.relative_to(decisoes_dir)
    except ValueError:
        raise ValueError(
            f"Thresholds note must reside under repository's TCC/decisões/: {note_path}"
        ) from None

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Thresholds note is empty: {note_path}")

    if not re.search(r"^status:\s*aceita\s*$", content, re.MULTILINE | re.IGNORECASE):
        raise ValueError(f"Thresholds note must have 'status: aceita': {note_path}")

    if split_hash is not None and split_hash.lower() not in content.lower():
        raise ValueError(
            f"Split SHA-256 hash {split_hash} was not found recorded in decision note: {note_path}"
        )

    return content


@dataclass(frozen=True)
class PriceCandidateSim:
    id: int
    price: Decimal
    similarity: float
    unit: str = "UNIDADE"


def derive_item_seed(base_seed: int, item_id: str | int) -> int:
    """Derive deterministic item seed from base seed and item id."""
    h = hashlib.sha256(f"{base_seed}:{item_id}".encode()).hexdigest()
    return int(h[:8], 16)


def generate_anchor_prices(
    chosen_prices: Sequence[Decimal | float],
    sigmas: Sequence[float],
    n_draws: int = 200,
    seed: int = 42,
    item_id: str | int | None = None,
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

    effective_seed = derive_item_seed(seed, item_id) if item_id is not None else seed
    rng = random.Random(effective_seed)
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
    """Classify an item as easy if expected Success@k of price-only under ties > 0."""
    anchor_f = float(anchor)
    if anchor_f <= 0:
        raise ValueError("Anchor price must be positive")
    if not ground_truth_ids or not candidates:
        return False

    scored_candidates: list[tuple[Any, float]] = []
    for candidate in candidates:
        p = getattr(candidate, "price", None)
        p_val = float(p) if p is not None else 0.0
        if p_val <= 0:
            scored_candidates.append((candidate, float("-inf")))
        else:
            dist = abs(math.log(p_val / anchor_f))
            scored_candidates.append((candidate, -round(dist, 9)))

    p_success = compute_expected_success_at_k(scored_candidates, ground_truth_ids, k=k)
    return p_success > 0.0


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
    description: str = ""
    published_on: Any = None
    modality: int | None = None
    state: str = ""
    awarded_unit_price: Decimal | None = None
    estimated_unit_price: Decimal | None = None
    secret_budget: bool = False
    unit: str = "UNIDADE"
    price: Decimal | None = None


def filter_candidate_corpus(
    items: Iterable[Any],
    survey_date: date,
    allowed_modalities: tuple[int, ...] = ALLOWED_MODALITIES,
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
        if isinstance(it, dict):
            pub = it.get("published_on")
            mod = it.get("modality")
        else:
            pub = getattr(it, "published_on", None)
            mod = getattr(it, "modality", None)
        if pub is None or mod is None:
            continue
        if start_date <= pub <= survey_date and mod in allowed_modalities:
            filtered.append(it)
    return filtered


def select_finalist(
    method_tuning_metrics: dict[str, dict[str, float]],
    baseline_name: str = "bm25",
) -> str:
    """Select the finalist method based on highest Recall@10, ties broken by MRR@20.

    BM25 is the baseline and cannot be chosen as a finalist candidate.
    """
    if not method_tuning_metrics:
        raise ValueError("Cannot select finalist from empty metrics")
    eligible = {k: v for k, v in method_tuning_metrics.items() if k != baseline_name}
    if not eligible:
        raise ValueError(
            f"No eligible candidate methods to select finalist ({baseline_name} is baseline)"
        )
    sorted_methods = sorted(eligible.keys())
    return max(
        sorted_methods,
        key=lambda m: (
            eligible[m].get("recall_at_10", 0.0),
            eligible[m].get("mrr_at_20", 0.0),
        ),
    )


class FakeDeterministicEmbeddingModel:
    """Deterministic fake embedding model for tests without external dependencies.

    The model does not have access to evaluation labels.
    """

    name: str = "fake-embed"
    revision: str = "v1"
    dimension: int = 8

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        vectors = []
        for text in queries:
            vector = [0.0] * self.dimension
            for word in text.lower().split():
                index = sum(ord(character) for character in word) % self.dimension
                vector[index] += 1.0
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector] if norm else vector)
        return vectors

    def embed_passages(self, passages: Sequence[str]) -> list[list[float]]:
        return self.embed_queries(passages)


class BM25SearchMethod:
    """Baseline keyword search using BM25Okapi over candidate corpus."""

    def __init__(self, name: str = "bm25", k1: float = 1.5, b: float = 0.75):
        self.name = name
        self.k1 = k1
        self.b = b

    def rank(
        self,
        query: str,
        candidates: Sequence[Any],
    ) -> list[tuple[Any, float]]:
        if not candidates:
            return []

        from rank_bm25 import BM25Okapi

        descriptions = [
            candidate.get("description", "")
            if isinstance(candidate, dict)
            else getattr(candidate, "description", "")
            for candidate in candidates
        ]
        corpus_tokens = [
            [token.lower() for token in description.split() if token.strip()]
            for description in descriptions
        ]
        model = BM25Okapi(corpus_tokens, k1=self.k1, b=self.b)
        query_tokens = [token.lower() for token in query.split() if token.strip()]
        scores = model.get_scores(query_tokens)

        ranked = sorted(
            zip(candidates, scores, strict=False),
            key=lambda x: (
                x[1],
                -getattr(x[0], "id", x[0].get("id", 0) if isinstance(x[0], dict) else 0),
            ),
            reverse=True,
        )
        return [(doc, float(score)) for doc, score in ranked]


class SemanticSearchMethod:
    """Rank candidates with semantic_index vectors, without access to evaluation labels."""

    def __init__(self, model: EmbeddingModel, name: str = "semantic", client: Any = None):
        self.name = name
        self.model = model
        self.client = client

    def rank(
        self,
        query: str,
        candidates: Sequence[Any],
    ) -> list[tuple[Any, float]]:
        if not candidates:
            return []

        from ingestion.models import PublicItem

        if all(isinstance(candidate, PublicItem) for candidate in candidates):
            from semantic_index.search import StructuredFilter, semantic_search

            dates = [candidate.published_on for candidate in candidates]
            date_window = (min(dates), max(dates))
            search_limit = len(candidates) + 20
            scored_items = semantic_search(
                self.model,
                query,
                structured_filter=StructuredFilter(
                    date_window=date_window,
                    modality=list(ALLOWED_MODALITIES),
                ),
                limit=search_limit,
                client=self.client,
                exact=True,
            )
            candidates_by_id = {candidate.pk: candidate for candidate in candidates}
            return [
                (candidates_by_id[result.item.pk], float(result.score))
                for result in scored_items
                if result.item.pk in candidates_by_id
                and candidates_by_id[result.item.pk].modality in ALLOWED_MODALITIES
            ]

        query_vectors = self.model.embed_queries([query])
        if not query_vectors:
            return []
        query_vec = query_vectors[0]
        passages = [
            candidate.get("description", "")
            if isinstance(candidate, dict)
            else getattr(candidate, "description", "")
            for candidate in candidates
        ]
        passage_vecs = self.model.embed_passages(passages)

        query_norm = math.sqrt(sum(value * value for value in query_vec))
        scores = []
        for passage_vec in passage_vecs:
            dot_product = sum(
                query_value * passage_value
                for query_value, passage_value in zip(query_vec, passage_vec, strict=False)
            )
            passage_norm = math.sqrt(sum(value * value for value in passage_vec))
            if query_norm == 0.0 or passage_norm == 0.0:
                scores.append(0.0)
            else:
                scores.append(dot_product / (query_norm * passage_norm))

        ranked = sorted(
            zip(candidates, scores, strict=False),
            key=lambda x: (
                x[1],
                -getattr(x[0], "id", x[0].get("id", 0) if isinstance(x[0], dict) else 0),
            ),
            reverse=True,
        )
        return ranked


class BenchmarkOrchestrator:
    """Orchestrates search benchmark evaluation, finalist selection, and R2 RF23 ranking."""

    def __init__(
        self,
        n_noise_draws: int = 200,
        n_bootstrap_resamples: int = 10000,
        seed: int = 42,
        top_n: int = 20,
    ) -> None:
        self.n_noise_draws = n_noise_draws
        self.n_bootstrap_resamples = n_bootstrap_resamples
        self.seed = seed
        self.top_n = top_n

    def rank_with_rf23(
        self,
        candidates: Sequence[Any],
        anchor: Decimal | float | None = None,
        unit: str = "UNIDADE",
    ) -> list[Any]:
        """Rank candidates using RF23 proximity rules via pricing.ranking.rank_candidates."""
        from pricing.ranking import rank_candidates

        expected_price = Decimal(str(anchor)) if anchor is not None else None
        return rank_candidates(
            candidates,
            expected_price=expected_price,
            item_unit=normalize_unit(unit),
        )

    def run_benchmark(
        self,
        items: Sequence[dict[str, Any]],
        corpus: Sequence[Any] | QuerySet[Any],
        split_name: str = "tuning",
        active_item_ids: set[str] | None = None,
        finalist: str | None = None,
        candidate_methods: Sequence[Any] | None = None,
        baseline_method: Any | None = None,
        synthetic: bool = False,
        top_n: int | None = None,
        n: int | None = None,
        include_full_rankings: bool = False,
    ) -> dict[str, Any]:
        effective_top_n = n if n is not None else (top_n if top_n is not None else self.top_n)
        """Run benchmark over items, applying per-item C(q), evaluating R1 and R2."""
        if candidate_methods is None or len(candidate_methods) == 0:
            raise ValueError(
                "At least one candidate search method must be provided to BenchmarkOrchestrator"
            )

        if baseline_method is None:
            baseline_method = BM25SearchMethod()

        baseline_name = baseline_method.name
        candidate_names = [m.name for m in candidate_methods]
        if baseline_name in candidate_names:
            raise ValueError("The baseline method cannot also be a finalist candidate")
        if len(set(candidate_names)) != len(candidate_names):
            raise ValueError("Candidate search method names must be unique")
        if split_name not in {"tuning", "measurement"}:
            raise ValueError(f"Unsupported benchmark split: {split_name}")
        if split_name == "measurement":
            if not finalist:
                raise ValueError(
                    "Finalist must be provided for measurement split, read from tuning output"
                )
            if finalist == baseline_name:
                raise ValueError(f"Finalist cannot be the baseline method ({baseline_name})")
            if finalist not in candidate_names:
                raise ValueError(f"Finalist '{finalist}' is not among provided candidate methods")

        if active_item_ids is not None:
            eval_items = [it for it in items if str(it.get("item_id")) in active_item_ids]
        else:
            eval_items = list(items)

        if not eval_items:
            raise ValueError(f"No items available to evaluate for split: {split_name}")

        # Validate survey_date and chosen_prices upfront before running retrieval/measurement
        parsed_survey_dates: dict[str, date] = {}
        missing_price_count = 0
        for item in eval_items:
            item_id = str(item.get("item_id"))
            s_date = item.get("survey_date")
            if isinstance(s_date, str):
                from datetime import datetime

                s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
            elif s_date is None:
                raise ValueError(f"Item {item_id} is missing survey_date")
            parsed_survey_dates[item_id] = s_date

            raw_prices = item.get("chosen_prices") or []
            if not [p for p in raw_prices if p is not None and float(p) > 0]:
                missing_price_count += 1

        if missing_price_count > 0:
            raise ValueError(
                f"{missing_price_count} item(s) have no chosen price for the R2 anchor"
            )

        all_methods = [baseline_method] + list(candidate_methods)
        all_method_names = [m.name for m in all_methods]

        # Build per-item candidate corpus C(q) first
        c_q_by_item: dict[str, list[Any]] = {}
        whole_c_q_by_item: dict[str, list[PriceCandidateSim]] = {}

        for item in eval_items:
            item_id = str(item.get("item_id"))
            s_date = parsed_survey_dates[item_id]

            source_corpus = corpus
            if hasattr(corpus, "model") and corpus.model.__name__ == "PublicItem":
                source_corpus = (
                    corpus.filter(
                        published_on__gte=s_date - timedelta(days=366),
                        published_on__lte=s_date,
                        modality__in=ALLOWED_MODALITIES,
                    )
                    .only(
                        "pk",
                        "description",
                        "unit",
                        "unit_normalized",
                        "published_on",
                        "modality",
                        "state",
                        "awarded_unit_price",
                        "estimated_unit_price",
                        "secret_budget",
                    )
                    .iterator()
                )
            c_q_corpus = list(
                filter_candidate_corpus(
                    source_corpus,
                    survey_date=s_date,
                    allowed_modalities=ALLOWED_MODALITIES,
                )
            )
            c_q_by_item[item_id] = c_q_corpus

            # Price-only baseline ranks whole C(q)
            whole_cq_sim = []
            for doc in c_q_corpus:
                d_id = getattr(
                    doc,
                    "id",
                    getattr(doc, "pk", doc.get("id") if isinstance(doc, dict) else None),
                )
                p_val = doc.get("price") if isinstance(doc, dict) else getattr(doc, "price", None)
                if p_val is None:
                    p_val = resolve_candidate_price(doc)
                p_dec = Decimal(str(p_val)) if p_val is not None else Decimal("0")
                d_unit = _normalized_candidate_unit(doc)
                whole_cq_sim.append(
                    PriceCandidateSim(
                        id=d_id,
                        price=p_dec,
                        similarity=0.0,
                        unit=d_unit,
                    )
                )
            whole_c_q_by_item[item_id] = whole_cq_sim

        # N4: Verify vector index coverage of C(q) IDs before measuring
        index_coverage: dict[str, dict[str, Any]] = {}
        is_queryset_corpus = hasattr(corpus, "model") and corpus.model.__name__ == "PublicItem"
        has_public_items = is_queryset_corpus
        if not has_public_items:
            all_docs = [doc for c_q in c_q_by_item.values() for doc in c_q]
            if all_docs:
                from ingestion.models import PublicItem

                has_public_items = all(isinstance(doc, PublicItem) for doc in all_docs)

        if has_public_items:
            all_c_q_ids = sorted(
                {
                    getattr(doc, "pk", getattr(doc, "id", None))
                    for c_q in c_q_by_item.values()
                    for doc in c_q
                    if getattr(doc, "pk", getattr(doc, "id", None)) is not None
                }
            )
            for method in all_methods:
                model = getattr(method, "model", None)
                if model is not None:
                    coverage = check_collection_coverage(
                        model,
                        all_c_q_ids,
                        client=getattr(method, "client", None),
                    )
                    if coverage["missing_count"] > 0:
                        raise ValueError(
                            f"Incomplete semantic index coverage for '{method.name}' in "
                            f"collection '{coverage['collection']}': "
                            f"{coverage['present_count']}/{coverage['expected_count']} C(q) IDs "
                            f"present ({coverage['missing_count']} missing)"
                        )
                    index_coverage[method.name] = coverage
        else:
            all_c_q_ids_mem = {
                getattr(
                    doc,
                    "id",
                    getattr(doc, "pk", doc.get("id") if isinstance(doc, dict) else None),
                )
                for c_q in c_q_by_item.values()
                for doc in c_q
            }
            for method in all_methods:
                if getattr(method, "model", None) is not None:
                    index_coverage[method.name] = {
                        "collection": "in_memory",
                        "expected_count": len(all_c_q_ids_mem),
                        "present_count": len(all_c_q_ids_mem),
                        "missing_count": 0,
                        "coverage_ratio": 1.0,
                    }

        # Full rankings (preserving exact scores for tie groups) and top-N IDs by method
        full_ranked_by_method: dict[str, dict[str, list[tuple[Any, float]]]] = {
            m: {} for m in all_method_names
        }
        ranked_ids_by_method: dict[str, dict[str, list[Any]]] = {m: {} for m in all_method_names}
        full_ranked_groups_by_method: dict[str, dict[str, list[tuple[float, list[Any]]]]] | None = (
            {m: {} for m in all_method_names} if include_full_rankings else None
        )

        for item in eval_items:
            item_id = str(item.get("item_id"))
            item_desc = str(item.get("description", ""))
            c_q_corpus = c_q_by_item[item_id]

            for method in all_methods:
                ranked_pairs = method.rank(query=item_desc, candidates=c_q_corpus)
                full_pairs = sorted(
                    ((doc, float(score)) for doc, score in ranked_pairs),
                    key=lambda pair: pair[1],
                    reverse=True,
                )
                full_ranked_by_method[method.name][item_id] = full_pairs
                top_pairs = full_pairs[:effective_top_n]
                ranked_ids_by_method[method.name][item_id] = [
                    _extract_doc_id(doc) for doc, _score in top_pairs
                ]
                if full_ranked_groups_by_method is not None:
                    full_ranked_groups_by_method[method.name][item_id] = group_tied_scored_ids(
                        full_pairs
                    )

        # Compute expected descriptive metrics & tie sensitivity per method over FULL ranked lists
        method_item_metrics: dict[str, dict[str, list[float]]] = {
            m: {
                "recall_at_1": [],
                "recall_at_5": [],
                "recall_at_10": [],
                "recall_at_20": [],
                "mrr_at_20": [],
                "success_at_10": [],
            }
            for m in all_method_names
        }
        method_tie_counts: dict[str, dict[str, int]] = {
            m: {"recall_at_10": 0, "mrr_at_20": 0, "r2_pool": 0} for m in all_method_names
        }

        for item in eval_items:
            item_id = str(item.get("item_id"))
            gt_ids = set(item.get("ground_truth", set()))
            for m in all_method_names:
                full_pairs = full_ranked_by_method[m][item_id]
                method_item_metrics[m]["recall_at_1"].append(
                    compute_expected_recall_at_k(full_pairs, gt_ids, k=1)
                )
                method_item_metrics[m]["recall_at_5"].append(
                    compute_expected_recall_at_k(full_pairs, gt_ids, k=5)
                )
                method_item_metrics[m]["recall_at_10"].append(
                    compute_expected_recall_at_k(full_pairs, gt_ids, k=10)
                )
                method_item_metrics[m]["recall_at_20"].append(
                    compute_expected_recall_at_k(full_pairs, gt_ids, k=20)
                )
                method_item_metrics[m]["mrr_at_20"].append(
                    compute_expected_mrr_at_k(full_pairs, gt_ids, k=20)
                )
                method_item_metrics[m]["success_at_10"].append(
                    compute_expected_success_at_k(full_pairs, gt_ids, k=10)
                )
                sens = compute_tie_sensitivity(full_pairs, gt_ids, top_n=effective_top_n)
                for key in ("recall_at_10", "mrr_at_20", "r2_pool"):
                    if sens[key]:
                        method_tie_counts[m][key] += 1

        method_summary_metrics: dict[str, dict[str, float]] = {}
        method_tie_sensitivity: dict[str, dict[str, float]] = {}
        for m in all_method_names:
            method_summary_metrics[m] = {
                metric: sum(scores) / len(scores) if scores else 0.0
                for metric, scores in method_item_metrics[m].items()
            }
            method_tie_sensitivity[m] = {
                key: count / len(eval_items) for key, count in method_tie_counts[m].items()
            }

        # Finalist selection / pinning
        if split_name == "tuning":
            candidate_metrics = {m: method_summary_metrics[m] for m in candidate_names}
            active_finalist = select_finalist(candidate_metrics, baseline_name=baseline_name)
        else:
            active_finalist = finalist

        # R1 Confirmatory Contrast (Finalist vs Baseline)
        fin_r10 = method_item_metrics[active_finalist]["recall_at_10"]
        bm_r10 = method_item_metrics[baseline_name]["recall_at_10"]
        diff_mean, ci_95_l, ci_95_u = bootstrap_paired_difference(
            fin_r10, bm_r10, alpha=0.05, n_resamples=self.n_bootstrap_resamples, seed=self.seed
        )
        _, ci_90_l, ci_90_u = bootstrap_paired_difference(
            fin_r10, bm_r10, alpha=0.10, n_resamples=self.n_bootstrap_resamples, seed=self.seed
        )
        p_val = permutation_test_paired(
            fin_r10, bm_r10, n_resamples=self.n_bootstrap_resamples, seed=self.seed
        )
        r1_acceptance = evaluate_r1_acceptance(diff_mean, ci_95_l, ci_95_u, ci_90_l, ci_90_u)
        r1_acceptance["p_value"] = p_val

        # R2 Simulation across sigmas using active finalist's full ranking
        sigmas = [0.0, 0.1, 0.25, 0.5, 1.0]
        item_system_r10: dict[float, list[float]] = {s: [] for s in sigmas}
        item_po_r10: dict[float, list[float]] = {s: [] for s in sigmas}
        easy_items_count = 0
        hard_indices: list[int] = []

        active_full_rankings = full_ranked_by_method.get(active_finalist, {})

        for idx, item in enumerate(eval_items):
            item_id = str(item.get("item_id"))
            chosen_prices = [p for p in item["chosen_prices"] if float(p) > 0]
            gt_ids = set(item.get("ground_truth", set()))
            full_pairs = active_full_rankings.get(item_id, [])
            whole_cq = whole_c_q_by_item.get(item_id, [])
            unit = normalize_unit(item.get("unit", "UNIDADE"))

            anchors_by_sigma = generate_anchor_prices(
                chosen_prices,
                sigmas=sigmas,
                n_draws=self.n_noise_draws,
                seed=self.seed,
                item_id=item_id,
            )

            # Classify easy/hard using exact geometric mean anchor (sigma = 0) over whole C(q)
            geo_anchor = math.exp(
                sum(math.log(float(p)) for p in chosen_prices) / len(chosen_prices)
            )
            is_easy = classify_easy_hard_items(
                whole_cq, anchor=geo_anchor, ground_truth_ids=gt_ids, k=10
            )
            if is_easy:
                easy_items_count += 1
            else:
                hard_indices.append(idx)

            # Group full finalist pairs once per item for pre-cut tie shuffling across draws
            grouped_finalist_docs: list[tuple[float, list[Any]]] = []
            if full_pairs:
                g_score = full_pairs[0][1]
                g_docs = [full_pairs[0][0]]
                for doc, score in full_pairs[1:]:
                    if score == g_score:
                        g_docs.append(doc)
                    else:
                        grouped_finalist_docs.append((g_score, g_docs))
                        g_score = score
                        g_docs = [doc]
                grouped_finalist_docs.append((g_score, g_docs))

            # Precompute per-draw tie-shuffled top-N finalist candidates with random rank IDs
            # (replacing persistent DB IDs inside RF23), and per-draw random rank IDs for whole C(q)
            # in price-only ranking. Seeds never depend on labels.
            tie_rng = random.Random(derive_item_seed(self.seed, f"tie:{item_id}"))
            rf23_candidates_by_draw: list[list[PriceCandidateSim]] = []
            sys_rank_to_real_by_draw: list[dict[int, Any]] = []
            po_candidates_by_draw: list[list[PriceCandidateSim]] = []
            po_rank_to_real_by_draw: list[dict[int, Any]] = []

            for _draw_idx in range(self.n_noise_draws):
                selected_top_pairs: list[tuple[Any, float]] = []
                for g_score, g_docs in grouped_finalist_docs:
                    if len(selected_top_pairs) >= effective_top_n:
                        break
                    needed = effective_top_n - len(selected_top_pairs)
                    if len(g_docs) <= needed:
                        picked = list(g_docs)
                        tie_rng.shuffle(picked)
                    else:
                        picked = tie_rng.sample(g_docs, needed)
                    for doc in picked:
                        selected_top_pairs.append((doc, g_score))

                sys_ranks = list(range(len(selected_top_pairs)))
                tie_rng.shuffle(sys_ranks)
                sys_draw_candidates: list[PriceCandidateSim] = []
                sys_id_map: dict[int, Any] = {}
                for rank_pos, (doc, score) in zip(sys_ranks, selected_top_pairs, strict=True):
                    d_id = _extract_doc_id(doc)
                    p_val = (
                        doc.get("price") if isinstance(doc, dict) else getattr(doc, "price", None)
                    )
                    if p_val is None:
                        p_val = resolve_candidate_price(doc)
                    p_dec = Decimal(str(p_val)) if p_val is not None else Decimal("0")
                    d_unit = _normalized_candidate_unit(doc)
                    sys_id_map[rank_pos] = d_id
                    sys_draw_candidates.append(
                        PriceCandidateSim(
                            id=rank_pos,
                            price=p_dec,
                            similarity=score,
                            unit=d_unit,
                        )
                    )
                rf23_candidates_by_draw.append(sys_draw_candidates)
                sys_rank_to_real_by_draw.append(sys_id_map)

                po_ranks = list(range(len(whole_cq)))
                tie_rng.shuffle(po_ranks)
                po_draw_candidates: list[PriceCandidateSim] = []
                po_id_map: dict[int, Any] = {}
                for rank_pos, candidate in zip(po_ranks, whole_cq, strict=True):
                    po_id_map[rank_pos] = candidate.id
                    po_draw_candidates.append(
                        PriceCandidateSim(
                            id=rank_pos,
                            price=candidate.price,
                            similarity=0.0,
                            unit=candidate.unit,
                        )
                    )
                po_candidates_by_draw.append(po_draw_candidates)
                po_rank_to_real_by_draw.append(po_id_map)

            for s in sigmas:
                draw_anchors = anchors_by_sigma[s]
                sys_draw_recalls: list[float] = []
                po_draw_recalls: list[float] = []
                for draw_idx, a in enumerate(draw_anchors):
                    # System with RF23 reordering the tie-shuffled top N candidates
                    ranked_sys = self.rank_with_rf23(
                        rf23_candidates_by_draw[draw_idx],
                        anchor=Decimal(str(round(a, 4))),
                        unit=unit,
                    )
                    sys_real_ids = [sys_rank_to_real_by_draw[draw_idx][c.id] for c in ranked_sys]
                    sys_draw_recalls.append(compute_recall_at_k(sys_real_ids, gt_ids, k=10))
                    # Price-only baseline ranking the WHOLE C(q) with equal-price ties reshuffled
                    ranked_po = rank_by_price_only(po_candidates_by_draw[draw_idx], anchor=a)
                    po_real_ids = [po_rank_to_real_by_draw[draw_idx][c.id] for c in ranked_po]
                    po_draw_recalls.append(compute_recall_at_k(po_real_ids, gt_ids, k=10))

                item_system_r10[s].append(sum(sys_draw_recalls) / len(sys_draw_recalls))
                item_po_r10[s].append(sum(po_draw_recalls) / len(po_draw_recalls))

        g_sigma: dict[str, float] = {}
        for s in sigmas:
            mean_sys = sum(item_system_r10[s]) / len(eval_items)
            mean_po = sum(item_po_r10[s]) / len(eval_items)
            g_sigma[str(s)] = round(mean_sys - mean_po, 4)

        # Conditions for R2 acceptance
        sigma_025_ci = bootstrap_paired_difference(
            item_system_r10[0.25],
            item_po_r10[0.25],
            alpha=0.05,
            n_resamples=self.n_bootstrap_resamples,
            seed=self.seed,
        )

        if hard_indices:
            hard_fin = [fin_r10[i] for i in hard_indices]
            hard_bm = [bm_r10[i] for i in hard_indices]
            hard_gain_ci = bootstrap_paired_difference(
                hard_fin,
                hard_bm,
                alpha=0.05,
                n_resamples=self.n_bootstrap_resamples,
                seed=self.seed,
            )
        else:
            hard_gain_ci = (0.0, 0.0, 0.0)

        r2_accepted = evaluate_r2_acceptance(r1_acceptance, sigma_025_ci, hard_gain_ci)
        r2_acceptance = {
            "accepted": r2_accepted,
            "sigma_025_ci": list(sigma_025_ci),
            "hard_gain_ci": list(hard_gain_ci),
        }

        price_only_baseline = sum(item_po_r10[0.25]) / len(eval_items)

        result: dict[str, Any] = {
            "split": split_name,
            "synthetic": synthetic,
            "items_count": len(eval_items),
            "top_n": effective_top_n,
            "n": effective_top_n,
            "finalist": active_finalist,
            "index_coverage": index_coverage,
            "tie_sensitivity": method_tie_sensitivity[active_finalist],
            "methods": {
                m: {
                    "metrics": method_summary_metrics[m],
                    "tie_sensitivity": method_tie_sensitivity[m],
                }
                for m in all_method_names
            },
            "constants": {
                "n_noise_draws": self.n_noise_draws,
                "n_bootstrap_resamples": self.n_bootstrap_resamples,
                "seed": self.seed,
                "r2_tie_break_seed": self.seed,
                "top_n": effective_top_n,
                "n": effective_top_n,
            },
            "r1_acceptance": r1_acceptance,
            "r2_acceptance": r2_acceptance,
            "r2": {
                "g_sigma": g_sigma,
                "price_only_baseline": price_only_baseline,
                "easy_items_count": easy_items_count,
            },
            "ranked_ids_by_method": ranked_ids_by_method,
        }
        if full_ranked_groups_by_method is not None:
            result["full_ranked_groups_by_method"] = full_ranked_groups_by_method
        return result
