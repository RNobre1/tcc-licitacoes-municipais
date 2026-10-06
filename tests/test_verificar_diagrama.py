"""Testes do verificador de diagrama.

O diagrama da arquitetura é desenhado à mão e vai ser mexido muitas vezes até a
defesa. Mover uma caixa e fazer duas linhas se cruzarem é o tipo de estrago que
ninguém nota relendo o arquivo — só olhando a figura, e nem sempre.

Cada teste abaixo monta um diagrama mínimo com um defeito conhecido e confere
que o verificador o acusa. A contraprova, um diagrama limpo, também está aqui:
guarda que nunca reclama não é guarda.
"""

from __future__ import annotations

from pathlib import Path

from scripts import verificar_diagrama as vd

RAIZ = Path(__file__).resolve().parent.parent
DIAGRAMA = RAIZ / "docs" / "arquitetura" / "arquitetura.drawio"


def _diagrama(celulas: str, largura: int = 1000, altura: int = 800) -> str:
    return f"""<mxfile>
  <diagram name="teste" id="t">
    <mxGraphModel pageWidth="{largura}" pageHeight="{altura}">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {celulas}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""


def _caixa(
    ident: str, x: int, y: int, w: int = 100, h: int = 60, estilo: str = "rounded=1;"
) -> str:
    return (
        f'<mxCell id="{ident}" value="{ident}" style="{estilo}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>'
    )


def _aresta(ident: str, origem: str, destino: str, estilo: str, pontos: str = "") -> str:
    arranjo = f'<Array as="points">{pontos}</Array>' if pontos else ""
    return (
        f'<mxCell id="{ident}" style="{estilo}" edge="1" parent="1" '
        f'source="{origem}" target="{destino}">'
        f'<mxGeometry relative="1" as="geometry">{arranjo}</mxGeometry></mxCell>'
    )


# --- Contraprova -------------------------------------------------------------


def test_diagrama_limpo_nao_acusa_nada():
    xml = _diagrama(
        _caixa("a", 100, 100)
        + _caixa("b", 400, 100)
        + _aresta("e", "a", "b", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.problemas == 0


# --- Cada defeito é acusado --------------------------------------------------


def test_acusa_caixa_fora_da_pagina():
    xml = _diagrama(_caixa("a", 950, 100), largura=1000)
    (pagina,) = vd.verificar(xml)
    assert pagina.fora_da_pagina == ["a"]


def test_acusa_caixas_sobrepostas():
    xml = _diagrama(_caixa("a", 100, 100) + _caixa("b", 150, 120))
    (pagina,) = vd.verificar(xml)
    assert pagina.sobrepostas == [("a", "b")]


def test_acusa_trecho_diagonal():
    """Ponto de saída e de chegada desalinhados: o editor inventa o caminho."""
    xml = _diagrama(
        _caixa("a", 100, 100)
        + _caixa("b", 400, 300)
        + _aresta("e", "a", "b", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.diagonais == ["e"]


def test_acusa_linhas_que_se_cruzam():
    xml = _diagrama(
        _caixa("a", 100, 100)
        + _caixa("b", 100, 400)
        + _caixa("c", 20, 250)
        + _caixa("d", 300, 250)
        + _aresta("v", "a", "b", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
        + _aresta("h", "c", "d", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.cruzamentos == [("h", "v")]


def test_acusa_linha_atravessando_caixa_alheia():
    xml = _diagrama(
        _caixa("a", 100, 100)
        + _caixa("b", 700, 100)
        + _caixa("meio", 350, 80)
        + _aresta("e", "a", "b", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
    )
    (pagina,) = vd.verificar(xml)
    assert ("e", "meio") in pagina.atravessam


def test_toque_na_extremidade_nao_conta_como_cruzamento():
    """Duas arestas que partem do mesmo ponto se encontram ali por construção."""
    xml = _diagrama(
        _caixa("a", 100, 100)
        + _caixa("b", 100, 400)
        + _caixa("c", 400, 400)
        + _aresta("e1", "a", "b", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
        + _aresta(
            "e2",
            "a",
            "c",
            "exitX=0.5;exitY=1;entryX=0.5;entryY=0;",
            '<mxPoint x="150" y="300" /><mxPoint x="450" y="300" />',
        )
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.cruzamentos == []


def test_diferenca_de_subpixel_nao_vira_diagonal():
    """Fração de âncora produz centésimo de pixel. Isso não é defeito."""
    # 120 + 0,333 × 270 = 209,91 contra 120 + 0,36 × 250 = 210,00. Nove
    # centésimos de pixel, que o editor arredonda e ninguém enxerga.
    xml = _diagrama(
        _caixa("a", 120, 100, w=270)
        + _caixa("b", 120, 400, w=250)
        + _aresta("e", "a", "b", "exitX=0.333;exitY=1;entryX=0.36;entryY=0;")
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.diagonais == []


def test_desalinhamento_de_verdade_continua_sendo_acusado():
    """Contraprova da tolerância: ela perdoa centésimo, não perdoa vinte pixels."""
    xml = _diagrama(
        _caixa("a", 100, 100, w=270)
        + _caixa("b", 120, 400, w=250)
        + _aresta("e", "a", "b", "exitX=0.333;exitY=1;entryX=0.36;entryY=0;")
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.diagonais == ["e"]


def test_fronteira_tracejada_nao_conta_como_sobreposicao():
    """Ela existe para conter as outras caixas; encavalar é o desenho."""
    xml = _diagrama(
        _caixa("limite", 50, 50, w=600, h=500, estilo="dashed=1;fillColor=none;")
        + _caixa("dentro", 100, 100)
    )
    (pagina,) = vd.verificar(xml)
    assert pagina.sobrepostas == []


# --- O diagrama real ---------------------------------------------------------


def test_o_diagrama_da_arquitetura_existe():
    assert DIAGRAMA.is_file()


def test_o_diagrama_da_arquitetura_esta_limpo():
    paginas = vd.verificar(DIAGRAMA.read_text(encoding="utf-8"))
    assert len(paginas) == 3
    ruins = {p.nome: p for p in paginas if p.problemas}
    detalhe = {
        nome: {
            "fora da página": p.fora_da_pagina,
            "sobrepostas": p.sobrepostas,
            "diagonais": p.diagonais,
            "cruzamentos": p.cruzamentos,
            "atravessam": p.atravessam,
        }
        for nome, p in ruins.items()
    }
    assert ruins == {}, f"o diagrama tem problemas de leitura: {detalhe}"
