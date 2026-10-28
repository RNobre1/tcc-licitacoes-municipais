"""Guarda dos casos de uso: cobertura dos requisitos e concordância com o diagrama.

POR QUE ESTA GUARDA EXISTE

A orientação pediu, em 24/10/2026, um diagrama geral de casos de uso agora, e
cada caso documentado à medida que for implementado. Três lugares passam a
falar dos mesmos casos: a lista em ``docs/casos-de-uso/README.md``, o diagrama
na página "Casos de uso" de ``docs/arquitetura/arquitetura.drawio`` e, mais
tarde, o texto do TCC.

A lista é a fonte. O diagrama a desenha, e o texto a cita. Sem uma guarda, o
caso de uso novo entra num lugar e falta no outro, e quem lê o diagrama não
sabe que ele está velho.

O que se verifica:

1. **Todo requisito essencial está coberto** por algum caso de uso. Os
   essenciais vêm da especificação, que é a fonte deles, e não do texto: a
   Tabela 5 do texto é uma seleção dela.
2. **Nenhum caso de uso cita requisito que não existe.** É o erro de digitação
   que passaria despercebido no item 1.
3. **O diagrama e a lista têm exatamente os mesmos casos.**

As três são regras, e não listas: o caso de uso e o requisito de amanhã já
entram nelas.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET  # noqa: S405 — arquivo versionado neste repositório
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REQUISITOS = RAIZ / "docs" / "requisitos" / "README.md"
CASOS = RAIZ / "docs" / "casos-de-uso" / "README.md"
DIAGRAMA = RAIZ / "docs" / "arquitetura" / "arquitetura.drawio"
PAGINA = "Casos de uso"

RF = re.compile(r"\bRF\d{2}\b")
UC = re.compile(r"\bUC\d{2}\b")


PRIORIDADES = ("Essencial", "Importante", "Desejável")


def _requisitos() -> dict[str, str]:
    """Código de cada requisito funcional e sua prioridade, lidos da especificação.

    A linha do requisito é reconhecida pela **coluna de prioridade**, e não pelo
    começo do enunciado. A primeira versão desta leitura exigia "O sistema deve"
    e perdia os requisitos escritos do ponto de vista do usuário — "O usuário
    pode editar..." —, que então pareciam não existir. Outras tabelas da
    especificação também começam por um código de requisito, mas terminam em
    texto livre; por isso a prioridade precisa ser uma das três conhecidas.
    """
    padrao = re.compile(r"^\|\s*(RF\d{2})\s*\|.*\|\s*(" + "|".join(PRIORIDADES) + r")\s*\|\s*$")
    prioridades: dict[str, str] = {}
    for linha in REQUISITOS.read_text(encoding="utf-8").splitlines():
        achado = padrao.match(linha)
        if achado:
            prioridades[achado.group(1)] = achado.group(2)
    return prioridades


def _casos() -> dict[str, set[str]]:
    """Cada caso de uso da tabela da lista, com os requisitos que ele cobre."""
    casos: dict[str, set[str]] = {}
    for linha in CASOS.read_text(encoding="utf-8").splitlines():
        achado = re.match(r"^\|\s*(UC\d{2})\s*\|", linha)
        if achado:
            casos[achado.group(1)] = set(RF.findall(linha))
    return casos


def _casos_no_diagrama() -> set[str]:
    raiz = ET.fromstring(DIAGRAMA.read_text(encoding="utf-8"))
    for pagina in raiz.findall("diagram"):
        if pagina.get("name") == PAGINA:
            return {
                codigo
                for celula in pagina.iter("mxCell")
                if "ellipse" in (celula.get("style") or "")
                for codigo in UC.findall(celula.get("value") or "")
            }
    raise AssertionError(f'o diagrama não tem a página "{PAGINA}"')


def test_a_especificacao_tem_requisitos_essenciais():
    """Contraprova: se a leitura da especificação falhar, as guardas abaixo passam no vazio."""
    essenciais = [rf for rf, p in _requisitos().items() if p == "Essencial"]
    assert len(essenciais) >= 20, f"só {len(essenciais)} essenciais lidos — leitura quebrada?"


def test_a_lista_de_casos_de_uso_existe_e_nao_esta_vazia():
    assert CASOS.is_file(), f"{CASOS.relative_to(RAIZ)} não existe"
    assert _casos(), "a lista de casos de uso não tem nenhuma linha UCnn"


def test_todo_requisito_essencial_esta_coberto_por_algum_caso_de_uso():
    essenciais = {rf for rf, p in _requisitos().items() if p == "Essencial"}
    cobertos = set().union(*_casos().values())
    faltando = sorted(essenciais - cobertos)
    assert faltando == [], (
        f"requisito(s) essencial(is) sem caso de uso: {faltando}. Ou o caso de uso "
        "que o atende ainda não foi listado, ou o requisito deixou de ser essencial."
    )


def test_nenhum_caso_de_uso_cita_requisito_inexistente():
    existentes = set(_requisitos())
    inventados = {uc: sorted(rfs - existentes) for uc, rfs in _casos().items() if rfs - existentes}
    assert inventados == {}, f"caso(s) de uso citando requisito que não existe: {inventados}"


def test_o_diagrama_tem_exatamente_os_casos_de_uso_da_lista():
    na_lista, no_diagrama = set(_casos()), _casos_no_diagrama()
    assert no_diagrama == na_lista, (
        f"só na lista: {sorted(na_lista - no_diagrama)}; "
        f"só no diagrama: {sorted(no_diagrama - na_lista)}. "
        "A lista é a fonte: corrija o diagrama."
    )
