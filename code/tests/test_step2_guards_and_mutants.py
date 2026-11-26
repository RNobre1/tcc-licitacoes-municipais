"""Behavioral red tests and mutant-killing tests for Step 2 (N1, N4, N6, N7)."""

import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from evaluation.benchmark import (
    BenchmarkOrchestrator,
    BM25SearchMethod,
    FakeDeterministicEmbeddingModel,
    PublicItemSim,
    SemanticSearchMethod,
    create_dataset_split,
)
from semantic_index.search import ScoredPublicItem


def _write_frozen_eval_fixture(eval_dir):
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
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                    {
                        "item_number": 2,
                        "description": "Papel sulfite A4",
                        "unit": "UNIDADE",
                        "chosen_prices": [{"unit_price": "25.00"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return split.sha256_hash


@pytest.mark.django_db
def test_n1_measurement_reads_tuning_output_checks_hash_and_rejects_mismatched_finalist(
    monkeypatch, tmp_path
):
    from ingestion.models import PublicItem

    eval_dir = tmp_path / "avaliacao"
    split_hash = _write_frozen_eval_fixture(eval_dir)

    public_item = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite A4",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )

    monkeypatch.setattr(
        "semantic_index.search.semantic_search",
        lambda model, query, structured_filter, limit, client=None: [
            ScoredPublicItem(item=public_item, score=0.9)
        ],
    )
    monkeypatch.setattr(
        "pricing.views.get_embedding_model",
        lambda: FakeDeterministicEmbeddingModel(),
    )
    monkeypatch.setattr(
        "evaluation.management.commands.run_benchmark.check_thresholds_note_guard",
        lambda note_path, split_hash=None: "accepted",
    )

    fake_qdrant = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: fake_qdrant)

    # 1. Refuses measurement when benchmark_tuning_results.json is missing
    with pytest.raises(CommandError, match="tuning"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # 2. Refuses measurement when tuning output split_hash mismatches frozen split
    tuning_file = eval_dir / "benchmark_tuning_results.json"
    tuning_file.write_text(
        json.dumps({"split": "tuning", "split_hash": "0" * 64, "finalist": "semantic"}),
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="split_hash"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            finalist="semantic",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # 3. Refuses --finalist when it differs from tuning output's finalist
    tuning_file.write_text(
        json.dumps({"split": "tuning", "split_hash": split_hash, "finalist": "semantic"}),
        encoding="utf-8",
    )
    with pytest.raises(CommandError, match="does not match"):
        call_command(
            "run_benchmark",
            split="measurement",
            thresholds_note="note.md",
            finalist="other_method",
            eval_dir=str(eval_dir),
            pattern="*.report.json",
            allow_real_data=True,
        )

    # 4. Reads finalist from benchmark_tuning_results.json cleanly when --finalist omitted
    out_file = eval_dir / "measurement_out.json"
    call_command(
        "run_benchmark",
        split="measurement",
        thresholds_note="note.md",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(out_file),
        allow_real_data=True,
    )
    measurement_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert measurement_data["finalist"] == "semantic"


@pytest.mark.django_db
def test_n4_fails_on_partial_index_and_records_complete_coverage(monkeypatch):
    from ingestion.models import PublicItem

    indexed_item = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
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
    missing_from_index = PublicItem.objects.create(
        cnpj="22222222000122",
        year=2026,
        purchase_sequence=200,
        item_number=1,
        description="Papel sulfite reciclado",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("24"),
        awarded_unit_price=Decimal("24"),
        secret_budget=False,
        published_on=date(2026, 5, 2),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="22222222000122",
        state="PA",
        modality=6,
        item_kind="product",
    )

    search_called = False

    def fake_semantic_search(model, query, structured_filter, limit, client=None):
        nonlocal search_called
        search_called = True
        return [
            ScoredPublicItem(item=indexed_item, score=0.9),
            ScoredPublicItem(item=missing_from_index, score=0.8),
        ]

    monkeypatch.setattr("semantic_index.search.semantic_search", fake_semantic_search)

    partial_client = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=indexed_item.pk)
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: partial_client)

    items = [
        {
            "item_id": "item_cov",
            "description": "Papel sulfite",
            "ground_truth": {indexed_item.pk},
            "chosen_prices": [Decimal("25")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
    ]
    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)

    with pytest.raises(ValueError, match="coverage"):
        orch.run_benchmark(
            items=items,
            corpus=PublicItem.objects.all(),
            split_name="tuning",
            candidate_methods=[SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())],
            baseline_method=BM25SearchMethod(),
        )
    assert not search_called

    complete_client = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: complete_client)
    results = orch.run_benchmark(
        items=items,
        corpus=PublicItem.objects.all(),
        split_name="tuning",
        candidate_methods=[SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())],
        baseline_method=BM25SearchMethod(),
    )
    assert search_called
    assert results["index_coverage"]["semantic"]["expected_count"] == 2
    assert results["index_coverage"]["semantic"]["present_count"] == 2
    assert results["index_coverage"]["semantic"]["missing_count"] == 0
    assert results["index_coverage"]["semantic"]["coverage_ratio"] == 1.0


def test_n6_refuses_items_without_chosen_price_with_count():
    corpus = [
        PublicItemSim(
            id=1,
            description="Papel Sulfite A4",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
    ]
    items = [
        {
            "item_id": "missing_1",
            "description": "Papel A4",
            "ground_truth": {1},
            "chosen_prices": [],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
        {
            "item_id": "missing_2",
            "description": "Caneta",
            "ground_truth": {1},
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
        {
            "item_id": "valid_1",
            "description": "Papel",
            "ground_truth": {1},
            "chosen_prices": [Decimal("25.0")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        },
    ]
    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    with pytest.raises(ValueError, match="2 item\\(s\\).*chosen price"):
        orch.run_benchmark(
            items=items,
            corpus=corpus,
            split_name="tuning",
            candidate_methods=[SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())],
            baseline_method=BM25SearchMethod(),
        )


@pytest.mark.django_db
def test_n7_real_benchmark_requires_explicit_pattern_and_ignores_other_json(monkeypatch, tmp_path):
    from ingestion.models import PublicItem

    eval_dir = tmp_path / "avaliacao"
    _write_frozen_eval_fixture(eval_dir)
    # Put an unrelated invalid JSON in eval_dir; explicit pattern must ignore it
    (eval_dir / "unrelated_notes.json").write_text('{"note": "ignore me"}', encoding="utf-8")

    # 1. Refuses without --pattern
    with pytest.raises(CommandError, match="--pattern"):
        call_command(
            "run_benchmark",
            split="tuning",
            eval_dir=str(eval_dir),
            allow_real_data=True,
        )

    public_item = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="Papel sulfite A4",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=None,
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="11111111000111",
        state="PA",
        modality=6,
        item_kind="product",
    )
    monkeypatch.setattr(
        "semantic_index.search.semantic_search",
        lambda model, query, structured_filter, limit, client=None: [
            ScoredPublicItem(item=public_item, score=0.9)
        ],
    )
    monkeypatch.setattr(
        "pricing.views.get_embedding_model",
        lambda: FakeDeterministicEmbeddingModel(),
    )
    monkeypatch.setattr(
        "evaluation.management.commands.run_benchmark.check_thresholds_note_guard",
        lambda note_path, split_hash=None: "accepted",
    )
    fake_qdrant = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )
    monkeypatch.setattr("semantic_index.get_qdrant_client", lambda *a, **kw: fake_qdrant)

    out_file = eval_dir / "tuning_out.json"
    call_command(
        "run_benchmark",
        split="tuning",
        eval_dir=str(eval_dir),
        pattern="*.report.json",
        output=str(out_file),
        allow_real_data=True,
    )
    assert out_file.exists()
