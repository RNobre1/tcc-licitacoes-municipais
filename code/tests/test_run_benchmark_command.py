"""Tests for run_benchmark management command and benchmark orchestrator."""

import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    PriceCandidateSim,
    select_finalist,
)


def test_select_finalist_rule():
    # Finalist rule: highest Recall@10 on tuning_split, ties broken by MRR@20
    metrics = {
        "model_a": {"recall_at_10": 0.60, "mrr_at_20": 0.30},
        "model_b": {"recall_at_10": 0.75, "mrr_at_20": 0.20},
        "model_c": {"recall_at_10": 0.75, "mrr_at_20": 0.40},
    }
    # model_c wins tiebreak over model_b on MRR@20
    assert select_finalist(metrics) == "model_c"


def test_run_benchmark_refuses_measurement_without_thresholds_note():
    # N10: Must raise CommandError instead of ValueError
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()

        with pytest.raises(CommandError, match="Thresholds note must be provided"):
            call_command(
                "run_benchmark",
                split="measurement",
                eval_dir=str(eval_dir),
            )


def test_run_benchmark_synthetic_full_orchestration():
    with TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir) / "output"
        out_dir.mkdir()
        out_file = out_dir / "benchmark_run_results.json"

        call_command(
            "run_benchmark",
            split="tuning",
            output=str(out_file),
            synthetic=True,
        )

        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))

        # Verify output JSON schema contains all required elements (B2)
        assert data["split"] == "tuning"
        assert data["synthetic"] is True
        assert "finalist" in data
        assert "methods" in data
        assert "bm25" in data["methods"]
        assert "semantic" in data["methods"]

        # Method metrics include all descriptive metrics
        bm25_metrics = data["methods"]["bm25"]["metrics"]
        for metric in ["recall_at_1", "recall_at_5", "recall_at_10", "recall_at_20", "mrr_at_20", "success_at_10"]:
            assert metric in bm25_metrics

        # Constants recorded
        assert data["constants"]["n_noise_draws"] == 200
        assert data["constants"]["n_bootstrap_resamples"] == 10000
        assert "seed" in data["constants"]

        # R2 metrics and G(sigma)
        assert "r2" in data
        assert "g_sigma" in data["r2"]
        for s in ["0.0", "0.1", "0.25", "0.5", "1.0"]:
            assert s in data["r2"]["g_sigma"]
        assert "price_only_baseline" in data["r2"]
        assert "easy_items_count" in data["r2"]

        # R1 and R2 acceptance results
        assert "r1_acceptance" in data
        assert "r2_acceptance" in data
        assert "ci_95" in data["r1_acceptance"]
        assert "ci_90" in data["r1_acceptance"]
        assert "p_value" in data["r1_acceptance"]


def test_benchmark_orchestrator_r2_uses_rf23_rank_candidates():
    # B2: R2 must go through pricing.ranking.rank_candidates
    candidates = [
        PriceCandidateSim(id=1, price=Decimal("10.0"), similarity=0.85, unit="UNIDADE"),
        PriceCandidateSim(id=2, price=Decimal("50.0"), similarity=0.88, unit="UNIDADE"),
        PriceCandidateSim(id=3, price=Decimal("10.5"), similarity=0.70, unit="UNIDADE"),
    ]

    orch = BenchmarkOrchestrator()
    # Rank without anchor
    ranked_no_anchor = orch.rank_with_rf23(candidates, anchor=None, unit="UNIDADE")
    # In High band (>=0.80): id 2 (0.88), id 1 (0.85)
    assert [c.id for c in ranked_no_anchor[:2]] == [2, 1]

    # Rank with anchor=10.0: id 1 (dist 0) precedes id 2 (dist log(5)) within High band
    ranked_with_anchor = orch.rank_with_rf23(candidates, anchor=Decimal("10.0"), unit="UNIDADE")
    assert [c.id for c in ranked_with_anchor[:2]] == [1, 2]
