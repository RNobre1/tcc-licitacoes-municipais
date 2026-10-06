"""Gera os entregáveis da especificação de requisitos a partir do markdown.

`docs/requisitos/README.md` é a **fonte única**. Deste script saem o `.docx`
que vai para a orientação — editável, porque é assim que o documento circula no
domínio — e o `.pdf`, na mesma geometria do guia da UFOPA usada no resto do
trabalho.

Nada aqui se edita à mão: mude o markdown e regere.

    python scripts/gerar_requisitos.py

Por que um gerador próprio, e não pandoc: a máquina de trabalho não tem pandoc,
`python-docx` nem LibreOffice, e instalar dependência para converter um
documento é custo permanente por ganho de uma vez. O subconjunto de markdown que
o documento usa é pequeno e está coberto por teste.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "docs" / "requisitos" / "README.md"
SAIDA = RAIZ / "docs" / "requisitos"

# Geometria do guia do SIBI/Ufopa, em twips (1 cm = 566,93 twips).
# Espelha `scripts/normas_ufopa.py`; ver a justificativa lá.
MARGEM_TOPO = 1701  # 3 cm
MARGEM_ESQUERDA = 1701  # 3 cm
MARGEM_DIREITA = 1134  # 2 cm
MARGEM_INFERIOR = 1134  # 2 cm
ENTRELINHA = 360  # 1,5 linha
CORPO = 24  # 12 pt, em meios-pontos

# O documento gerado é entregue sozinho, e é lido por quem não tem acesso ao
# repositório. Por isso nenhum texto emitido aqui pode apontar para caminho de
# arquivo do projeto: o aviso descreve a ausência, não indica onde suprir.
AVISO_DIAGRAMA = "[Diagrama não reproduzido neste formato de saída.]"


# --- Leitura do markdown -----------------------------------------------------


@dataclass
class Bloco:
    tipo: str  # titulo | paragrafo | lista | tabela | citacao | diagrama | regua
    texto: str = ""
    nivel: int = 0
    itens: list[str] = field(default_factory=list)
    cabecalho: list[str] = field(default_factory=list)
    linhas: list[list[str]] = field(default_factory=list)


def _celulas(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def _e_tracejado(linha: str) -> bool:
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", linha.strip())) and "-" in linha


def blocos(markdown: str) -> list[Bloco]:
    """Divide o markdown nos blocos que o documento de requisitos usa."""
    out: list[Bloco] = []
    linhas = markdown.splitlines()
    i = 0
    while i < len(linhas):
        ln = linhas[i]
        crua = ln.strip()

        if not crua:
            i += 1
            continue

        if crua.startswith("```"):
            rotulo = crua.strip("`").strip().lower()
            corpo = []
            i += 1
            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                corpo.append(linhas[i])
                i += 1
            i += 1
            texto = AVISO_DIAGRAMA if rotulo == "mermaid" else "\n".join(corpo)
            out.append(Bloco("diagrama" if rotulo == "mermaid" else "paragrafo", texto))
            continue

        if re.fullmatch(r"-{3,}|_{3,}|\*{3,}", crua):
            out.append(Bloco("regua"))
            i += 1
            continue

        if m := re.match(r"(#{1,6})\s+(.*)", crua):
            out.append(Bloco("titulo", m.group(2).strip(), nivel=len(m.group(1))))
            i += 1
            continue

        if crua.startswith(">"):
            corpo = []
            while i < len(linhas) and linhas[i].strip().startswith(">"):
                corpo.append(linhas[i].strip().lstrip(">").strip())
                i += 1
            out.append(Bloco("citacao", " ".join(x for x in corpo if x)))
            continue

        if crua.startswith("|") and i + 1 < len(linhas) and _e_tracejado(linhas[i + 1]):
            cabecalho = _celulas(crua)
            i += 2
            corpo_tabela = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                corpo_tabela.append(_celulas(linhas[i]))
                i += 1
            out.append(Bloco("tabela", cabecalho=cabecalho, linhas=corpo_tabela))
            continue

        if re.match(r"([-*+]|\d+\.)\s+", crua):
            itens = []
            while i < len(linhas):
                atual = linhas[i]
                if m := re.match(r"\s*(?:[-*+]|\d+\.)\s+(.*)", atual):
                    itens.append(m.group(1).strip())
                    i += 1
                elif atual.strip() and atual.startswith((" ", "\t")) and itens:
                    itens[-1] += " " + atual.strip()  # continuação recuada
                    i += 1
                else:
                    break
            out.append(Bloco("lista", itens=itens))
            continue

        corpo = []
        while i < len(linhas) and linhas[i].strip() and not _inicia_bloco(linhas[i]):
            corpo.append(linhas[i].strip())
            i += 1
        out.append(Bloco("paragrafo", " ".join(corpo)))
    return out


def _inicia_bloco(linha: str) -> bool:
    c = linha.strip()
    return (
        c.startswith(("#", ">", "|", "```"))
        or bool(re.match(r"([-*+]|\d+\.)\s+", c))
        or bool(re.fullmatch(r"-{3,}|_{3,}|\*{3,}", c))
    )


def trechos(texto: str) -> list[tuple[str, set[str]]]:
    """Quebra a marcação inline em pares de (texto, estilos)."""
    out: list[tuple[str, set[str]]] = []
    padrao = re.compile(r"\*\*(.+?)\*\*|`(.+?)`|\[(.+?)\]\((?:.+?)\)")
    pos = 0
    for m in padrao.finditer(texto):
        if m.start() > pos:
            out.append((texto[pos : m.start()], set()))
        if m.group(1) is not None:
            out.append((m.group(1), {"negrito"}))
        elif m.group(2) is not None:
            out.append((m.group(2), {"mono"}))
        else:
            out.append((m.group(3), set()))
        pos = m.end()
    if pos < len(texto):
        out.append((texto[pos:], set()))
    return [(t, e) for t, e in out if t]


# --- Saída .docx -------------------------------------------------------------


def _xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _corrida(texto: str, estilos: set[str], *, tamanho: int = CORPO) -> str:
    props = [
        f'<w:rFonts w:ascii="{"Courier New" if "mono" in estilos else "Times New Roman"}" '
        f'w:hAnsi="{"Courier New" if "mono" in estilos else "Times New Roman"}"/>'
    ]
    if "negrito" in estilos:
        props.append("<w:b/>")
    props.append(f'<w:sz w:val="{tamanho - 4 if "mono" in estilos else tamanho}"/>')
    return (
        f'<w:r><w:rPr>{"".join(props)}</w:rPr><w:t xml:space="preserve">{_xml(texto)}</w:t></w:r>'
    )


def _paragrafo(
    texto: str,
    *,
    estilos: set[str] | None = None,
    alinhamento: str = "both",
    recuo: int = 0,
    espaco_antes: int = 0,
    tamanho: int = CORPO,
    entrelinha: int = ENTRELINHA,
) -> str:
    pr = (
        f'<w:pPr><w:jc w:val="{alinhamento}"/>'
        f'<w:spacing w:line="{entrelinha}" w:lineRule="auto"'
        f' w:before="{espaco_antes}" w:after="60"/>'
        f'<w:ind w:left="{recuo}"/></w:pPr>'
    )
    corridas = "".join(
        _corrida(t, e | (estilos or set()), tamanho=tamanho) for t, e in trechos(texto)
    )
    return f"<w:p>{pr}{corridas or _corrida('', set())}</w:p>"


def _celula(texto: str, *, negrito: bool = False) -> str:
    p = _paragrafo(
        texto,
        estilos={"negrito"} if negrito else set(),
        alinhamento="left",
        tamanho=20,
        entrelinha=240,
    )
    return f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>{p}</w:tc>'


def _tabela(b: Bloco) -> str:
    bordas = "".join(
        f'<w:{lado} w:val="single" w:sz="4" w:color="999999"/>'
        for lado in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    props = (
        f'<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{bordas}</w:tblBorders>'
        f'<w:tblLayout w:type="autofit"/></w:tblPr>'
    )
    linhas = ["<w:tr>" + "".join(_celula(c, negrito=True) for c in b.cabecalho) + "</w:tr>"]
    for linha in b.linhas:
        completa = list(linha) + [""] * (len(b.cabecalho) - len(linha))
        linhas.append(
            "<w:tr>" + "".join(_celula(c) for c in completa[: len(b.cabecalho)]) + "</w:tr>"
        )
    return f"<w:tbl>{props}{''.join(linhas)}</w:tbl>"


_TAMANHO_TITULO = {1: 32, 2: 28, 3: 24, 4: 22, 5: 22, 6: 22}


def _corpo_docx(bs: list[Bloco]) -> str:
    partes = []
    for b in bs:
        if b.tipo == "titulo":
            partes.append(
                _paragrafo(
                    b.texto,
                    estilos={"negrito"},
                    alinhamento="left",
                    espaco_antes=280 if b.nivel <= 2 else 200,
                    tamanho=_TAMANHO_TITULO.get(b.nivel, CORPO),
                    entrelinha=240,
                )
            )
        elif b.tipo == "tabela":
            partes.append(_tabela(b))
            partes.append(_paragrafo(""))
        elif b.tipo == "lista":
            partes.extend(_paragrafo(f"•  {x}", recuo=340) for x in b.itens)
        elif b.tipo == "citacao":
            partes.append(_paragrafo(b.texto, recuo=680, tamanho=22))
        elif b.tipo == "diagrama":
            partes.append(_paragrafo(b.texto, alinhamento="center", tamanho=20))
        elif b.tipo == "regua":
            partes.append(_paragrafo(""))
        else:
            partes.append(_paragrafo(b.texto))
    return "".join(partes)


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package'
    '.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.styles+xml"/></Types>'
)

_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
)

_DOC_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/styles" Target="styles.xml"/></Relationships>'
)

_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:docDefaults><w:rPrDefault><w:rPr>"
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    f'<w:sz w:val="{CORPO}"/><w:lang w:val="pt-BR"/>'
    "</w:rPr></w:rPrDefault></w:docDefaults></w:styles>"
)


def escrever_docx(bs: list[Bloco], destino: Path) -> Path:
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{_corpo_docx(bs)}"
        f'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        f'<w:pgMar w:top="{MARGEM_TOPO}" w:right="{MARGEM_DIREITA}" '
        f'w:bottom="{MARGEM_INFERIOR}" w:left="{MARGEM_ESQUERDA}" '
        f'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/document.xml", documento)
    return destino


# --- Saída .tex --------------------------------------------------------------

_RESERVADOS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


# Símbolos acima do Latin-1 que o `inputenc` com T1 não resolve sozinho. A
# guarda de varredura em `nao_mapeados` é que faz esta tabela envelhecer bem:
# ela é regra, não lista, e acusa o próximo símbolo em vez de deixá-lo quebrar a
# compilação lá na frente.
_SIMBOLOS = {
    "—": "---",  # travessão
    "–": "--",  # meia-risca
    "↔": r"$\leftrightarrow$",
    "→": r"$\rightarrow$",
    "←": r"$\leftarrow$",
    "≥": r"$\geq$",
    "≤": r"$\leq$",
    "×": r"$\times$",
    "…": r"\ldots{}",
    "•": r"\textbullet{}",
    "▣": r"[X]",
    "☐": r"[ ]",
    "✓": r"[v]",
    "“": "``",
    "”": "''",
    "‘": "`",
    "’": "'",
}


def _tex(s: str) -> str:
    return "".join(_SIMBOLOS.get(c) or _RESERVADOS.get(c, c) for c in s)


def nao_mapeados(tex: str) -> set[str]:
    """Caracteres do .tex que o pdflatex desta configuração não sabe compor.

    Regra, e não lista de arquivos conhecidos: qualquer símbolo acima do
    Latin-1 que sobreviva à conversão é acusado aqui, inclusive um que só
    apareça amanhã.
    """
    return {c for c in tex if ord(c) > 0xFF}


def _tex_inline(texto: str) -> str:
    out = []
    for t, estilos in trechos(texto):
        e = _tex(t)
        if "negrito" in estilos:
            e = rf"\textbf{{{e}}}"
        elif "mono" in estilos:
            e = rf"\texttt{{\small {e}}}"
        out.append(e)
    return "".join(out)


_SECAO = {
    1: "section",
    2: "section",
    3: "subsection",
    4: "subsubsection",
    5: "paragraph",
    6: "paragraph",
}


def escrever_tex(bs: list[Bloco]) -> str:
    corpo = []
    for b in bs:
        if b.tipo == "titulo":
            if b.nivel == 1:
                corpo.append(
                    rf"\begin{{center}}\Large\textbf{{{_tex_inline(b.texto)}}}\end{{center}}"
                )
                corpo.append(r"\vspace{1em}")
            else:
                corpo.append(rf"\{_SECAO[b.nivel]}*{{{_tex_inline(b.texto)}}}")
        elif b.tipo == "tabela":
            n = len(b.cabecalho)
            larguras = "|" + "|".join([f"p{{{0.92 / n:.3f}\\textwidth}}"] * n) + "|"
            linhas = [
                " & ".join(rf"\textbf{{{_tex_inline(c)}}}" for c in b.cabecalho) + r" \\ \hline"
            ]
            for linha in b.linhas:
                completa = list(linha) + [""] * (n - len(linha))
                linhas.append(" & ".join(_tex_inline(c) for c in completa[:n]) + r" \\ \hline")
            corpo.append(
                r"\begin{center}\footnotesize"
                + f"\n\\begin{{longtable}}{{{larguras}}}\n\\hline\n"
                + "\n".join(linhas)
                + "\n\\end{longtable}\n"
                + r"\end{center}"
            )
        elif b.tipo == "lista":
            itens = "\n".join(rf"  \item {_tex_inline(x)}" for x in b.itens)
            corpo.append("\\begin{itemize}\n" + itens + "\n\\end{itemize}")
        elif b.tipo == "citacao":
            corpo.append(r"\begin{quote}\small " + _tex_inline(b.texto) + r"\end{quote}")
        elif b.tipo == "diagrama":
            corpo.append(r"\begin{center}\small\textit{" + _tex_inline(b.texto) + r"}\end{center}")
        elif b.tipo == "regua":
            corpo.append(r"\vspace{0.6em}\hrule\vspace{0.6em}")
        else:
            corpo.append(_tex_inline(b.texto))
    preambulo = r"""\documentclass[12pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage{mathptmx}
\usepackage[top=3cm,left=3cm,right=2cm,bottom=2cm]{geometry}
\usepackage{longtable}
\usepackage{array}
\usepackage{setspace}
% Sem \usepackage{parskip}: ele nao esta no TinyTeX desta maquina, e as duas
% linhas abaixo fazem o mesmo: paragrafo sem recuo, separado por espaco.
% Evitar dependencia que precisa ser instalada mantem o gerador reprodutivel.
% Comentario em ASCII de proposito: a guarda `nao_mapeados` varre o .tex
% inteiro, e simbolo fora do Latin-1 aqui a faria acusar o proprio preambulo.
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
\onehalfspacing
\sloppy
\setlength{\LTpre}{0.5em}\setlength{\LTpost}{0.5em}
\begin{document}
"""
    return preambulo + "\n\n".join(corpo) + "\n\\end{document}\n"


def compilar_pdf(bs: list[Bloco], diretorio: Path) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)
    tex = diretorio / "requisitos.tex"
    tex.write_text(escrever_tex(bs), encoding="utf-8")
    for _ in range(2):  # duas passadas: longtable precisa da segunda
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
            cwd=diretorio,
            capture_output=True,
            check=False,
        )
    pdf = diretorio / "requisitos.pdf"
    if not pdf.is_file():
        registro = diretorio / "requisitos.log"
        cauda = registro.read_text(errors="replace")[-2500:] if registro.is_file() else "(sem log)"
        raise RuntimeError(f"pdflatex não produziu o PDF. Fim do log:\n{cauda}")
    return pdf


# --- Linha de comando --------------------------------------------------------


def _relativo(caminho: Path) -> str:
    try:
        return str(caminho.relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera .docx e PDF a partir de um markdown.")
    p.add_argument("--fonte", type=Path, default=FONTE, help="markdown de origem")
    p.add_argument("--saida", type=Path, default=SAIDA, help="diretório de destino")
    p.add_argument("--sem-pdf", action="store_true", help="emite só o .docx")
    args = p.parse_args(argv)

    if not args.fonte.is_file():
        print(f"não encontrei a fonte: {args.fonte}", file=sys.stderr)
        return 1

    nome = args.fonte.stem
    if nome.lower() == "readme":  # o documento vive num diretório que o nomeia
        nome = args.fonte.parent.name
    bs = blocos(args.fonte.read_text(encoding="utf-8"))

    docx = escrever_docx(bs, args.saida / f"{nome}.docx")
    print(f"escrito {_relativo(docx)} ({docx.stat().st_size // 1024} KiB)")

    if args.sem_pdf:
        return 0
    if not shutil.which("pdflatex"):
        print("pdflatex ausente: PDF não gerado")
        return 0

    temporario = args.saida / "_build"
    pdf = compilar_pdf(bs, temporario)
    destino = args.saida / f"{nome}.pdf"
    shutil.move(str(pdf), destino)
    shutil.rmtree(temporario, ignore_errors=True)
    print(f"escrito {_relativo(destino)} ({destino.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
