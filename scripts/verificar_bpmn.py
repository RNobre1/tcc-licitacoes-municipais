"""Verifica a legibilidade geométrica de um modelo BPMN.

Mesma ideia de `verificar_diagrama.py`, aplicada ao outro formato de desenho do
projeto. O que se confere a olho — linha cruzando linha, linha atravessando
caixa — vira teste, porque o modelo vai ser mexido muitas vezes até a defesa e
o estrago não aparece relendo XML.

A função que decide interseção é importada daquele módulo, e não recriada: duas
implementações do mesmo cálculo divergem na primeira correção que só uma delas
receber.

    python scripts/verificar_bpmn.py docs/arquitetura/processo-licitacao.bpmn
"""

from __future__ import annotations

import argparse
import sys

# Entrada confiável: o arquivo é versionado neste repositório e escrito por quem
# o roda. Ver a nota equivalente em verificar_diagrama.py.
import xml.etree.ElementTree as ET  # noqa: S405
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from scripts.verificar_diagrama import TOLERANCIA, Ponto, _horizontal, _trechos, cruzam

DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
D = "{http://www.omg.org/spec/DD/20100524/DI}"

# Caixas que contêm outras por desenho. Excluí-las da checagem de sobreposição é
# regra, não exceção pontual: um elemento sempre fica dentro da sua raia.
CONTINENTES = ("pool_", "raia_")


@dataclass
class Resultado:
    caixas: int = 0
    ligacoes: int = 0
    diagonais: list[str] = field(default_factory=list)
    cruzamentos: list[tuple[str, str]] = field(default_factory=list)
    atravessam: list[tuple[str, str]] = field(default_factory=list)
    sobrepostas: list[tuple[str, str]] = field(default_factory=list)

    @property
    def problemas(self) -> int:
        return (
            len(self.diagonais)
            + len(self.cruzamentos)
            + len(self.atravessam)
            + len(self.sobrepostas)
        )


def _limites(elemento: ET.Element) -> tuple[float, float, float, float] | None:
    alvo = elemento.find(f"{DC}Bounds")
    if alvo is None:
        return None
    return (
        float(alvo.get("x", 0)),
        float(alvo.get("y", 0)),
        float(alvo.get("width", 0)),
        float(alvo.get("height", 0)),
    )


def verificar(xml: str) -> Resultado:
    raiz = ET.fromstring(xml)
    r = Resultado()

    caixas: dict[str, tuple[float, float, float, float]] = {}
    # Rótulo desenhado fora da forma — de evento, de decisão, de ramificação —
    # ocupa área como qualquer caixa, e seta passando por cima dele é tão ruim
    # quanto seta passando por cima de caixa. Entra aqui com o dono anotado,
    # porque a ligação que sai do nó passa perto do rótulo **dele** por
    # construção, e isso não é defeito.
    donos: dict[str, str] = {}

    for forma in raiz.iter(f"{DI}BPMNShape"):
        ident = forma.get("bpmnElement", "")
        limites = _limites(forma)
        if limites is None:
            continue
        caixas[ident] = limites
        donos[ident] = ident
        rotulo = forma.find(f"{DI}BPMNLabel")
        if rotulo is not None and (marca := _limites(rotulo)) is not None:
            caixas[f"rot_{ident}"] = marca
            donos[f"rot_{ident}"] = ident

    caminhos: dict[str, list[Ponto]] = {}
    for aresta in raiz.iter(f"{DI}BPMNEdge"):
        ident = aresta.get("bpmnElement", "")
        pontos = [
            (float(p.get("x", 0)), float(p.get("y", 0))) for p in aresta.findall(f"{D}waypoint")
        ]
        if len(pontos) >= 2:
            caminhos[ident] = pontos
        rotulo = aresta.find(f"{DI}BPMNLabel")
        if rotulo is not None and (marca := _limites(rotulo)) is not None:
            caixas[f"rot_{ident}"] = marca
            donos[f"rot_{ident}"] = ident

    r.caixas, r.ligacoes = len(caixas), len(caminhos)
    desenhaveis = {i: b for i, b in caixas.items() if not donos[i].startswith(CONTINENTES)}

    for a, b in combinations(sorted(desenhaveis), 2):
        ax, ay, aw, ah = desenhaveis[a]
        bx, by, bw, bh = desenhaveis[b]
        if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
            r.sobrepostas.append((a, b))

    for ident, pontos in caminhos.items():
        for trecho in _trechos(pontos):
            (x1, y1), (x2, y2) = trecho
            if abs(x1 - x2) > TOLERANCIA and abs(y1 - y2) > TOLERANCIA:
                r.diagonais.append(ident)
                break

    for a, b in combinations(sorted(caminhos), 2):
        if any(cruzam(sa, sb) for sa in _trechos(caminhos[a]) for sb in _trechos(caminhos[b])):
            r.cruzamentos.append((a, b))

    # Uma ligação pode tocar a caixa que liga; atravessar uma terceira, não.
    for ident, pontos in caminhos.items():
        for trecho in _trechos(pontos):
            (x1, y1), (x2, y2) = trecho
            for alvo, (bx, by, bw, bh) in desenhaveis.items():
                if donos[alvo] in ident:
                    continue
                dentro = (
                    by + TOLERANCIA < y1 < by + bh - TOLERANCIA
                    and min(x1, x2) < bx + bw - TOLERANCIA
                    and bx + TOLERANCIA < max(x1, x2)
                    if _horizontal(trecho)
                    else bx + TOLERANCIA < x1 < bx + bw - TOLERANCIA
                    and min(y1, y2) < by + bh - TOLERANCIA
                    and by + TOLERANCIA < max(y1, y2)
                )
                if dentro and (ident, alvo) not in r.atravessam:
                    r.atravessam.append((ident, alvo))
    return r


def relatar(r: Resultado) -> int:
    print(f"{r.caixas} caixas, {r.ligacoes} ligações")
    for rotulo, achados in (
        ("caixas sobrepostas", r.sobrepostas),
        ("trechos diagonais", r.diagonais),
        ("ligações se cruzando", r.cruzamentos),
        ("ligação atravessando caixa alheia", r.atravessam),
    ):
        marca = " " if not achados else "!"
        print(f" {marca} {rotulo:36s} {achados if achados else 'nenhum'}")
    print("\n" + ("Tudo limpo." if not r.problemas else f"{r.problemas} problemas a resolver."))
    return r.problemas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("arquivo", type=Path)
    a = p.parse_args(argv)
    if not a.arquivo.is_file():
        print(f"não encontrei: {a.arquivo}", file=sys.stderr)
        return 1
    return 0 if relatar(verificar(a.arquivo.read_text(encoding="utf-8"))) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
