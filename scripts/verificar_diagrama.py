"""Verifica a legibilidade geométrica de um diagrama do diagrams.net.

Diagrama desenhado à mão envelhece torto: move-se uma caixa, e uma linha passa a
cruzar outra sem que ninguém perceba. Este verificador transforma em teste o que
normalmente se confere a olho.

O que ele checa, por página:

1. **Caixa fora da página.** O que sai da margem some na exportação.
2. **Caixas sobrepostas.** Duas caixas encavaladas escondem texto.
3. **Trecho diagonal.** Aresta cujos pontos consecutivos não compartilham eixo. O
   roteador do editor inventa o caminho, e caminho inventado não dá para
   verificar.
4. **Linhas se cruzando.** O defeito que mais atrapalha a leitura.
5. **Linha atravessando caixa alheia.** Aresta que passa por dentro de uma caixa
   que não é origem nem destino sugere ligação que não existe.

    python scripts/verificar_diagrama.py docs/arquitetura/arquitetura.drawio
"""

from __future__ import annotations

import argparse
import sys

# Entrada confiável: o arquivo verificado é versionado neste repositório e escrito
# por quem o roda. Não há aqui XML vindo de fora, de rede ou de usuário anônimo.
# Se um dia este verificador passar a ler diagrama de terceiro, trocar por um
# analisador endurecido contra expansão de entidade, que hoje seria dependência
# nova para risco inexistente.
import xml.etree.ElementTree as ET  # noqa: S405
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

# Tolerância em pixels. Fração de ponto de ancoragem produz diferença de
# centésimo de pixel, que o editor arredonda e ninguém enxerga. Tratar isso como
# defeito enche o relatório de ruído e esconde o problema de verdade.
TOLERANCIA = 1.0

Ponto = tuple[float, float]
Caixa = tuple[float, float, float, float]
Segmento = tuple[Ponto, Ponto]


@dataclass
class Pagina:
    nome: str
    fora_da_pagina: list[str] = field(default_factory=list)
    sobrepostas: list[tuple[str, str]] = field(default_factory=list)
    diagonais: list[str] = field(default_factory=list)
    cruzamentos: list[tuple[str, str]] = field(default_factory=list)
    atravessam: list[tuple[str, str]] = field(default_factory=list)

    @property
    def problemas(self) -> int:
        return (
            len(self.fora_da_pagina)
            + len(self.sobrepostas)
            + len(self.diagonais)
            + len(self.cruzamentos)
            + len(self.atravessam)
        )


def _geometria(celula: ET.Element) -> Caixa:
    g = celula.find("mxGeometry")
    if g is None:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        float(g.get("x", 0)),
        float(g.get("y", 0)),
        float(g.get("width", 0)),
        float(g.get("height", 0)),
    )


def _estilo(celula: ET.Element, chave: str, padrao: str) -> str:
    for parte in (celula.get("style") or "").split(";"):
        if parte.startswith(f"{chave}="):
            return parte.split("=", 1)[1]
    return padrao


def _ancora(caixa: Caixa, fx: float, fy: float) -> Ponto:
    x, y, largura, altura = caixa
    return (x + fx * largura, y + fy * altura)


def _trechos(pontos: list[Ponto]) -> list[Segmento]:
    return list(zip(pontos, pontos[1:], strict=False))


def _horizontal(s: Segmento) -> bool:
    return abs(s[0][1] - s[1][1]) <= TOLERANCIA


def _vertical(s: Segmento) -> bool:
    return abs(s[0][0] - s[1][0]) <= TOLERANCIA


def cruzam(a: Segmento, b: Segmento) -> bool:
    """Interseção própria de dois trechos ortogonais.

    Toque nas extremidades não conta: duas arestas que partem do mesmo ponto de
    uma caixa se encontram ali por construção, e isso não atrapalha a leitura.
    """
    ah, bh = _horizontal(a), _horizontal(b)
    if ah == bh:
        return False  # paralelos
    h, v = (a, b) if ah else (b, a)
    hy = h[0][1]
    hx0, hx1 = sorted((h[0][0], h[1][0]))
    vx = v[0][0]
    vy0, vy1 = sorted((v[0][1], v[1][1]))
    return (hx0 + TOLERANCIA < vx < hx1 - TOLERANCIA) and (vy0 + TOLERANCIA < hy < vy1 - TOLERANCIA)


def caminho(celula: ET.Element, origem: Caixa, destino: Caixa) -> list[Ponto]:
    pontos = [
        _ancora(
            origem, float(_estilo(celula, "exitX", "0.5")), float(_estilo(celula, "exitY", "0.5"))
        )
    ]
    g = celula.find("mxGeometry")
    arranjo = g.find("Array") if g is not None else None
    if arranjo is not None:
        pontos += [(float(p.get("x", 0)), float(p.get("y", 0))) for p in arranjo.findall("mxPoint")]
    pontos.append(
        _ancora(
            destino,
            float(_estilo(celula, "entryX", "0.5")),
            float(_estilo(celula, "entryY", "0.5")),
        )
    )
    return pontos


def verificar(xml: str) -> list[Pagina]:
    raiz = ET.fromstring(xml)
    paginas: list[Pagina] = []

    for diagrama in raiz.findall("diagram"):
        modelo = diagrama.find("mxGraphModel")
        if modelo is None:
            continue
        pagina = Pagina(nome=diagrama.get("name", "sem nome"))
        largura = float(modelo.get("pageWidth", 1169))
        altura = float(modelo.get("pageHeight", 826))

        celulas = {c.get("id"): c for c in modelo.findall(".//mxCell") if c.get("id")}
        caixas = {i: _geometria(c) for i, c in celulas.items() if c.get("vertex") == "1"}

        # Fronteiras tracejadas e rótulos soltos existem para conter ou anotar, e
        # se sobrepõem por desenho. Excluí-los é regra, não exceção pontual.
        decorativas = {
            i
            for i, c in celulas.items()
            if (c.get("style") or "").startswith("text;") or "dashed=1" in (c.get("style") or "")
        }

        for i, (x, y, w, h) in caixas.items():
            if x < 0 or y < 0 or x + w > largura or y + h > altura:
                pagina.fora_da_pagina.append(i)

        for a, b in combinations(sorted(set(caixas) - decorativas), 2):
            ax, ay, aw, ah = caixas[a]
            bx, by, bw, bh = caixas[b]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                pagina.sobrepostas.append((a, b))

        caminhos: dict[str, list[Ponto]] = {}
        for i, c in celulas.items():
            if c.get("edge") != "1":
                continue
            origem, destino = caixas.get(c.get("source", "")), caixas.get(c.get("target", ""))
            if not origem or not destino:
                continue
            caminhos[i] = caminho(c, origem, destino)

        for i, pontos in caminhos.items():
            for trecho in _trechos(pontos):
                if not _horizontal(trecho) and not _vertical(trecho):
                    pagina.diagonais.append(i)
                    break

        for a, b in combinations(sorted(caminhos), 2):
            if any(cruzam(sa, sb) for sa in _trechos(caminhos[a]) for sb in _trechos(caminhos[b])):
                pagina.cruzamentos.append((a, b))

        for i, pontos in caminhos.items():
            ligadas = {celulas[i].get("source"), celulas[i].get("target")}
            for trecho in _trechos(pontos):
                (x1, y1), (x2, y2) = trecho
                for j, (bx, by, bw, bh) in caixas.items():
                    if j in ligadas or j in decorativas:
                        continue
                    dentro = (
                        by + TOLERANCIA < y1 < by + bh - TOLERANCIA
                        and min(x1, x2) < bx + bw
                        and bx < max(x1, x2)
                        if _horizontal(trecho)
                        else bx + TOLERANCIA < x1 < bx + bw - TOLERANCIA
                        and min(y1, y2) < by + bh
                        and by < max(y1, y2)
                    )
                    if dentro and (j, i) not in pagina.atravessam:
                        pagina.atravessam.append((i, j))

        paginas.append(pagina)
    return paginas


def relatar(paginas: list[Pagina]) -> int:
    total = 0
    for p in paginas:
        print(f"\n=== {p.nome} ===")
        linhas = [
            ("caixas fora da página", p.fora_da_pagina),
            ("caixas sobrepostas", p.sobrepostas),
            ("trechos diagonais", p.diagonais),
            ("linhas se cruzando", p.cruzamentos),
            ("linha atravessando caixa alheia", p.atravessam),
        ]
        for rotulo, achados in linhas:
            marca = " " if not achados else "!"
            print(f" {marca} {rotulo:34s} {achados if achados else 'nenhum'}")
        total += p.problemas
    print(f"\n{'Tudo limpo.' if total == 0 else f'{total} problemas a resolver.'}")
    return total


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verifica a geometria de um diagrama.")
    p.add_argument("arquivo", type=Path)
    args = p.parse_args(argv)
    if not args.arquivo.is_file():
        print(f"não encontrei: {args.arquivo}", file=sys.stderr)
        return 1
    return 0 if relatar(verificar(args.arquivo.read_text(encoding="utf-8"))) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
