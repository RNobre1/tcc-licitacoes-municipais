"""Compila os três layouts em modo limpo e guarda o resultado em `entregas/`.

Modo limpo é o documento sem os marcadores de pendência — eles são bilhete de
trabalho para quem escreve, e não fazem sentido para quem lê o trabalho. O
mecanismo está em `texto/comum/pendencia.sty`: definir `\\ufopalimpo` antes do
documento faz `\\pendente{...}` não imprimir nada.

Há um fonte só, e dois modos de compilá-lo. Gerar a versão apresentável apagando
os marcadores produziria dois fontes a manter, e o segundo envelheceria.

**Por que estes PDFs são versionados**, contrariando a regra geral de não
versionar o que é gerado: eles precisam estar disponíveis para quem não vai
compilar nada. O preço é o risco de envelhecerem em silêncio, e por isso este
script grava a impressão digital de tudo que entra na compilação —
`tests/test_entregas_apresentaveis.py` compara com o estado atual e falha quando
divergem.

    python scripts/gerar_entregas.py
    python scripts/gerar_entregas.py --conferir
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCUMENTO = RAIZ / "texto" / "tcc1"
ENTREGAS = RAIZ / "entregas"
PROCEDENCIA = ENTREGAS / "procedencia.txt"

# Arquivo-alvo do documento → nome com que ele é publicado em entregas/.
# O nome de saída diz o destino, não o arquivo de origem: quem recebe o PDF não
# sabe o que é "main-sbc".
SAIDAS = {
    "main-curso.tex": "tcc1-modelo-do-curso.pdf",
    "main-sbc.tex": "tcc1-formato-sbc.pdf",
    "main.tex": "tcc1-formato-sibi.pdf",
}

# Tudo que entra na composição do PDF. A impressão digital cobre este conjunto,
# e é por isso que mexer numa seção, num estilo ou numa figura invalida as
# entregas. O padrão é por extensão e posição, não por nome de arquivo — o
# arquivo que nascer amanhã já está coberto.
FONTES = (
    ("texto/tcc1/secoes", "*.tex"),
    ("texto/tcc1", "main*.tex"),
    ("texto/tcc1/figuras", "*.pdf"),
    ("texto/comum", "*.sty"),
    ("texto/comum", "*.bib"),
    ("texto/comum/sbc", "*"),
)


def _arquivos_fonte() -> list[Path]:
    achados: list[Path] = []
    for pasta, padrao in FONTES:
        base = RAIZ / pasta
        if base.is_dir():
            achados += [p for p in base.glob(padrao) if p.is_file()]
    return sorted(set(achados))


def impressao_das_fontes() -> str:
    """Resumo de tudo que afeta o PDF, em ordem estável."""
    somador = hashlib.sha256()
    for arquivo in _arquivos_fonte():
        somador.update(arquivo.relative_to(RAIZ).as_posix().encode())
        somador.update(arquivo.read_bytes())
    return somador.hexdigest()


def compilar(alvo: str, saida: str) -> bool:
    """Compila um alvo em modo limpo e move o PDF para entregas/."""
    trabalho = DOCUMENTO / f"limpo-{Path(alvo).stem}"
    resultado = subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            r"-usepretex=\def\ufopalimpo{}",
            f"-jobname={trabalho.name}",
            alvo,
        ],
        cwd=DOCUMENTO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        # O TeX ecoa trechos do documento no encoding da fonte, que não é UTF-8.
        # Sem isto, um acento numa mensagem de erro derruba o script inteiro e
        # esconde justamente o erro que ele ia reportar. Mesma razão do que já
        # está em tests/execucao.py.
        errors="replace",
        check=False,
    )
    produzido = DOCUMENTO / f"{trabalho.name}.pdf"
    if resultado.returncode != 0 or not produzido.is_file():
        print(f"  ! {alvo} não compilou em modo limpo", file=sys.stderr)
        for linha in resultado.stdout.splitlines():
            if linha.startswith("!"):
                print(f"    {linha}", file=sys.stderr)
                break
        return False

    ENTREGAS.mkdir(exist_ok=True)
    shutil.move(str(produzido), ENTREGAS / saida)
    # Os intermediários do modo limpo não interessam a ninguém e confundiriam
    # quem olhar a pasta do documento procurando os do modo normal.
    for lixo in DOCUMENTO.glob(f"{trabalho.name}.*"):
        lixo.unlink()
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--conferir",
        action="store_true",
        help="só informa se as entregas estão atualizadas, sem gerar nada",
    )
    args = p.parse_args(argv)

    atual = impressao_das_fontes()

    if args.conferir:
        registrada = (
            PROCEDENCIA.read_text(encoding="utf-8").strip() if PROCEDENCIA.is_file() else ""
        )
        if registrada == atual:
            print("entregas atualizadas")
            return 0
        print("entregas desatualizadas — rode sem --conferir", file=sys.stderr)
        return 2

    if not shutil.which("latexmk"):
        print("latexmk não encontrado", file=sys.stderr)
        return 1

    falhas = 0
    for alvo, saida in SAIDAS.items():
        if not (DOCUMENTO / alvo).is_file():
            print(f"  {alvo} não existe neste documento — pulado")
            continue
        if compilar(alvo, saida):
            tamanho = (ENTREGAS / saida).stat().st_size // 1024
            print(f"  {saida}  ({tamanho} KB)")
        else:
            falhas += 1

    if falhas:
        print(f"\n{falhas} alvo(s) não gerado(s) — procedência não gravada", file=sys.stderr)
        return 2

    PROCEDENCIA.write_text(atual + "\n", encoding="utf-8")
    print(f"\nprocedência gravada: {atual[:16]}…")
    print(f"entregas em {ENTREGAS.relative_to(RAIZ)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
