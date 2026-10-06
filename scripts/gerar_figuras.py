"""Exporta as páginas do diagrama da arquitetura como figuras do texto.

`docs/arquitetura/arquitetura.drawio` é a **fonte única** dos diagramas. As
figuras em `texto/tcc1/figuras/` são derivadas dele e não se editam à mão.

Versionar as figuras é decisão deliberada, e contraria a regra geral de não
versionar o que é gerado: o texto precisa compilar na máquina de quem avalia,
que não tem o editor instalado. O preço disso é o risco de a figura envelhecer
em silêncio, e é por isso que este script grava, junto das figuras, a impressão
digital do diagrama que as produziu. `tests/test_figuras_do_diagrama.py` compara
as duas e falha quando divergem.

Exige o aplicativo do diagrams.net instalado. No macOS:

    brew install --cask drawio

    python scripts/gerar_figuras.py
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIAGRAMA = RAIZ / "docs" / "arquitetura" / "arquitetura.drawio"
DESTINO = RAIZ / "texto" / "tcc1" / "figuras"
PROCEDENCIA = DESTINO / "procedencia.txt"

# Página do diagrama → nome do arquivo de saída. As páginas do editor são
# numeradas **a partir de 1** desde a versão 27; versões anteriores contavam de
# zero, e o executável avisa quando o índice está fora da faixa.
PAGINAS = {
    1: "arquitetura-nivel1-contexto.pdf",
    2: "arquitetura-nivel2-conteineres.pdf",
    3: "arquitetura-fluxo-processo.pdf",
}


def executavel() -> str | None:
    """Caminho do executável do editor, se houver."""
    achado = shutil.which("drawio")
    if achado:
        return achado
    # O pacote do macOS nem sempre deixa um atalho no caminho de busca.
    interno = Path("/Applications/draw.io.app/Contents/MacOS/draw.io")
    return str(interno) if interno.is_file() else None


def exportar(binario: str, pagina: int, saida: Path) -> bool:
    """Exporta uma página. Devolve se o arquivo foi de fato produzido."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    resultado = subprocess.run(
        [
            binario,
            "--export",
            "--format",
            "pdf",
            "--page-index",
            str(pagina),
            "--crop",
            "--no-sandbox",
            "--output",
            str(saida),
            str(DIAGRAMA),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not saida.is_file() or saida.stat().st_size == 0:
        print(f"  ! página {pagina} não gerou arquivo", file=sys.stderr)
        if resultado.stderr.strip():
            print(f"    {resultado.stderr.strip().splitlines()[0]}", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--conferir",
        action="store_true",
        help="só informa se as figuras estão atualizadas, sem gerar nada",
    )
    args = p.parse_args(argv)

    if not DIAGRAMA.is_file():
        print(f"não encontrei o diagrama: {DIAGRAMA}", file=sys.stderr)
        return 1

    atual = hashlib.sha256(DIAGRAMA.read_bytes()).hexdigest()

    if args.conferir:
        registrada = (
            PROCEDENCIA.read_text(encoding="utf-8").strip() if PROCEDENCIA.is_file() else ""
        )
        if registrada == atual:
            print("figuras atualizadas")
            return 0
        print("figuras desatualizadas — rode sem --conferir", file=sys.stderr)
        return 2

    binario = executavel()
    if not binario:
        print(
            "o aplicativo do diagrams.net não foi encontrado.\n"
            "No macOS: brew install --cask drawio",
            file=sys.stderr,
        )
        return 1

    falhas = 0
    for pagina, nome in PAGINAS.items():
        destino = DESTINO / nome
        if exportar(binario, pagina, destino):
            print(f"  {nome}  ({destino.stat().st_size // 1024} KB)")
        else:
            falhas += 1

    if falhas:
        print(f"\n{falhas} página(s) não exportada(s) — procedência não gravada", file=sys.stderr)
        return 2

    PROCEDENCIA.write_text(atual + "\n", encoding="utf-8")
    print(f"\nprocedência gravada: {atual[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
