"""Tests for run_benchmark management command."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command


def test_run_benchmark_refuses_measurement_without_thresholds_note():
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()

        with pytest.raises(ValueError, match="Thresholds note must be provided"):
            call_command(
                "run_benchmark",
                split="measurement",
                eval_dir=str(eval_dir),
            )


def test_run_benchmark_tuning_split_on_synthetic_data():
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()

        call_command(
            "run_benchmark",
            split="tuning",
            eval_dir=str(eval_dir),
            synthetic=True,
        )

        out_results = eval_dir / "benchmark_tuning_results.json"
        assert out_results.exists()
