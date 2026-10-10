"""Guarda contra sintaxe de Markdown escrita dentro do LaTeX.

Este repositório tem muito markdown — especificação, arquitetura, backlog, notas
do vault — e o texto do trabalho é LaTeX. Escrever `**assim**` num `.tex` é o
deslize natural de quem passou a manhã no outro formato.

O que torna o deslize perigoso é que **nada reclama**. O LaTeX não conhece `**`,
então imprime os asteriscos como texto. O documento compila, nenhum aviso
aparece, e os asteriscos chegam ao PDF que vai para a orientadora. Aconteceu em
07/10/2026, na seção de sistemas em operação: cinco ocorrências, todas visíveis
no PDF entregue.

A guarda cobre o que é inequívoco. `**` e `__` delimitando texto não existem em
LaTeX nenhum; título com `#` e lista com `- ` no começo da linha também não.
Fora daqui ficam `_` solto, que é subscrito legítimo em matemática, e a crase,
que em LaTeX abre aspas.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

ARQUIVOS = sorted(
    [*(RAIZ / "texto").glob("*/secoes/*.tex"), *(RAIZ / "texto").glob("*/capitulos/*.tex")]
)

# Cada padrão vem com o que deveria ter sido escrito, porque a mensagem de falha
# precisa dizer o conserto, não só o defeito.
PADROES = (
    (re.compile(r"\*\*[^*\n]+\*\*"), "negrito de markdown", r"\textbf{...}"),
    (re.compile(r"(?<![\\_])__[^_\n]+__"), "negrito de markdown", r"\textbf{...}"),
    (re.compile(r"^#{1,6}\s+\S", re.M), "título de markdown", r"\section{...}"),
    (re.compile(r"^\s*[-*]\s+\S", re.M), "lista de markdown", "ambiente itemize"),
)


def test_ha_texto_para_verificar():
    """Contraprova: guarda que varre o vazio passa sempre."""
    assert ARQUIVOS, "nenhum arquivo de texto encontrado — a varredura é vazia"


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda p: p.name)
def test_nenhuma_sintaxe_de_markdown_no_latex(arquivo: Path):
    achados: list[str] = []
    for linha_n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
        if linha.lstrip().startswith("%"):
            continue  # comentário de LaTeX não vai para o PDF
        for padrao, nome, conserto in PADROES:
            if padrao.search(linha):
                achados.append(f"linha {linha_n}: {nome} — usar {conserto}")
    assert achados == [], (
        f"{arquivo.relative_to(RAIZ)} tem sintaxe de markdown:\n  "
        + "\n  ".join(achados)
        + "\nO LaTeX imprime esses caracteres como texto, sem avisar."
    )


def test_a_guarda_reconhece_o_que_procura():
    """Contraprova dos padrões: sem isto, eles poderiam não casar com nada."""
    amostras = {
        "texto **em negrito** aqui": True,
        "texto __em negrito__ aqui": True,
        "# Título": True,
        "- item de lista": True,
        r"texto \textbf{em negrito} aqui": False,
        r"\section{Título}": False,
        r"  \item item de lista": False,
        r"$x_1$ e $y_{ij}$": False,
        r"aspas ``assim''": False,
    }
    for amostra, deve_casar in amostras.items():
        casou = any(p.search(amostra) for p, _, _ in PADROES)
        assert casou == deve_casar, f"{amostra!r}: esperado {deve_casar}, obtido {casou}"
