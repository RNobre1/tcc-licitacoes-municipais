"""Conformidade do alvo de layout do curso com o modelo cedido pela orientação.

Há uma diferença de natureza entre este teste e o do alvo da SBC, e ela precisa
estar clara para quem ler uma falha aqui.

O alvo da SBC é conferido contra o ``.sty`` **publicado** pela SBC: há
especificação normativa, e o teste compara a nossa geometria com a dela. Já o
modelo do curso chegou apenas como **PDF**, sem arquivo de estilo. Não existe
especificação para comparar — existe um documento impresso, do qual se mede.

Por isso o que se verifica aqui é **semelhança ao modelo dentro de uma
tolerância**, e não conformidade a uma norma. Uma falha significa que o alvo se
afastou do modelo, não que violou uma regra: pode ser defeito nosso, ou pode ser
que o modelo tenha sido substituído por outro. As duas hipóteses merecem olhar
antes de mexer no ``.sty``.

A tolerância é de meio centímetro nas margens. Medição sobre PDF carrega o erro
de quem mede régua em papel: a caixa de uma palavra não coincide com a margem
tipográfica, porque depende da letra que começa e termina a linha.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.medir_geometria_pdf import PONTO_POR_CM, medir
from tests.execucao import executar

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "docs" / "normas" / "exemplo-tcc-savio-artigo.pdf"
NOSSO = RAIZ / "texto" / "tcc1" / "main-curso.pdf"
FONTE = RAIZ / "texto" / "tcc1" / "main-curso.tex"

# Meio centímetro. Ver o cabeçalho para o porquê de não ser mais apertado.
TOLERANCIA_CM = 0.5


def _cm(pontos: float) -> float:
    return pontos / PONTO_POR_CM


@pytest.fixture(scope="module")
def medidas() -> tuple[dict[str, float], dict[str, float]]:
    if not MODELO.is_file():
        pytest.skip(
            f"{MODELO.relative_to(RAIZ)} não está nesta máquina. É trabalho de "
            "terceiro, mantido fora do versionamento pela política do projeto."
        )
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext não encontrado")
    if not NOSSO.is_file():
        pytest.skip(f"{NOSSO.relative_to(RAIZ)} não compilado — rode `make pdf-curso`")
    return medir(MODELO, 3, 14), medir(NOSSO, 2, 8)


def test_o_alvo_do_curso_existe():
    assert FONTE.is_file(), (
        f"{FONTE.relative_to(RAIZ)} não existe. O alvo do curso é um dos três "
        "layouts do mesmo conteúdo."
    )


def test_o_alvo_do_curso_usa_as_mesmas_secoes_dos_outros():
    """Conteúdo é único: três layouts, uma fonte de texto.

    Guarda contra a tentação de copiar seções para o alvo novo em vez de incluí-las.
    """
    import re

    entradas = re.compile(r"\\input\{(secoes/[^}]+)\}")
    curso = entradas.findall(FONTE.read_text(encoding="utf-8"))
    sibi = entradas.findall((RAIZ / "texto" / "tcc1" / "main.tex").read_text(encoding="utf-8"))
    assert curso, "o alvo do curso não inclui nenhuma seção"
    assert curso == sibi, (
        f"o alvo do curso e o do SIBI incluem seções diferentes:\n  curso: {curso}\n  SIBI : {sibi}"
    )


def test_o_alvo_do_curso_compila():
    if not shutil.which("latexmk"):
        pytest.skip("latexmk não encontrado")
    resultado = executar(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main-curso.tex"],
        cwd=RAIZ / "texto" / "tcc1",
    )
    assert resultado.returncode == 0, "o alvo do curso não compila"
    assert NOSSO.is_file()


@pytest.mark.lento
@pytest.mark.parametrize("margem", ["esquerda", "direita", "topo"])
def test_margens_proximas_do_modelo(
    medidas: tuple[dict[str, float], dict[str, float]], margem: str
):
    """A margem inferior fica fora: o rodapé institucional do modelo a desloca."""
    modelo, nosso = medidas
    diferenca = abs(_cm(modelo[margem]) - _cm(nosso[margem]))
    assert diferenca <= TOLERANCIA_CM, (
        f"margem {margem}: modelo {_cm(modelo[margem]):.2f} cm, "
        f"nosso {_cm(nosso[margem]):.2f} cm, diferença {diferenca:.2f} cm "
        f"acima da tolerância de {TOLERANCIA_CM} cm"
    )


@pytest.mark.lento
def test_entrelinha_proxima_do_modelo(medidas: tuple[dict[str, float], dict[str, float]]):
    """Entrelinha muda o número de páginas mais que qualquer margem."""
    modelo, nosso = medidas
    diferenca = abs(modelo["entrelinha"] - nosso["entrelinha"])
    assert diferenca <= 2.0, (
        f"entrelinha: modelo {modelo['entrelinha']:.1f} pt, "
        f"nosso {nosso['entrelinha']:.1f} pt, diferença {diferenca:.1f} pt"
    )


@pytest.mark.lento
def test_corpo_de_letra_proximo_do_modelo(medidas: tuple[dict[str, float], dict[str, float]]):
    modelo, nosso = medidas
    diferenca = abs(modelo["altura_letra"] - nosso["altura_letra"])
    assert diferenca <= 1.5, (
        f"altura de letra: modelo {modelo['altura_letra']:.2f} pt, "
        f"nosso {nosso['altura_letra']:.2f} pt"
    )
