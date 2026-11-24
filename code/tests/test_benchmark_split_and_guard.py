"""Tests for evaluation dataset split and thresholds-note guard."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from evaluation.benchmark import (
    DatasetSplit,
    create_dataset_split,
    verify_split_hash,
)


def test_create_dataset_split_stratified_and_sha256():
    # Synthetic item list with (item_id, report_id, item_kind)
    items = []
    for rep in ["rep1", "rep2", "rep3"]:
        for kind in ["product", "service"]:
            for idx in range(10):
                items.append(
                    {
                        "item_id": f"{rep}_{kind}_{idx}",
                        "report_id": rep,
                        "item_kind": kind,
                    }
                )

    split = create_dataset_split(items, tuning_fraction=0.4, seed=42)

    assert isinstance(split, DatasetSplit)
    assert len(split.tuning_items) == 24  # 40% of 60
    assert len(split.measurement_items) == 36  # 60% of 60

    # Test deterministic hash
    assert len(split.sha256_hash) == 64
    assert verify_split_hash(split.tuning_items, split.measurement_items, split.sha256_hash) is True
    assert verify_split_hash(split.tuning_items, split.measurement_items, "wrong_hash") is False


def test_guard_refuses_measurement_without_valid_thresholds_note():
    from evaluation.benchmark import check_thresholds_note_guard

    with TemporaryDirectory() as tmp_dir:
        fake_note = Path(tmp_dir) / "2026-11-24-limiares.md"
        fake_note.write_text("# Limiares", encoding="utf-8")

        # Refuses non-existent path
        with pytest.raises(ValueError, match="does not exist"):
            check_thresholds_note_guard(Path("/nonexistent/file.md"))

        # Refuses path outside TCC/decisões/
        with pytest.raises(ValueError, match="must point to a file in TCC/decisões/"):
            check_thresholds_note_guard(fake_note)
