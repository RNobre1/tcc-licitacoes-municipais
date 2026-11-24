"""Tests for parsing quotation reports (QuotationReport)."""

from decimal import Decimal
from pathlib import Path

import pytest

from evaluation.parser import (
    extract_pdf_layout_text,
    parse_quotation_report_text,
)


def _pad(left: str, right: str, width: int = 70) -> str:
    space = max(2, width - len(left) - len(right))
    return left + (" " * space) + right


SYNTHETIC_REPORT_TEXT = f"""
                        PREFEITURA FICTÍCIA DE DEMO
                        CNPJ: 00.000.000/0001-99
                        Responsável: SETOR DE LICITAÇÕES
                        Departamento: CPL

  Relatório de Cotação: COTAÇÃO DEMO DE MATERIAIS

  Pesquisa realizada entre 01/06/2026 10:00:00 e 15/06/2026 18:00:00

  Relatório gerado no dia 16/06/2026 09:00:00 (IP: 192.168.1.1)

 Em conformidade com a Instrução Normativa Nº 65 de 07 de Julho de 2021 (Lei nº 14.133).

  Método Matemático Aplicado: Média Aritmética dos preços obtidos

                                                                             Detalhamento dos Itens

  Item 1: DEMO-PAPEL SULFITE A4

      Preço Estimado: R$ 25,50 (un)
      Preço Estimado Calculado: R$ 25,50
      Média dos Preços Obtidos: R$ 25,50

 Quantidade        Descrição                                                Observação

 100 Pacotes       DEMO-Papel sulfite A4 75g/m2 resma com 500 folhas, cor branca.


Preço (Compras Governamentais) 1: Mediana das Propostas Finais       R$ 25,00
Inc. I Art. 5º da IN 65 de 07 de Julho de 2021 (Lei nº 14.133)

{_pad("CNPJ: 11.111.111/0001-11", "Data: 10/05/2026 09:00")}
{_pad("Órgão: PREFEITURA FICTÍCIA ALFA", "Modalidade: Pregão - Eletrônico")}
{_pad("Objeto: DEMO-Aquisição de material", "SRP: SIM")}
{_pad("Descrição: DEMO-Papel sulfite A4 resma 500 fls", "Identificação: 11111111-1-100/2026")}
{_pad("", "Lote/Item: 1/1")}
{_pad("Fonte: https://pncp.gov.br/app/editais/11111111000111/2026/100", "Ata: N/A")}
{_pad("", "Homologação: 15/05/2026 00:00")}
{_pad("", "Quantidade: 50")}
{_pad("", "Unidade: PACOTE")}
{_pad("", "UF: PA")}

  CNPJ                       Razão Social do Fornecedor             Valor da Proposta Final
  99.999.999/0001-99         DEMO FORNECEDOR VENCEDOR LTDA          R$ 25,00
  *VENCEDOR*


Preço (Outros Entes Públicos) 2: Menor Preço                         R$ 26,00
Inc. II Art. 5º da IN 65 de 07 de Julho de 2021 (Lei nº 14.133)

{_pad("CNPJ: 22.222.222/0001-22", "Data: 12/05/2026 14:00")}
{_pad("Órgão: MUNICIPIO FICTÍCIO BETA", "Modalidade: DISPENSA")}
{_pad("Objeto: DEMO-Compra direta material", "SRP: NÃO")}
{_pad("Descrição: DEMO-Papel A4 comum", "Identificação: 998877")}
{_pad("", "Lote/Item: /2")}
{_pad("Fonte: portalexemplo.gov.br/licitacao/123", "Ata: N/A")}
{_pad("", "Homologação: 14/05/2026 00:00")}
{_pad("", "Quantidade: 10")}
{_pad("", "Unidade: PCT")}
{_pad("", "UF: SP")}

  CNPJ                       Razão Social do Fornecedor             Valor da Proposta Final
  88.888.888/0001-88         DEMO FORNECEDOR BETA LTDA              R$ 26,00
  *VENCEDOR*

  Item 2: DEMO-CANETA ESFEROGRÁFICA AZUL

      Preço Estimado: R$ 1,50 (un)
      Preço Estimado Calculado: R$ 1,50
      Média dos Preços Obtidos: R$ 1,50

 Quantidade        Descrição                                                Observação

 500 Unidades      DEMO-Caneta esferográfica ponta média 1.0mm cor azul.


Preço (Compras Governamentais) 1: Média das Propostas Finais         R$ 1,50
Inc. I Art. 5º da IN 65 de 07 de Julho de 2021 (Lei nº 14.133)

{_pad("CNPJ: 33.333.333/0001-33", "Data: 20/05/2026 10:00")}
{_pad("Órgão: PREFEITURA FICTÍCIA GAMA", "Modalidade: Pregão - Eletrônico")}
{_pad("Objeto: DEMO-Material de escritório", "SRP: NÃO")}
{_pad("Descrição: DEMO-Caneta azul 1.0mm", "Identificação: 33333333000133-1-000050/2026")}
{_pad("", "Lote/Item: 1/5")}
{_pad("Fonte: https://pncp.gov.br/app/editais/33333333000133/2026/50", "Ata: N/A")}
{_pad("", "Homologação: 25/05/2026 00:00")}
{_pad("", "Quantidade: 200")}
{_pad("", "Unidade: UNIDADE")}
{_pad("", "UF: AM")}

  CNPJ                       Razão Social do Fornecedor             Valor da Proposta Final
  77.777.777/0001-77         DEMO FORNECEDOR GAMA LTDA              R$ 1,50
  *VENCEDOR*

           Extrato de fontes utilizadas neste relatório
"""


def test_parse_synthetic_quotation_report():
    report = parse_quotation_report_text(SYNTHETIC_REPORT_TEXT, report_id="demo_report")

    assert report.report_id == "demo_report"
    assert report.title == "COTAÇÃO DEMO DE MATERIAIS"
    assert report.survey_start == "01/06/2026 10:00:00"
    assert report.survey_end == "15/06/2026 18:00:00"
    assert len(report.items) == 2

    # Item 1 checks
    item1 = report.items[0]
    assert item1.item_number == 1
    assert item1.short_description == "DEMO-PAPEL SULFITE A4"
    assert "DEMO-Papel sulfite A4 75g/m2" in item1.description
    assert item1.quantity == Decimal("100")
    assert item1.unit == "Pacotes"
    assert item1.estimated_unit_price == Decimal("25.50")
    assert item1.estimation_method == "Média dos Preços Obtidos"
    assert len(item1.chosen_prices) == 2

    # Item 1, Price 1 (with PNCP key)
    p1 = item1.chosen_prices[0]
    assert p1.price_number == 1
    assert p1.source_category == "Compras Governamentais"
    assert p1.calculation_method == "Mediana das Propostas Finais"
    assert p1.unit_price == Decimal("25.00")
    assert p1.agency == "PREFEITURA FICTÍCIA ALFA"
    assert p1.date == "10/05/2026 09:00"
    assert p1.chosen_description == "DEMO-Papel sulfite A4 resma 500 fls"
    assert p1.source == "https://pncp.gov.br/app/editais/11111111000111/2026/100"
    assert p1.pncp_key == {
        "cnpj": "11111111000111",
        "ano": 2026,
        "sequencial": 100,
        "numero_item": 1,
    }
    assert p1.state == "PA"

    # Item 1, Price 2 (without PNCP key)
    p2 = item1.chosen_prices[1]
    assert p2.price_number == 2
    assert p2.source_category == "Outros Entes Públicos"
    assert p2.unit_price == Decimal("26.00")
    assert p2.pncp_key is None
    assert p2.state == "SP"

    # Item 2 checks
    item2 = report.items[1]
    assert item2.item_number == 2
    assert item2.short_description == "DEMO-CANETA ESFEROGRÁFICA AZUL"
    assert item2.quantity == Decimal("500")
    assert item2.unit == "Unidades"
    assert item2.estimated_unit_price == Decimal("1.50")
    assert len(item2.chosen_prices) == 1
    p3 = item2.chosen_prices[0]
    assert p3.pncp_key == {
        "cnpj": "33333333000133",
        "ano": 2026,
        "sequencial": 50,
        "numero_item": 5,
    }
    assert p3.state == "AM"


def test_extract_pdf_layout_text_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_pdf_layout_text(Path("/nonexistent/file.pdf"))
