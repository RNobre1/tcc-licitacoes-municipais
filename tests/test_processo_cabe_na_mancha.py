"""O modelo de processo tem de caber na mancha de texto, em retrato e sem reduzir.

POR QUE ESTA GUARDA EXISTE

A primeira versão da figura foi desenhada com raias horizontais e fluxo da
esquerda para a direita. Catorze etapas nessa disposição produzem um desenho de
mais de 1500 pt de largura. Encaixá-lo numa coluna de 427 pt exige reduzir a
figura a 28% do tamanho, e a 28% o rótulo de 9 pt vira 2,5 pt: ilegível. A saída
adotada na ocasião foi girar a página para paisagem, e ela foi recusada — gira a
numeração, gira o cabeçalho e quebra a leitura do documento.

A correção não é de diagramação da página, é de desenho do modelo: o processo é
longo, e processo longo ocupa o eixo longo da página. As raias viram colunas e o
fluxo desce. A guarda abaixo é o que impede a volta do defeito, porque o sintoma
só aparece no PDF compilado, depois de muitas etapas.

O limite vem medido dos três alvos, e não arbitrado:

    sbc-tcc    426,79 x 674,33 pt   <- o mais estreito, e portanto o que manda
    curso-tcc  443,86 x 711,32 pt
    ufopa-tcc  455,24 x 702,78 pt

A figura entra em tamanho natural, sem `width=`, exatamente para que nenhuma
redução aconteça em silêncio. Por isso o que se verifica aqui é o tamanho do
modelo, e não o da imagem: é ele que determina o corpo do rótulo no papel.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET  # noqa: S405 — arquivo versionado neste repositório
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
D = "{http://www.omg.org/spec/DD/20100524/DI}"

# Mancha do alvo mais estreito, menos uma folga de 7 pt para a borda do desenho
# não encostar na margem.
LARGURA_MAX = 420.0

# Altura útil de uma figura de página inteira no alvo mais baixo: 674 pt de
# mancha menos a legenda, a linha de fonte e o respiro do flutuante. Medido com
# folga, porque legenda de duas linhas é o caso comum aqui.
ALTURA_MAX = 580.0


def _modelos() -> list[Path]:
    from scripts.gerar_bpmn import modelos

    return modelos()


def _extensao(xml: str) -> tuple[float, float]:
    """Largura e altura ocupadas pelo desenho, caixas e ligações incluídas.

    As ligações entram na conta porque um desvio roteado por fora da última
    raia aumenta o desenho sem mexer em caixa nenhuma — e é justamente esse
    caso que passaria despercebido medindo só as caixas.
    """
    raiz = ET.fromstring(xml)
    xs: list[float] = []
    ys: list[float] = []
    for forma in raiz.iter(f"{DI}BPMNShape"):
        limites = forma.find(f"{DC}Bounds")
        if limites is None:
            continue
        x, y = float(limites.get("x", 0)), float(limites.get("y", 0))
        xs += [x, x + float(limites.get("width", 0))]
        ys += [y, y + float(limites.get("height", 0))]
    for aresta in raiz.iter(f"{DI}BPMNEdge"):
        for ponto in aresta.findall(f"{D}waypoint"):
            xs.append(float(ponto.get("x", 0)))
            ys.append(float(ponto.get("y", 0)))
    return max(xs) - min(xs), max(ys) - min(ys)


def test_cada_parte_do_processo_cabe_na_coluna_sem_reduzir():
    for modelo in _modelos():
        largura, _altura = _extensao(modelo.read_text(encoding="utf-8"))
        assert largura <= LARGURA_MAX, (
            f"{modelo.name} tem {largura:.0f} pt de largura; a coluna mais "
            f"estreita dos três alvos oferece {LARGURA_MAX:.0f} pt. Encaixar "
            "isso exigiria reduzir a figura, e reduzir deixa o rótulo "
            f"ilegível ({9 * LARGURA_MAX / largura:.1f} pt). Redesenhar o "
            "modelo, não a página."
        )


def test_cada_parte_do_processo_cabe_na_altura_da_pagina():
    for modelo in _modelos():
        _largura, altura = _extensao(modelo.read_text(encoding="utf-8"))
        assert altura <= ALTURA_MAX, (
            f"{modelo.name} tem {altura:.0f} pt de altura; uma figura de "
            f"página inteira comporta {ALTURA_MAX:.0f} pt depois da legenda. "
            "Quebrar o processo em mais uma parte."
        )


def test_o_texto_nao_gira_a_pagina_do_processo():
    """Contraprova da guarda acima: ela só vale enquanto a página for retrato.

    Sem esta verificação, bastaria devolver o ``landscape`` ao redor da figura
    para que um modelo largo voltasse a caber — e o defeito recusado voltaria
    junto, com os dois testes acima passando.
    """
    secoes = sorted((RAIZ / "texto" / "tcc1" / "secoes").glob("*.tex"))
    texto = "\n".join(arquivo.read_text(encoding="utf-8") for arquivo in secoes)
    assert "landscape" not in texto, (
        "alguma seção voltou a girar a página. A orientação recusou o recurso: "
        "gira a numeração e o cabeçalho junto. Redesenhar o modelo."
    )
