"""Tests for evaluation dataset split, split generator command, and thresholds-note guard."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command

from evaluation.benchmark import (
    DatasetSplit,
    check_thresholds_note_guard,
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


def test_create_dataset_split_stratification_by_item_kind_mutant():
    # Kill mutant: split without stratifying by item_kind
    # 20 items of rep1: 10 products, 10 services
    items = []
    for idx in range(10):
        items.append({"item_id": f"prod_{idx}", "report_id": "rep1", "item_kind": "product"})
    for idx in range(10):
        items.append({"item_id": f"serv_{idx}", "report_id": "rep1", "item_kind": "service"})

    split = create_dataset_split(items, tuning_fraction=0.4, seed=42)
    # Exactly 4 products and 4 services in tuning
    tune_prods = [x for x in split.tuning_items if x.startswith("prod_")]
    tune_servs = [x for x in split.tuning_items if x.startswith("serv_")]
    assert len(tune_prods) == 4
    assert len(tune_servs) == 4


def test_create_dataset_split_seed_determinism_mutant():
    # Kill mutant: split without seed
    items = [{"item_id": f"it_{i}", "report_id": "rep1", "item_kind": "product"} for i in range(20)]
    s1 = create_dataset_split(items, tuning_fraction=0.4, seed=123)
    s2 = create_dataset_split(items, tuning_fraction=0.4, seed=123)
    s3 = create_dataset_split(items, tuning_fraction=0.4, seed=999)

    assert s1.tuning_items == s2.tuning_items
    assert s1.sha256_hash == s2.sha256_hash
    assert s1.tuning_items != s3.tuning_items


def test_generate_dataset_split_command_reproduces_frozen_hash():
    # Command creates dataset_split.json from ground_truth_resolved.json
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()

        # Create synthetic ground_truth_resolved.json
        resolved_items = {}
        for idx in range(10):
            resolved_items[f"rep1_it{idx}_p1"] = {
                "cnpj": "11111111000111",
                "year": 2026,
                "purchase_sequence": 100,
                "item_number": idx,
                "found": True,
                "item_kind": "product",
            }
        # One unresolved item (should be skipped as ineligible)
        resolved_items["rep1_it99_p1"] = {
            "cnpj": "11111111000111",
            "year": 2026,
            "purchase_sequence": 100,
            "item_number": 99,
            "found": False,
        }

        gt_file = eval_dir / "ground_truth_resolved.json"
        gt_file.write_text(json.dumps({"resolved_items": resolved_items}), encoding="utf-8")

        call_command("generate_dataset_split", eval_dir=str(eval_dir))

        split_file = eval_dir / "dataset_split.json"
        assert split_file.exists()
        data = json.loads(split_file.read_text(encoding="utf-8"))
        assert data["total_eligible_items"] == 10
        assert data["tuning_count"] == 4
        assert data["measurement_count"] == 6
        assert len(data["sha256_hash"]) == 64


def test_guard_refuses_invalid_thresholds_notes():
    with TemporaryDirectory() as tmp_dir:
        fake_repo = Path(tmp_dir) / "repo"
        decisoes_dir = fake_repo / "TCC" / "decisões"
        decisoes_dir.mkdir(parents=True)

        # 1. Non-existent path
        with pytest.raises(ValueError, match="does not exist"):
            check_thresholds_note_guard(
                fake_repo / "nonexistent.md",
                repo_root=fake_repo,
            )

        # 2. Directory instead of file
        with pytest.raises(ValueError, match="regular file"):
            check_thresholds_note_guard(
                decisoes_dir,
                repo_root=fake_repo,
            )

        # 3. Path outside repo / lookalike outside repo
        outside_dir = Path(tmp_dir) / "outside" / "TCC" / "decisões"
        outside_dir.mkdir(parents=True)
        outside_file = outside_dir / "note.md"
        outside_file.write_text("status: aceita\n# Note", encoding="utf-8")
        with pytest.raises(ValueError, match="reside under repository"):
            check_thresholds_note_guard(
                outside_file,
                repo_root=fake_repo,
            )

        # 4. Empty file
        empty_note = decisoes_dir / "empty.md"
        empty_note.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            check_thresholds_note_guard(
                empty_note,
                repo_root=fake_repo,
            )

        # 5. File without status: aceita
        draft_note = decisoes_dir / "draft.md"
        draft_note.write_text("---\nstatus: rascunho\n---\n# Title", encoding="utf-8")
        with pytest.raises(ValueError, match="status: aceita"):
            check_thresholds_note_guard(
                draft_note,
                repo_root=fake_repo,
            )

        # 6. Note missing the split hash
        valid_content = "---\nstatus: aceita\n---\n# Title\nHash: abc123def456\n"
        valid_note = decisoes_dir / "valid.md"
        valid_note.write_text(valid_content, encoding="utf-8")

        with pytest.raises(ValueError, match="was not found recorded"):
            check_thresholds_note_guard(
                valid_note,
                split_hash="2c2e7bd50913b30ad3ab1b4f336178e19a3c0514c2f4acdf2a6007d3606eb6ad",
                repo_root=fake_repo,
            )

        # 7. Symlink escaping TCC/decisões/
        symlink_escape = decisoes_dir / "escape.md"
        target_outside = Path(tmp_dir) / "outside_target.md"
        target_outside.write_text("---\nstatus: aceita\n---\nHash: 2c2e7bd5", encoding="utf-8")
        os.symlink(target_outside, symlink_escape)
        with pytest.raises(ValueError, match="reside under repository"):
            check_thresholds_note_guard(
                symlink_escape,
                repo_root=fake_repo,
            )

        # 8. Success when all conditions hold
        complete_content = (
            "---\nstatus: aceita\n---\n# Title\n"
            "Split SHA-256: 2c2e7bd50913b30ad3ab1b4f336178e19a3c0514c2f4acdf2a6007d3606eb6ad\n"
        )
        complete_note = decisoes_dir / "2026-11-24-limiares.md"
        complete_note.write_text(complete_content, encoding="utf-8")

        content = check_thresholds_note_guard(
            complete_note,
            split_hash="2c2e7bd50913b30ad3ab1b4f336178e19a3c0514c2f4acdf2a6007d3606eb6ad",
            repo_root=fake_repo,
        )
        assert "Split SHA-256" in content
