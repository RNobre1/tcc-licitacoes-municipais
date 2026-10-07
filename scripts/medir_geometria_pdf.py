"""Mede a geometria de página de um PDF a partir das caixas do texto.

Usado para inferir o layout de um documento-modelo do qual não existe arquivo de
estilo publicado. É o caso do modelo do curso, cedido pela orientação apenas como
PDF — ao contrário do padrão da SBC, cujo `.sty` canônico é distribuído e pode
ser lido diretamente.

A diferença importa e está registrada aqui de propósito: o que este script produz
é **medição inferida**, com a imprecisão de quem mede régua sobre papel impresso,
e não a especificação normativa. Toda medida daqui carrega essa ressalva.

Método: `pdftotext -bbox` devolve a caixa de cada palavra. A margem é o extremo
alcançado pelo corpo do texto, descartando cabeçalho e rodapé, que ficam fora da
mancha. A entrelinha sai da diferença entre topos de linhas consecutivas, pela
mediana — média seria puxada pelo espaço entre parágrafos e entre seções.

    python scripts/medir_geometria_pdf.py docs/normas/exemplo.pdf
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# Um ponto tipográfico é 1/72 de polegada; um centímetro, 1/2,54.
PONTO_POR_CM = 72 / 2.54


@dataclass
class Caixa:
    pagina: int
    x0: float
    y0: float
    x1: float
    y1: float


def caixas(pdf: Path, primeira: int, ultima: int) -> list[Caixa]:
    saida = subprocess.run(
        ["pdftotext", "-bbox", "-f", str(primeira), "-l", str(ultima), str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    achadas: list[Caixa] = []
    pagina = 0
    for linha in saida.splitlines():
        if "<page" in linha:
            pagina += 1
        m = re.search(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', linha
        )
        if m:
            achadas.append(Caixa(pagina, *(float(g) for g in m.groups())))
    return achadas


def _moda_arredondada(valores: list[float], casa: float = 0.5) -> float:
    """Valor mais frequente, agrupado em faixas — o texto nunca alinha ao exato."""
    contagem = Counter(round(v / casa) * casa for v in valores)
    return contagem.most_common(1)[0][0]


def medir(pdf: Path, primeira: int, ultima: int) -> dict[str, float]:
    todas = caixas(pdf, primeira, ultima)
    if not todas:
        raise SystemExit("nenhuma palavra extraída — o PDF é imagem?")

    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    tam = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info)
    largura, altura = (float(tam.group(1)), float(tam.group(2))) if tam else (595.0, 842.0)

    # Cabeçalho e rodapé ficam fora da mancha: descarta o que está nas bordas
    # verticais extremas, que é onde numeração e endereço institucional moram.
    corpo = [c for c in todas if 0.08 * altura < c.y0 < 0.92 * altura]

    esquerda = _moda_arredondada([c.x0 for c in corpo])
    direita = largura - _moda_arredondada([c.x1 for c in corpo])
    topo = min(c.y0 for c in corpo)
    base = altura - max(c.y1 for c in corpo)

    # Entrelinha: diferença entre topos de linhas vizinhas, pela mediana.
    linhas: dict[int, list[Caixa]] = {}
    for c in corpo:
        linhas.setdefault(c.pagina, []).append(c)
    saltos: list[float] = []
    for caixas_da_pagina in linhas.values():
        topos = sorted({round(c.y0, 1) for c in caixas_da_pagina})
        saltos += [b - a for a, b in zip(topos, topos[1:], strict=False) if 0 < b - a < 40]
    entrelinha = statistics.median(saltos) if saltos else 0.0

    # Altura de letra: a mais frequente entre as caixas do corpo.
    alturas = [c.y1 - c.y0 for c in corpo]
    altura_letra = _moda_arredondada(alturas, 0.25)

    return {
        "largura": largura,
        "altura": altura,
        "esquerda": esquerda,
        "direita": direita,
        "topo": topo,
        "base": base,
        "entrelinha": entrelinha,
        "altura_letra": altura_letra,
        "palavras": len(todas),
        "corpo": len(corpo),
    }


def relatar(m: dict[str, float]) -> None:
    def cm(p: float) -> str:
        return f"{p / PONTO_POR_CM:.2f} cm"

    print(f"página .................. {m['largura']:.0f} x {m['altura']:.0f} pt")
    print(f"palavras lidas .......... {m['palavras']:.0f} ({m['corpo']:.0f} no corpo)")
    print()
    print("margens, medidas pelo extremo do corpo do texto:")
    for nome in ("esquerda", "direita", "topo", "base"):
        print(f"  {nome:<12} {m[nome]:>7.1f} pt   {cm(m[nome]):>9}")
    print()
    print(f"entrelinha (mediana) .... {m['entrelinha']:.1f} pt")
    print(f"altura de letra ......... {m['altura_letra']:.2f} pt")
    if m["altura_letra"]:
        print(f"entrelinha / altura ..... {m['entrelinha'] / m['altura_letra']:.2f}")
    print()
    print("Medição INFERIDA do PDF, não especificação normativa.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pdf", type=Path)
    p.add_argument("--de", type=int, default=3, help="primeira página (pula capa)")
    p.add_argument("--ate", type=int, default=12)
    a = p.parse_args(argv)
    if not a.pdf.is_file():
        print(f"não encontrei: {a.pdf}", file=sys.stderr)
        return 1
    relatar(medir(a.pdf, a.de, a.ate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
