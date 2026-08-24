"""Conformidade do PDF compilado com o manifesto de normas da UFOPA.

Compilar sem erro não prova nada sobre formatação: um `.sty` errado compila
perfeitamente e entrega um PDF fora da norma. Estes testes abrem o PDF gerado e
medem o que ele realmente entrega.

São lentos (compilam o documento). Rode só eles com:

    pytest -m lento

E o resto com:

    pytest -m "not lento"
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts import normas_ufopa
from tests import leitura_pdf
from tests.execucao import executar
from tests.leitura_pdffonts import fontes_bitmap, fontes_nao_embutidas

RAIZ = Path(__file__).resolve().parent.parent
DOCUMENTOS = ["tcc1", "tcc2"]
MARCADOR_PENDENTE = "PENDENTE"

pytestmark = pytest.mark.lento


# --- Infraestrutura -----------------------------------------------------------
# A leitura do PDF vive em tests/leitura_pdf.py desde que o alvo SBC passou a
# precisar dos mesmos utilitários. Ver a nota naquele módulo: duas suítes com
# duas cópias das mesmas funções seria a duplicação que o projeto proíbe.

_exige = leitura_pdf.exige
_texto = leitura_pdf.texto
_info = leitura_pdf.info
_caixas_de_palavra = leitura_pdf.caixas_de_palavra


@pytest.fixture(scope="session", params=DOCUMENTOS)
def pdf(request) -> Path:
    """Compila o documento e devolve o caminho do PDF."""
    return leitura_pdf.compilar(RAIZ / "texto" / request.param, "main.tex")


# --- Página -------------------------------------------------------------------


def test_pagina_e_a4(pdf: Path):
    tamanho = _info(pdf)["Page size"]
    largura, altura = (float(n) for n in re.findall(r"[\d.]+", tamanho)[:2])
    assert largura == pytest.approx(595.28, abs=1.0), f"largura fora do A4: {tamanho}"
    assert altura == pytest.approx(841.89, abs=1.0), f"altura fora do A4: {tamanho}"


def test_fonte_do_corpo_e_times(pdf: Path):
    """O guia admite Times ou Arial; o projeto usa Times (via Nimbus Roman)."""
    _exige("pdffonts")
    fontes = executar(["pdffonts", str(pdf)], exigir_sucesso=True).stdout
    assert re.search(r"Times|NimbusRom", fontes, re.IGNORECASE), (
        f"nenhuma fonte Times/Nimbus Roman embutida:\n{fontes}"
    )


def test_todas_as_fontes_estao_embutidas(pdf: Path):
    """PDF de entrega com fonte não embutida troca de tipografia na banca."""
    _exige("pdffonts")
    saida = executar(["pdffonts", str(pdf)], exigir_sucesso=True).stdout
    nao_embutidas = fontes_nao_embutidas(saida)
    assert nao_embutidas == [], f"fontes não embutidas: {nao_embutidas}\n{saida}"


def test_nenhuma_fonte_e_bitmap(pdf: Path):
    """Type 3 é fonte rasterizada: serrilha na tela e na impressão.

    Aparece quando falta a versão vetorial de uma fonte do encoding T1/TS1 e o
    TeX gera bitmap PK no lugar. O PDF continua válido e as fontes continuam
    embutidas — por isso o teste acima não pega.
    """
    _exige("pdffonts")
    saida = executar(["pdffonts", str(pdf)], exigir_sucesso=True).stdout
    bitmap = fontes_bitmap(saida)
    assert bitmap == [], f"fontes rasterizadas: {bitmap} — falta cm-super?\n{saida}"


# --- Margens ------------------------------------------------------------------

# O microtype projeta pontuação para fora da mancha de propósito (protrusão
# óptica): um ponto final no fim da linha ultrapassa a margem em cerca de 2 pt
# em Times 12. Isso é tipografia correta, não violação de norma. A folga existe
# para conviver com ela — o que estes testes precisam pegar é invasão
# estrutural: tabela mais larga que a mancha, figura sem escala, bloco de código
# sem quebra.
FOLGA_PROTRUSAO_PT = 3.0


def test_margem_esquerda_respeita_o_manifesto(pdf: Path):
    """Nenhuma palavra pode invadir os 3 cm da margem esquerda.

    Medido na última página do documento, que é textual em qualquer estágio de
    escrita — a capa e a folha de rosto têm caixas próprias.
    """
    esperado = normas_ufopa.em_pontos(normas_ufopa.valor("margem_esquerda"))
    pagina = int(_info(pdf)["Pages"])
    caixas = _caixas_de_palavra(pdf, pagina)
    if not caixas:
        pytest.skip("última página sem texto extraível")
    menor_x = min(x0 for x0, _, _, _ in caixas)
    assert menor_x >= esperado - FOLGA_PROTRUSAO_PT, (
        f"texto invade a margem esquerda: {menor_x:.1f}pt < {esperado:.1f}pt"
    )


def test_margem_direita_respeita_o_manifesto(pdf: Path):
    esperado = normas_ufopa.em_pontos(normas_ufopa.valor("margem_direita"))
    largura = float(re.findall(r"[\d.]+", _info(pdf)["Page size"])[0])
    limite = largura - esperado
    pagina = int(_info(pdf)["Pages"])
    caixas = _caixas_de_palavra(pdf, pagina)
    if not caixas:
        pytest.skip("última página sem texto extraível")
    maior_x = max(x1 for _, _, x1, _ in caixas)
    assert maior_x <= limite + FOLGA_PROTRUSAO_PT, (
        f"texto invade a margem direita: {maior_x:.1f}pt > {limite:.1f}pt"
    )


# --- Resumo -------------------------------------------------------------------


def _bloco_do_resumo(pdf: Path) -> str | None:
    texto = _texto(pdf)
    achado = re.search(r"\bRESUMO\b(.*?)(?=Palavras-chave\s*:)", texto, re.IGNORECASE | re.DOTALL)
    return achado.group(1) if achado else None


def test_resumo_tem_entre_150_e_500_palavras(pdf: Path):
    bloco = _bloco_do_resumo(pdf)
    if bloco is None:
        pytest.skip("documento ainda não tem resumo")
    if MARCADOR_PENDENTE in bloco.upper():
        pytest.skip("resumo ainda marcado como pendente — escrever antes da entrega")
    palavras = len(bloco.split())
    assert normas_ufopa.RESUMO_MIN_PALAVRAS <= palavras <= normas_ufopa.RESUMO_MAX_PALAVRAS, (
        f"resumo com {palavras} palavras; a NBR 6028 exige entre "
        f"{normas_ufopa.RESUMO_MIN_PALAVRAS} e {normas_ufopa.RESUMO_MAX_PALAVRAS}"
    )


def test_palavras_chave_entre_3_e_5(pdf: Path):
    texto = _texto(pdf)
    achado = re.search(r"Palavras-chave\s*:(.+?)(?:\n\s*\n|$)", texto, re.DOTALL)
    if achado is None:
        pytest.skip("documento ainda não tem palavras-chave")
    bruto = achado.group(1)
    if MARCADOR_PENDENTE in bruto.upper():
        pytest.skip("palavras-chave ainda marcadas como pendentes")
    termos = [t.strip() for t in bruto.replace("\n", " ").strip().rstrip(".").split(";")]
    termos = [t for t in termos if t]
    assert normas_ufopa.PALAVRAS_CHAVE_MIN <= len(termos) <= normas_ufopa.PALAVRAS_CHAVE_MAX, (
        f"{len(termos)} palavras-chave ({termos}); o guia exige entre "
        f"{normas_ufopa.PALAVRAS_CHAVE_MIN} e {normas_ufopa.PALAVRAS_CHAVE_MAX}"
    )


# --- Citações -----------------------------------------------------------------


def test_citacao_no_texto_nao_usa_caixa_alta(pdf: Path):
    """NBR 10520:2023 — '(Canto, 2014)', nunca '(CANTO, 2014)'.

    Regressão do erro clássico de herdar o preâmbulo de trabalhos antigos, que
    usavam abntex2cite[alf] e produziam caixa alta.
    """
    texto = _texto(pdf)
    caixa_alta = re.findall(r"\(([A-ZÀ-Ú]{3,}(?:\s+[A-ZÀ-Ú]{2,})*),\s*\d{4}[a-z]?\)", texto)
    assert caixa_alta == [], (
        f"citações em caixa alta encontradas: {sorted(set(caixa_alta))}. "
        "O guia da UFOPA exige caixa e baixa no texto."
    )
