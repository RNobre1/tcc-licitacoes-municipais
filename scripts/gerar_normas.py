"""Deriva o `.sty` do LaTeX e a documentação a partir do manifesto de normas.

Uso::

    python scripts/gerar_normas.py            # escreve os arquivos
    python scripts/gerar_normas.py --conferir # só verifica se estão atualizados

Os arquivos gerados não devem ser editados à mão: ``tests/test_manifesto.py``
falha se o disco divergir do manifesto.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Permite tanto `python scripts/gerar_normas.py` quanto `python -m scripts.gerar_normas`.
if __package__ in (None, ""):
    sys.path.insert(0, str(RAIZ))

from scripts import normas_ufopa  # noqa: E402

AVISO = "ARQUIVO GERADO — não edite à mão. Fonte: scripts/normas_ufopa.py"


def gerar_sty() -> str:
    """Comprimentos e constantes do LaTeX derivados do manifesto."""
    linhas = [
        f"% {AVISO}",
        f"% Norma: {normas_ufopa.GUIA_CITACAO_ABNT}",
        "",
        "\\NeedsTeXFormat{LaTeX2e}",
        "\\ProvidesPackage{ufopa-normas}[Medidas normativas da UFOPA (gerado)]",
        "",
        "% --- Comprimentos ----------------------------------------------------------",
    ]
    for norma in normas_ufopa.TODAS:
        if norma.macro_latex is None:
            continue
        linhas += [
            f"% {norma.secao_guia} — {norma.justificativa}",
            f"\\newlength{{\\{norma.macro_latex}}}",
            f"\\setlength{{\\{norma.macro_latex}}}{{{norma.valor}}}",
        ]
    linhas += [
        "",
        "% --- Constantes textuais ---------------------------------------------------",
        f"% 3.2.8 Resumo — entre {normas_ufopa.RESUMO_MIN_PALAVRAS} e "
        f"{normas_ufopa.RESUMO_MAX_PALAVRAS} palavras.",
        f"\\newcommand{{\\ufoparesumomin}}{{{normas_ufopa.RESUMO_MIN_PALAVRAS}}}",
        f"\\newcommand{{\\ufoparesumomax}}{{{normas_ufopa.RESUMO_MAX_PALAVRAS}}}",
        f"\\newcommand{{\\ufopapalavraschavemin}}{{{normas_ufopa.PALAVRAS_CHAVE_MIN}}}",
        f"\\newcommand{{\\ufopapalavraschavemax}}{{{normas_ufopa.PALAVRAS_CHAVE_MAX}}}",
        f"\\newcommand{{\\ufopacorpofonte}}{{{normas_ufopa.valor('corpo_fonte_pt')}}}",
        f"\\newcommand{{\\ufopacorpofontemenor}}{{{normas_ufopa.valor('corpo_fonte_menor_pt')}}}",
        "",
        "\\endinput",
        "",
    ]
    return "\n".join(linhas)


def gerar_markdown() -> str:
    """Tabela operacional das normas, para consulta humana."""
    linhas = [
        "# Normas de formatação — UFOPA",
        "",
        f"> {AVISO}",
        "",
        "Destilado operacional do guia oficial da instituição: apenas o que o",
        "template LaTeX precisa obedecer. Para os casos não cobertos aqui",
        "(referências de cada tipo de documento, formas de citação, notas de",
        "rodapé), consulte o guia completo.",
        "",
        f"- **Norma:** {normas_ufopa.GUIA_CITACAO_ABNT}",
        f"- **Cópia local:** [`{normas_ufopa.GUIA_ARQUIVO}`]"
        f"({Path(normas_ufopa.GUIA_ARQUIVO).name})",
        "- **Exemplo de TCC aprovado no curso:** "
        "[`exemplo-tcc-cc-ufopa-2025-rego.pdf`](exemplo-tcc-cc-ufopa-2025-rego.pdf)",
        "",
        "Todo valor abaixo vive em `scripts/normas_ufopa.py` e é verificado no PDF",
        "compilado por `tests/test_conformidade_pdf.py`.",
        "",
    ]
    for grupo, normas in normas_ufopa.GRUPOS.items():
        linhas += [
            f"## {grupo}",
            "",
            "| Item | Valor | Seção do guia | Por quê |",
            "|---|---|---|---|",
        ]
        for norma in normas:
            justificativa = norma.justificativa.replace("\n", " ").replace("|", "\\|")
            linhas.append(
                f"| `{norma.chave}` | {norma.valor} | {norma.secao_guia} | {justificativa} |"
            )
        linhas.append("")
    linhas += [
        "## O que o teste ainda não cobre",
        "",
        "Verificação automática alcança o mensurável no PDF: tamanho da página,",
        "fonte embutida, margens, tamanho do resumo, caixa das citações. O resto",
        "continua sendo leitura atenta antes da entrega:",
        "",
        "- ordem dos elementos pré-textuais e sua paginação;",
        "- ficha catalográfica (solicitada via SIGAA, elaborada por bibliotecário da UFOPA);",
        "- forma de cada referência conforme o tipo de documento;",
        "- citação longa com recuo, espaçamento simples e corpo menor;",
        "- legendas e fontes de ilustrações e tabelas.",
        "",
    ]
    return "\n".join(linhas)


ALVOS: dict[str, Callable[[], str]] = {
    "texto/comum/ufopa-normas.sty": gerar_sty,
    "docs/normas/README.md": gerar_markdown,
}


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--conferir",
        action="store_true",
        help="não escreve; sai com código 1 se algum arquivo estiver desatualizado",
    )
    argumentos = analisador.parse_args(argv)

    desatualizados: list[str] = []
    for destino, gerador in ALVOS.items():
        caminho = RAIZ / destino
        conteudo = gerador()
        atual = caminho.read_text(encoding="utf-8") if caminho.is_file() else None
        if atual == conteudo:
            continue
        if argumentos.conferir:
            desatualizados.append(destino)
            continue
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8")
        print(f"gerado: {destino}")

    if desatualizados:
        print("desatualizados (rode `python scripts/gerar_normas.py`):", file=sys.stderr)
        for destino in desatualizados:
            print(f"  - {destino}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
