---
tipo: paper
autores: ["Michele A. Brandão", "Arthur P. G. Reis", "Bárbara M. A. Mendes", "Clara A. Bacha de Almeida", "Gabriel P. Oliveira", "Henrique Hott", "Larissa D. Gomide", "Lucas L. Costa", "Mariana O. Silva", "Anisio Lacerda", "Gisele L. Pappa"]
ano: 2024
titulo: "PLUS: A Semi-automated Pipeline for Fraud Detection in Public Bids"
venue: "Digital Government: Research and Practice, v. 5, n. 1, artigo 5"
tags: [trabalhos-relacionados, pesquisa-de-precos, trilha-de-auditoria, controle-externo, brasil]
citacao_abnt: "BRANDÃO, Michele A. et al. PLUS: a semi-automated pipeline for fraud detection in public bids. Digital Government: Research and Practice, [s. l.], v. 5, n. 1, art. 5, p. 1-16, mar. 2024. DOI: 10.1145/3616396."
arquivo_local: ""
verificado: true
---

# PLUS: A Semi-automated Pipeline for Fraud Detection in Public Bids

> **`verificado: true`** — conferido em 06/10/2026 contra a primeira página do
> PDF da editora (bloco "ACM Reference format" e rodapé): periódico, volume,
> número, artigo 5, março de 2024, 16 páginas, DOI e os onze autores na ordem.
> A base de busca informava 2023, que é a data de publicação antecipada; o
> fascículo é de 2024. O PDF foi lido na página da ACM e não ficou salvo em
> disco, por isso `arquivo_local` está vazio.

## Síntese

Os autores, da UFMG e do IFMG, propõem um fluxo semiautomático para organizar
documentos de licitação de Minas Gerais e torná-los analisáveis por quem
fiscaliza. O fluxo tem dois módulos — um classificador de tipo de documento por
palavras-chave e um módulo de qualidade de dados — e alimenta um armazém de
dados. Sobre esse armazém são descritas duas aplicações: trilhas de auditoria
para indício de fraude e um banco de preços de referência para detectar
sobrepreço. O trabalho foi feito em parceria com o Ministério Público do estado.

## Contribuições

- Fluxo reproduzível para tratar documentos longos de licitação.
- Meta-classificador heurístico em quatro classes (ata, edital,
  adjudicação/homologação, outros), usando só título e primeira página.
- Indicadores de qualidade de dados, nativos e sob medida, executados a cada
  carga.
- Onze trilhas de auditoria derivadas de dois tipos de regra: vínculo entre
  licitantes e restrição de licitante.
- Primeira versão de um banco de preços de referência com alerta de sobrepreço.

## Método

Dados: 378.137 licitações de 2014 a 2021 (14.565 estaduais e 363.572
municipais), de 17 modalidades, com 103.858 empresas licitantes. Fontes: sistema
de contas municipais do tribunal de contas estadual, portal de transparência do
estado, portais de 18 municípios, e cadastros federais de empresas e de
sancionadas.

O classificador foi avaliado em 6.337 documentos de 18 municípios, rotulados à
mão pelo título. A qualidade de dados é medida por indicadores com sucesso ou
falha por tabela.

O banco de preços agrupa itens pela descrição textual, com algoritmo de
agrupamento, e marca como sobrepreço o item cujo preço unitário se afasta da
média do grupo além de um múltiplo do desvio-padrão — a regra usual citada é
três desvios.

## Resultados-chave

- Classificador com acerto acima de 90% na classe edital; a confusão maior é
  entre "outros" e "ata".
- Entre 16% e 57% dos indicadores de qualidade falham, conforme a tabela;
  valores nulos e fora do esperado são os erros mais comuns.
- 211.459 licitações com algum alerta (55,9%), das quais 196.517 vêm da trilha
  de licitante único. Sem ela, restam 15.430 (4,1%).
- As trilhas de e-mail e telefone em comum geram falso positivo: muitas
  empresas cadastram os dados do escritório de contabilidade.

## Limitações

- Só dados brasileiros, e várias etapas dependem de conhecimento desses
  documentos.
- O fluxo exige intervenção de especialista.
- A classe "outros" concentra a maior parte dos documentos.
- O banco de preços é descrito sem avaliação quantitativa neste artigo; a
  medição está em trabalhos do mesmo grupo — ver [[silva-2024-sobrepreco-itens-licitacao]]
  e [[brum-2024-agrupamento-itens-similares]].

## Relevância para este TCC

É o trabalho brasileiro mais próximo do módulo de preços, e as diferenças
precisam ser ditas com cuidado, porque dois termos coincidem e os conceitos não.

**"Trilha de auditoria" aqui é outra coisa.** No artigo, é uma sequência de
passos para achar indício de irregularidade em licitações já realizadas. Neste
TCC, é o registro de cada decisão do operador e o que permite reconstituir uma
pesquisa como estava na data. Citar o PLUS como precedente de trilha
reproduzível seria erro.

**O banco de preços serve ao controle, não ao planejamento.** Ele olha para
trás, para apontar preço suspeito; não ajuda quem está montando a cotação a
decidir se um preço candidato é comparável ao item pedido. O agrupamento é por
texto da descrição, sem filtro de unidade, quantidade ou natureza como condição.

Sustenta, na seção de trabalhos relacionados, a afirmação de que há tratamento
computacional de preço de licitação no Brasil em escala estadual, voltado ao
controle externo.

## Citáveis

> "an audit trail is a sequence of steps necessary to identify evidence of
> specific irregularities in public bids" (Brandão et al., 2024, p. 5:11)

> "we also apply a clustering algorithm to group similar bidding items to define
> price reference groups" (Brandão et al., 2024, p. 5:13)

> "audit trails are very useful in the fraud detection process but they must not
> be used alone" (Brandão et al., 2024, p. 5:12)

## Backlinks

- [[silva-2024-sobrepreco-itens-licitacao]]
- [[brum-2024-agrupamento-itens-similares]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
