"""Testes da medição documental.

Os números que a especificação de requisitos afirma — similaridade entre
seções, preços por item, cobertura de procedência — precisam ser reproduzíveis
por quem ler o trabalho. Um número que só existe porque alguém rodou um comando
uma vez não é medição, é lembrança.

Estes testes usam **fixtures sintéticas**, nunca documento real: a política de
dados do projeto proíbe dado verdadeiro em teste, e a medição não depende dele
para ser verificada. O que se testa aqui é o instrumento, não o dado.
"""

from __future__ import annotations

import pytest

from scripts import medicao_documental as md

# --- Fixtures sintéticas -----------------------------------------------------

ETP_SINTETICO_A = """ESTUDO TÉCNICO PRELIMINAR
03-DESCRIÇÃO DA NECESSIDADE
(Art.18,§1°,I)
3.1. A aquisição de guarda-chuvas atende à necessidade da secretaria fictícia.
04-REQUISITOS DA CONTRATAÇÃO
4.1. O objeto deve ser entregue lacrado.
13 - CONTRATAÇÕES CORRELATAS
13.1. Não se faz necessária a realização de contratações correlatas.
"""

ETP_SINTETICO_B = """ESTUDO TÉCNICO PRELIMINAR
03-DESCRIÇÃO DA NECESSIDADE
(Art.18,§1°,I)
3.1. A contratação de bicicletas serve ao transporte de equipes ribeirinhas.
04-REQUISITOS DA CONTRATAÇÃO
4.1. O objeto deve ser entregue lacrado.
13 - CONTRATAÇÕES CORRELATAS
13.1. Não se faz necessária a realização de contratações correlatas.
"""

COTACAO_SINTETICA = """Relatório de Cotação: EXEMPLO SINTÉTICO
Pesquisa realizada entre 01/03/2026 10:00:00 e 10/03/2026 11:00:00
Método Matemático Aplicado: Média Aritmética dos preços obtidos

  Item 1: GUARDA-CHUVA

Preço (Compras Governamentais) 1: Mediana das Propostas Finais    R$ 10,00
   CNPJ: 00.000.000/0001-00                Data: 01/02/2026
   Órgão: MUNICIPIO FICTÍCIO A
   Fonte: https://exemplo.gov.br/app/editais/1/2026/1
   UF: PA

Preço (Outros Entes Públicos) 2: Mediana das Propostas Finais     R$ 12,00
   CNPJ: 00.000.000/0001-01                Data: 15/01/2026
   Órgão: MUNICIPIO FICTÍCIO B
   Fonte: plataforma.exemplo.com.br
   UF: SP

Preço (Compras Governamentais) 3: Mediana das Propostas Finais    R$ 14,00
   CNPJ: 00.000.000/0001-02                Data: 20/03/2025
   Órgão: MUNICIPIO FICTÍCIO C
   Fonte: https://exemplo.gov.br/app/editais/3/2025/9
   UF: PA

  Item 2: CAPA DE CHUVA

Preço (Compras Governamentais) 1: Mediana das Propostas Finais    R$ 20,00
   CNPJ: 00.000.000/0001-03                Data: 05/02/2026
   Órgão: MUNICIPIO FICTÍCIO D
   Fonte: https://exemplo.gov.br/app/editais/4/2026/2
   UF: PA
"""


# --- Similaridade ------------------------------------------------------------


def test_texto_identico_da_um():
    assert md.similaridade("o mesmo texto aqui", "o mesmo texto aqui") == 1.0


def test_textos_sem_nada_em_comum_dao_zero():
    assert md.similaridade("guarda chuva azul", "bicicleta vermelha ontem") == 0.0


def test_similaridade_e_simetrica():
    a, b = "prazo de entrega de trinta dias", "entrega em trinta dias corridos"
    assert md.similaridade(a, b) == md.similaridade(b, a)


def test_acento_e_caixa_nao_alteram_o_resultado():
    assert md.similaridade("Análise Técnica Preliminar", "analise tecnica preliminar") == 1.0


def test_pontuacao_nao_conta_como_diferenca():
    assert md.similaridade("entrega, lacrada.", "entrega lacrada") == 1.0


def test_a_unidade_de_comparacao_e_a_palavra_e_nao_o_caractere():
    """Duas palavras distintas que compartilham letras não podem parecer iguais."""
    assert md.similaridade("cotação", "coação") == 0.0


def test_similaridade_parcial_fica_entre_zero_e_um():
    v = md.similaridade(
        "o objeto deve ser entregue lacrado no prazo",
        "o objeto deve ser entregue no prazo combinado",
    )
    assert 0.0 < v < 1.0


# --- Fatiamento em seções ----------------------------------------------------


def test_reconhece_as_secoes_numeradas():
    secs = md.secoes(ETP_SINTETICO_A)
    assert sorted(secs) == ["03", "04", "13"]


def test_a_secao_carrega_o_proprio_texto_ate_a_seguinte():
    secs = md.secoes(ETP_SINTETICO_A)
    assert "guarda-chuvas" in secs["03"]
    assert "lacrado" not in secs["03"]


def test_o_cabecalho_e_a_citacao_legal_saem_antes_de_comparar():
    """São fixos pelo modelo. Compará-los mede o formulário, não o texto."""
    secao = md.secoes(ETP_SINTETICO_A)["03"]
    corpo = md.corpo_da_secao(secao)
    assert "DESCRIÇÃO DA NECESSIDADE" not in corpo
    assert "Art.18" not in corpo
    assert "guarda-chuvas" in corpo


def test_comparar_devolve_a_menor_similaridade_entre_todos_os_pares():
    r = md.comparar_secoes({"A": ETP_SINTETICO_A, "B": ETP_SINTETICO_B})
    assert r["13"]["menor"] == pytest.approx(1.0)  # texto idêntico nos dois
    assert r["04"]["menor"] == pytest.approx(1.0)
    assert r["03"]["menor"] < 0.5  # objetos diferentes


def test_descartar_o_cabecalho_derruba_a_similaridade_de_secao_curta():
    """Contraprova de que a correção importa: sem ela, o número sai inflado."""
    a, b = md.secoes(ETP_SINTETICO_A)["03"], md.secoes(ETP_SINTETICO_B)["03"]
    com_cabecalho = md.similaridade(a, b)
    sem_cabecalho = md.similaridade(md.corpo_da_secao(a), md.corpo_da_secao(b))
    assert com_cabecalho - sem_cabecalho > 0.15


def test_comparar_exige_pelo_menos_dois_documentos():
    with pytest.raises(ValueError, match="pelo menos dois"):
        md.comparar_secoes({"A": ETP_SINTETICO_A})


def test_so_compara_secao_presente_em_todos_os_documentos():
    """Seção que só existe em um documento não entra: o par não existe."""
    parcial = ETP_SINTETICO_B.replace("13 - CONTRATAÇÕES CORRELATAS", "99 - SEÇÃO INVENTADA")
    r = md.comparar_secoes({"A": ETP_SINTETICO_A, "B": parcial})
    assert "13" not in r and "99" not in r


# --- Cotação -----------------------------------------------------------------


def test_conta_itens_e_precos():
    c = md.ler_cotacao(COTACAO_SINTETICA)
    assert c.itens == 2
    assert c.precos == 4
    assert c.precos_por_item == pytest.approx(2.0)


def test_le_a_janela_da_pesquisa():
    c = md.ler_cotacao(COTACAO_SINTETICA)
    assert (c.inicio.day, c.inicio.month) == (1, 3)
    assert c.duracao_dias == 9


def test_separa_procedencia_com_link_de_procedencia_so_nomeada():
    c = md.ler_cotacao(COTACAO_SINTETICA)
    assert c.com_link == 3
    assert c.so_dominio == 1
    assert c.sem_fonte == 0


def test_distribui_as_fontes_por_dominio():
    c = md.ler_cotacao(COTACAO_SINTETICA)
    assert c.fontes["exemplo.gov.br"] == 3
    assert c.fontes["plataforma.exemplo.com.br"] == 1


def test_idade_do_preco_conta_do_inicio_da_pesquisa():
    """Regra verificada nos documentos reais: a validade corre da coleta.

    Contar do fim faria preço válido parecer vencido, que foi o erro cometido
    na primeira medição.
    """
    c = md.ler_cotacao(COTACAO_SINTETICA)
    assert c.idade_maxima_dias == 346  # 20/03/2025 até 01/03/2026
    assert c.fora_da_validade == 0


def test_preco_realmente_vencido_e_acusado():
    vencido = COTACAO_SINTETICA.replace("Data: 20/03/2025", "Data: 20/01/2025")
    c = md.ler_cotacao(vencido)
    assert c.fora_da_validade == 1


def test_cotacao_vazia_nao_estoura():
    c = md.ler_cotacao("Relatório de Cotação: nada aqui\n")
    assert c.itens == 0 and c.precos == 0 and c.precos_por_item == 0.0
