"""Manifesto das normas de formatação da produção acadêmica da UFOPA.

FONTE ÚNICA. Este módulo é o único lugar do repositório onde os valores de
formatação são declarados. Deles derivam, por geração automática:

  - ``texto/comum/ufopa-normas.sty``  (comprimentos e macros do LaTeX)
  - ``docs/normas/README.md``          (tabela operacional para leitura humana)

E contra eles o PDF compilado é verificado em ``tests/test_conformidade_pdf.py``.

Nunca edite o ``.sty`` gerado nem a tabela do README à mão: edite aqui e rode
``python scripts/gerar_normas.py``. O teste ``tests/test_manifesto.py`` falha se
o disco divergir do que este manifesto gera.

Fonte normativa: UNIVERSIDADE FEDERAL DO OESTE DO PARÁ. Sistema Integrado de
Bibliotecas. Guia para a elaboração e apresentação da produção acadêmica da
Ufopa. 3. ed. rev. e atual. Santarém: Ufopa, 2025. Cópia em
``docs/normas/guia-ufopa-producao-academica-3ed-2025.pdf``.

Cada entrada carrega a seção do guia que a justifica. Sem seção, não entra.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Procedência --------------------------------------------------------------

GUIA_EDICAO = "3. ed. rev. e atual."
GUIA_ANO = 2025
GUIA_ARQUIVO = "docs/normas/guia-ufopa-producao-academica-3ed-2025.pdf"
GUIA_CITACAO_ABNT = (
    "UNIVERSIDADE FEDERAL DO OESTE DO PARÁ. Sistema Integrado de Bibliotecas. "
    "Guia para a elaboração e apresentação da produção acadêmica da Ufopa. "
    "3. ed. rev. e atual. Santarém: Ufopa, 2025."
)


@dataclass(frozen=True)
class Norma:
    """Um valor de formatação, com o porquê e a seção do guia que o exige."""

    chave: str
    valor: str
    secao_guia: str
    justificativa: str
    macro_latex: str | None = None
    """Nome do comprimento/macro gerado no .sty. None = não vira macro."""


# --- Página e mancha gráfica --------------------------------------------------

PAGINA = [
    Norma(
        chave="papel",
        valor="a4paper",
        secao_guia="2.1 Formato",
        justificativa="NBR 14724:2024 — texto em cor preta, papel A4.",
    ),
    Norma(
        chave="margem_esquerda",
        valor="3cm",
        secao_guia="2.2 Margens",
        justificativa="Margens esquerda e superior de 3 cm.",
        macro_latex="ufopamargemesquerda",
    ),
    Norma(
        chave="margem_superior",
        valor="3cm",
        secao_guia="2.2 Margens",
        justificativa="Margens esquerda e superior de 3 cm.",
        macro_latex="ufopamargemsuperior",
    ),
    Norma(
        chave="margem_direita",
        valor="2cm",
        secao_guia="2.2 Margens",
        justificativa="Margens direita e inferior de 2 cm.",
        macro_latex="ufopamargemdireita",
    ),
    Norma(
        chave="margem_inferior",
        valor="2cm",
        secao_guia="2.2 Margens",
        justificativa="Margens direita e inferior de 2 cm.",
        macro_latex="ufopamargeminferior",
    ),
    Norma(
        chave="recuo_paragrafo",
        valor="2cm",
        secao_guia="2.2 Margens",
        justificativa=(
            "'Para o recuo da primeira linha do parágrafo, recomenda-se um recuo "
            "de 2 cm.' Difere do padrão abnTeX2 (1,5 cm) — não herdar o default."
        ),
        macro_latex="ufoparecuoparagrafo",
    ),
    Norma(
        chave="recuo_citacao_longa",
        valor="4cm",
        secao_guia="2.2 Margens",
        justificativa=(
            "Citação com mais de três linhas: recuo de 4 cm da margem esquerda, "
            "justificada, sem aspas, com 1,5 cm de espaço antes e depois."
        ),
        macro_latex="ufoparecuocitacao",
    ),
    Norma(
        chave="distancia_paginacao_borda",
        valor="2cm",
        secao_guia="2.6 Paginação",
        justificativa=(
            "Número de página no canto superior direito, a 2 cm da borda superior "
            "e o último algarismo a 2 cm da borda direita."
        ),
        macro_latex="ufopadistpaginacao",
    ),
]

# --- Tipografia ---------------------------------------------------------------

TIPOGRAFIA = [
    Norma(
        chave="familia_fonte",
        valor="Times New Roman",
        secao_guia="2.3 Fonte",
        justificativa=(
            "'Recomenda-se o tipo da fonte, Times New Roman ou Arial'. Escolhida "
            "Times: em pdfLaTeX o substituto livre (Nimbus Roman, via mathptmx) é "
            "metricamente idêntico, o que não vale para Arial."
        ),
    ),
    Norma(
        chave="corpo_fonte_pt",
        valor="12",
        secao_guia="2.3 Fonte",
        justificativa="Corpo 12 em todo o trabalho, inclusive na capa.",
    ),
    Norma(
        chave="corpo_fonte_menor_pt",
        valor="10",
        secao_guia="2.3 Fonte",
        justificativa=(
            "Tamanho menor e uniforme para citações longas, notas de rodapé, "
            "paginação, ficha catalográfica, legendas e fontes de ilustrações."
        ),
    ),
    Norma(
        chave="espacamento_corpo",
        valor="1,5",
        secao_guia="2.4 Espaçamento",
        justificativa="Todo o texto em espaçamento 1,5 entre linhas.",
    ),
    Norma(
        chave="espacamento_simples_em",
        valor=(
            "citações longas; notas de rodapé; ficha catalográfica; referências; "
            "legendas de ilustrações e tabelas; natureza do trabalho"
        ),
        secao_guia="2.4 Espaçamento",
        justificativa=(
            "Exceções explícitas ao espaçamento 1,5. Referências separadas entre "
            "si por um espaço simples em branco."
        ),
    ),
]

# --- Estrutura ----------------------------------------------------------------

ESTRUTURA = [
    Norma(
        chave="titulos_sem_indicativo",
        valor=(
            "errata; agradecimentos; listas; resumos; sumário; referências; "
            "glossário; apêndices; anexos; índices"
        ),
        secao_guia="2.5.1 Títulos sem indicativo numérico",
        justificativa="Devem ser centralizados e sem numeração de seção.",
    ),
    Norma(
        chave="elementos_sem_titulo",
        valor="folha de aprovação; dedicatória; epígrafe",
        secao_guia="2.5.2 Elementos sem títulos e sem indicativo numérico",
        justificativa="Não recebem título nem indicativo numérico.",
    ),
    Norma(
        chave="nivel_maximo_secao",
        valor="5",
        secao_guia="2.7 Numeração progressiva",
        justificativa="'Deve-se limitar a numeração progressiva até a seção quinária.'",
    ),
    Norma(
        chave="pontuacao_apos_indicativo",
        valor="nenhuma",
        secao_guia="2.7 Numeração progressiva",
        justificativa=(
            "'Não se utilizam ponto, hífen, travessão ou qualquer sinal após o "
            "indicativo de seção ou de seu título.'"
        ),
    ),
    Norma(
        chave="secao_primaria_nova_pagina",
        valor="sim",
        secao_guia="2.5 Indicativo de seção",
        justificativa=(
            "Títulos de seções primárias começam em nova página, no topo da "
            "mancha gráfica, separados do texto por espaço de 1,5."
        ),
    ),
    Norma(
        chave="paginacao_conta_desde",
        valor="folha de rosto",
        secao_guia="2.6 Paginação",
        justificativa=(
            "Pré-textuais são contados mas não numerados; a numeração aparece a "
            "partir da primeira folha da parte textual, em algarismos arábicos."
        ),
    ),
]

# --- Resumo -------------------------------------------------------------------

RESUMO_MIN_PALAVRAS = 150
RESUMO_MAX_PALAVRAS = 500
PALAVRAS_CHAVE_MIN = 3
PALAVRAS_CHAVE_MAX = 5

RESUMO = [
    Norma(
        chave="resumo_palavras",
        valor=f"{RESUMO_MIN_PALAVRAS} a {RESUMO_MAX_PALAVRAS}",
        secao_guia="3.2.8 Resumo",
        justificativa=(
            "NBR 6028 — trabalhos acadêmicos: 150 a 500 palavras, parágrafo "
            "único, frases afirmativas, sem enumeração de tópicos."
        ),
    ),
    Norma(
        chave="palavras_chave",
        valor=f"{PALAVRAS_CHAVE_MIN} a {PALAVRAS_CHAVE_MAX}",
        secao_guia="3.2.8 Resumo",
        justificativa=(
            "Separadas por ponto e vírgula, finalizadas por ponto, iniciais "
            "minúsculas exceto nomes próprios e científicos."
        ),
    ),
]

# --- Citações e referências ---------------------------------------------------

CITACAO = [
    Norma(
        chave="sistema_chamada",
        valor="autor-data",
        secao_guia="5.3 Sistema de chamada",
        justificativa=(
            "Autor-data ou numérico; o guia registra o autor-data como o mais "
            "usado e exemplifica com ele em todo o documento."
        ),
    ),
    Norma(
        chave="caixa_na_citacao",
        valor="caixa e baixa",
        secao_guia="5.3 Sistema de chamada",
        justificativa=(
            "Os exemplos do guia são '(Barbosa, C., 1958)', '(Santos, 2011a, p. 50)' "
            "e '(Brasil, 2005b)' — padrão NBR 10520:2023, sem versalete nem caixa "
            "alta. É o comportamento default do biblatex-abnt (toggle 'accite' "
            "desligado); ligar 'accite' violaria a norma."
        ),
    ),
    Norma(
        chave="caixa_na_referencia",
        valor="sobrenome em caixa alta",
        secao_guia="4.1.1 Com um(a) autor(a)",
        justificativa=(
            "Os exemplos do guia são 'CANTO, Sidney Augusto.' e 'ASSOCIAÇÃO "
            "BRASILEIRA DE NORMAS TÉCNICAS.' — NBR 6023:2018 mantida na lista."
        ),
    ),
]

# --- Agregado -----------------------------------------------------------------

GRUPOS: dict[str, list[Norma]] = {
    "Página e mancha gráfica": PAGINA,
    "Tipografia": TIPOGRAFIA,
    "Estrutura e numeração": ESTRUTURA,
    "Resumo": RESUMO,
    "Citações e referências": CITACAO,
}

TODAS: list[Norma] = [n for grupo in GRUPOS.values() for n in grupo]


def por_chave(chave: str) -> Norma:
    """Devolve a norma de chave ``chave``. Erro alto e claro se não existir."""
    for norma in TODAS:
        if norma.chave == chave:
            return norma
    disponiveis = ", ".join(sorted(n.chave for n in TODAS))
    raise KeyError(f"norma '{chave}' não existe no manifesto. Disponíveis: {disponiveis}")


def valor(chave: str) -> str:
    """Atalho para o valor de uma norma."""
    return por_chave(chave).valor


def em_pontos(medida: str) -> float:
    """Converte uma medida do manifesto (ex.: '3cm') para pontos tipográficos.

    Usado pelo teste de conformidade para comparar com o que o PDF entrega.
    1 cm = 28,3465 pt.
    """
    if not medida.endswith("cm"):
        raise ValueError(f"medida '{medida}' não está em cm; converta antes de usar")
    return float(medida.removesuffix("cm").replace(",", ".")) * 28.3464567
