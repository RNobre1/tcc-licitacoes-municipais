"""Step 2 tests for N1, N2, N3 (mutants), N4, N6, and N7."""

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
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
        lambda model, query, structured_filter, limit, client=None, exact=False: [
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
        json.dumps(
            {
                "split": "tuning",
                "synthetic": False,
                "items_count": 1,
                "split_hash": split_hash,
                "finalist": "semantic",
                "methods": {
                    "bm25": {"metrics": {"recall_at_10": 0.4, "mrr_at_20": 0.3}},
                    "semantic": {"metrics": {"recall_at_10": 0.8, "mrr_at_20": 0.7}},
                },
            }
        ),
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


def test_n2_metamorphic_sentinel_swapping_ground_truth_preserves_method_rankings():
    # N2: Same query, same candidates, ground truth swapped -> identical ranking per method.
    # Catches a mutant that reads item["ground_truth"] directly and adds +0.2 to relevant docs.
    corpus = [
        PublicItemSim(
            id=1,
            description="papel sulfite a4 75g branco",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
        PublicItemSim(
            id=2,
            description="papel sulfite escolar pautado",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
        PublicItemSim(
            id=3,
            description="papel sulfite escolar pautado",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
    ]

    class LexicalSimMethod:
        name = "lexical_cand"

        def rank(self, query, candidates):
            q_words = set(query.lower().split())
            scored = []
            for c in candidates:
                c_words = set(c.description.lower().split())
                score = len(q_words & c_words) / max(len(q_words | c_words), 1)
                scored.append((c, score))
            return sorted(scored, key=lambda pair: (-pair[1], pair[0].id))

    bm25 = BM25SearchMethod(name="bm25")
    semantic = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), name="semantic")
    lexical = LexicalSimMethod()
    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)

    base_item = {
        "item_id": "item_meta",
        "description": "papel sulfite branco",
        "chosen_prices": [Decimal("25.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    res_gt2 = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {2}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[semantic, lexical],
        baseline_method=bm25,
    )
    res_gt3 = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {3}}],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[semantic, lexical],
        baseline_method=bm25,
    )

    for method_name in ["bm25", "semantic", "lexical_cand"]:
        assert (
            res_gt2["ranked_ids_by_method"][method_name]["item_meta"]
            == res_gt3["ranked_ids_by_method"][method_name]["item_meta"]
        )


@pytest.mark.django_db
def test_n2_metamorphic_sentinel_on_public_item_db_corpus(monkeypatch):
    from ingestion.models import PublicItem

    doc_1 = PublicItem.objects.create(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        description="papel sulfite branco",
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
    doc_2 = PublicItem.objects.create(
        cnpj="22222222000122",
        year=2026,
        purchase_sequence=200,
        item_number=1,
        description="papel sulfite pautado",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="22222222000122",
        state="PA",
        modality=6,
        item_kind="product",
    )
    doc_3 = PublicItem.objects.create(
        cnpj="33333333000133",
        year=2026,
        purchase_sequence=300,
        item_number=1,
        description="papel sulfite pautado",
        unit="UNIDADE",
        quantity=Decimal("1"),
        estimated_unit_price=Decimal("25"),
        awarded_unit_price=Decimal("25"),
        secret_budget=False,
        published_on=date(2026, 5, 1),
        agency_name="Prefeitura Fictícia",
        agency_cnpj="33333333000133",
        state="PA",
        modality=6,
        item_kind="product",
    )

    monkeypatch.setattr(
        "semantic_index.search.semantic_search",
        lambda model, query, structured_filter, limit, client=None, exact=False: [
            ScoredPublicItem(item=doc_1, score=0.90),
            ScoredPublicItem(item=doc_2, score=0.75),
            ScoredPublicItem(item=doc_3, score=0.75),
        ],
    )
    fake_qdrant = SimpleNamespace(
        collection_exists=lambda name: True,
        retrieve=lambda collection_name, ids, with_payload=False, with_vectors=False: [
            SimpleNamespace(id=pk) for pk in ids
        ],
    )

    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    base_item = {
        "item_id": "db_meta",
        "description": "papel sulfite branco",
        "chosen_prices": [Decimal("25")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    res_gt2 = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {doc_2.pk}}],
        corpus=PublicItem.objects.all(),
        split_name="tuning",
        candidate_methods=[
            SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), client=fake_qdrant)
        ],
        baseline_method=BM25SearchMethod(),
    )
    res_gt3 = orch.run_benchmark(
        items=[{**base_item, "ground_truth": {doc_3.pk}}],
        corpus=PublicItem.objects.all(),
        split_name="tuning",
        candidate_methods=[
            SemanticSearchMethod(model=FakeDeterministicEmbeddingModel(), client=fake_qdrant)
        ],
        baseline_method=BM25SearchMethod(),
    )

    assert res_gt2["ranked_ids_by_method"]["bm25"] == res_gt3["ranked_ids_by_method"]["bm25"]
    assert (
        res_gt2["ranked_ids_by_method"]["semantic"] == res_gt3["ranked_ids_by_method"]["semantic"]
    )


def test_n3_mutant_top3_price_only_ranks_whole_cq_not_top_n():
    # TOP-3: If price_only ranked only top_n instead of whole C(q), price_only_baseline would be 0.0
    corpus = [
        PublicItemSim(
            id=1,
            description="Papel sulfite A",
            price=Decimal("100.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
        PublicItemSim(
            id=2,
            description="Papel sulfite B",
            price=Decimal("90.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
        PublicItemSim(
            id=99,
            description="Outro item fora top n",
            price=Decimal("25.0"),
            published_on=date(2026, 5, 1),
            modality=6,
        ),
    ]

    class ExplicitTop2:
        name = "explicit"

        def rank(self, query, candidates):
            scores = {1: 0.9, 2: 0.8, 99: 0.1}
            return sorted([(c, scores[c.id]) for c in candidates], key=lambda x: -x[1])

    item = {
        "item_id": "top3_item",
        "description": "Papel sulfite",
        "ground_truth": {99},
        "chosen_prices": [Decimal("25.0")],
        "unit": "UNIDADE",
        "survey_date": date(2026, 6, 1),
    }

    results = BenchmarkOrchestrator(
        n_noise_draws=5, n_bootstrap_resamples=5, seed=42
    ).run_benchmark(
        items=[item],
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[ExplicitTop2()],
        baseline_method=BM25SearchMethod(),
        top_n=2,
    )

    assert results["ranked_ids_by_method"]["explicit"]["top3_item"] == [1, 2]
    assert results["r2"]["price_only_baseline"] == 1.0
    assert results["r2"]["g_sigma"]["0.25"] == -1.0


def test_n3_mutant_orq2b_r1_ci90_contrasts_finalist_against_baseline():
    # ORQ-2b: Only the 90% CI contrasts finalist with itself -> ci_90 would be (0.0, 0.0)
    # and inconclusive gains could turn into false "tie".
    class MatchAlpha:
        name = "alpha_cand"

        def rank(self, query, candidates):
            return sorted(
                [(c, 1.0 if "alpha" in c.description else 0.0) for c in candidates],
                key=lambda x: (-x[1], x[0].id),
            )

    corpus = [
        PublicItemSim(
            id=index,
            description=(
                "alpha" if index in (1, 2) else ("distractor" if index <= 13 else "filler")
            ),
            price=Decimal("10"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for index in range(1, 27)
    ]
    items = [
        {
            "item_id": f"i_{idx}",
            "description": "distractor" if idx in (1, 2) else "unrelated_query",
            "ground_truth": {1 if idx == 1 else (2 if idx == 2 else 26)},
            "chosen_prices": [Decimal("10")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
        for idx in range(1, 11)
    ]

    results = BenchmarkOrchestrator(
        n_noise_draws=1, n_bootstrap_resamples=20, seed=42
    ).run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[MatchAlpha()],
        baseline_method=BM25SearchMethod(),
    )

    ci_90 = results["r1_acceptance"]["ci_90"]
    assert ci_90 != (0.0, 0.0)
    assert ci_90[1] >= 0.08
    assert results["r1_acceptance"]["outcome"] == "inconclusive"


def test_n3_mutant_r2_1_condition_b_uses_sigma_025_not_050():
    # R2-1: Condition (b) uses sigma=0.25 (accepted=True here),
    # whereas sigma=0.50 has sys==po==0.0 (mutant would return accepted=False).
    corpus = [
        PublicItemSim(
            id=1,
            description="highband target",
            price=Decimal("80"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
    ]
    corpus.extend(
        PublicItemSim(
            id=idx,
            description=f"highband distractor {idx}",
            price=Decimal("200"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for idx in range(2, 12)
    )
    corpus.extend(
        PublicItemSim(
            id=idx,
            description=f"bm25match distractor {idx}",
            price=Decimal("100"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
        for idx in range(12, 22)
    )

    class HighBandMethod:
        name = "highband_cand"

        def rank(self, query, candidates):
            return sorted(
                [(c, 0.85 if "highband" in c.description else 0.10) for c in candidates],
                key=lambda x: (-x[1], x[0].id),
            )

    items = [
        {
            "item_id": item_id,
            "description": "bm25match",
            "ground_truth": {1},
            "chosen_prices": [Decimal("100")],
            "unit": "UNIDADE",
            "survey_date": date(2026, 6, 1),
        }
        for item_id in ("r2_4", "r2_5", "r2_13", "r2_16")
    ]

    results = BenchmarkOrchestrator(
        n_noise_draws=1, n_bootstrap_resamples=20, seed=42
    ).run_benchmark(
        items=items,
        corpus=corpus,
        split_name="tuning",
        candidate_methods=[HighBandMethod()],
        baseline_method=BM25SearchMethod(),
        top_n=11,
    )

    assert results["r1_acceptance"]["outcome"] == "accepted"
    assert results["r2"]["easy_items_count"] == 0
    assert results["r2"]["g_sigma"]["0.25"] == 1.0
    assert results["r2"]["g_sigma"]["0.5"] == 0.0
    assert results["r2_acceptance"]["sigma_025_ci"][1] > 0
    assert results["r2_acceptance"]["accepted"] is True


def test_n3_mutant_sv1_missing_survey_date_raises_instead_of_defaulting():
    corpus = [
        PublicItemSim(
            id=1,
            description="Papel sulfite",
            price=Decimal("25"),
            published_on=date(2026, 5, 1),
            modality=6,
        )
    ]
    orch = BenchmarkOrchestrator(n_noise_draws=1, n_bootstrap_resamples=5, seed=42)
    method = SemanticSearchMethod(model=FakeDeterministicEmbeddingModel())

    for bad_item in (
        {"item_id": "no_key", "description": "Papel", "ground_truth": {1}, "chosen_prices": [25]},
        {
            "item_id": "none_val",
            "description": "Papel",
            "ground_truth": {1},
            "chosen_prices": [25],
            "survey_date": None,
        },
    ):
        with pytest.raises(ValueError, match="survey_date"):
            orch.run_benchmark(
                items=[bad_item],
                corpus=corpus,
                split_name="tuning",
                candidate_methods=[method],
                baseline_method=BM25SearchMethod(),
            )


def test_n3_mutant_lk3_real_handler_verifies_split_hash_even_when_note_hash_matches(
    monkeypatch, tmp_path
):
    from django.conf import settings

    repo_root = Path(__file__).resolve().parents[2]
    decision_path = repo_root / "TCC" / "decisões" / "2026-11-24-limiares-de-aceitacao-r1-r2.md"
    frozen_hash_match = re.search(
        r"resumo SHA-256\s+`([0-9a-f]{64})`",
        decision_path.read_text(encoding="utf-8"),
    )
    assert frozen_hash_match is not None
    frozen_hash = frozen_hash_match.group(1)

    project_root = tmp_path / "synthetic-repo"
    decision_copy = project_root / "TCC" / "decisões" / decision_path.name
    decision_copy.parent.mkdir(parents=True)
    decision_copy.write_text(
        f"---\nstatus: aceita\n---\nresumo SHA-256 `{frozen_hash}`\n",
        encoding="utf-8",
    )
    eval_dir = tmp_path / "evaluation"
    eval_dir.mkdir()
    # Tampered tuning_items paired with the valid frozen hash so only verify_split_hash catches it
    (eval_dir / "dataset_split.json").write_text(
        json.dumps(
            {
                "tuning_items": ["tampered_1"],
                "measurement_items": ["tampered_2"],
                "sha256_hash": frozen_hash,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "BASE_DIR", project_root / "code")

    with pytest.raises(CommandError, match="SHA-256 verification"):
        call_command(
            "run_benchmark",
            split="tuning",
            eval_dir=str(eval_dir),
            pattern="*.json",
            allow_real_data=True,
        )


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

    def fake_semantic_search(model, query, structured_filter, limit, client=None, exact=False):
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
        lambda model, query, structured_filter, limit, client=None, exact=False: [
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
