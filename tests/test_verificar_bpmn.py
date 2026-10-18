"""Testes do verificador do modelo BPMN.

O modelo é gerado por script, mas o script calcula rotas, e rota calculada
erra: na primeira versão do desenho duas ligações desciam pela mesma coluna, e
uma terceira passava por dentro de uma caixa. Nada disso aparece relendo XML.

Cada teste abaixo monta um modelo mínimo com um defeito conhecido e confere que
o verificador o acusa. A contraprova — um modelo limpo — também está aqui:
guarda que nunca reclama não é guarda.
"""

from __future__ import annotations

from scripts import verificar_bpmn as vb


def _modelo(formas: str, arestas: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI">
  <bpmndi:BPMNDiagram id="d">
    <bpmndi:BPMNPlane id="p" bpmnElement="colaboracao">
      {formas}
      {arestas}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>"""


def _forma(ident: str, x: int, y: int, w: int = 100, h: int = 40, rotulo: str = "") -> str:
    marca = ""
    if rotulo:
        lx, ly, lw, lh = (int(n) for n in rotulo.split(","))
        marca = (
            "<bpmndi:BPMNLabel>"
            f'<dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}" />'
            "</bpmndi:BPMNLabel>"
        )
    return (
        f'<bpmndi:BPMNShape id="di_{ident}" bpmnElement="{ident}">'
        f'<dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />{marca}'
        "</bpmndi:BPMNShape>"
    )


def _aresta(ident: str, pontos: list[tuple[int, int]]) -> str:
    wp = "".join(f'<di:waypoint x="{x}" y="{y}" />' for x, y in pontos)
    return f'<bpmndi:BPMNEdge id="di_{ident}" bpmnElement="{ident}">{wp}</bpmndi:BPMNEdge>'


def test_modelo_limpo_nao_acusa_nada():
    """Contraprova. Sem ela, todo teste abaixo passaria com um verificador quebrado."""
    xml = _modelo(
        _forma("a", 0, 0) + _forma("b", 0, 200),
        _aresta("fl_a_b", [(50, 40), (50, 200)]),
    )
    assert vb.verificar(xml).problemas == 0


def test_acusa_caixas_sobrepostas():
    xml = _modelo(_forma("a", 0, 0) + _forma("b", 50, 20), "")
    assert vb.verificar(xml).sobrepostas == [("a", "b")]


def test_acusa_trecho_diagonal():
    xml = _modelo(
        _forma("a", 0, 0) + _forma("b", 200, 200),
        _aresta("fl_a_b", [(50, 40), (250, 200)]),
    )
    assert vb.verificar(xml).diagonais == ["fl_a_b"]


def test_acusa_ligacoes_que_se_cruzam():
    """Uma desce, a outra atravessa: o cruzamento cai em (150, 150)."""
    xml = _modelo(
        _forma("a", 120, 0, 60)
        + _forma("b", 120, 260, 60)
        + _forma("c", 0, 130, 60)
        + _forma("d", 300, 130, 60),
        _aresta("fl_a_b", [(150, 40), (150, 260)]) + _aresta("fl_c_d", [(60, 150), (300, 150)]),
    )
    assert vb.verificar(xml).cruzamentos == [("fl_a_b", "fl_c_d")]


def test_acusa_ligacao_atravessando_caixa_alheia():
    xml = _modelo(
        _forma("a", 0, 0) + _forma("b", 0, 300) + _forma("c", 20, 140),
        _aresta("fl_a_b", [(50, 40), (50, 300)]),
    )
    assert vb.verificar(xml).atravessam == [("fl_a_b", "c")]


def test_acusa_ligacao_passando_por_cima_de_rotulo_alheio():
    """O defeito que o verificador não via antes de contar rótulo como caixa.

    Rótulo de evento e pergunta de decisão são desenhados **fora** da forma.
    Enquanto só as formas contavam, uma seta podia atravessar o texto inteiro
    sem que nada reclamasse — e na figura isso é tão ruim quanto atravessar
    uma caixa, porque o texto é o que se lê.
    """
    xml = _modelo(
        _forma("a", 0, 0)
        + _forma("b", 0, 300)
        + _forma("c", 300, 140, 30, 30, rotulo="20,150,120,20"),
        _aresta("fl_a_b", [(50, 40), (50, 300)]),
    )
    assert vb.verificar(xml).atravessam == [("fl_a_b", "rot_c")]


def test_o_proprio_rotulo_da_origem_nao_conta_como_estorvo():
    """Contraprova do teste acima: a ligação passa rente ao rótulo **dela**.

    Sem a anotação de dono, todo evento com rótulo externo seria acusado, e a
    guarda viraria ruído que se aprende a ignorar.
    """
    xml = _modelo(
        _forma("a", 0, 0, 30, 30, rotulo="0,30,120,20") + _forma("b", 0, 300),
        _aresta("fl_a_b", [(15, 30), (15, 300)]),
    )
    assert vb.verificar(xml).atravessam == []


def test_os_modelos_do_projeto_passam():
    from scripts.gerar_bpmn import modelos

    for modelo in modelos():
        r = vb.verificar(modelo.read_text(encoding="utf-8"))
        assert r.problemas == 0, (
            f"{modelo.name}: sobrepostas={r.sobrepostas} diagonais={r.diagonais} "
            f"cruzamentos={r.cruzamentos} atravessam={r.atravessam}"
        )
