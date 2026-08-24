"""Leitura da geometria declarada no ``sbc-template.sty`` canônico.

FONTE ÚNICA DO PADRÃO SBC. As medidas do formato SBC **não** são redeclaradas
no manifesto ``scripts/normas_ufopa.py``: elas já vivem no ``.sty`` publicado
pela Sociedade Brasileira de Computação, em ``texto/comum/sbc/``, e este módulo
as lê de lá.

O motivo é o mesmo que criou o manifesto para as normas da UFOPA, aplicado ao
contrário. Ali o repositório é o dono do fato, porque não existe artefato
oficial em LaTeX. Aqui o artefato oficial existe, e é ele que os congressos
aceitam — copiar `top=3.5cm` para um segundo arquivo criaria dois lugares que
precisariam concordar, e o compilador não alcançaria nenhum dos dois.

Consequência prática: se a SBC publicar uma revisão do `.sty`, basta substituir
o arquivo. Os testes passam a medir contra a geometria nova sem que uma linha de
Python mude.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
STY_SBC = RAIZ / "texto" / "comum" / "sbc" / "sbc-template.sty"

PONTOS_POR_CM = 28.3464567

# \RequirePackage[a4paper,top=3.5cm,left=3cm,right=3cm,bottom=2.5cm]{geometry}
_OPCOES_GEOMETRY = re.compile(r"\\RequirePackage\s*\[([^]]*)\]\s*\{geometry\}")

# \parindent 1.27cm   /   \parskip 6pt
_COMPRIMENTO_SOLTO = re.compile(r"\\(parindent|parskip)\s+([\d.]+)(cm|pt|mm)")

# \renewcommand{\normalsize}{\@setfontsize\normalsize\@xiipt\@xivpt}
_CORPO_NORMALSIZE = re.compile(r"\\@setfontsize\\normalsize\\@(\w+)pt\\@(\w+)pt")

_NUMERAL_ROMANO_TEX = {
    "vi": 6,
    "vii": 7,
    "viii": 8,
    "ix": 9,
    "x": 10,
    "xi": 11,
    "xii": 12,
    "xiii": 13,
    "xiv": 14,
    "xvi": 16,
    "xvii": 17,
    "xx": 20,
}


def _para_cm(valor: str, unidade: str) -> float:
    numero = float(valor)
    if unidade == "cm":
        return numero
    if unidade == "mm":
        return numero / 10
    if unidade == "pt":
        return numero / PONTOS_POR_CM
    raise ValueError(f"unidade '{unidade}' não reconhecida")


@lru_cache(maxsize=1)
def _fonte() -> str:
    if not STY_SBC.is_file():
        raise FileNotFoundError(
            f"{STY_SBC} não existe. É o .sty canônico da SBC e não deve ser "
            "editado nem recriado à mão — reponha o arquivo publicado pela SBC."
        )
    # O arquivo original vem em latin1; só os comentários têm acento.
    return STY_SBC.read_text(encoding="latin-1")


@lru_cache(maxsize=1)
def margens_cm() -> dict[str, float]:
    """Margens declaradas nas opções do ``geometry``, em centímetros."""
    achado = _OPCOES_GEOMETRY.search(_fonte())
    if achado is None:
        raise ValueError(f"{STY_SBC.name} não declara opções de geometry")
    margens: dict[str, float] = {}
    for item in achado.group(1).split(","):
        chave, _, bruto = item.partition("=")
        chave = chave.strip()
        bruto = bruto.strip()
        if not bruto:
            continue
        medida = re.fullmatch(r"([\d.]+)(cm|mm|pt)", bruto)
        if medida:
            margens[chave] = _para_cm(medida.group(1), medida.group(2))
    faltando = {"top", "bottom", "left", "right"} - margens.keys()
    if faltando:
        raise ValueError(f"{STY_SBC.name} não declara as margens {sorted(faltando)}")
    return margens


@lru_cache(maxsize=1)
def papel() -> str:
    """Nome do papel declarado nas opções do ``geometry`` (ex.: ``a4paper``)."""
    achado = _OPCOES_GEOMETRY.search(_fonte())
    if achado is None:
        raise ValueError(f"{STY_SBC.name} não declara opções de geometry")
    for item in achado.group(1).split(","):
        item = item.strip()
        if item.endswith("paper"):
            return item
    raise ValueError(f"{STY_SBC.name} não declara o papel")


@lru_cache(maxsize=1)
def comprimentos_cm() -> dict[str, float]:
    """``parindent`` e ``parskip``, convertidos para centímetros."""
    return {
        nome: _para_cm(valor, unidade)
        for nome, valor, unidade in _COMPRIMENTO_SOLTO.findall(_fonte())
    }


@lru_cache(maxsize=1)
def corpo_e_entrelinha_pt() -> tuple[int, int]:
    """Corpo e entrelinha do ``\\normalsize``, em pontos.

    O ``.sty`` os declara por nome interno do LaTeX (``\\@xiipt``), não por
    número, e é assim que se descobre que o SBC usa 12 pt sobre 14 pt.
    """
    achado = _CORPO_NORMALSIZE.search(_fonte())
    if achado is None:
        raise ValueError(f"{STY_SBC.name} não redefine \\normalsize")
    corpo, entrelinha = achado.groups()
    if corpo not in _NUMERAL_ROMANO_TEX or entrelinha not in _NUMERAL_ROMANO_TEX:
        raise ValueError(f"numeral do TeX não reconhecido: {corpo!r}, {entrelinha!r}")
    return _NUMERAL_ROMANO_TEX[corpo], _NUMERAL_ROMANO_TEX[entrelinha]


def em_pontos(centimetros: float) -> float:
    """Converte centímetros para pontos tipográficos."""
    return centimetros * PONTOS_POR_CM
