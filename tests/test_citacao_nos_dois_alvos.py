"""Guarda sobre comandos de citação em conteúdo compartilhado.

O conteúdo de cada documento vive uma vez só, em ``secoes/`` ou ``capitulos/``, e
é incluído por **dois** alvos de layout com motores de bibliografia diferentes:

- o alvo do SIBI usa ``biblatex``, que oferece ``\\cite`` e ``\\textcite``;
- o alvo da SBC usa ``bibtex`` clássico com o ``sbc.bst``, que oferece ``\\cite``
  e mais nada.

Um comando que existe só em um dos dois compila num alvo e aborta no outro. O
defeito é assimétrico e por isso escapa: quem compila só o alvo que funciona não
vê nada, e o erro aparece horas depois, em outra máquina ou na véspera da
entrega. Aconteceu em 06/10/2026 com ``\\textcite``.

A guarda é regra e não lista: ela varre o conteúdo compartilhado, extrai **todo**
comando que pareça de citação, e exige que cada um esteja definido nos dois
pacotes. Um comando novo, inventado amanhã, já nasce coberto.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
COMUM = RAIZ / "texto" / "comum"

# Pacotes de estilo, um por alvo de layout. Lidos com os arquivos que cada um
# puxa, porque um comando pode ser definido em dependência e não no pacote raiz.
ALVOS = {
    "SIBI (biblatex)": [COMUM / "ufopa-tcc.sty"],
    "SBC (bibtex)": [COMUM / "sbc-tcc.sty", COMUM / "sbc" / "sbc-template.sty"],
}

# Comandos que o LaTeX ou o pacote de bibliografia já garantem nos dois motores.
# `\cite` é o único universal: existe no núcleo do LaTeX.
UNIVERSAIS = {"cite"}

CONTEUDO = sorted(
    [*(RAIZ / "texto").glob("*/secoes/*.tex"), *(RAIZ / "texto").glob("*/capitulos/*.tex")]
)

# Qualquer macro cujo nome contenha "cite" é candidata a comando de citação.
# Pega \textcite, \citeonline, \citep, \parencite e o que vier depois.
CITACAO = re.compile(r"\\([A-Za-z]*cite[A-Za-z]*)\s*[\[{]")


def _definidos(arquivos: list[Path]) -> set[str]:
    """Comandos definidos por um conjunto de pacotes."""
    nomes: set[str] = set()
    for arquivo in arquivos:
        if not arquivo.is_file():
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        nomes |= set(
            re.findall(
                r"\\(?:new|renew|provide)command\*?\s*\{?\\([A-Za-z@]+)", texto
            )
        )
    return nomes


def _usados() -> dict[str, list[str]]:
    """Comandos de citação usados no conteúdo, com os arquivos onde aparecem."""
    achados: dict[str, list[str]] = {}
    for arquivo in CONTEUDO:
        texto = arquivo.read_text(encoding="utf-8")
        for nome in CITACAO.findall(texto):
            achados.setdefault(nome, []).append(arquivo.relative_to(RAIZ).as_posix())
    return achados


def test_ha_conteudo_compartilhado_para_verificar():
    """Contraprova: guarda que varre o vazio passa sempre e não protege nada."""
    assert CONTEUDO, "nenhum arquivo de conteúdo encontrado — a varredura é vazia"


@pytest.mark.parametrize("alvo", sorted(ALVOS))
def test_todo_comando_de_citacao_existe_nos_dois_alvos(alvo: str):
    """Cada comando de citação do conteúdo precisa existir no pacote de cada alvo.

    Falha nomeia o comando e o arquivo, porque a correção é escolher entre
    definir o comando no alvo que não o tem ou trocá-lo por um que ambos tenham.
    """
    definidos = _definidos(ALVOS[alvo]) | UNIVERSAIS
    faltando = {
        nome: arquivos for nome, arquivos in _usados().items() if nome not in definidos
    }
    assert faltando == {}, (
        f"comando(s) de citação ausente(s) no alvo {alvo}: "
        + "; ".join(
            f"\\{nome} em {', '.join(sorted(set(arqs)))}" for nome, arqs in faltando.items()
        )
        + ". Conteúdo é compartilhado pelos dois alvos: o que só existe em um "
        "aborta a compilação do outro."
    )


def test_a_guarda_reconhece_comando_de_citacao():
    """Contraprova do extrator: se ele não achasse nada, o teste acima passaria sempre."""
    amostra = r"Texto \cite{a} e \textcite{b} e \citeonline[p. 3]{c} e \naoehcitacao{d}."
    assert set(CITACAO.findall(amostra)) == {"cite", "textcite", "citeonline"}


def test_a_guarda_reconhece_definicao_de_comando():
    """Contraprova do leitor de definições, pelas três formas que o LaTeX admite."""
    arquivo = COMUM / "ufopa-tcc.sty"
    assert arquivo.is_file()
    assert _definidos([arquivo]), "nenhuma definição lida do pacote do SIBI"
