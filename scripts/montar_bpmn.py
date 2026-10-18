"""Monta o modelo BPMN do processo a partir da declaração abaixo.

FONTE E DERIVAÇÃO — leia antes de editar qualquer arquivo desta cadeia.

Este script é a fonte do desenho: ele produz os `.bpmn` de
`docs/arquitetura/` com coordenadas calculadas. Daí sai, por
`scripts/gerar_bpmn.py`, a figura do texto. Calcular as coordenadas em vez de
digitá-las é o que garante que nenhuma ligação cruze outra, e
`scripts/verificar_bpmn.py` prova que a garantia valeu.

O `.bpmn` é XML padrão da OMG e abre em qualquer ferramenta da notação —
inclusive na que a orientação indicou — para conferência. Rodar este script de
novo o sobrescreve: ajuste feito por lá é descartado.

POR QUE AS RAIAS SÃO VERTICAIS

A primeira versão usava raias horizontais, com o fluxo da esquerda para a
direita. Catorze etapas nessa disposição dão um desenho de mais de 1500 pt de
largura. A coluna de texto mais estreita dos três alvos tem 427 pt, o que
exigiria reduzir a figura a 28% — e a 28% o rótulo de 9 pt vira 2,5 pt.

A saída tentada na ocasião foi girar a página para paisagem, e foi recusada:
gira a numeração e o cabeçalho junto, e quebra a leitura do documento.

A correção certa não é de diagramação da página, é de desenho do modelo. O
processo é longo, e coisa longa ocupa o eixo longo do papel: as raias viram
colunas e o fluxo desce. A notação prevê isso — `isHorizontal="false"` é
atributo do próprio padrão de intercâmbio. O desenho passa a nascer com 418 pt
de largura, cabe em tamanho natural, e o rótulo fica no corpo do documento.

`tests/test_processo_cabe_na_mancha.py` é o que impede a volta do defeito.

O LAYOUT, E POR QUE ELE É ASSIM

Cada etapa ocupa uma linha própria, na coluna de quem a executa. Ligação entre
linhas vizinhas desce pelo vão entre elas, onde não há caixa nenhuma. Desvio
longo — o salto de uma decisão exclusiva por cima de etapas que não acontecem —
corre por um canal reservado à esquerda, dentro da primeira raia, largo o
bastante para a linha não encostar em caixa.

Decisão exclusiva recebe por cima e ramifica pelos lados, nunca por baixo: por
baixo fica a pergunta, e seta sobre texto é exatamente o tipo de estrago que
este arquivo existe para evitar.

    python scripts/montar_bpmn.py
    python scripts/gerar_bpmn.py     # depois, para a figura
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "arquitetura" / "processo-licitacao.bpmn"

# --- Geometria, em pontos ----------------------------------------------------
# Os números saem da mancha de texto do alvo mais estreito (sbc-tcc, 426,79 pt).
# Somados: 22 + 3 x 132 = 418 pt. A folga de 9 pt é deliberada — figura
# encostada na margem parece erro de composição mesmo quando não é.
CAB_POOL = 22  # faixa vertical com o nome do pool, à esquerda
CAB_RAIA = 20  # faixa horizontal com o nome da raia, no topo da coluna
RAIA_W = 132

# O desvio longo desce por um canal dentro da primeira raia, junto à borda. Não
# se reserva coluna para ele: alargar uma raia só para isso deixa as três
# visivelmente desiguais, e a desigualdade sugere hierarquia que não existe. A
# folga de 16 pt entre a caixa e a borda da raia é o que torna o canal
# possível, e `verificar_bpmn.py` é quem prova que ele não encosta em nada.
CANAL = 9  # distância do canal à borda esquerda da primeira raia

T_W, T_H = 100, 36  # tarefa
G_W = 34  # decisão exclusiva
E_W = 30  # evento
ROTULO_W = 112  # rótulo externo, de evento e de decisão
ROTULO_1, ROTULO_2 = 11, 20  # uma e duas linhas de rótulo externo

VAO = 20  # vão vertical entre linhas
PAD_TOPO, PAD_BASE = 12, 14
POOL_X, POOL_Y = 10, 10

RAIAS = [
    ("raia_secretaria", "Secretaria demandante"),
    ("raia_licitacoes", "Setor de licitações"),
    ("raia_sistema", "Sistema de apoio"),
]

# O processo é declarado em duas partes, ligadas por eventos intermediários.
# Catorze linhas numa figura só passam de 900 pt de altura, e não existe página
# que as comporte. Cada parte cabe inteira numa, com folga.
#
# A ordem da lista é a ordem das linhas: a primeira etapa declarada ocupa a
# primeira linha. Não há número de linha a manter em dia.
#
# Nó: id, tipo, rótulo, raia. Ligação: origem, destino, rótulo, desvio.

PARTES = [
    (
        "1-demanda",
        "Da demanda à minuta do estudo técnico",
        [
            ("ev_inicio", "start", "Necessidade identificada", "raia_secretaria"),
            ("t_formalizar", "task", "Formalizar demanda", "raia_secretaria"),
            ("t_importar", "task", "Importar documentos de demanda", "raia_licitacoes"),
            ("t_extrair", "task", "Extrair itens, quantidades e unidades", "raia_sistema"),
            (
                "g_consolida",
                "gateway",
                "Item pedido por mais de uma secretaria?",
                "raia_licitacoes",
            ),
            ("t_consenso", "task", "Propor descrição de consenso", "raia_sistema"),
            ("t_alinhar", "task", "Alinhar descrição com as secretarias", "raia_licitacoes"),
            ("t_minuta", "task", "Emitir minuta do estudo técnico", "raia_sistema"),
            ("ev_segue", "end", "Segue na parte 2", "raia_sistema"),
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
            ("ev_vem", "start", "Minuta emitida", "raia_sistema"),
            ("g_ata", "gateway", "Preço vem de ata ou contrato vigente?", "raia_licitacoes"),
            ("t_recuperar", "task", "Recuperar candidatos por significado", "raia_sistema"),
            ("t_triar", "task", "Triar candidatos e decidir", "raia_licitacoes"),
            ("t_calcular", "task", "Calcular valor e gerar mapa de cotação", "raia_sistema"),
            ("t_pecas", "task", "Gerar estudo final e termo de referência", "raia_sistema"),
            ("t_revisar", "task", "Revisar e assinar as peças", "raia_licitacoes"),
            ("ev_fim", "end", "Processo instruído", "raia_licitacoes"),
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

TAG = {
    "start": "startEvent",
    "end": "endEvent",
    "task": "task",
    "gateway": "exclusiveGateway",
}

# Largura e altura da forma, por tipo.
FORMA = {"start": (E_W, E_W), "end": (E_W, E_W), "task": (T_W, T_H), "gateway": (G_W, G_W)}

# Altura do rótulo externo; tarefa escreve dentro da caixa e não tem.
ROTULO = {"start": ROTULO_1, "end": ROTULO_1, "task": 0, "gateway": ROTULO_2}

# Em que ponto da linha a forma fica, e onde sobra espaço para o rótulo. O
# evento inicial põe o rótulo **em cima**, porque sai por baixo; os demais põem
# embaixo, porque entram por cima. É o que mantém seta e texto separados.
ROTULO_ACIMA = ("start",)


class Parte:
    """Uma metade do processo, com a geometria já resolvida."""

    def __init__(self, sufixo: str, titulo: str, nos: list, fluxos: list) -> None:
        self.sufixo, self.titulo, self.nos, self.fluxos = sufixo, titulo, nos, fluxos
        self.tipo = {n[0]: n[1] for n in nos}
        self.raia = {n[0]: n[3] for n in nos}

        self.largura = CAB_POOL + len(RAIAS) * RAIA_W
        self.canal_x = POOL_X + CAB_POOL + CANAL

        self.caixa: dict[str, tuple[float, float, float, float]] = {}
        self.rotulo: dict[str, tuple[float, float, float, float]] = {}
        topo = POOL_Y + CAB_RAIA + PAD_TOPO
        for ident, tipo, _nome, _raia in nos:
            w, h = FORMA[tipo]
            alto_rotulo = ROTULO[tipo]
            cx = self._centro_da_raia(ident)
            if tipo in ROTULO_ACIMA and alto_rotulo:
                self.rotulo[ident] = (cx - ROTULO_W / 2, topo, ROTULO_W, alto_rotulo)
                y = topo + alto_rotulo + 2
            else:
                y = topo
                if alto_rotulo:
                    self.rotulo[ident] = (cx - ROTULO_W / 2, y + h + 2, ROTULO_W, alto_rotulo)
            self.caixa[ident] = (cx - w / 2, y, w, h)
            topo += h + (alto_rotulo + 2 if alto_rotulo else 0) + VAO
        self.altura = topo - VAO + PAD_BASE - POOL_Y

    def _indice_da_raia(self, ident: str) -> int:
        return [r[0] for r in RAIAS].index(self.raia[ident])

    def _limite_da_raia(self, indice: int) -> tuple[float, float]:
        """Esquerda e largura da coluna. As três são iguais."""
        return POOL_X + CAB_POOL + indice * RAIA_W, RAIA_W

    def _centro_da_raia(self, ident: str) -> float:
        x, largura = self._limite_da_raia(self._indice_da_raia(ident))
        return x + largura / 2

    def rota(self, origem: str, destino: str, desvio: bool) -> list[tuple[float, float]]:
        ox, oy, ow, oh = self.caixa[origem]
        dx, dy, dw, dh = self.caixa[destino]
        ocx, odx = ox + ow / 2, dx + dw / 2
        oy_meio, dy_meio = oy + oh / 2, dy + dh / 2

        if desvio:
            # Sai pelo lado esquerdo, desce pelo canal reservado, entra pelo
            # lado esquerdo do destino. Nunca por baixo da decisão: lá está a
            # pergunta.
            return [
                (ox, oy_meio),
                (self.canal_x, oy_meio),
                (self.canal_x, dy_meio),
                (dx, dy_meio),
            ]

        if self.tipo[origem] == "gateway":
            # Ramifica pelo lado e desce já na coluna do destino, fora do
            # alcance da pergunta.
            lado = ox + ow if odx > ocx else ox
            return [(lado, oy_meio), (odx, oy_meio), (odx, dy)]

        if abs(ocx - odx) < 1:
            return [(ocx, oy + oh), (odx, dy)]

        meio = (oy + oh + dy) / 2
        return [(ocx, oy + oh), (ocx, meio), (odx, meio), (odx, dy)]

    def conferir(self) -> None:
        """Pressupostos do roteamento, cobrados aqui e não descobertos na figura."""
        for origem, destino, _rotulo, desvio in self.fluxos:
            if self.tipo[origem] != "gateway":
                continue
            if desvio:
                continue
            if self.raia[origem] == self.raia[destino]:
                raise ValueError(
                    f"{origem} ramifica para {destino} na mesma raia. A saída lateral "
                    "desceria por cima da pergunta da decisão. Mover um dos dois de raia."
                )


def _xml(p: Parte) -> str:
    nl = chr(10)
    elementos, formas, arestas = [], [], []

    for ident, tipo, rotulo, _raia in p.nos:
        entra = [f for f in p.fluxos if f[1] == ident]
        sai = [f for f in p.fluxos if f[0] == ident]
        corpo = "\n".join(
            [f"      <bpmn:incoming>fl_{o}_{d}</bpmn:incoming>" for o, d, _r, _b in entra]
            + [f"      <bpmn:outgoing>fl_{o}_{d}</bpmn:outgoing>" for o, d, _r, _b in sai]
        )
        elementos.append(
            f'    <bpmn:{TAG[tipo]} id="{ident}" name="{escape(rotulo)}">\n{corpo}\n'
            f"    </bpmn:{TAG[tipo]}>"
        )
        x, y, w, h = p.caixa[ident]
        marca = ""
        if ident in p.rotulo:
            lx, ly, lw, lh = p.rotulo[ident]
            marca = (
                f"\n        <bpmndi:BPMNLabel>\n"
                f'          <dc:Bounds x="{lx:.0f}" y="{ly:.0f}" '
                f'width="{lw:.0f}" height="{lh:.0f}" />\n'
                f"        </bpmndi:BPMNLabel>"
            )
        formas.append(
            f'      <bpmndi:BPMNShape id="di_{ident}" bpmnElement="{ident}">\n'
            f'        <dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" />'
            f"{marca}\n      </bpmndi:BPMNShape>"
        )

    for origem, destino, rotulo, desvio in p.fluxos:
        ident = f"fl_{origem}_{destino}"
        nome = f' name="{escape(rotulo)}"' if rotulo else ""
        elementos.append(
            f'    <bpmn:sequenceFlow id="{ident}"{nome} '
            f'sourceRef="{origem}" targetRef="{destino}" />'
        )
        pontos = p.rota(origem, destino, desvio)
        wp = "\n".join(f'        <di:waypoint x="{x:.0f}" y="{y:.0f}" />' for x, y in pontos)
        marca = ""
        if rotulo:
            # Logo depois da origem, e não no meio do trecho: o rótulo de uma
            # ramificação diz por onde se sai da decisão, e lido a meio caminho
            # do destino ele deixa de responder a isso.
            (x1, y1), (x2, _y2) = pontos[0], pontos[1]
            lx = x1 + (18 if x2 > x1 else -40)
            marca = (
                f"\n        <bpmndi:BPMNLabel>\n"
                f'          <dc:Bounds x="{lx:.0f}" y="{y1 - 12:.0f}" width="22" height="10" />\n'
                f"        </bpmndi:BPMNLabel>"
            )
        arestas.append(
            f'      <bpmndi:BPMNEdge id="di_{ident}" bpmnElement="{ident}">\n{wp}{marca}\n'
            f"      </bpmndi:BPMNEdge>"
        )

    raias_xml, raias_di = [], []
    for indice, (rid, nome) in enumerate(RAIAS):
        refs = "\n".join(
            f"        <bpmn:flowNodeRef>{n[0]}</bpmn:flowNodeRef>" for n in p.nos if n[3] == rid
        )
        raias_xml.append(
            f'      <bpmn:lane id="{rid}" name="{escape(nome)}">\n{refs}\n      </bpmn:lane>'
        )
        x, largura = p._limite_da_raia(indice)
        raias_di.append(
            f'      <bpmndi:BPMNShape id="di_{rid}" bpmnElement="{rid}" isHorizontal="false">\n'
            f'        <dc:Bounds x="{x:.0f}" y="{POOL_Y + CAB_RAIA}" '
            f'width="{largura:.0f}" height="{p.altura - CAB_RAIA:.0f}" />\n'
            f"      </bpmndi:BPMNShape>"
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  Processo da fase preparatória de uma contratação, em BPMN 2.0.

  GERADO por `scripts/montar_bpmn.py`. Rodar aquele script SOBRESCREVE este
  arquivo: ajuste feito à mão aqui, ou numa ferramenta de modelagem, é
  descartado. O arquivo existe para ser **aberto e conferido** em qualquer
  ferramenta da notação, inclusive a indicada pela orientação.

  As raias são verticais (`isHorizontal="false"`), e isso é deliberado: o
  processo tem catorze etapas, e nessa disposição ele ocupa o eixo longo da
  página, em vez de exigir uma figura larga demais para a coluna de texto.

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
    <bpmn:participant id="pool_prefeitura" name="Prefeitura — {escape(p.titulo)}"
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
      <bpmndi:BPMNShape id="di_pool" bpmnElement="pool_prefeitura" isHorizontal="false">
        <dc:Bounds x="{POOL_X}" y="{POOL_Y}" width="{p.largura:.0f}" \
height="{p.altura:.0f}" />
      </bpmndi:BPMNShape>
{nl.join(raias_di)}
{nl.join(formas)}
{nl.join(arestas)}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


def main() -> None:
    for sufixo, titulo, nos, fluxos in PARTES:
        parte = Parte(sufixo, titulo, nos, fluxos)
        parte.conferir()
        arquivo = DESTINO.with_name(f"processo-licitacao-{sufixo}.bpmn")
        arquivo.write_text(_xml(parte), encoding="utf-8")
        print(
            f"{arquivo.name}: {len(nos)} nós, {len(fluxos)} ligações, "
            f"{parte.largura:.0f}x{parte.altura:.0f} pt"
        )


if __name__ == "__main__":
    main()
