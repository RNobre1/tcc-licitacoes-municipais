"""Gera a figura do processo, em TikZ, a partir do modelo BPMN.

Os `.bpmn` de `docs/arquitetura/` são a **fonte**. São XML padrão da OMG,
versionados, e abrem em qualquer ferramenta da notação — inclusive na que a
orientação indicou, para conferência. A figura do texto é derivada deles e
nunca editada à mão.

O QUE ESTE SCRIPT PRODUZ

Um fragmento TikZ por parte, em `texto/tcc1/figuras/`, que o texto inclui com
`\\input`. Não é imagem: é desenho feito pelo próprio compositor do documento.

POR QUE DEIXOU DE SER IMAGEM EXPORTADA

A versão anterior renderizava num navegador controlado por script. Trouxe três
defeitos de uma vez — marca do renderizador no rodapé, fonte dessa marca
embutida como bitmap, e redução da imagem para caber na coluna, que levava o
rótulo a menos de 5 pt. Ver `texto/comum/figura-bpmn.sty`, onde a aparência é
decidida.

Com o desenho em TikZ o texto compila sem navegador nenhum instalado, o que
também era um problema: a dependência quebrou duas vezes por conta da versão
do Chrome que o pacote de renderização esperava.

    python scripts/gerar_bpmn.py
    python scripts/gerar_bpmn.py --conferir   # só informa se está atualizada
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# Entrada confiável: os modelos são versionados neste repositório e gerados por
# `scripts/montar_bpmn.py`. Ver a nota equivalente em verificar_diagrama.py.
import xml.etree.ElementTree as ET  # noqa: S405
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUITETURA = RAIZ / "docs" / "arquitetura"
FIGURAS = RAIZ / "texto" / "tcc1" / "figuras"
PROCEDENCIA = FIGURAS / "procedencia-bpmn.txt"

M = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
D = "{http://www.omg.org/spec/DD/20100524/DI}"

# O processo vem em duas partes. Catorze linhas numa figura só passam de 900 pt
# de altura, e não há página que as comporte.
PARTES = ("1-demanda", "2-precos")

# Estilo TikZ por tipo de elemento. O desenho de cada um está em `_forma`.
ESTILO = {
    f"{M}task": "bpmn tarefa",
    f"{M}exclusiveGateway": "bpmn decisao",
    f"{M}startEvent": "bpmn evento inicial",
    f"{M}endEvent": "bpmn evento final",
}

# Margem interna do texto dentro da caixa da tarefa, de cada lado.
RESPIRO = 6


def modelos() -> list[Path]:
    return [ARQUITETURA / f"processo-licitacao-{s}.bpmn" for s in PARTES]


def figuras() -> list[Path]:
    return [FIGURAS / f"processo-licitacao-{s}.tex" for s in PARTES]


def impressao() -> str:
    """Resumo das duas partes, em ordem estável."""
    somador = hashlib.sha256()
    for modelo in modelos():
        somador.update(modelo.name.encode())
        somador.update(modelo.read_bytes())
    return somador.hexdigest()


def _escapar(texto: str) -> str:
    """O que o TeX leria como comando, e não como texto."""
    for de, para in (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ):
        texto = texto.replace(de, para)
    return texto


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


def _forma(estilo: str, caixa: tuple[float, float, float, float]) -> str:
    """Traço de uma forma da notação, nas coordenadas do modelo.

    O eixo y do BPMN cresce para baixo e o do TikZ para cima; a conversão é
    feita aqui, uma vez, negando o y na emissão.
    """
    x, y, w, h = caixa
    cx, cy = x + w / 2, y + h / 2
    if estilo == "bpmn decisao":
        return (
            f"  \\draw[{estilo}] ({cx:.1f},{-y:.1f}) -- ({x + w:.1f},{-cy:.1f}) -- "
            f"({cx:.1f},{-(y + h):.1f}) -- ({x:.1f},{-cy:.1f}) -- cycle;"
        )
    if estilo.startswith("bpmn evento"):
        return f"  \\draw[{estilo}] ({cx:.1f},{-cy:.1f}) circle[radius={w / 2:.1f}pt];"
    return f"  \\draw[{estilo}] ({x:.1f},{-y:.1f}) rectangle ({x + w:.1f},{-(y + h):.1f});"


def _tikz(xml: str) -> str:
    raiz = ET.fromstring(xml)

    tipos = {
        filho.get("id", ""): filho.tag
        for processo in raiz.iter(f"{M}process")
        for filho in processo
        if filho.tag in ESTILO
    }
    nomes = {
        filho.get("id", ""): filho.get("name", "")
        for pai in raiz.iter()
        for filho in pai
        if filho.get("id")
    }

    plano = raiz.find(f".//{DI}BPMNPlane")
    assert plano is not None, "modelo sem BPMNPlane"

    linhas: list[str] = []
    molduras: list[str] = []
    textos: list[str] = []
    pool: tuple[float, float, float, float] | None = None

    for forma in plano.iter(f"{DI}BPMNShape"):
        ident = forma.get("bpmnElement", "")
        caixa = _limites(forma)
        if caixa is None:
            continue
        x, y, w, h = caixa
        cx, cy = x + w / 2, y + h / 2
        rotulo = _escapar(nomes.get(ident, ""))

        if ident.startswith("pool_"):
            pool = caixa
            # Faixa do nome, à esquerda, com o título deitado. A divisa é a
            # linha vertical; a moldura externa é o retângulo da piscina.
            faixa = x + 22
            molduras.append(
                f"  \\draw[bpmn raia] ({x:.1f},{-y:.1f}) rectangle ({x + w:.1f},{-(y + h):.1f});"
            )
            molduras.append(
                f"  \\draw[bpmn raia] ({faixa:.1f},{-y:.1f}) -- ({faixa:.1f},{-(y + h):.1f});"
            )
            textos.append(
                f"  \\node[bpmn texto, rotate=90, text width={h - 12:.1f}pt] "
                f"at ({x + 11:.1f},{-cy:.1f}) {{{rotulo}}};"
            )
            continue

        if ident.startswith("raia_"):
            # A raia já começa abaixo da faixa de nomes; a faixa é o espaço
            # entre o topo da piscina e o topo da raia. A divisa horizontal
            # fecha essa faixa — sem ela o nome da raia fica solto sobre o
            # desenho, como se fosse rótulo de alguma coisa lá dentro.
            topo_pool = pool[1] if pool else y
            molduras.append(
                f"  \\draw[bpmn raia] ({x:.1f},{-topo_pool:.1f}) "
                f"rectangle ({x + w:.1f},{-(y + h):.1f});"
            )
            molduras.append(f"  \\draw[bpmn raia] ({x:.1f},{-y:.1f}) -- ({x + w:.1f},{-y:.1f});")
            textos.append(
                f"  \\node[bpmn texto, text width={w - 8:.1f}pt] "
                f"at ({cx:.1f},{-(topo_pool + y) / 2:.1f}) {{{rotulo}}};"
            )
            continue

        estilo = ESTILO.get(tipos.get(ident, ""), "bpmn tarefa")
        linhas.append(_forma(estilo, caixa))

        marca = forma.find(f"{DI}BPMNLabel")
        if marca is not None and (fora := _limites(marca)) is not None:
            lx, ly, lw, lh = fora
            textos.append(
                f"  \\node[bpmn texto, text width={lw:.1f}pt] "
                f"at ({lx + lw / 2:.1f},{-(ly + lh / 2):.1f}) {{{rotulo}}};"
            )
        elif rotulo:
            textos.append(
                f"  \\node[bpmn texto, text width={w - 2 * RESPIRO:.1f}pt] "
                f"at ({cx:.1f},{-cy:.1f}) {{{rotulo}}};"
            )

    for aresta in plano.iter(f"{DI}BPMNEdge"):
        ident = aresta.get("bpmnElement", "")
        pontos = [
            (float(p.get("x", 0)), float(p.get("y", 0))) for p in aresta.findall(f"{D}waypoint")
        ]
        if len(pontos) < 2:
            continue
        caminho = " -- ".join(f"({x:.1f},{-y:.1f})" for x, y in pontos)
        linhas.append(f"  \\draw[bpmn ligacao] {caminho};")
        marca = aresta.find(f"{DI}BPMNLabel")
        rotulo = _escapar(nomes.get(ident, ""))
        if rotulo and marca is not None and (fora := _limites(marca)) is not None:
            lx, ly, lw, lh = fora
            textos.append(
                f"  \\node[bpmn texto] at ({lx + lw / 2:.1f},{-(ly + lh / 2):.1f}) {{{rotulo}}};"
            )

    assert pool is not None, "modelo sem piscina"
    px, py, pw, ph = pool
    corpo = "\n".join(molduras + linhas + textos)
    return f"""% GERADO por scripts/gerar_bpmn.py — não editar à mão.
% Fonte: docs/arquitetura/ — regerar depois de mexer no modelo.
% A aparência (traço, ponta de seta, corpo do rótulo) está em
% texto/comum/figura-bpmn.sty, e não aqui.
\\begin{{tikzpicture}}[x=1pt, y=1pt]
  \\useasboundingbox ({px:.1f},{-py:.1f}) rectangle ({px + pw:.1f},{-(py + ph):.1f});
{corpo}
\\end{{tikzpicture}}%
"""


def gerar() -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for modelo, figura in zip(modelos(), figuras(), strict=True):
        figura.write_text(_tikz(modelo.read_text(encoding="utf-8")), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--conferir", action="store_true", help="só informa se está atualizada")
    args = p.parse_args(argv)

    ausentes = [m.name for m in modelos() if not m.is_file()]
    if ausentes:
        print(f"não encontrei: {ausentes}", file=sys.stderr)
        return 1

    atual = impressao()

    if args.conferir:
        registrada = (
            PROCEDENCIA.read_text(encoding="utf-8").strip() if PROCEDENCIA.is_file() else ""
        )
        if registrada == atual and all(f.is_file() for f in figuras()):
            print("figura do processo atualizada")
            return 0
        print("figura do processo desatualizada — rode sem --conferir", file=sys.stderr)
        return 2

    gerar()
    PROCEDENCIA.write_text(atual + "\n", encoding="utf-8")
    for f in figuras():
        print(f"  {f.name}  ({len(f.read_text(encoding='utf-8').splitlines())} linhas)")
    print(f"procedência gravada: {atual[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
