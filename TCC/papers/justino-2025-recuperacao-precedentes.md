---
tipo: paper
autores: ["Adrielson Ferreira Justino", "Antônio Fernando Lavareda Jacob Junior", "Fábio Manoel França Lobato"]
ano: 2025
titulo: "A Comparative Study of BERT Models for Semantic Retrieval of Brazilian Legal Precedents"
venue: "Anais do XIII Symposium on Knowledge Discovery, Mining and Learning (KDMiLe 2025)"
tags: [fundamentacao, representacao-de-texto, recuperacao-de-informacao, portugues, brasil, decisao-a2]
citacao_abnt: "JUSTINO, Adrielson Ferreira; JACOB JUNIOR, Antônio Fernando Lavareda; LOBATO, Fábio Manoel França. A comparative study of BERT models for semantic retrieval of Brazilian legal precedents. In: SYMPOSIUM ON KNOWLEDGE DISCOVERY, MINING AND LEARNING (KDMILE), 13., 2025, Fortaleza. Anais [...]. Porto Alegre: Sociedade Brasileira de Computação, 2025. p. 65-72. DOI: 10.5753/kdmile.2025.247782."
arquivo_local: "TCC/papers/justino-2025-recuperacao-precedentes.pdf"
verificado: true
---

# A Comparative Study of BERT Models for Semantic Retrieval of Brazilian Legal Precedents

> **`verificado: true`** — conferido em 06/10/2026. Autores, evento, cidade e
> paginação (65 a 72), no cabeçalho e no rodapé do PDF; edição, local e editora,
> na referência fornecida pela biblioteca digital da SBC na página do artigo.
> O título é em inglês, mas **o texto é em português**. Um dos autores é da
> UFOPA.

## Síntese

Trabalho da Universidade Estadual do Maranhão com a UFOPA, em cooperação com o
tribunal de justiça do Maranhão. Compara cinco modelos de linguagem em português
na tarefa de, dada uma petição inicial, recuperar petições anteriores do mesmo
precedente. Os modelos são de três classes: um de uso geral, três especializados
em texto jurídico, e um ajustado para similaridade de sentenças. A pergunta é o
que pesa mais na qualidade da busca: conhecer o domínio ou ser treinado para a
tarefa.

## Contribuições

- Comparação direta entre especialização de domínio e especialização de tarefa,
  em recuperação, em português.
- Fluxo de segmentação, indexação vetorial e agregação por documento, de baixo
  custo.
- Linha de base para recuperação de precedentes em português.

## Método

Acervo de 7.031 petições, com 70% indexadas e 30% usadas como consulta. Cada
petição é cortada em trechos de até 480 unidades, com sobreposição. Os vetores
vão para um motor de busca com campo de vetor denso; a pontuação do documento é
a soma das pontuações de seus trechos.

Sem ajuste dos modelos para a tarefa. **A relevância não foi julgada por
pessoa:** considera-se relevante a petição que tem a mesma classe de precedente
da consulta.

## Resultados-chave

| Modelo | Classe | Precisão no 1º | Precisão média |
|---|---|---|---|
| Ajustado para similaridade | tarefa | 0,787 | 0,806 |
| Jurídico A | domínio | 0,778 | 0,805 |
| Jurídico B | domínio | 0,780 | 0,801 |
| Jurídico C | domínio | 0,774 | 0,802 |
| Geral de português | geral | 0,778 | 0,801 |

- O modelo ajustado para similaridade fica à frente em quase todas as medidas.
- Os modelos de domínio ficam "muito próximos ou ligeiramente superiores" ao
  geral; os autores qualificam o ganho como marginal.

## Limitações

Declaradas: relevância por indicador substituto, sem validação por
especialista; classes raras agrupadas; uma só estratégia de agregação; medidas
restritas aos quinze primeiros.

Da leitura, e pesam na interpretação:

- **Não há teste de significância, e as diferenças são de menos de um ponto.**
  A leitura honesta da tabela é que os cinco modelos são indistinguíveis neste
  experimento, e não que um deles é "consistentemente superior".
- **Uma só classe concentra metade do acervo** (3.576 de 7.031 petições). Com
  relevância definida por classe, acertar a classe dominante já garante
  pontuação alta para qualquer modelo, o que comprime as diferenças.

## Relevância para este TCC

Entra como **segunda fonte, revisada por pares e em português**, para o que
[[stekel-2026-mteb-br]] mostra em escala maior: em recuperação, especializar o
modelo no domínio por pré-treino rende pouco ou nada.

O que sustenta, com a força que tem:

- **Sustenta bem:** três modelos especializados em texto jurídico não se
  distinguiram de um modelo geral ao recuperar texto jurídico. É evidência
  direta contra esperar ganho grande de [[lima-2026-helbert]] só por ele ser de
  licitação.
- **Sustenta fracamente:** que o ajuste para similaridade seja o fator
  determinante. A vantagem existe na tabela, mas é menor que o ruído provável.

Dois usos de método, pelo exemplo e pelo contraexemplo:

1. O desenho em três classes — geral, domínio, tarefa — é o que a bateria de
   testes deste trabalho deve reproduzir, porque isola a pergunta certa.
2. A avaliação por indicador substituto sem teste de significância é o que
   **não** repetir. Este trabalho tem gabarito humano; falta acrescentar o teste
   pareado.

Há ainda um ponto prático: é um grupo com vínculo na própria universidade
trabalhando com recuperação semântica em português para o setor público.

## Citáveis

> "a otimização da arquitetura do SBERT para gerar vetores de similaridade teve
> um impacto mais determinante do que a especialização do vocabulário no domínio
> jurídico" (Justino; Jacob Junior; Lobato, 2025, p. 70)

> "a magnitude dessa melhoria foi marginal em métricas mais abrangentes como o
> MAP" (Justino; Jacob Junior; Lobato, 2025, p. 70)

## Backlinks

- [[stekel-2026-mteb-br]]
- [[lima-2026-helbert]]
- [[rassin-2024-anotacao-parcial-recuperacao]]
