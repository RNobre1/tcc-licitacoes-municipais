"""Monta o modelo BPMN do processo a partir da declaração abaixo.

FONTE E DERIVAÇÃO — leia antes de editar qualquer um dos dois arquivos.

Este script é a fonte do **primeiro** desenho: ele produz
`docs/arquitetura/processo-licitacao.bpmn` com coordenadas calculadas, que é o
que evita o erro de digitá-las à mão e o que garante que nenhuma linha cruze
outra.

Daí em diante o `.bpmn` passa a valer por si. Ele é XML padrão da OMG e abre em
qualquer ferramenta da notação — inclusive na que a orientação indicou. Se
alguém mover uma caixa por lá, aquela edição é a que vale, e rodar este script
de novo a descarta. Por isso ele não roda em cadeia com os outros geradores:
é ferramenta de partida, não de rotina.

O LAYOUT, E POR QUE ELE É ASSIM

A primeira versão roteava cada ligação pelo ponto médio entre origem e destino.
O resultado foi um emaranhado: ligações diferentes que mudam de raia no mesmo
trecho acabam no mesmo x e se cruzam.

Aqui cada ligação que troca de raia recebe um **canal vertical próprio**, e os
canais são distribuídos no vão entre as caixas. Duas ligações nunca descem pela
mesma coluna. As que atravessam o diagrama inteiro usam a faixa livre no pé da
raia de destino, por baixo das caixas, em vez de cortá-las.

    python scripts/montar_bpmn.py
    python scripts/gerar_bpmn.py     # depois, para a figura
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "arquitetura" / "processo-licitacao.bpmn"

# --- Geometria ---------------------------------------------------------------
T_W, T_H = 125, 76
G_W = 60
E_W = 40
MARGEM_POOL = 30

RAIAS = [
    ("raia_secretaria", "Secretaria demandante", 215),
    ("raia_licitacoes", "Setor de licitações", 245),
    ("raia_sistema", "Sistema de apoio", 255),
]

# O processo é declarado em duas partes, ligadas por eventos intermediários.
# Catorze etapas numa faixa só produzem figura de proporção 4,2 para 1, que não
# cabe legível em página nenhuma: o rótulo das caixas fica com menos de cinco
# pontos. Cada parte fica perto de 2 para 1.
#
# Estrutura de cada parte: (sufixo do arquivo, título, nós, ligações).
# Nó: id, tipo, rótulo, raia, coluna. Ligação: origem, destino, rótulo, por_baixo.

PARTES = [
    (
        "1-demanda",
        "Da demanda à minuta do estudo técnico",
        [
            ("ev_inicio", "start", "Necessidade identificada", "raia_secretaria", 0),
            ("t_formalizar", "task", "Formalizar demanda", "raia_secretaria", 1),
            ("t_importar", "task", "Importar documentos de demanda", "raia_licitacoes", 2),
            ("t_extrair", "task", "Extrair itens, quantidades e unidades", "raia_sistema", 3),
            (
                "g_consolida",
                "gateway",
                "Item pedido por mais de uma secretaria?",
                "raia_licitacoes",
                4,
            ),
            ("t_consenso", "task", "Propor descrição de consenso", "raia_sistema", 5),
            (
                "t_alinhar",
                "task",
                "Alinhar descrição com as secretarias",
                "raia_licitacoes",
                6,
            ),
            ("t_minuta", "task", "Emitir minuta do estudo técnico", "raia_sistema", 7),
            ("ev_segue", "end", "Segue na parte 2", "raia_sistema", 8),
        ],
        [
            ("ev_inicio", "t_formalizar", "", False),
            ("t_formalizar", "t_importar", "", False),
            ("t_importar", "t_extrair", "", False),
            ("t_extrair", "g_consolida", "", False),
            ("g_consolida", "t_consenso", "sim", False),
            ("t_consenso", "t_alinhar", "", False),
            ("t_alinhar", "t_minuta", "", False),
            ("g_consolida", "t_minuta", "não", True),
            ("t_minuta", "ev_segue", "", False),
        ],
    ),
    (
        "2-precos",
        "Da pesquisa de preços às peças do processo",
        [
            ("ev_vem", "start", "Minuta emitida", "raia_sistema", 0),
            (
                "g_ata",
                "gateway",
                "Preço vem de ata ou contrato vigente?",
                "raia_licitacoes",
                1,
            ),
            (
                "t_recuperar",
                "task",
                "Recuperar candidatos por significado",
                "raia_sistema",
                2,
            ),
            ("t_triar", "task", "Triar candidatos e decidir", "raia_licitacoes", 3),
            (
                "t_calcular",
                "task",
                "Calcular valor e gerar mapa de cotação",
                "raia_sistema",
                4,
            ),
            (
                "t_pecas",
                "task",
                "Gerar estudo final e termo de referência",
                "raia_sistema",
                5,
            ),
            ("t_revisar", "task", "Revisar e assinar as peças", "raia_licitacoes", 6),
            ("ev_fim", "end", "Processo instruído", "raia_licitacoes", 7),
        ],
        [
            ("ev_vem", "g_ata", "", False),
            ("g_ata", "t_recuperar", "não", False),
            ("t_recuperar", "t_triar", "", False),
            ("t_triar", "t_calcular", "", False),
            ("t_calcular", "t_pecas", "", False),
            ("g_ata", "t_pecas", "sim", True),
            ("t_pecas", "t_revisar", "", False),
            ("t_revisar", "ev_fim", "", False),
        ],
    ),
]

# Preenchidos por parte, durante a geração.
NOS: list = []
FLUXOS: list = []

TIPOS = {
    "start": ("startEvent", E_W, E_W),
    "end": ("endEvent", E_W, E_W),
    "task": ("task", T_W, T_H),
    "gateway": ("exclusiveGateway", G_W, G_W),
}

COL_X0 = 220
COL_PASSO = 158
POOL_X, POOL_Y = 160, 60


def _topo(rid: str) -> float:
    y = POOL_Y
    for ident, _nome, altura in RAIAS:
        if ident == rid:
            return y
        y += altura
    raise KeyError(rid)


def _centro(rid: str) -> float:
    altura = next(a for i, _n, a in RAIAS if i == rid)
    return _topo(rid) + altura / 2


def geo(ident: str) -> tuple[float, float, float, float]:
    _, tipo, _, raia, coluna = next(n for n in NOS if n[0] == ident)
    _, w, h = TIPOS[tipo]
    return COL_X0 + coluna * COL_PASSO, _centro(raia) - h / 2, w, h


def caminho(origem: str, destino: str, por_baixo: bool, canal: float) -> list[tuple[float, float]]:
    ox, oy, ow, oh = geo(origem)
    dx, dy, dw, dh = geo(destino)
    x1, y1 = ox + ow, oy + oh / 2
    x2, y2 = dx, dy + dh / 2

    if abs(y1 - y2) < 1:
        return [(x1, y1), (x2, y2)]

    if por_baixo:
        # Desce pelo canal logo após a origem, corre no pé da raia de destino e
        # sobe só na frente do destino. Nunca passa por dentro de uma caixa.
        rid = next(n[3] for n in NOS if n[0] == destino)
        pe = _topo(rid) + next(a for i, _n, a in RAIAS if i == rid) - 18
        return [(x1, y1), (canal, y1), (canal, pe), (x2 - 22, pe), (x2 - 22, y2), (x2, y2)]

    return [(x1, y1), (canal, y1), (canal, y2), (x2, y2)]


def main() -> None:
    global NOS, FLUXOS
    for sufixo, titulo, nos, fluxos in PARTES:
        NOS, FLUXOS = nos, fluxos
        arquivo = DESTINO.with_name(f"processo-licitacao-{sufixo}.bpmn")
        _escrever(arquivo, titulo)


def _escrever(arquivo: Path, titulo: str) -> None:
    # Um canal por ligação que troca de raia, distribuído no vão entre as
    # colunas de origem e destino. Duas ligações nunca compartilham o x.
    canais: dict[tuple[str, str], float] = {}
    usados: dict[int, int] = {}
    for origem, destino, _rot, por_baixo in FLUXOS:
        ox, _oy, ow, _oh = geo(origem)
        dx, _dy, _dw, _dh = geo(destino)
        fim_origem, inicio_destino = ox + ow, dx
        chave = int(fim_origem)
        ordem = usados.get(chave, 0)
        usados[chave] = ordem + 1
        if por_baixo:
            # Desvio longo desce logo depois da origem. Calcular o canal no meio
            # do vão faz a descida cair sobre uma caixa do caminho principal —
            # foi o defeito que a verificação geométrica apanhou.
            canais[(origem, destino)] = fim_origem + 24 + 14 * ordem
        else:
            vao = max(inicio_destino - fim_origem, 40)
            canais[(origem, destino)] = fim_origem + vao * (0.4 + 0.25 * ordem)

    elementos, formas, arestas = [], [], []

    for ident, tipo, rotulo, _raia, _col in NOS:
        tag, _, _ = TIPOS[tipo]
        entra = [f for f in FLUXOS if f[1] == ident]
        sai = [f for f in FLUXOS if f[0] == ident]
        corpo = "\n".join(
            [f"      <bpmn:incoming>fl_{o}_{d}</bpmn:incoming>" for o, d, _r, _b in entra]
            + [f"      <bpmn:outgoing>fl_{o}_{d}</bpmn:outgoing>" for o, d, _r, _b in sai]
        )
        elementos.append(
            f'    <bpmn:{tag} id="{ident}" name="{escape(rotulo)}">\n{corpo}\n    </bpmn:{tag}>'
        )
        x, y, w, h = geo(ident)
        formas.append(
            f'      <bpmndi:BPMNShape id="di_{ident}" bpmnElement="{ident}">\n'
            f'        <dc:Bounds x="{x:.0f}" y="{y:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" />\n'
            f"      </bpmndi:BPMNShape>"
        )

    for origem, destino, rotulo, por_baixo in FLUXOS:
        ident = f"fl_{origem}_{destino}"
        nome = f' name="{escape(rotulo)}"' if rotulo else ""
        elementos.append(
            f'    <bpmn:sequenceFlow id="{ident}"{nome} '
            f'sourceRef="{origem}" targetRef="{destino}" />'
        )
        pontos = caminho(origem, destino, por_baixo, canais[(origem, destino)])
        wp = "\n".join(f'        <di:waypoint x="{x:.0f}" y="{y:.0f}" />' for x, y in pontos)
        arestas.append(
            f'      <bpmndi:BPMNEdge id="di_{ident}" bpmnElement="{ident}">\n{wp}\n'
            f"      </bpmndi:BPMNEdge>"
        )

    largura = COL_X0 + (len(NOS) - 1) * COL_PASSO + T_W + 60 - POOL_X
    altura = sum(a for _i, _n, a in RAIAS)

    raias_xml, raias_di = [], []
    for rid, nome, alt in RAIAS:
        refs = "\n".join(
            f"        <bpmn:flowNodeRef>{n[0]}</bpmn:flowNodeRef>" for n in NOS if n[3] == rid
        )
        raias_xml.append(
            f'      <bpmn:lane id="{rid}" name="{escape(nome)}">\n{refs}\n      </bpmn:lane>'
        )
        raias_di.append(
            f'      <bpmndi:BPMNShape id="di_{rid}" bpmnElement="{rid}" isHorizontal="true">\n'
            f'        <dc:Bounds x="{POOL_X + MARGEM_POOL}" y="{_topo(rid):.0f}" '
            f'width="{largura - MARGEM_POOL}" height="{alt}" />\n'
            f"      </bpmndi:BPMNShape>"
        )

    nl = chr(10)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  Processo da fase preparatória de uma contratação, em BPMN 2.0.

  ESTE ARQUIVO É A FONTE a partir de agora. É XML padrão da OMG e abre em
  qualquer ferramenta da notação, inclusive na indicada pela orientação, para
  conferência e edição. A figura do texto é gerada dele por
  `scripts/gerar_bpmn.py`, e nunca o contrário.

  O desenho inicial saiu de `scripts/montar_bpmn.py`, que calcula as
  coordenadas de modo que nenhuma ligação cruze outra. Rodar aquele script de
  novo SOBRESCREVE este arquivo e descarta qualquer ajuste feito à mão.

  Recorte: contratação de material ou serviço comum, com valor estimado montado
  por pesquisa de preços. Obras ficam de fora, porque seu orçamento sai de
  planilha de custos sobre tabela de referência, que é outro mecanismo.

  As duas decisões exclusivas marcam etapas que podem não acontecer: a
  consolidação só existe quando mais de uma secretaria pede o mesmo item, e a
  pesquisa de preços é pulada quando o preço vem de ata ou contrato vigente.
-->
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="defs_licitacao"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:collaboration id="colaboracao">
    <bpmn:participant id="pool_prefeitura" name="Prefeitura — {titulo}"
                      processRef="processo_licitacao" />
  </bpmn:collaboration>
  <bpmn:process id="processo_licitacao" isExecutable="false">
    <bpmn:laneSet id="raias">
{nl.join(raias_xml)}
    </bpmn:laneSet>
{nl.join(elementos)}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="diagrama">
    <bpmndi:BPMNPlane id="plano" bpmnElement="colaboracao">
      <bpmndi:BPMNShape id="di_pool" bpmnElement="pool_prefeitura" isHorizontal="true">
        <dc:Bounds x="{POOL_X}" y="{POOL_Y}" width="{largura:.0f}" height="{altura}" />
      </bpmndi:BPMNShape>
{nl.join(raias_di)}
{nl.join(formas)}
{nl.join(arestas)}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""
    arquivo.write_text(xml, encoding="utf-8")
    print(f"{arquivo.name}: {len(NOS)} nós, {len(FLUXOS)} ligações, {largura:.0f}x{altura} pt")


if __name__ == "__main__":
    main()
