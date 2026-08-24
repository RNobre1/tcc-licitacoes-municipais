"""Leitura do PDF compilado: metadados, texto e caixas de palavra.

Extraído de ``test_conformidade_pdf.py`` quando o alvo SBC passou a precisar dos
mesmos utilitários. Duas suítes medindo o mesmo PDF com duas cópias das mesmas
quatro funções seriam a duplicação que o projeto proíbe em qualquer outro lugar.

Nenhuma mudança de comportamento em relação às versões privadas anteriores: as
funções foram movidas, não reescritas.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from tests.execucao import executar


def exige(binario: str) -> None:
    """Pula o teste se o binário não estiver no PATH."""
    if shutil.which(binario) is None:
        pytest.skip(f"'{binario}' não encontrado no PATH")


def texto(pdf: Path) -> str:
    """Texto extraído do PDF, preservando a disposição das colunas."""
    exige("pdftotext")
    return executar(["pdftotext", "-layout", str(pdf), "-"], exigir_sucesso=True).stdout


def info(pdf: Path) -> dict[str, str]:
    """Saída do ``pdfinfo`` como dicionário."""
    exige("pdfinfo")
    saida = executar(["pdfinfo", str(pdf)], exigir_sucesso=True).stdout
    return dict(
        (chave.strip(), valor.strip())
        for chave, _, valor in (linha.partition(":") for linha in saida.splitlines())
        if chave.strip()
    )


def paginas(pdf: Path) -> int:
    """Número de páginas do PDF."""
    return int(info(pdf)["Pages"])


def largura_pt(pdf: Path) -> float:
    """Largura da página em pontos."""
    return float(re.findall(r"[\d.]+", info(pdf)["Page size"])[0])


_ATRIBUTOS_DA_CAIXA = re.compile(
    r'xMin="([\d.]+)"\s+yMin="([\d.]+)"\s+xMax="([\d.]+)"\s+yMax="([\d.]+)"'
)


def caixas_de_palavra(pdf: Path, pagina: int) -> list[tuple[float, float, float, float]]:
    """Coordenadas (x0, y0, x1, y1) de cada palavra de uma página, em pontos.

    A saída de ``pdftotext -bbox`` é XHTML, mas é lida por expressão regular de
    propósito: um parser XML da stdlib sobre conteúdo derivado de PDF abriria
    espaço para XXE e billion-laughs, e a alternativa (defusedxml) seria uma
    dependência só para ler quatro atributos numéricos.
    """
    exige("pdftotext")
    bruto = executar(
        ["pdftotext", "-bbox", "-f", str(pagina), "-l", str(pagina), str(pdf), "-"],
        exigir_sucesso=True,
    ).stdout
    return [
        (float(x0), float(y0), float(x1), float(y1))
        for x0, y0, x1, y1 in _ATRIBUTOS_DA_CAIXA.findall(bruto)
    ]


def texto_da_pagina(pdf: Path, pagina: int) -> str:
    """Texto de uma única página, preservando a disposição."""
    exige("pdftotext")
    return executar(
        ["pdftotext", "-layout", "-f", str(pagina), "-l", str(pagina), str(pdf), "-"],
        exigir_sucesso=True,
    ).stdout


def paginas_antes_das_referencias(pdf: Path) -> list[int]:
    """Páginas do corpo, isto é, anteriores à que abre a lista de referências.

    Existe porque a lista de referências tem regras de recuo próprias — no
    formato SBC o rótulo é pendurado à esquerda da mancha de propósito — e medir
    margem sobre ela mede o estilo da bibliografia, não invasão de conteúdo.

    Se a bibliografia começa no meio de uma página, essa página inteira sai da
    medição. É perda de cobertura aceita: o alternativa seria recortar por
    coordenada vertical, e um título deslocado por uma linha faria o teste medir
    a coisa errada sem avisar.
    """
    total = paginas(pdf)
    titulo = re.compile(r"^\s*Refer[êe]ncias\s*$", re.MULTILINE)
    for n in range(1, total + 1):
        if titulo.search(texto_da_pagina(pdf, n)):
            return list(range(1, n))
    return list(range(1, total + 1))


def compilar(projeto: Path, fonte: str) -> Path:
    """Compila ``fonte`` em ``projeto`` com latexmk e devolve o PDF.

    Falha o teste com os erros do log, não com o traceback do subprocesso — o
    diagnóstico útil está no ``.log`` do TeX, não no código de saída.
    """
    exige("latexmk")
    resultado = executar(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", fonte],
        cwd=projeto,
    )
    caule = Path(fonte).stem
    destino = projeto / f"{caule}.pdf"
    if resultado.returncode != 0 or not destino.is_file():
        log = projeto / f"{caule}.log"
        erros: list[str] = []
        if log.is_file():
            conteudo = log.read_text(encoding="utf-8", errors="replace")
            erros = [linha for linha in conteudo.splitlines() if linha.startswith("!")]
        pytest.fail(
            f"compilação de {projeto.name}/{fonte} falhou.\n"
            + "\n".join(erros[:10] or resultado.stdout.splitlines()[-15:])
        )
    return destino
