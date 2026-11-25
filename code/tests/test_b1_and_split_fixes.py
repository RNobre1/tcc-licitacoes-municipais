"""Tests for B1 leftovers, N3 required pattern, Portuguese properties removal and split force."""

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from evaluation.ground_truth import ResolvedGroundTruthItem
from evaluation.parser import ParseError, parse_quotation_report_text
from tests.test_quotation_report_parser import SYNTHETIC_REPORT_TEXT


def test_parser_fails_on_missing_survey_dates():
    # B1: Missing "Pesquisa realizada entre" must raise ParseError
    text = SYNTHETIC_REPORT_TEXT.replace(
        "Pesquisa realizada entre 01/06/2026 10:00:00 e 15/06/2026 18:00:00", ""
    )
    with pytest.raises(ParseError, match="missing 'Pesquisa realizada entre'"):
        parse_quotation_report_text(text)


def test_parser_fails_when_unit_swallows_description_single_space():
    # B1: Single space separating unit and description must raise ParseError
    text = SYNTHETIC_REPORT_TEXT.replace(
        "100 Pacotes       DEMO-Papel sulfite A4",
        "100 Pacotes DEMO-Papel sulfite A4",
    )
    with pytest.raises(ParseError, match="not separated by column boundary"):
        parse_quotation_report_text(text)


def test_resolved_ground_truth_item_has_no_portuguese_properties():
    # Coordinator: Remove the Portuguese properties ano, sequencial and numero_item
    item = ResolvedGroundTruthItem(
        cnpj="11111111000111",
        year=2026,
        purchase_sequence=100,
        item_number=1,
        found=True,
    )
    assert not hasattr(item, "ano")
    assert not hasattr(item, "sequencial")
    assert not hasattr(item, "numero_item")


def test_generate_dataset_split_refuses_overwrite_without_force():
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()
        split_file = eval_dir / "dataset_split.json"
        split_file.write_text("{}", encoding="utf-8")

        gt_file = eval_dir / "ground_truth_resolved.json"
        gt_file.write_text(
            '{"resolved_items": {"rep1_it1_p1": {"found": true, "item_kind": "product"}}}',
            encoding="utf-8",
        )

        # Refuses to overwrite without --force
        with pytest.raises(CommandError, match="already exists"):
            call_command("generate_dataset_split", eval_dir=str(eval_dir))

        # Overwrites with --force
        stdout = StringIO()
        call_command("generate_dataset_split", eval_dir=str(eval_dir), force=True, stdout=stdout)
        generated = json.loads(split_file.read_text(encoding="utf-8"))
        assert generated != {}
        assert f"SHA-256: {generated['sha256_hash']}" in stdout.getvalue()


def test_commands_require_pattern_argument():
    # N3: --pattern has no default: it becomes a required argument in both commands
    with pytest.raises(CommandError):
        call_command("parse_quotation_reports")

    with pytest.raises(CommandError):
        call_command("resolve_ground_truth")
