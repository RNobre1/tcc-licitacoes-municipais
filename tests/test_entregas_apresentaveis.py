"""Guarda das versões apresentáveis do texto.

`entregas/` guarda os três layouts compilados em **modo limpo**: sem os
marcadores de pendência, que são bilhete de trabalho interno e não fazem sentido
para quem lê o trabalho.

São arquivos gerados, e versioná-los contraria a regra geral do projeto. A razão
de abrir exceção é a mesma das figuras: o PDF precisa estar disponível para
quem não vai compilar nada — a orientadora, a banca, um colega. "Sempre vivo"
foi o pedido, e um arquivo que só existe depois de alguém rodar um comando não
está sempre vivo.

O preço dessa escolha é o risco de o PDF envelhecer em silêncio enquanto o texto
avança. Esta guarda cobre isso por procedência: o script grava a impressão
digital de tudo que entra na compilação, e o teste compara com o estado atual.
Não usa data de modificação, que não sobrevive a um clone.

Regerar com `python scripts/gerar_entregas.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.gerar_entregas import ENTREGAS, PROCEDENCIA, SAIDAS, impressao_das_fontes

RAIZ = Path(__file__).resolve().parent.parent

# O que o marcador de pendência imprime quando está visível. Se este texto
# aparecer numa entrega, o modo limpo não funcionou.
MARCA = "PENDENTE"


def _texto(pdf: Path) -> str:
    return subprocess.run(
        ["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=False
    ).stdout


def test_a_pasta_de_entregas_existe():
    assert ENTREGAS.is_dir(), (
        f"{ENTREGAS.relative_to(RAIZ)} não existe. Gerar com `python scripts/gerar_entregas.py`."
    )


@pytest.mark.parametrize("nome", sorted(SAIDAS.values()))
def test_cada_alvo_tem_sua_entrega(nome: str):
    arquivo = ENTREGAS / nome
    assert arquivo.is_file(), f"{nome} não foi gerado"
    assert arquivo.stat().st_size > 0, f"{nome} está vazio — a compilação falhou"


@pytest.mark.parametrize("nome", sorted(SAIDAS.values()))
def test_nenhuma_entrega_mostra_marcador_de_pendencia(nome: str):
    """O coração desta guarda.

    Uma entrega com bilhete interno visível é pior que entrega nenhuma: passa a
    impressão de descuido justamente no artefato feito para ser lido por outros.
    """
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext não encontrado")
    arquivo = ENTREGAS / nome
    if not arquivo.is_file():
        pytest.skip(f"{nome} não gerado")
    ocorrencias = _texto(arquivo).count(MARCA)
    assert ocorrencias == 0, (
        f"{nome} mostra {ocorrencias} marcador(es) de pendência. O modo limpo "
        "não foi aplicado — conferir o `-usepretex` em scripts/gerar_entregas.py."
    )


@pytest.mark.parametrize("nome", sorted(SAIDAS.values()))
def test_cada_entrega_tem_conteudo_de_verdade(nome: str):
    """Contraprova do teste acima: PDF em branco também não tem marcador.

    Sem isto, uma compilação que produzisse páginas vazias passaria por entrega
    limpa — e o teste anterior daria a impressão de que está tudo bem.
    """
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext não encontrado")
    arquivo = ENTREGAS / nome
    if not arquivo.is_file():
        pytest.skip(f"{nome} não gerado")
    palavras = len(_texto(arquivo).split())
    assert palavras > 2000, (
        f"{nome} tem só {palavras} palavras. Entrega vazia passaria na guarda de "
        "marcador sem ter conteúdo nenhum."
    )


def test_as_entregas_correspondem_ao_texto_em_disco():
    """Texto mexido sem regerar a entrega é acusado aqui."""
    assert PROCEDENCIA.is_file(), (
        f"{PROCEDENCIA.relative_to(RAIZ)} não existe. Sem ele não há como saber "
        "de que versão do texto as entregas saíram — regerar."
    )
    registrada = PROCEDENCIA.read_text(encoding="utf-8").strip()
    atual = impressao_das_fontes()
    assert registrada == atual, (
        "o texto mudou depois que as entregas foram geradas. Os PDFs em "
        "entregas/ mostram a versão antiga. "
        "Regerar com `python scripts/gerar_entregas.py`."
    )


def test_a_impressao_cobre_o_que_afeta_o_pdf():
    """Contraprova da procedência: ela precisa mudar quando o texto muda.

    Uma impressão digital que ignorasse as seções deixaria o teste acima passar
    para sempre, dando a impressão de proteção que não existe.
    """
    secao = RAIZ / "texto" / "tcc1" / "secoes" / "01-introducao.tex"
    original = secao.read_bytes()
    antes = impressao_das_fontes()
    try:
        secao.write_bytes(original + b"\n% toque temporario\n")
        assert impressao_das_fontes() != antes, (
            "a impressão digital não mudou ao alterar uma seção — ela não cobre "
            "o conteúdo do texto, e a guarda de frescor é decorativa."
        )
    finally:
        secao.write_bytes(original)
