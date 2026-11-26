"""Pre-measurement tests for P1 (tuning file SHA-256 pinning), P2 (13 mutant guards),
P3 (tie-shuffle reproducibility), and P4 (inverted R2 loop memory & bit-exactness).
"""

import hashlib
import itertools
import json
import os
import random
import tracemalloc
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from qdrant_client import models

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    FakeDeterministicEmbeddingModel,
    PriceCandidateSim,
    PublicItemSim,
    SemanticSearchMethod,
    check_collection_coverage,
    check_thresholds_note_guard,
    classify_easy_hard_items,
    compute_expected_mrr_at_k,
    compute_expected_recall_at_k,
    compute_expected_success_at_k,
    compute_mrr_at_k,
    compute_recall_at_k,
    compute_success_at_k,
    compute_tie_sensitivity,
    create_dataset_split,
    shuffle_tied_groups,
)
from semantic_index.search import ScoredPublicItem, StructuredFilter, semantic_search


def _setup_real_eval_fixture(monkeypatch, tmp_path: Path):
    from django.conf import settings

    from ingestion.models import PublicItem

    repo_root = Path(__file__).resolve().parents[2]
    real_decision = repo_root / "TCC" / "decisões" / "2026-11-24-limiares-de-aceitacao-r1-r2.md"
    project_root = tmp_path / "repo"
    decision_copy = project_root / "TCC" / "decisões" / real_decision.name
    decision_copy.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "BASE_DIR", project_root / "code")

    eval_dir = tmp_path / "avaliacao"
    eval_dir.mkdir(parents=True, exist_ok=True)

    split = create_dataset_split(
        [
            {"item_id": "rep_1", "report_id": "rep", "item_kind": "product"},
            {"item_id": "rep_2", "report_id": "rep", "item_kind": "product"},
        ],
        tuning_fraction=0.5,
        seed=42,
    )
    (eval_dir / "dataset_split.json").write_text(
        json.dumps(
            {
                "tuning_items": list(split.tuning_items),
                "measurement_items": list(split.measurement_items),
                "sha256_hash": split.sha256_hash,
            }
        ),
        encoding="utf-8",
    )
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\nresumo SHA-256 `{split.sha256_hash}`\n",
        encoding="utf-8",
    )
    (eval_dir / "ground_truth_resolved.json").write_text(
        json.dumps(
            {
                "resolved_items": {
                    "rep_it1_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                    "rep_it2_p1": {
                        "cnpj": "11111111000111",
                        "year": 2026,
                        "purchase_sequence": 100,
                        "item_number": 1,
                        "found": True,
                        "item_kind": "product",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "rep.report.json").write_text(
        json.dumps(
            {
                "report_id": "rep",
                "survey_end": "15/06/2026",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Papel sulfite A4 75g",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                    {
                        "item_number": 2,
                        "description": "Papel sulfite A4 75g",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    p1 = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite A4 75g",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    p2 = PublicItem.objects.create(
        cnpj="22222222000122",
        year=2026,
        purchase_sequence=200,
        item_number=1,
        description="Caneta esferográfica azul",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("2"),
        awarded_unit_price=Decimal("2"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="22222222000122",
        state="PA",
        modality=6,
        item_kind="product",
    )

    monkeypatch.setattr(
        "pricing.views.get_embedding_model",
        lambda: FakeDeterministicEmbeddingModel(),
    )
    monkeypatch.setattr(
        "semantic_index.search.semantic_search",
        lambda model, query, structured_filter, limit, client=None, exact=False: [
            ScoredPublicItem(item=p1, score=0.95),
            ScoredPublicItem(item=p2, score=0.10),
        ],
    )
    fake_qdrant = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: fake_qdrant)

    return project_root, decision_copy, eval_dir, split


# ---------------------------------------------------------------------------
# P1 — Pinning benchmark_tuning_results.json SHA-256 in the thresholds note
# ---------------------------------------------------------------------------


def test_p1_check_thresholds_note_guard_verifies_tuning_output_hash(tmp_path):
    repo_root = tmp_path / "repo"
    decisoes_dir = repo_root / "TCC" / "decisões"
    decisoes_dir.mkdir(parents=True)
    split_hash = "a" * 64
    tuning_hash = "b" * 64
    wrong_hash = "c" * 64

    note_without_tuning_hash = decisoes_dir / "without.md"
    note_without_tuning_hash.write_text(
        f"---\nstatus: aceita\n---\nresumo SHA-256 `{split_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SHA-256"):
        check_thresholds_note_guard(
            note_without_tuning_hash,
            split_hash=split_hash,
            repo_root=repo_root,
            tuning_output_hash=tuning_hash,
        )

    note_with_wrong_hash = decisoes_dir / "wrong.md"
    note_with_wrong_hash.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split_hash}`\n"
        f"resumo SHA-256 do ajuste `{wrong_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SHA-256"):
        check_thresholds_note_guard(
            note_with_wrong_hash,
            split_hash=split_hash,
            repo_root=repo_root,
            tuning_output_hash=tuning_hash,
        )

    note_with_right_hash = decisoes_dir / "right.md"
    note_with_right_hash.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split_hash}`\n"
        f"resumo SHA-256 do ajuste `{tuning_hash}`\n",
        encoding="utf-8",
    )
    content = check_thresholds_note_guard(
        note_with_right_hash,
        split_hash=split_hash,
        repo_root=repo_root,
        tuning_output_hash=tuning_hash,
    )
    assert tuning_hash in content


@pytest.mark.django_db
def test_p1_measurement_pins_tuning_output_sha256_before_reading_content(monkeypatch, tmp_path):
    _project_root, decision_copy, eval_dir, split = _setup_real_eval_fixture(monkeypatch, tmp_path)

    # Produce a real tuning output file first
    tuning_file = eval_dir / "benchmark_tuning_results.json"
    call_command(
        "run_benchmark",
        split="tuning",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(tuning_file),
        allow_real_data=True,
    )
    real_tuning_sha = hashlib.sha256(tuning_file.read_bytes()).hexdigest()

    # 1. Real tuning file + note WITHOUT the tuning SHA-256 line -> refused
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\nresumo SHA-256 `{split.sha256_hash}`\n",
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="SHA-256"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # 2. Real tuning file + note with a WRONG tuning SHA-256 -> refused
    wrong_sha = "0" * 64
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split.sha256_hash}`\n"
        f"resumo SHA-256 do ajuste `{wrong_sha}`\n",
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="SHA-256"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # 3. Verify hash check runs BEFORE reading/parsing tuning file JSON content:
    # With corrupted JSON and wrong hash in note, failure MUST be SHA-256 guard, not JSON error.
    saved_bytes = tuning_file.read_bytes()
    tuning_file.write_text("{corrupt non-json content", encoding="utf-8")
    with pytest.raises(CommandError, match="SHA-256"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )
    tuning_file.write_bytes(saved_bytes)

    # 4. Real tuning file + note WITH the right tuning SHA-256 -> accepted
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split.sha256_hash}`\n"
        f"resumo SHA-256 do ajuste `{real_tuning_sha}`\n",
        encoding="utf-8",
    )
    measurement_out = eval_dir / "benchmark_measurement_results.json"
    call_command(
        "run_benchmark",
        split="measurement",
        thresholds_note=str(decision_copy),
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(measurement_out),
        allow_real_data=True,
    )
    assert measurement_out.exists()

    # 5. Edit a metric inside the tuning file AFTER the hash was recorded -> refused
    edited = json.loads(tuning_file.read_text(encoding="utf-8"))
    edited["methods"]["semantic"]["metrics"]["recall_at_10"] = 0.99
    tuning_file.write_text(json.dumps(edited), encoding="utf-8")
    with pytest.raises(CommandError, match="SHA-256"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )


# ---------------------------------------------------------------------------
# P2 — Kill the 13 surviving mutants (one dedicated test per item)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_p2_e2_semantic_method_limit_at_least_cq_size_above_10(monkeypatch):
    from ingestion.models import PublicItem

    created = [
        PublicItem.objects.create(
            cnpj=f"{i:014d}",
            year=2026,
            purchase_sequence=i,
            item_number=1,
            description=f"Papel sulfite item {i}",
            unit="UNIDADE",
            quantity=Decimal("1"),
            estimated_unit_price=Decimal("25"),
            awarded_unit_price=Decimal("25"),
            secret_budget=False,
            published_on=date(2026, 5, 1),
            agency_name="Prefeitura Fictícia",
            agency_cnpj=f"{i:014d}",
            state="PA",
            modality=6,
            item_kind="product",
        )
        for i in range(1, 41)
    ]
    seen_limits: list[int] = []

    def fake_semantic_search(model, query, structured_filter, limit, client=None, exact=False):
        seen_limits.append(limit)
        scored = [
            ScoredPublicItem(item=item, score=1.0 - 0.01 * idx) for idx, item in enumerate(created)
        ]
        return scored[:limit]

    monkeypatch.setattr("semantic_index.search.semantic_search", fake_semantic_search)
    ranked = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel()).rank(
        query="papel sulfite",
        candidates=created,
    )
    assert len(seen_limits) == 1
    assert seen_limits[0] >= 40
    assert len(ranked) == 40
    assert {doc.pk for doc, _score in ranked} == {item.pk for item in created}


@pytest.mark.django_db
def test_p2_e4_semantic_search_defaults_to_exact_false():
    from ingestion.models import PublicItem

    item = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=1,
        item_number=1,
        description="Papel sulfite A4",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    captured_query_kwargs: list[dict] = []

    class SpyQdrantClient:
        def collection_exists(self, collection_name):
            return True

        def get_collection(self, collection_name):
            return SimpleNamespace(
                payload_schema={
                    "modality": SimpleNamespace(data_type=models.PayloadSchemaType.INTEGER)
                }
            )

        def count(self, collection_name, count_filter, exact=False):
            return SimpleNamespace(count=0)

        def query_points(self, **kwargs):
            captured_query_kwargs.append(kwargs)
            return SimpleNamespace(points=[SimpleNamespace(id=item.pk, score=0.9)])

    results = semantic_search(
        FakeDeterministicEmbeddingModel(),
        "papel sulfite",
        StructuredFilter(date_window=(date(2026, 1, 1), date(2026, 6, 1)), modality=[6]),
        client=SpyQdrantClient(),
    )
    assert len(results) == 1
    assert len(captured_query_kwargs) == 1
    search_params = captured_query_kwargs[0].get("search_params")
    assert search_params is None or getattr(search_params, "exact", False) is False


def test_p2_r6_easy_hard_cut_is_p_strictly_greater_than_zero():
    # 25 equal-price candidates with 1 relevant -> expected Success@10 = 10/25 = 0.40 (0 < p < 0.5)
    candidates_easy = [
        PriceCandidateSim(id=i, price=Decimal("25.0"), similarity=0.5) for i in range(1, 26)
    ]
    assert (
        classify_easy_hard_items(
            candidates_easy,
            anchor=Decimal("25.0"),
            ground_truth_ids={25},
            k=10,
        )
        is True
    )
    # 10 exact-match distractors + 1 relevant outside top 10 -> p = 0.0 -> HARD
    candidates_hard = [
        PriceCandidateSim(id=i, price=Decimal("25.0"), similarity=0.5) for i in range(1, 11)
    ] + [PriceCandidateSim(id=11, price=Decimal("80.0"), similarity=0.5)]
    assert (
        classify_easy_hard_items(
            candidates_hard,
            anchor=Decimal("25.0"),
            ground_truth_ids={11},
            k=10,
        )
        is False
    )


def test_p2_r7_r2_tie_break_seed_does_not_depend_on_ground_truth():
    corpus = [
        PublicItemSim(
            id=i,
            description=f"papel item {i}",
            price=Decimal("25.0") if i % 2 == 0 else Decimal("30.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 26)
    ]

    class TiedMethod:
        name = "tied_sem"

        def rank(self, query, candidates):
            return [(c, 0.85 if c.id <= 22 else 0.40) for c in candidates]

    def run_and_spy(gt_ids: set[int]):
        orch = BenchmarkOrchestrator(n_noise_draws=25, n_bootstrap_resamples=10, seed=42, top_n=20)
        recorded_rf23_inputs = []
        orig_rank = orch.rank_with_rf23

        def spy_rank_with_rf23(candidates, anchor=None, unit="UNIDADE"):
            recorded_rf23_inputs.append(
                (
                    str(anchor),
                    unit,
                    [(c.id, str(c.price), c.similarity, c.unit) for c in candidates],
                )
            )
            return orig_rank(candidates, anchor=anchor, unit=unit)

        orch.rank_with_rf23 = spy_rank_with_rf23
        orch.run_benchmark(
            items=[
                {
                    "item_id": "r7_item",
                    "description": "papel sulfite",
                    "ground_truth": gt_ids,
                    "chosen_prices": [Decimal("25.0")],
                    "unit": "UNIDADE",
                    "survey_date": date(2026, 6, 1),
                }
            ],
            corpus=corpus,
            split_name="tuning",
            candidate_methods=[TiedMethod()],
            baseline_method=BM25SearchMethod(),
        )
        return recorded_rf23_inputs

    calls_a = run_and_spy({1, 2})
    calls_b = run_and_spy({18, 25})
    assert len(calls_a) == 25 * 5
    assert calls_a == calls_b


@pytest.mark.django_db
def test_p2_q8_real_path_stdout_prints_exact_output_file_sha256(monkeypatch, tmp_path, capsys):
    _project_root, _decision_copy, eval_dir, _split = _setup_real_eval_fixture(
        monkeypatch, tmp_path
    )
    out_file = eval_dir / "real_tuning_out.json"
    capsys.readouterr()
    call_command(
        "run_benchmark",
        split="tuning",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(out_file),
        allow_real_data=True,
    )
    captured = capsys.readouterr().out
    expected_sha256 = hashlib.sha256(out_file.read_bytes()).hexdigest()
    assert expected_sha256 in captured


@pytest.mark.django_db
def test_p2_q2_symlink_inside_eval_dir_pointing_outside_is_refused(monkeypatch, tmp_path):
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
    outside_target = tmp_path / "outside_tuning.json"
    outside_target.write_text(json.dumps(tuning_payload), encoding="utf-8")
    outside_sha = hashlib.sha256(outside_target.read_bytes()).hexdigest()
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\n"
        f"resumo SHA-256 `{split.sha256_hash}`\n"
        f"resumo SHA-256 do ajuste `{outside_sha}`\n",
        encoding="utf-8",
    )

    symlink_in_eval = eval_dir / "benchmark_tuning_results.json"
    os.symlink(outside_target, symlink_in_eval)

    with pytest.raises(CommandError, match="eval directory"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note=str(decision_copy),
            eval_dir=str(eval_dir),
            tuning_output=str(symlink_in_eval),
            pattern="*.report.json",
            allow_real_data=True,
        )


def test_p2_f2_tied_group_entirely_inside_cut_with_multiple_relevant_counts_all():
    # Tied group of 4 items at ranks 3..6 (offset=2, offset+m=6 <= k=10), 2 relevant ({3, 4}),
    # plus 1 relevant at rank 15 outside cut -> expected Recall@10 = 2/3 (not 1/3!).
    ranked_scored = (
        [(1, 1.0), (2, 0.9)]
        + [(i, 0.8) for i in range(3, 7)]
        + [(i, 0.5 - 0.01 * i) for i in range(7, 16)]
    )
    gt_ids = {3, 4, 15}

    assert compute_expected_recall_at_k(ranked_scored, gt_ids, k=10) == pytest.approx(
        2.0 / 3.0, abs=1e-12
    )

    # Brute-force agreement check for Recall@10, Success@10, and MRR@20
    group_3_to_6 = list(itertools.permutations([3, 4, 5, 6]))
    recalls, successes, mrrs = [], [], []
    for perm in group_3_to_6:
        full_order = [1, 2, *perm, *range(7, 16)]
        recalls.append(compute_recall_at_k(full_order, gt_ids, k=10))
        successes.append(compute_success_at_k(full_order, gt_ids, k=10))
        mrrs.append(compute_mrr_at_k(full_order, gt_ids, k=20))

    assert compute_expected_recall_at_k(ranked_scored, gt_ids, k=10) == pytest.approx(
        sum(recalls) / len(recalls), abs=1e-12
    )
    assert compute_expected_success_at_k(ranked_scored, gt_ids, k=10) == pytest.approx(
        sum(successes) / len(successes), abs=1e-12
    )
    assert compute_expected_mrr_at_k(ranked_scored, gt_ids, k=20) == pytest.approx(
        sum(mrrs) / len(mrrs), abs=1e-12
    )


@pytest.mark.django_db
def test_p2_n4b_check_collection_coverage_detects_missing_id_in_second_batch(monkeypatch):
    from ingestion.models import PublicItem

    ids = list(range(1, 601))

    class SecondBatchMissingClient:
        def collection_exists(self, collection_name):
            return True

        def retrieve(self, collection_name, ids, with_payload=False, with_vectors=False):
            # Batch 1 (1..500) is complete; batch 2 drops ID 550
            return [SimpleNamespace(id=pk) for pk in ids if pk != 550]

    cov = check_collection_coverage(
        FakeDeterministicEmbeddingModel(),
        ids,
        client=SecondBatchMissingClient(),
        batch_size=500,
    )
    assert cov["expected_count"] == 600
    assert cov["present_count"] == 599
    assert cov["missing_count"] == 1

    # Also verify BenchmarkOrchestrator fails on a missing ID in batch 2 (> 500 PublicItems)
    created = PublicItem.objects.bulk_create(
        [
            PublicItem(
                cnpj=f"{i:014d}",
                year=2026,
                purchase_sequence=i,
                item_number=1,
                description=f"Papel item {i}",
                unit="UNIDADE",
                quantity=Decimal("1"),
                estimated_unit_price=Decimal("25"),
                awarded_unit_price=Decimal("25"),
                secret_budget=False,
                published_on=date(2026, 5, 1),
                agency_name="Prefeitura Fictícia",
                agency_cnpj=f"{i:014d}",
                state="PA",
                modality=6,
                item_kind="product",
            )
            for i in range(1, 506)
        ]
    )
    missing_pk = sorted(item.pk for item in created)[-1]
    monkeypatch.setattr(
        "semantic_index.get_qdrant_client",
        lambda *a, **kw: SimpleNamespace(
            collection_exists=lambda name: True,
            retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
                SimpleNamespace(id=pk) for pk in ids if pk != missing_pk
            ],
        ),
    )
    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    with pytest.raises(ValueError, match="504/505"):
        orch.run_benchmark(
            items=[
                {
                    "item_id": "n4b_it",
                    "description": "Papel item",
                    "ground_truth": {created[0].pk},
                    "chosen_prices": [Decimal("25")],
                    "unit": "UNIDADE",
                    "survey_date": date(2026, 6, 1),
                }
            ],
            corpus=PublicItem.objects.all(),
            split_name="tuning",
            candidate_methods=[SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())],
            baseline_method=BM25SearchMethod(),
        )


def test_p2_n6c_orchestrator_refuses_zero_chosen_price_upfront():
    corpus = [
        PublicItemSim(
            id=1,
            description="Papel Sulfite A4",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
    ]
    rank_called = False

    class SpyMethod:
        name = "cand"

        def rank(self, query, candidates):
            nonlocal rank_called
            rank_called = True
            return [(c, 1.0) for c in candidates]

    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    with pytest.raises(ValueError, match=r"1 item\(s\) have no chosen price for the R2 anchor"):
        orch.run_benchmark(
            items=[
                {
                    "item_id": "zero_price",
                    "description": "Papel A4",
                    "ground_truth": {1},
                    "chosen_prices": [Decimal("0")],
                    "unit": "UNIDADE",
                    "survey_date": date(2026, 6, 1),
                },
                {
                    "item_id": "ok_price",
                    "description": "Papel A4",
                    "ground_truth": {1},
                    "chosen_prices": [Decimal("25.0")],
                    "unit": "UNIDADE",
                    "survey_date": date(2026, 6, 1),
                },
            ],
            corpus=corpus,
            split_name="tuning",
            candidate_methods=[SpyMethod()],
            baseline_method=BM25SearchMethod(),
        )
    assert not rank_called


def test_p2_s2_tie_sensitivity_recall_does_not_count_group_starting_at_rank_11():
    # Group starting at rank 11 (offset == 10, ranks 11..14) must NOT count for Recall@10
    ranked_start_11 = [(i, 1.0 - 0.01 * i) for i in range(1, 11)] + [
        (i, 0.5) for i in range(11, 15)
    ]
    assert compute_tie_sensitivity(ranked_start_11, {11, 12}, top_n=20)["recall_at_10"] is False
    # Group ending right at rank 10 (offset=6, m=4 -> offset+m=10) also does NOT cross rank 10
    ranked_end_10 = (
        [(i, 1.0 - 0.01 * i) for i in range(1, 7)] + [(i, 0.7) for i in range(7, 11)] + [(11, 0.2)]
    )
    assert compute_tie_sensitivity(ranked_end_10, {7, 8}, top_n=20)["recall_at_10"] is False


def test_p2_s4_tie_sensitivity_mrr_at_20_window_includes_ranks_11_to_20():
    # First relevant group sits at ranks 13..16 (offset=12, inside top 20, outside top 10)
    ranked_13_to_16 = (
        [(i, 1.0 - 0.01 * i) for i in range(1, 13)]
        + [(i, 0.5) for i in range(13, 17)]
        + [(17, 0.1)]
    )
    assert compute_tie_sensitivity(ranked_13_to_16, {13}, top_n=20)["mrr_at_20"] is True
    # First relevant group starting at rank 21 (offset == 20) is outside window 20 -> False
    ranked_at_21 = [(i, 1.0 - 0.01 * i) for i in range(1, 21)] + [(i, 0.5) for i in range(21, 25)]
    assert compute_tie_sensitivity(ranked_at_21, {21}, top_n=20)["mrr_at_20"] is False


def test_p2_s5_tie_sensitivity_r2_pool_does_not_count_group_ending_at_top_n():
    # Tied group at ranks 17..20 (offset=16, offset+m=20 == top_n) does NOT cross top_n=20
    ranked_end_20 = (
        [(i, 1.0 - 0.01 * i) for i in range(1, 17)]
        + [(i, 0.5) for i in range(17, 21)]
        + [(i, 0.2 - 0.01 * i) for i in range(21, 25)]
    )
    assert compute_tie_sensitivity(ranked_end_20, {1}, top_n=20)["r2_pool"] is False
    # Tied group starting at rank 21 (offset=20 == top_n) also does NOT cross top_n=20
    ranked_start_21 = [(i, 1.0 - 0.01 * i) for i in range(1, 21)] + [
        (i, 0.5) for i in range(21, 25)
    ]
    assert compute_tie_sensitivity(ranked_start_21, {1}, top_n=20)["r2_pool"] is False


def test_p2_s7_orchestrator_passes_effective_top_n_to_compute_tie_sensitivity():
    # Distinct scores 1..18 (no ties near rank 10), tied group at 19..22 crossing top_n=20
    corpus = [
        PublicItemSim(
            id=i,
            description=f"doc {i}",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 26)
    ]

    class Cross20OnlyMethod:
        name = "cross20"

        def rank(self, query, candidates):
            out = []
            for c in candidates:
                if c.id <= 18:
                    out.append((c, 1.0 - 0.01 * c.id))
                elif c.id <= 22:
                    out.append((c, 0.5))
                else:
                    out.append((c, 0.2 - 0.01 * c.id))
            return out

    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    res = orch.run_benchmark(
        items=[
            {
                "item_id": "s7_item",
                "description": "doc 1",
                "ground_truth": {1},
                "chosen_prices": [Decimal("25.0")],
                "unit": "UNIDADE",
                "survey_date": date(2026, 6, 1),
            }
        ],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[Cross20OnlyMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=20,
    )
    assert res["tie_sensitivity"]["r2_pool"] == pytest.approx(1.0)
    assert res["tie_sensitivity"]["recall_at_10"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# P3 — Reproducibility under reversed tied-input ordering
# ---------------------------------------------------------------------------


def test_p3_shuffle_tied_groups_identical_for_reversed_input_same_seed():
    forward = [(i, 0.75) for i in range(1, 21)]
    reversed_in = list(reversed(forward))

    shuffled_fwd = [doc for doc, _ in shuffle_tied_groups(forward, random.Random(42))]
    shuffled_rev = [doc for doc, _ in shuffle_tied_groups(reversed_in, random.Random(42))]
    assert shuffled_fwd == shuffled_rev


def test_p3_orchestrator_r2_identical_when_corpus_and_ranked_input_reversed():
    corpus_fwd = [
        PublicItemSim(
            id=i,
            description=f"papel item {i % 3}",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for i in range(1, 31)
    ]
    corpus_rev = list(reversed(corpus_fwd))

    class TiedInputOrderMethod:
        name = "tied_cand"

        def rank(self, query, candidates):
            return [(c, 0.85 if c.id <= 25 else 0.30) for c in candidates]

    items = [
        {
            "item_id": "p3_it",
            "description": "papel item 1",
            "ground_truth": {3, 14, 22},
            "chosen_prices": [Decimal("25.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]
    orch = BenchmarkOrchestrator(n_noise_draws=50, n_bootstrap_resamples=20, seed=42, top_n=20)
    res_fwd = orch.run_benchmark(
        items=items,
        corpus=corpus_fwd,
        split_name="tuning",
        candidate_methods=[TiedInputOrderMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=20,
    )
    res_rev = orch.run_benchmark(
        items=items,
        corpus=corpus_rev,
        split_name="tuning",
        candidate_methods=[TiedInputOrderMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=20,
    )
    assert res_fwd["methods"] == res_rev["methods"]
    assert res_fwd["tie_sensitivity"] == res_rev["tie_sensitivity"]
    assert res_fwd["r1_acceptance"] == res_rev["r1_acceptance"]
    assert res_fwd["r2_acceptance"] == res_rev["r2_acceptance"]
    assert res_fwd["r2"] == res_rev["r2"]
    assert res_fwd["ranked_ids_by_method"] == res_rev["ranked_ids_by_method"]


# ---------------------------------------------------------------------------
# P4 — Inverted R2 loop: bit-identical output & O(|C(q)|) peak memory
# ---------------------------------------------------------------------------


def test_p4_loop_inversion_bit_identical_to_pre_change_reference():
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

    assert res["r2"]["g_sigma"] == {
        "0.0": -0.1231,
        "0.1": -0.1135,
        "0.25": -0.0733,
        "0.5": -0.064,
        "1.0": -0.066,
    }
    assert res["r2"]["price_only_baseline"] == pytest.approx(0.22666666666666666, abs=1e-15)
    assert res["r2"]["easy_items_count"] == 2
    assert res["r2_acceptance"]["accepted"] is False
    assert res["r2_acceptance"]["sigma_025_ci"] == pytest.approx(
        [-0.07333333333333332, -0.16166666666666665, 0.015000000000000013],
        abs=1e-15,
    )
    assert res["r2_acceptance"]["hard_gain_ci"] == [0.0, 0.0, 0.0]


def test_p4_r2_peak_memory_does_not_grow_linearly_with_noise_draws():
    corpus = [
        PublicItemSim(
            id=i,
            description=f"papel item {i % 20}",
            published_on=date(2026, 5, 1),
            modality=6,
            price=Decimal(f"{10 + (i % 10)}.00"),
        )
        for i in range(1, 1501)
    ]
    items = [
        {
            "item_id": "p4_mem",
            "description": "papel item 1",
            "ground_truth": {1, 5, 10},
            "chosen_prices": [Decimal("10.00")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]

    class FastMethod:
        def __init__(self, name):
            self.name = name

        def rank(self, query, candidates):
            return [(c, 1.0 if c.id <= 15 else 0.5) for c in candidates]

    def measure_peak(n_draws: int) -> int:
        orch = BenchmarkOrchestrator(
            n_noise_draws=n_draws, n_bootstrap_resamples=10, seed=42, top_n=20
        )
        tracemalloc.start()
        try:
            orch.run_benchmark(
                items=items,
                corpus=corpus,
                split_name="tuning",
                candidate_methods=[FastMethod("cand")],
                baseline_method=FastMethod("bm25"),
                synthetic=True,
                top_n=20,
            )
            _cur, peak = tracemalloc.get_traced_memory()
            return peak
        finally:
            tracemalloc.stop()

    peak_10 = measure_peak(10)
    peak_100 = measure_peak(100)
    # With O(n_draws * |C(q)|), 100 draws adds ~15-25 MiB over 10 draws.
    # With O(|C(q)|) loop inversion, peak memory stays virtually flat regardless of n_draws.
    assert peak_100 < peak_10 * 1.5
