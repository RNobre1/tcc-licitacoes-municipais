"""Tests for benchmark acceptance rules (R1, R2), success@10 metric, and C(q) filter."""

from datetime import date
from decimal import Decimal

from evaluation.benchmark import (
    PublicItemSim,
    compute_success_at_k,
    evaluate_r1_acceptance,
    evaluate_r2_acceptance,
    filter_candidate_corpus,
)


def test_compute_success_at_k():
    gt = {10, 20}
    # Hits at least one in top 1 -> 1.0
    assert compute_success_at_k([10, 30], gt, k=1) == 1.0
    # No hits in top 1 -> 0.0
    assert compute_success_at_k([30, 10], gt, k=1) == 0.0
    # Hits at rank 2 in top 2 -> 1.0
    assert compute_success_at_k([30, 10], gt, k=2) == 1.0
    # Empty ground truth -> 0.0
    assert compute_success_at_k([10, 20], set(), k=5) == 0.0


def test_evaluate_r1_acceptance():
    # Accept: lower bound of 95% CI > 0.05
    res_accept = evaluate_r1_acceptance(
        diff_mean=0.08,
        ci_95_lower=0.055,
        ci_95_upper=0.105,
        ci_90_lower=0.06,
        ci_90_upper=0.10,
    )
    assert res_accept["outcome"] == "accepted"

    # Tie: 90% CI lies completely within (-0.08, 0.08) and lower bound not > 0.05
    res_tie = evaluate_r1_acceptance(
        diff_mean=0.01,
        ci_95_lower=-0.02,
        ci_95_upper=0.04,
        ci_90_lower=-0.015,
        ci_90_upper=0.035,
    )
    assert res_tie["outcome"] == "tie"

    # Inconclusive: neither accepted nor tie
    res_inconclusive = evaluate_r1_acceptance(
        diff_mean=0.04,
        ci_95_lower=-0.01,
        ci_95_upper=0.09,
        ci_90_lower=0.00,
        ci_90_upper=0.085,
    )
    assert res_inconclusive["outcome"] == "inconclusive"


def test_evaluate_r2_acceptance():
    # R2 requires:
    # (a) R1 accepted
    # (b) at sigma=0.25, system beats price-only with lower 95% CI > 0
    # (c) finalist gain over BM25 on hard items with lower 95% CI > 0
    r1_result = {"outcome": "accepted"}
    sigma_025_ci = (0.05, 0.01, 0.09)  # mean, lower, upper
    hard_gain_ci = (0.04, 0.005, 0.075)

    assert evaluate_r2_acceptance(r1_result, sigma_025_ci, hard_gain_ci) is True

    # Fails if r1 not accepted
    assert evaluate_r2_acceptance({"outcome": "tie"}, sigma_025_ci, hard_gain_ci) is False

    # Fails if sigma 0.25 lower bound <= 0
    assert evaluate_r2_acceptance(r1_result, (0.02, -0.01, 0.05), hard_gain_ci) is False

    # Fails if hard gain lower bound <= 0
    assert evaluate_r2_acceptance(r1_result, sigma_025_ci, (0.02, -0.001, 0.04)) is False


def test_filter_candidate_corpus_cq():
    survey_date = date(2026, 7, 1)

    items = [
        PublicItemSim(
            id=1,
            published_on=date(2026, 6, 15),
            modality=6,
            state="PA",
            awarded_unit_price=Decimal("10.0"),
        ),
        PublicItemSim(
            id=2,
            published_on=date(2025, 6, 30),
            modality=8,
            state="SP",
            awarded_unit_price=None,
            estimated_unit_price=Decimal("12.0"),
        ),  # 1 day > 12 months before
        PublicItemSim(
            id=3,
            published_on=date(2025, 7, 1),
            modality=7,
            state="MG",
            awarded_unit_price=Decimal("15.0"),
        ),  # exactly 12 months before
        PublicItemSim(
            id=4,
            published_on=date(2026, 7, 2),
            modality=6,
            state="PA",
            awarded_unit_price=Decimal("20.0"),
        ),  # after survey date
        PublicItemSim(
            id=5,
            published_on=date(2026, 5, 10),
            modality=1,
            state="PA",
            awarded_unit_price=Decimal("5.0"),
        ),  # modality not in {6, 7, 8}
    ]

    filtered = filter_candidate_corpus(items, survey_date=survey_date)
    assert [it.id for it in filtered] == [1, 3]


def test_candidate_price_resolution():
    from evaluation.benchmark import resolve_candidate_price

    # Awarded price takes precedence
    item1 = PublicItemSim(
        id=1,
        published_on=date(2026, 1, 1),
        modality=6,
        awarded_unit_price=Decimal("10.0"),
        estimated_unit_price=Decimal("12.0"),
    )
    assert resolve_candidate_price(item1) == Decimal("10.0")

    # Estimated price when awarded is None
    item2 = PublicItemSim(
        id=2,
        published_on=date(2026, 1, 1),
        modality=6,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("12.0"),
    )
    assert resolve_candidate_price(item2) == Decimal("12.0")

    # Secret budget has no price
    item3 = PublicItemSim(
        id=3,
        published_on=date(2026, 1, 1),
        modality=6,
        awarded_unit_price=None,
        estimated_unit_price=Decimal("0.0"),
        secret_budget=True,
    )
    assert resolve_candidate_price(item3) is None

    # Zero price is never a price
    item4 = PublicItemSim(
        id=4,
        published_on=date(2026, 1, 1),
        modality=6,
        awarded_unit_price=Decimal("0.0"),
        estimated_unit_price=Decimal("0.0"),
    )
    assert resolve_candidate_price(item4) is None
