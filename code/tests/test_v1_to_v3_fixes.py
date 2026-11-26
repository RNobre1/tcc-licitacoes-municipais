"""Tests for V2 (ready-to-paste tuning SHA-256 line), V1 (Q-2 symlink resolve pinning and
P1-b multiple tuning SHA-256 lines rule), and V3 (per-item candidate object reuse across draws).
"""

import hashlib
import json
import os
from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

import evaluation.benchmark as benchmark_module
from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    PublicItemSim,
    check_thresholds_note_guard,
)
from evaluation.management.commands.run_benchmark import DecimalEncoder
from tests.test_p1_to_p4_pre_measurement import _setup_real_eval_fixture

# ---------------------------------------------------------------------------
# V2 — Tuning run prints ready-to-paste `resumo SHA-256 do ajuste `<hash>``
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_v2_real_tuning_prints_ready_to_paste_hash_line_and_measurement_accepts_it(
    monkeypatch, tmp_path, capsys
):
    _project_root, decision_copy, eval_dir, split = _setup_real_eval_fixture(monkeypatch, tmp_path)
    tuning_out = eval_dir / "benchmark_tuning_results.json"

    capsys.readouterr()
    call_command(
        "run_benchmark",
        split="tuning",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(tuning_out),
        allow_real_data=True,
    )
    tuning_stdout = capsys.readouterr().out
    expected_sha256 = hashlib.sha256(tuning_out.read_bytes()).hexdigest()
    expected_paste_line = f"resumo SHA-256 do ajuste `{expected_sha256}`"

    assert f"(output SHA-256: {expected_sha256})." in tuning_stdout
    assert expected_paste_line in tuning_stdout.splitlines()

    # Copy the exact printed line into the thresholds note and run measurement
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\nresumo SHA-256 `{split.sha256_hash}`\n{expected_paste_line}\n",
        encoding="utf-8",
    )
    measurement_out = eval_dir / "benchmark_measurement_results.json"
    capsys.readouterr()
    call_command(
        "run_benchmark",
        split="measurement",
        thresholds_note=str(decision_copy),
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(measurement_out),
        allow_real_data=True,
    )
    measurement_stdout = capsys.readouterr().out
    assert measurement_out.exists()
    assert "resumo SHA-256 do ajuste" not in measurement_stdout


def test_v2_synthetic_tuning_prints_ready_to_paste_hash_line(monkeypatch, tmp_path, capsys):
    from django.conf import settings

    project_root = tmp_path / "repo"
    decision_copy = project_root / "TCC" / "decisões" / "thresholds.md"
    decision_copy.parent.mkdir(parents=True)
    monkeypatch.setattr(settings, "BASE_DIR", project_root / "code")

    eval_dir = tmp_path / "syn_eval"
    eval_dir.mkdir()
    tuning_out = eval_dir / "benchmark_tuning_results.json"

    capsys.readouterr()
    call_command(
        "run_benchmark",
        split="tuning",
        output=str(tuning_out),
        synthetic=True,
    )
    tuning_stdout = capsys.readouterr().out
    expected_sha256 = hashlib.sha256(tuning_out.read_bytes()).hexdigest()
    expected_paste_line = f"resumo SHA-256 do ajuste `{expected_sha256}`"

    assert f"(SHA-256: {expected_sha256})" in tuning_stdout
    assert expected_paste_line in tuning_stdout.splitlines()

    tuning_data = json.loads(tuning_out.read_text(encoding="utf-8"))
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{tuning_data['split_hash']}`\n"
        f"{expected_paste_line}\n",
        encoding="utf-8",
    )
    measurement_out = eval_dir / "benchmark_measurement_results.json"
    capsys.readouterr()
    call_command(
        "run_benchmark",
        split="measurement",
        thresholds_note=str(decision_copy),
        eval_dir=str(eval_dir),
        output=str(measurement_out),
        synthetic=True,
    )
    measurement_stdout = capsys.readouterr().out
    assert measurement_out.exists()
    assert "resumo SHA-256 do ajuste" not in measurement_stdout


# ---------------------------------------------------------------------------
# V1 — Q-2 (pin .resolve() on symlink paths) & P1-b (multiple SHA-256 lines)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_v1_q2_default_and_subdir_symlinks_inside_eval_dir_resolving_outside_refused(
    monkeypatch, tmp_path
):
    _project_root, decision_copy, eval_dir, split = _setup_real_eval_fixture(monkeypatch, tmp_path)
    tuning_payload = {
        "split": "tuning",
        "synthetic": False,
        "items_count": len(split.tuning_items),
        "split_hash": split.sha256_hash,
        "finalist": "semantic",
        "methods": {
            "bm25": {"metrics": {"recall_at_10": 0.4, "mrr_at_20": 0.3}},
            "semantic": {"metrics": {"recall_at_10": 0.8, "mrr_at_20": 0.7}},
        },
    }
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    outside_target = outside_dir / "outside_tuning.json"
    outside_target.write_text(json.dumps(tuning_payload), encoding="utf-8")
    outside_sha = hashlib.sha256(outside_target.read_bytes()).hexdigest()
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split.sha256_hash}`\n"
        f"resumo SHA-256 do ajuste `{outside_sha}`\n",
        encoding="utf-8",
    )

    # Case 1: Default benchmark_tuning_results.json (without --tuning-output) is a symlink outside
    default_symlink = eval_dir / "benchmark_tuning_results.json"
    os.symlink(outside_target, default_symlink)
    with pytest.raises(CommandError, match="eval directory"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )
    default_symlink.unlink()

    # Case 2: Symlinked subdirectory inside eval_dir containing a regular file outside eval_dir
    linked_subdir = eval_dir / "linked_sub"
    os.symlink(outside_dir, linked_subdir)
    with pytest.raises(CommandError, match="eval directory"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            tuning_output=str(linked_subdir / "outside_tuning.json"),
            pattern="*.report.json",
            allow_real_data=True,
        )


@pytest.mark.django_db
def test_v1_p1b_multiple_tuning_hash_lines_must_all_match_with_explicit_rule(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    decisoes_dir = repo_root / "TCC" / "decisões"
    decisoes_dir.mkdir(parents=True)
    split_hash = "a" * 64
    tuning_hash = "b" * 64
    wrong_hash = "c" * 64

    # First line wrong, second line right -> MUST fail and state "All ... lines ... must match"
    first_wrong = decisoes_dir / "first_wrong.md"
    first_wrong.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split_hash}`\n"
        f"resumo SHA-256 do ajuste `{wrong_hash}`\n"
        f"resumo SHA-256 do ajuste `{tuning_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"All 'resumo SHA-256 do ajuste' lines.*must match",
    ) as exc_first:
        check_thresholds_note_guard(
            first_wrong,
            split_hash=split_hash,
            repo_root=repo_root,
            tuning_output_hash=tuning_hash,
        )
    assert wrong_hash in str(exc_first.value)

    # First line right, second line wrong -> MUST fail with explicit rule
    second_wrong = decisoes_dir / "second_wrong.md"
    second_wrong.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split_hash}`\n"
        f"resumo SHA-256 do ajuste `{tuning_hash}`\n"
        f"resumo SHA-256 do ajuste `{wrong_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"All 'resumo SHA-256 do ajuste' lines.*must match",
    ) as exc_second:
        check_thresholds_note_guard(
            second_wrong,
            split_hash=split_hash,
            repo_root=repo_root,
            tuning_output_hash=tuning_hash,
        )
    assert wrong_hash in str(exc_second.value)

    # Two identical matching lines -> accepted
    both_match = decisoes_dir / "both_match.md"
    both_match.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split_hash}`\n"
        f"resumo SHA-256 do ajuste `{tuning_hash}`\n"
        f"resumo SHA-256 do ajuste `{tuning_hash}`\n",
        encoding="utf-8",
    )
    content = check_thresholds_note_guard(
        both_match,
        split_hash=split_hash,
        repo_root=repo_root,
        tuning_output_hash=tuning_hash,
    )
    assert tuning_hash in content

    # End-to-end measurement guard check via run_benchmark
    _project_root, decision_copy, eval_dir, split = _setup_real_eval_fixture(monkeypatch, tmp_path)
    tuning_out = eval_dir / "benchmark_tuning_results.json"
    call_command(
        "run_benchmark",
        split="tuning",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(tuning_out),
        allow_real_data=True,
    )
    real_sha = hashlib.sha256(tuning_out.read_bytes()).hexdigest()
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split.sha256_hash}`\n"
        f"resumo SHA-256 do ajuste `{real_sha}`\n"
        f"resumo SHA-256 do ajuste `{wrong_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(
        CommandError,
        match=r"All 'resumo SHA-256 do ajuste' lines.*must match",
    ):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )


# ---------------------------------------------------------------------------
# V3 — Build each item's candidate objects once and swap drawn rank per draw
# ---------------------------------------------------------------------------


def test_v3_builds_candidate_objects_once_per_item_and_swaps_id_per_draw(monkeypatch):
    corpus = [
        PublicItemSim(
            id=i,
            description=f"papel item {i % 10}",
            published_on=date(2026, 5, 1),
            modality=6,
            price=Decimal(f"{10 + (i % 7)}.00"),
        )
        for i in range(1, 101)
    ]
    items = [
        {
            "item_id": "v3_reuse",
            "description": "papel item 1",
            "ground_truth": {2, 16, 35},
            "chosen_prices": [Decimal("11.00")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]

    class CandMethod:
        name = "cand"

        def rank(self, query, candidates):
            return [(c, 0.9 if c.id <= 15 else (0.5 if c.id <= 35 else 0.1)) for c in candidates]

    po_object_id_sets: list[frozenset[int]] = []
    sys_object_id_sets: list[frozenset[int]] = []
    po_rank_id_tuples: list[tuple[int, ...]] = []

    orig_rank_po = benchmark_module.rank_by_price_only
    orig_rank_rf23 = BenchmarkOrchestrator.rank_with_rf23

    def spy_po(candidates, anchor):
        po_object_id_sets.append(frozenset(id(c) for c in candidates))
        po_rank_id_tuples.append(tuple(c.id for c in candidates))
        return orig_rank_po(candidates, anchor=anchor)

    def spy_rf23(self, candidates, anchor=None, unit="UNIDADE"):
        sys_object_id_sets.append(frozenset(id(c) for c in candidates))
        return orig_rank_rf23(self, candidates, anchor=anchor, unit=unit)

    monkeypatch.setattr(benchmark_module, "rank_by_price_only", spy_po)
    monkeypatch.setattr(BenchmarkOrchestrator, "rank_with_rf23", spy_rf23)

    n_draws = 15
    orch = BenchmarkOrchestrator(n_noise_draws=n_draws, n_bootstrap_resamples=10, seed=42, top_n=20)
    orch.run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[CandMethod()],
        baseline_method=BM25SearchMethod(),
        synthetic=True,
        top_n=20,
    )

    assert len(po_object_id_sets) == n_draws * 5
    # Same 100 candidate object instances reused across all draws (only .id swapped)
    assert len(set(po_object_id_sets)) == 1
    assert len(po_object_id_sets[0]) == len(corpus)
    # Ranks were actually swapped across draws (not stuck at initial order)
    assert len(set(po_rank_id_tuples)) > 1
    # Finalist candidate objects across all draws also reused from a per-item pool (<= |C(q)|)
    all_sys_obj_ids = set().union(*sys_object_id_sets)
    assert len(all_sys_obj_ids) <= 35


def test_v3_output_byte_identical_to_5290522_reference():
    corpus = [
        PublicItemSim(
            id=i,
            description=f"papel sulfite item {i % 5}",
            published_on=date(2026, 5, 1),
            modality=6,
            price=Decimal(f"{10 + (i % 7)}.00"),
        )
        for i in range(1, 61)
    ]
    items = [
        {
            "item_id": "p4_a",
            "description": "papel sulfite item 1",
            "ground_truth": {2, 16, 35, 50},
            "chosen_prices": [Decimal("11.00"), Decimal("12.00")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
        {
            "item_id": "p4_b",
            "description": "papel sulfite item 2",
            "ground_truth": {7, 22, 41},
            "chosen_prices": [Decimal("15.00")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
    ]

    class TiedCand:
        name = "tied_cand"

        def rank(self, query, candidates):
            return [(c, 0.9 if c.id <= 15 else (0.5 if c.id <= 35 else 0.1)) for c in candidates]

    class TiedBm:
        name = "bm25"

        def rank(self, query, candidates):
            return [(c, 0.8 if c.id <= 12 else 0.2) for c in candidates]

    orch = BenchmarkOrchestrator(n_noise_draws=200, n_bootstrap_resamples=200, seed=42, top_n=20)
    res = orch.run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[TiedCand()],
        baseline_method=TiedBm(),
        synthetic=True,
        top_n=20,
    )
    payload = json.dumps(res, indent=2, cls=DecimalEncoder)
    assert (
        hashlib.sha256(payload.encode("utf-8")).hexdigest()
        == "a19c69852bb72f80fa34ffaa758040c386254a435e773cbcb80be2bba888d776"
    )
