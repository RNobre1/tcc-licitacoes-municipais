"""Tests for parse_quotation_reports management command."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command

SYNTHETIC_TEXT = """
                        PREFEITURA FICTÍCIA DE DEMO
  Relatório de Cotação: COTAÇÃO DEMO

  Item 1: ITEM DEMO
      Preço Estimado: R$ 10,00 (un)  Média dos Preços Obtidos: R$ 10,00
 Quantidade        Descrição
 10 Unidades       DEMO-Item descrição detalhada

Preço (Compras Governamentais) 1: Média das Propostas Finais       R$ 10,00
       CNPJ: 11.111.111/0001-11                                Data: 10/05/2026 09:00
    Órgão: PREFEITURA FICTÍCIA                                 Modalidade: Pregão
Descrição: DEMO-Preço descrição                                Lote/Item: 1/1
       Fonte: https://pncp.gov.br/app/editais/11111111000111/2026/100
"""


def test_parse_quotation_reports_command_writes_json():
    with TemporaryDirectory() as tmp_dir:
        input_dir = Path(tmp_dir) / "input"
        output_dir = Path(tmp_dir) / "output"
        input_dir.mkdir()

        # create a dummy pdf file
        dummy_pdf = input_dir / "105588_Cotacao_DEMO.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 dummy")

        patch_target = (
            "evaluation.management.commands.parse_quotation_reports.extract_pdf_layout_text"
        )
        with patch(patch_target) as mock_extract:
            mock_extract.return_value = SYNTHETIC_TEXT

            call_command(
                "parse_quotation_reports",
                input_dir=str(input_dir),
                output_dir=str(output_dir),
            )

        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 1
        data = json.loads(output_files[0].read_text(encoding="utf-8"))

        assert data["report_id"] == "105588_Cotacao_DEMO"
        assert len(data["items"]) == 1
        assert data["items"][0]["item_number"] == 1
        assert data["items"][0]["chosen_prices"][0]["pncp_key"] == {
            "cnpj": "11111111000111",
            "ano": 2026,
            "sequencial": 100,
            "numero_item": 1,
        }
