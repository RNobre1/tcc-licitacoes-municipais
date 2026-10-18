"""Gera a figura do processo a partir do modelo BPMN.

`docs/arquitetura/processo-licitacao.bpmn` é a **fonte única**. É XML padrão da
OMG, versionado, e abre em qualquer ferramenta BPMN 2.0 — inclusive na que a
orientação indicou, para conferência. A figura do texto é derivada dele e nunca
editada à mão.

POR QUE NÃO A FERRAMENTA INDICADA PELA ORIENTAÇÃO

Ela não roda no sistema da máquina de trabalho: a página do produto declara que
o sistema não é suportado. Além disso grava em formato próprio, que não é
versionável de forma útil — um binário muda inteiro a cada gravação.

O caminho adotado preserva o que a orientação quis: o modelo é BPMN 2.0 padrão,
e a ferramenta dela **abre o arquivo** para revisão. O que muda é só onde se
edita.

DEPENDÊNCIA, E A ARMADILHA DELA

A renderização usa `bpmn-to-image`, do mesmo projeto que mantém o editor de
BPMN em navegador. Ele roda sobre um Chrome controlado por Puppeteer.

A armadilha: a versão de Chrome que o pacote pede por padrão pode não ser a que
está instalada, e a mensagem de erro fala em biblioteca dinâmica ausente, não em
versão errada. Por isso este script **localiza** o Chrome instalado e o informa
por variável de ambiente, em vez de deixar o pacote escolher.

    npx puppeteer browsers install chrome
    python scripts/gerar_bpmn.py
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "docs" / "arquitetura" / "processo-licitacao.bpmn"
FIGURA = RAIZ / "texto" / "tcc1" / "figuras" / "processo-licitacao.pdf"
PROCEDENCIA = RAIZ / "texto" / "tcc1" / "figuras" / "procedencia-bpmn.txt"

CACHE_CHROME = Path.home() / ".cache" / "puppeteer" / "chrome"


def chrome() -> str | None:
    """Caminho de um Chrome instalado e íntegro.

    Percorre o cache do Puppeteer da versão mais recente para a mais antiga e
    devolve a primeira que de fato tenha o binário — uma instalação
    interrompida deixa a pasta mas não o executável, e é esse caso que a
    mensagem de erro do pacote não explica.
    """
    if not CACHE_CHROME.is_dir():
        return shutil.which("google-chrome") or shutil.which("chromium")
    for pasta in sorted(CACHE_CHROME.iterdir(), reverse=True):
        for padrao in (
            "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/*",
            "chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/*",
            "chrome-linux64/chrome",
        ):
            achados = [p for p in pasta.glob(padrao) if p.is_file() and os.access(p, os.X_OK)]
            if achados:
                return str(achados[0])
    return None


def impressao() -> str:
    return hashlib.sha256(MODELO.read_bytes()).hexdigest()


def gerar() -> bool:
    binario = chrome()
    if not binario:
        print(
            "nenhum Chrome encontrado para a renderização.\n"
            "Instalar com: npx puppeteer browsers install chrome",
            file=sys.stderr,
        )
        return False

    FIGURA.parent.mkdir(parents=True, exist_ok=True)
    ambiente = {**os.environ, "PUPPETEER_EXECUTABLE_PATH": binario}
    resultado = subprocess.run(
        [
            "npx",
            "--yes",
            "bpmn-to-image@latest",
            # As duas opções, e não só uma: `--no-footer` sozinho deixa o nome do
            # arquivo impresso no rodapé, e ele é desenhado com a fonte do
            # sistema, que o Chrome embute como Type 3 — bitmap. A guarda de
            # fontes do projeto acusa isso, e com razão: Type 3 serrilha na
            # impressão. Com as duas, restam apenas fontes vetoriais.
            "--no-title",
            "--no-footer",
            f"{MODELO.relative_to(RAIZ)}:{FIGURA.relative_to(RAIZ)}",
        ],
        cwd=RAIZ,
        env=ambiente,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if not FIGURA.is_file() or FIGURA.stat().st_size == 0:
        print("a renderização não produziu arquivo", file=sys.stderr)
        for linha in (resultado.stderr or "").splitlines()[:3]:
            print(f"  {linha}", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--conferir", action="store_true", help="só informa se está atualizada")
    args = p.parse_args(argv)

    if not MODELO.is_file():
        print(f"não encontrei o modelo: {MODELO}", file=sys.stderr)
        return 1

    atual = impressao()

    if args.conferir:
        registrada = (
            PROCEDENCIA.read_text(encoding="utf-8").strip() if PROCEDENCIA.is_file() else ""
        )
        if registrada == atual:
            print("figura do processo atualizada")
            return 0
        print("figura do processo desatualizada — rode sem --conferir", file=sys.stderr)
        return 2

    if not gerar():
        return 2

    PROCEDENCIA.write_text(atual + "\n", encoding="utf-8")
    print(f"  {FIGURA.name}  ({FIGURA.stat().st_size // 1024} KB)")
    print(f"procedência gravada: {atual[:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
