"""Tests for resolve_ground_truth management command."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from django.core.management import call_command

from ingestion.models import RawRecord

SYNTHETIC_EVAL_JSON = {
    "report_id": "test_report",
    "title": "DEMO REPORT",
    "items": [
        {
            "item_number": 1,
            "short_description": "DEMO-Item",
            "chosen_prices": [
                {
                    "price_number": 1,
                    "pncp_key": {
                        "cnpj": "11111111000111",
                        "ano": 2026,
                        "sequencial": 100,
                        "numero_item": 1,
                    },
                }
            ],
        }
    ],
}


@pytest.mark.django_db
def test_resolve_ground_truth_command():
    with TemporaryDirectory() as tmp_dir:
        eval_dir = Path(tmp_dir) / "avaliacao"
        eval_dir.mkdir()
        json_file = eval_dir / "test_report.json"
        json_file.write_text(json.dumps(SYNTHETIC_EVAL_JSON), encoding="utf-8")

        mock_record = RawRecord(
            endpoint="/api/pncp/v1/orgaos/11111111000111/compras/2026/100/itens",
            params={"pagina": 1},
            status_code=200,
            payload=[
                {
                    "numeroItem": 1,
                    "descricao": "DEMO Item Desc",
                    "materialOuServico": "M",
                    "unidadeMedida": "UNIDADE",
                    "quantidade": 10.0,
                    "valorUnitarioEstimado": 5.0,
                    "valorUnitarioHomologado": 4.5,
                    "temResultado": True,
                    "orcamentoSigiloso": False,
                }
            ],
        )

        patch_target = "evaluation.management.commands.resolve_ground_truth.resolve_purchase_items"
        with patch(patch_target) as mock_fetch:
            mock_fetch.return_value = [mock_record]

            call_command(
                "resolve_ground_truth",
                eval_dir=str(eval_dir),
                skip_fetch=False,
            )

        gt_file = eval_dir / "ground_truth_resolved.json"
        assert gt_file.exists()
        gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
        assert gt_data["summary"]["resolved_records"] == 1
        assert gt_data["summary"]["failed_records"] == 0
