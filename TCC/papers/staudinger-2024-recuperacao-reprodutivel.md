---
tipo: paper
autores: ["Moritz Staudinger", "Florina Piroi", "Andreas Rauber"]
ano: 2024
titulo: "Reproducible Hybrid Time-Travel Retrieval in Evolving Corpora"
venue: "Proceedings of the 2024 Annual International ACM SIGIR Conference on Research and Development in Information Retrieval in the Asia Pacific Region (SIGIR-AP '24)"
tags: [fundamentacao, trilha-de-auditoria, reprodutibilidade, recuperacao-de-informacao, banco-de-dados-temporal]
citacao_abnt: "STAUDINGER, Moritz; PIROI, Florina; RAUBER, Andreas. Reproducible hybrid time-travel retrieval in evolving corpora. In: ANNUAL INTERNATIONAL ACM SIGIR CONFERENCE ON RESEARCH AND DEVELOPMENT IN INFORMATION RETRIEVAL IN THE ASIA PACIFIC REGION (SIGIR-AP), 2024, Tokyo. Proceedings [...]. New York: ACM, 2024. DOI: 10.1145/3673791.3698421."
arquivo_local: "TCC/papers/staudinger-2024-recuperacao-reprodutivel.pdf"
verificado: true
---

# Reproducible Hybrid Time-Travel Retrieval in Evolving Corpora

> **`verificado: true`**, com uma ressalva. Conferido em 06/10/2026 contra o
> bloco de referência impresso no próprio PDF: autores, título, evento, datas (9
> a 12 de dezembro de 2024), cidade, editora, DOI e extensão de 6 páginas. O PDF
> lido é a versão depositada pelos autores (arXiv:2411.04051v1), que **não traz
> a paginação dos anais**. O registro do DOI indica páginas 203-208; esse
> intervalo não foi visto no PDF da editora e por isso ficou fora da referência.

## Síntese

Grupo da Universidade Técnica de Viena. O problema: num acervo que muda, uma
busca ranqueada repetida mais tarde devolve outra lista — mesmo para os
documentos que não mudaram, porque as estatísticas globais de termos mudaram.
Onde se exige reprodutibilidade, a saída costuma ser busca booleana com filtro
de data. O artigo propõe um sistema híbrido: um motor de busca convencional
atende as consultas, e um banco colunar versionado guarda o estado do índice ao
longo do tempo, permitindo reexecutar uma consulta antiga e obter a mesma lista
ordenada.

## Contribuições

- Arquitetura híbrida de motor de busca mais banco colunar versionado.
- Esquema com intervalo de validade em cada documento, de modo que as
  estatísticas do acervo possam ser recalculadas para qualquer instante.
- Registro de cada consulta com identificador persistente, instante de execução
  e resumo criptográfico do resultado, usado para conferir a reexecução.
- Aplicação, à recuperação de informação, das recomendações de citação de dado
  dinâmico de uma aliança internacional de dados de pesquisa.

## Método

O modelo de ordenação é reescrito como consulta SQL sobre as tabelas
versionadas, filtrando pelo instante original.

Avaliação com 520 mil artigos de uma enciclopédia aberta em alemão, inseridos em
26 lotes. A cada lote, 400 consultas de um a dez termos, recuperando os vinte
primeiros. Medem-se tempo de indexação, tempo de consulta, diferença de
pontuação entre os dois sistemas e espaço.

## Resultados-chave

- Listas idênticas nos dois sistemas. Em 10.400 consultas, **um** caso de dois
  documentos trocados de posição por imprecisão de ponto flutuante, detectado
  pelo resumo criptográfico e corrigido.
- Consulta no motor convencional em cerca de 80 ms, estável. No banco
  versionado, de 2 a 20 segundos, crescendo com o acervo — aceitável para
  reexecução, proibitivo para uso ao vivo.
- O armazenamento praticamente dobra.

## Limitações

- Só cobre ordenação esparsa por um modelo clássico. **Recuperação densa
  reproduzível é declarada como trabalho futuro**, assim como reordenação
  neural.
- Avaliado sobre cópia estática do acervo, com atualização simulada em lotes.
- O banco versionado não foi otimizado para acervos maiores.

## Relevância para este TCC

Não é trabalho correlato de domínio — não fala de governo nem de compras. É
**fundamentação técnica** do requisito de reconstituir uma pesquisa de preços
tal como estava na data (RF30) e da trilha imutável (RNF08).

Importa por três razões:

1. **Dá nome e literatura ao problema.** O que o requisito pede chama-se, na
   área, recuperação reproduzível ou consulta com viagem no tempo sobre acervo
   que evolui. Sem isso, o requisito parece capricho do domínio; com isso, é
   problema reconhecido.
2. **Mostra onde a técnica para.** A solução publicada cobre busca por palavra.
   Para busca por proximidade de significado, que é o caso deste TCC, os autores
   dizem que fica para depois. É uma lacuna declarada por quem trabalha no
   assunto, e não inferida por ausência de resultado.
3. **Expõe a decisão de projeto que ainda falta tomar.** Há dois caminhos para
   reconstituir: **reexecutar** a consulta sobre o estado antigo do índice, que é
   o que o artigo faz, ou **guardar o resultado** tal como foi apresentado —
   candidatos, ordem e decisões. O artigo menciona o segundo como a alternativa
   corrente. O requisito de trilha deste TCC já aponta para guardar o que estava
   disponível e o que foi escolhido; se isso basta, ou se a reexecução também
   será exigida, é decisão em aberto e muda o desenho do armazenamento.

O registro de consulta com instante e resumo criptográfico do resultado é
mecanismo diretamente aproveitável na trilha.

## Citáveis

> "there are cases where, given a set of documents as a result of a search
> process, these search results must be traceable or reproducible at a later
> point in time" (Staudinger; Piroi; Rauber, 2024, p. 1 da versão dos autores)

> "Future work will focus on extending the range of retrieval models that are
> supported and mirrored by the column-store system beyond BM25, especially to
> enable reproducible dense retrieval." (Staudinger; Piroi; Rauber, 2024, p. 5
> da versão dos autores)

> "it is currently not possible to cite subsets of search engine results for
> tasks such as systematic literature reviews, without using Boolean Information
> Retrieval or storing the complete result sets" (Staudinger; Piroi; Rauber,
> 2024, p. 3 da versão dos autores)

## Backlinks

- [[sampaio-2026-indicadores-risco-proveniencia]]
- [[../decisões/2026-09-07-cobertura-de-fontes-e-memoria-de-calculo]]
