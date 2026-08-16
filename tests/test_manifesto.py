"""Guarda de frescor do manifesto de normas.

O `.sty` e a documentação das normas são GERADOS a partir de
``scripts/normas_ufopa.py``. Documento gerado sem teste que compare disco ×
código é pior que documento escrito à mão: os dois envelhecem igual, mas o
gerado carrega um selo de procedência que faz quem lê confiar mais.

Estes testes falham quando alguém edita o arquivo gerado à mão ou altera o
manifesto sem regerar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import gerar_normas, normas_ufopa

RAIZ = Path(__file__).resolve().parent.parent


# --- Integridade do próprio manifesto ----------------------------------------


def test_toda_norma_declara_secao_do_guia():
    """Sem seção do guia, o valor é folclore — não entra no manifesto."""
    sem_secao = [n.chave for n in normas_ufopa.TODAS if not n.secao_guia.strip()]
    assert sem_secao == [], f"normas sem seção do guia: {sem_secao}"


def test_toda_norma_declara_justificativa():
    sem_justificativa = [n.chave for n in normas_ufopa.TODAS if not n.justificativa.strip()]
    assert sem_justificativa == [], f"normas sem justificativa: {sem_justificativa}"


def test_chaves_sao_unicas():
    chaves = [n.chave for n in normas_ufopa.TODAS]
    duplicadas = {c for c in chaves if chaves.count(c) > 1}
    assert duplicadas == set(), f"chaves duplicadas no manifesto: {duplicadas}"


def test_por_chave_erra_alto_para_chave_inexistente():
    with pytest.raises(KeyError, match="não existe no manifesto"):
        normas_ufopa.por_chave("margem_inventada")


def test_guia_internalizado_existe_no_repositorio():
    """A procedência tem que estar no disco, não só na citação."""
    assert (RAIZ / normas_ufopa.GUIA_ARQUIVO).is_file(), (
        f"guia normativo ausente: {normas_ufopa.GUIA_ARQUIVO}"
    )


# --- Conversão de medidas -----------------------------------------------------


def test_em_pontos_converte_centimetros():
    assert normas_ufopa.em_pontos("3cm") == pytest.approx(85.04, abs=0.01)
    assert normas_ufopa.em_pontos("2cm") == pytest.approx(56.69, abs=0.01)


def test_em_pontos_recusa_unidade_desconhecida():
    with pytest.raises(ValueError, match="não está em cm"):
        normas_ufopa.em_pontos("12pt")


# --- Guarda de frescor: disco == gerado --------------------------------------


@pytest.mark.parametrize(
    ("destino", "gerador"),
    [
        ("texto/comum/ufopa-normas.sty", gerar_normas.gerar_sty),
        ("docs/normas/README.md", gerar_normas.gerar_markdown),
    ],
)
def test_arquivo_gerado_esta_atualizado(destino: str, gerador):
    """Falha quando o disco diverge do manifesto.

    A guarda é regra, não lista: ``gerar_normas.ALVOS`` é a única fonte dos
    pares (arquivo, gerador), e este teste varre essa estrutura.
    """
    caminho = RAIZ / destino
    assert caminho.is_file(), (
        f"arquivo gerado ausente: {destino}. Rode `python scripts/gerar_normas.py`."
    )
    assert caminho.read_text(encoding="utf-8") == gerador(), (
        f"{destino} divergiu do manifesto. "
        "Não edite o arquivo gerado: ajuste scripts/normas_ufopa.py e rode "
        "`python scripts/gerar_normas.py`."
    )


def test_a_varredura_cobre_todos_os_alvos_do_gerador():
    """O ponto que nascer amanhã tem que cair na guarda automaticamente."""
    cobertos = {"texto/comum/ufopa-normas.sty", "docs/normas/README.md"}
    declarados = set(gerar_normas.ALVOS)
    assert declarados == cobertos, (
        "gerar_normas.ALVOS mudou; acrescente o novo alvo à parametrização de "
        "test_arquivo_gerado_esta_atualizado"
    )
