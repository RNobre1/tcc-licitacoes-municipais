# Normas de formatação — UFOPA

> ARQUIVO GERADO — não edite à mão. Fonte: scripts/normas_ufopa.py

Destilado operacional do guia oficial da instituição: apenas o que o
template LaTeX precisa obedecer. Para os casos não cobertos aqui
(referências de cada tipo de documento, formas de citação, notas de
rodapé), consulte o guia completo.

- **Norma:** UNIVERSIDADE FEDERAL DO OESTE DO PARÁ. Sistema Integrado de Bibliotecas. Guia para a elaboração e apresentação da produção acadêmica da Ufopa. 3. ed. rev. e atual. Santarém: Ufopa, 2025.
- **Cópia local:** [`docs/normas/guia-ufopa-producao-academica-3ed-2025.pdf`](guia-ufopa-producao-academica-3ed-2025.pdf)

Todo valor abaixo vive em `scripts/normas_ufopa.py` e é verificado no PDF
compilado por `tests/test_conformidade_pdf.py`.

## Página e mancha gráfica

| Item | Valor | Seção do guia | Por quê |
|---|---|---|---|
| `papel` | a4paper | 2.1 Formato | NBR 14724:2024 — texto em cor preta, papel A4. |
| `margem_esquerda` | 3cm | 2.2 Margens | Margens esquerda e superior de 3 cm. |
| `margem_superior` | 3cm | 2.2 Margens | Margens esquerda e superior de 3 cm. |
| `margem_direita` | 2cm | 2.2 Margens | Margens direita e inferior de 2 cm. |
| `margem_inferior` | 2cm | 2.2 Margens | Margens direita e inferior de 2 cm. |
| `recuo_paragrafo` | 2cm | 2.2 Margens | 'Para o recuo da primeira linha do parágrafo, recomenda-se um recuo de 2 cm.' Difere do padrão abnTeX2 (1,5 cm) — não herdar o default. |
| `recuo_citacao_longa` | 4cm | 2.2 Margens | Citação com mais de três linhas: recuo de 4 cm da margem esquerda, justificada, sem aspas, com 1,5 cm de espaço antes e depois. |
| `distancia_paginacao_borda` | 2cm | 2.6 Paginação | Número de página no canto superior direito, a 2 cm da borda superior e o último algarismo a 2 cm da borda direita. |

## Tipografia

| Item | Valor | Seção do guia | Por quê |
|---|---|---|---|
| `familia_fonte` | Times New Roman | 2.3 Fonte | 'Recomenda-se o tipo da fonte, Times New Roman ou Arial'. Escolhida Times: em pdfLaTeX o substituto livre (Nimbus Roman, via mathptmx) é metricamente idêntico, o que não vale para Arial. |
| `corpo_fonte_pt` | 12 | 2.3 Fonte | Corpo 12 em todo o trabalho, inclusive na capa. |
| `corpo_fonte_menor_pt` | 10 | 2.3 Fonte | Tamanho menor e uniforme para citações longas, notas de rodapé, paginação, ficha catalográfica, legendas e fontes de ilustrações. |
| `espacamento_corpo` | 1,5 | 2.4 Espaçamento | Todo o texto em espaçamento 1,5 entre linhas. |
| `espacamento_simples_em` | citações longas; notas de rodapé; ficha catalográfica; referências; legendas de ilustrações e tabelas; natureza do trabalho | 2.4 Espaçamento | Exceções explícitas ao espaçamento 1,5. Referências separadas entre si por um espaço simples em branco. |

## Estrutura e numeração

| Item | Valor | Seção do guia | Por quê |
|---|---|---|---|
| `titulos_sem_indicativo` | errata; agradecimentos; listas; resumos; sumário; referências; glossário; apêndices; anexos; índices | 2.5.1 Títulos sem indicativo numérico | Devem ser centralizados e sem numeração de seção. |
| `elementos_sem_titulo` | folha de aprovação; dedicatória; epígrafe | 2.5.2 Elementos sem títulos e sem indicativo numérico | Não recebem título nem indicativo numérico. |
| `nivel_maximo_secao` | 5 | 2.7 Numeração progressiva | 'Deve-se limitar a numeração progressiva até a seção quinária.' |
| `pontuacao_apos_indicativo` | nenhuma | 2.7 Numeração progressiva | 'Não se utilizam ponto, hífen, travessão ou qualquer sinal após o indicativo de seção ou de seu título.' |
| `secao_primaria_nova_pagina` | sim | 2.5 Indicativo de seção | Títulos de seções primárias começam em nova página, no topo da mancha gráfica, separados do texto por espaço de 1,5. |
| `paginacao_conta_desde` | folha de rosto | 2.6 Paginação | Pré-textuais são contados mas não numerados; a numeração aparece a partir da primeira folha da parte textual, em algarismos arábicos. |

## Resumo

| Item | Valor | Seção do guia | Por quê |
|---|---|---|---|
| `resumo_palavras` | 150 a 500 | 3.2.8 Resumo | NBR 6028 — trabalhos acadêmicos: 150 a 500 palavras, parágrafo único, frases afirmativas, sem enumeração de tópicos. |
| `palavras_chave` | 3 a 5 | 3.2.8 Resumo | Separadas por ponto e vírgula, finalizadas por ponto, iniciais minúsculas exceto nomes próprios e científicos. |

## Citações e referências

| Item | Valor | Seção do guia | Por quê |
|---|---|---|---|
| `sistema_chamada` | autor-data | 5.3 Sistema de chamada | Autor-data ou numérico; o guia registra o autor-data como o mais usado e exemplifica com ele em todo o documento. |
| `caixa_na_citacao` | caixa e baixa | 5.3 Sistema de chamada | Os exemplos do guia são '(Barbosa, C., 1958)', '(Santos, 2011a, p. 50)' e '(Brasil, 2005b)' — padrão NBR 10520:2023, sem versalete nem caixa alta. É o comportamento default do biblatex-abnt (toggle 'accite' desligado); ligar 'accite' violaria a norma. |
| `caixa_na_referencia` | sobrenome em caixa alta | 4.1.1 Com um(a) autor(a) | Os exemplos do guia são 'CANTO, Sidney Augusto.' e 'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS.' — NBR 6023:2018 mantida na lista. |

## O que o teste ainda não cobre

Verificação automática alcança o mensurável no PDF: tamanho da página,
fonte embutida, margens, tamanho do resumo, caixa das citações. O resto
continua sendo leitura atenta antes da entrega:

- ordem dos elementos pré-textuais e sua paginação;
- ficha catalográfica (solicitada via SIGAA, elaborada por bibliotecário da UFOPA);
- forma de cada referência conforme o tipo de documento;
- citação longa com recuo, espaçamento simples e corpo menor;
- legendas e fontes de ilustrações e tabelas.
