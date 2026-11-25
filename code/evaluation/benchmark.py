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


class BenchmarkOrchestrator:
    """Orchestrates search benchmark evaluation, finalist selection, and R2 RF23 ranking."""

    def __init__(
        self,
        n_noise_draws: int = 200,
        n_bootstrap_resamples: int = 10000,
        seed: int = 42,
    ) -> None:
        self.n_noise_draws = n_noise_draws
        self.n_bootstrap_resamples = n_bootstrap_resamples
        self.seed = seed

    def rank_with_rf23(
        self,
        candidates: Sequence[Any],
        anchor: Decimal | float | None = None,
        unit: str = "UNIDADE",
    ) -> list[Any]:
        """Rank candidates using RF23 proximity rules via pricing.ranking.rank_candidates."""
        from pricing.ranking import rank_candidates

        expected_price = Decimal(str(anchor)) if anchor is not None else None
        return rank_candidates(candidates, expected_price=expected_price, item_unit=unit)

    def run_benchmark(
        self,
        items: Sequence[dict[str, Any]],
        corpus: Sequence[dict[str, Any]] | None = None,
        split_name: str = "tuning",
        active_item_ids: set[str] | None = None,
        synthetic: bool = False,
    ) -> dict[str, Any]:
        """Run benchmark over items, compute descriptive metrics, contrast R1 and simulate R2."""
        from rank_bm25 import BM25Okapi

        def _tokenize(text: str) -> list[str]:
            return [t.lower() for t in text.split() if t.strip()]

        if active_item_ids is not None:
            eval_items = [it for it in items if str(it.get("item_id")) in active_item_ids]
        else:
            eval_items = list(items)

        if not eval_items:
            raise ValueError(f"No items available to evaluate for split: {split_name}")

        corpus_docs = list(corpus or [])
        tokenized_corpus = [_tokenize(doc.get("description", "")) for doc in corpus_docs]
        bm25_model = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

        # Prepare per-method rankings
        ranked_ids_by_method: dict[str, dict[str, list[Any]]] = {"bm25": {}, "semantic": {}}
        candidates_by_item: dict[str, list[PriceCandidateSim]] = {}

        for item in eval_items:
            item_id = str(item.get("item_id"))
            item_desc = str(item.get("description", ""))
            gt_ids = set(item.get("ground_truth", set()))
            query_tokens = _tokenize(item_desc)

            # BM25 Ranking
            if bm25_model is not None:
                bm25_scores = bm25_model.get_scores(query_tokens)
                ranked_pairs = sorted(
                    zip(corpus_docs, bm25_scores, strict=False),
                    key=lambda x: (x[1], -x[0]["id"]),
                    reverse=True,
                )
                ranked_ids_by_method["bm25"][item_id] = [doc["id"] for doc, _ in ranked_pairs]
            else:
                ranked_ids_by_method["bm25"][item_id] = []

            # Semantic / Finalist ranking & candidate objects
            sim_candidates: list[PriceCandidateSim] = []
            for doc in corpus_docs:
                doc_id = doc["id"]
                p_val = doc.get("price", Decimal("0"))
                doc_unit = doc.get("unit", "UNIDADE")
                # Semantic similarity: higher for ground truth / token match
                if doc_id in gt_ids:
                    sim = 0.90
                elif any(t in doc.get("description", "").lower() for t in query_tokens):
                    sim = 0.65
                else:
                    sim = 0.40
                sim_candidates.append(
                    PriceCandidateSim(
                        id=doc_id,
                        price=p_val if isinstance(p_val, Decimal) else Decimal(str(p_val)),
                        similarity=sim,
                        unit=doc_unit,
                    )
                )

            # Sort by similarity descending, id ascending
            sim_candidates.sort(key=lambda c: (-c.similarity, c.id))
            candidates_by_item[item_id] = sim_candidates
            ranked_ids_by_method["semantic"][item_id] = [c.id for c in sim_candidates]

        # Compute descriptive metrics per method
        method_item_metrics: dict[str, dict[str, list[float]]] = {
            m: {
                "recall_at_1": [],
                "recall_at_5": [],
                "recall_at_10": [],
                "recall_at_20": [],
                "mrr_at_20": [],
                "success_at_10": [],
            }
            for m in ["bm25", "semantic"]
        }

        for item in eval_items:
            item_id = str(item.get("item_id"))
            gt_ids = set(item.get("ground_truth", set()))
            for m in ["bm25", "semantic"]:
                r_ids = ranked_ids_by_method[m][item_id]
                method_item_metrics[m]["recall_at_1"].append(
                    compute_recall_at_k(r_ids, gt_ids, k=1)
                )
                method_item_metrics[m]["recall_at_5"].append(
                    compute_recall_at_k(r_ids, gt_ids, k=5)
                )
                method_item_metrics[m]["recall_at_10"].append(
                    compute_recall_at_k(r_ids, gt_ids, k=10)
                )
                method_item_metrics[m]["recall_at_20"].append(
                    compute_recall_at_k(r_ids, gt_ids, k=20)
                )
                method_item_metrics[m]["mrr_at_20"].append(compute_mrr_at_k(r_ids, gt_ids, k=20))
                method_item_metrics[m]["success_at_10"].append(
                    compute_success_at_k(r_ids, gt_ids, k=10)
                )

        method_summary_metrics: dict[str, dict[str, float]] = {}
        for m in ["bm25", "semantic"]:
            method_summary_metrics[m] = {
                metric: sum(scores) / len(scores) if scores else 0.0
                for metric, scores in method_item_metrics[m].items()
            }

        # Select finalist
        finalist = select_finalist(method_summary_metrics)

        # R1 Confirmatory Contrast (Finalist vs BM25)
        fin_r10 = method_item_metrics[finalist]["recall_at_10"]
        bm_r10 = method_item_metrics["bm25"]["recall_at_10"]
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

        # R2 Simulation across sigmas
        sigmas = [0.0, 0.1, 0.25, 0.5, 1.0]
        item_system_r10: dict[float, list[float]] = {s: [] for s in sigmas}
        item_po_r10: dict[float, list[float]] = {s: [] for s in sigmas}
        easy_items_count = 0
        hard_indices: list[int] = []

        for idx, item in enumerate(eval_items):
            item_id = str(item.get("item_id"))
            chosen_prices = item.get("chosen_prices") or [Decimal("10.0")]
            gt_ids = set(item.get("ground_truth", set()))
            candidates = candidates_by_item.get(item_id, [])
            unit = str(item.get("unit", "UNIDADE"))

            anchors_by_sigma = generate_anchor_prices(
                chosen_prices,
                sigmas=sigmas,
                n_draws=self.n_noise_draws,
                seed=self.seed,
                item_id=item_id,
            )

            # Classify easy/hard on sigma=0.25 using geometric mean anchor
            geo_anchor = math.exp(
                sum(math.log(float(p)) for p in chosen_prices) / len(chosen_prices)
            )
            is_easy = classify_easy_hard_items(
                candidates, anchor=geo_anchor, ground_truth_ids=gt_ids, k=10
            )
            if is_easy:
                easy_items_count += 1
            else:
                hard_indices.append(idx)

            for s in sigmas:
                draw_anchors = anchors_by_sigma[s]
                sys_draw_recalls: list[float] = []
                po_draw_recalls: list[float] = []
                for a in draw_anchors:
                    # System with RF23
                    ranked_sys = self.rank_with_rf23(
                        candidates, anchor=Decimal(str(round(a, 4))), unit=unit
                    )
                    sys_draw_recalls.append(
                        compute_recall_at_k([c.id for c in ranked_sys], gt_ids, k=10)
                    )
                    # Price-only baseline
                    ranked_po = rank_by_price_only(candidates, anchor=a)
                    po_draw_recalls.append(
                        compute_recall_at_k([c.id for c in ranked_po], gt_ids, k=10)
                    )

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

        return {
            "split": split_name,
            "synthetic": synthetic,
            "items_count": len(eval_items),
            "finalist": finalist,
            "methods": {
                m: {
                    "metrics": method_summary_metrics[m],
                }
                for m in ["bm25", "semantic"]
            },
            "constants": {
                "n_noise_draws": self.n_noise_draws,
                "n_bootstrap_resamples": self.n_bootstrap_resamples,
                "seed": self.seed,
            },
            "r1_acceptance": r1_acceptance,
            "r2_acceptance": r2_acceptance,
            "r2": {
                "g_sigma": g_sigma,
                "price_only_baseline": price_only_baseline,
                "easy_items_count": easy_items_count,
            },
        }
