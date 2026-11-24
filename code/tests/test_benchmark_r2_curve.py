"""Tests for R2 curve simulation with log-normal noise and price-only baseline."""

import math
from decimal import Decimal

import pytest

from evaluation.benchmark import (
    PriceCandidateSim,
    classify_easy_hard_items,
    generate_anchor_prices,
    rank_by_price_only,
)


def test_generate_anchor_prices():
    # chosen prices: 10.0, 20.0 -> mean ln is ~2.649
    chosen = [Decimal("10.0"), Decimal("20.0")]
    sigmas = [0.0, 0.1, 0.25, 0.5, 1.0]

    anchors = generate_anchor_prices(chosen, sigmas, n_draws=10, seed=42)

    oracle_val = (math.log(10.0) + math.log(20.0)) / 2.0
    expected_oracle = math.exp(oracle_val)

    assert 0.0 in anchors
    assert len(anchors[0.0]) == 10
    for val in anchors[0.0]:
        assert pytest.approx(val, abs=1e-4) == expected_oracle

    assert 0.1 in anchors
    assert len(anchors[0.1]) == 10


def test_rank_by_price_only():
    candidates = [
        PriceCandidateSim(id=1, price=Decimal("10.0"), similarity=0.9),
        PriceCandidateSim(id=2, price=Decimal("15.0"), similarity=0.5),
        PriceCandidateSim(id=3, price=Decimal("20.0"), similarity=0.8),
    ]
    ranked = rank_by_price_only(candidates, anchor=Decimal("14.0"))
    assert [c.id for c in ranked] == [2, 1, 3]


def test_classify_easy_hard_items():
    candidates_1 = [
        PriceCandidateSim(id=i, price=Decimal(str(i)), similarity=0.5) for i in range(1, 20)
    ]
    ground_truth_1 = {1, 2}
    is_easy_1 = classify_easy_hard_items(
        candidates_1,
        anchor=Decimal("1.5"),
        ground_truth_ids=ground_truth_1,
        k=10,
    )
    assert is_easy_1 is True

    candidates_2 = [
        PriceCandidateSim(id=i, price=Decimal(str(i)), similarity=0.5) for i in range(1, 30)
    ]
    ground_truth_2 = {25}
    is_easy_2 = classify_easy_hard_items(
        candidates_2,
        anchor=Decimal("1.0"),
        ground_truth_ids=ground_truth_2,
        k=10,
    )
    assert is_easy_2 is False


def test_generate_anchor_prices_shared_z_mutant():
    # Kill mutant: new noise draw per level instead of shared Z
    chosen = [Decimal("10.0"), Decimal("20.0")]
    mean_ln = (math.log(10.0) + math.log(20.0)) / 2.0
    sigmas = [0.10, 0.25, 0.50, 1.00]

    anchors = generate_anchor_prices(chosen, sigmas, n_draws=20, seed=42)

    # For each draw index, (ln(anchor) - mean_ln) / sigma must be identical across sigmas
    for idx in range(20):
        z_values = [(math.log(anchors[s][idx]) - mean_ln) / s for s in sigmas]
        first_z = z_values[0]
        for z in z_values[1:]:
            assert pytest.approx(z, rel=1e-5) == first_z


def test_generate_anchor_prices_seed_per_item_n9():
    # N9: seed varies per item derived from base seed and item id
    chosen = [Decimal("10.0"), Decimal("20.0")]
    sigmas = [0.25]

    a1 = generate_anchor_prices(chosen, sigmas, n_draws=10, seed=42, item_id="item_1")
    a2 = generate_anchor_prices(chosen, sigmas, n_draws=10, seed=42, item_id="item_1")
    a3 = generate_anchor_prices(chosen, sigmas, n_draws=10, seed=42, item_id="item_2")

    assert a1[0.25] == a2[0.25]
    assert a1[0.25] != a3[0.25]


def test_generate_anchor_prices_std_mutant():
    # Kill mutant: sigma * 2 or standard deviation 2.0 instead of 1.0
    chosen = [Decimal("10.0")]
    mean_ln = math.log(10.0)
    sigmas = [1.0]

    anchors = generate_anchor_prices(chosen, sigmas, n_draws=5000, seed=42)
    z_samples = [math.log(a) - mean_ln for a in anchors[1.0]]
    variance = sum(z**2 for z in z_samples) / len(z_samples)
    std_dev = math.sqrt(variance)
    # std_dev of standard normal is 1.0, mutant with std 2.0 fails this
    assert pytest.approx(std_dev, abs=0.1) == 1.0
