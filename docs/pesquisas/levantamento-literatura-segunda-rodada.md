---
tipo: pesquisa
titulo: "Depois de ler as fontes: quais trabalhos entram no quadro comparativo, e como as lacunas da primeira rodada se saíram?"
status: doze consultas executadas; onze fontes lidas integralmente e conferidas; quadro em rascunho
criado: 2026-10-06
autor: Rafael Nobre de Souza
relacionado:
  - docs/pesquisas/levantamento-literatura-primeira-rodada.md
  - docs/requisitos/README.md
  - docs/arquitetura/README.md
  - TCC/papers/
tags: [pesquisa, literatura, trabalhos-relacionados, quadro-comparativo, pesquisa-de-precos, busca-semantica]
---

# Levantamento de literatura — segunda rodada

> ## O que muda em relação à primeira rodada
>
> A primeira rodada era **fila de leitura**: nada lido, nenhum metadado
> conferido. Esta rodada leu. As duas regras continuam valendo — fonte só entra
> se o texto completo for lido por inteiro, e metadado só vale conferido na
> fonte primária —, e a diferença é que agora há onze fontes que as cumprem.
>
> Cada fonte lida tem fichamento em `TCC/papers/`. O que está abaixo é a
> síntese, a triagem e o rascunho do quadro comparativo.
>
> **Três afirmações da primeira rodada não sobreviveram à leitura** e estão
> corrigidas na seção 6. Elas ficam registradas como caíram, e não apagadas.

## 1. Contexto

A orientação pediu um quadro comparando trabalhos existentes com este,
destacando o diferencial. A primeira rodada tinha candidatos devolvidos pela
base, descritos pelo resumo, e deixava em aberto dois eixos não buscados:
proveniência aplicada a compras públicas e governo digital em município
pequeno.

Entre as duas rodadas, o levantamento de requisitos reformulou o módulo de
preços: o gargalo medido não é coletar nem calcular, é decidir, item por item,
se um preço candidato é comparável ao item pedido. Isso abriu um terceiro eixo
que a primeira rodada não tinha como prever — casamento de descrição de item.

## 2. Pergunta

Lidas as fontes, quais trabalhos são de fato correlatos, em que cada um difere
deste, e quais das lacunas declaradas na primeira rodada continuam de pé?

## 3. Resposta curta

**Oito trabalhos entram no quadro, mais um por exceção autorizada.** Nenhum
junta as duas metades deste trabalho, e nenhum trata a triagem de preço
candidato na fase preparatória.

O mapa, depois da leitura:

- **Preço em licitação brasileira já é tratado, e com escala** — mas para
  controle, depois da contratação. Um grupo de Minas Gerais agrupa milhões de
  itens por descrição para apontar sobrepreço [1][4][5]. Um trabalho de Sergipe
  calcula o preço de referência a partir de cotações já reunidas [3]. Nenhum
  ajuda quem monta a cotação a decidir se o candidato é comparável.
- **Busca por significado em compras públicas já existe** — sobre editais, não
  sobre itens, e avaliada por usabilidade, não por recuperação [2].
- **Geração assistida de documento em órgão público já existe, inclusive em
  prefeitura e em produção** [8]. Em documento de licitação, existe em
  protótipo [9][10], e o relato mais cuidadoso conclui que geração livre e
  exigência de precisão não combinam [9].
- **Proveniência em compras públicas brasileiras já existe** [6] — para
  documentar como um indicador de risco foi derivado, não para reconstituir uma
  pesquisa de preços.
- **Recuperação reproduzível no tempo é problema reconhecido e parcialmente
  resolvido** [11]: para busca por palavra, há solução; para busca por
  proximidade de significado, os próprios autores dizem que fica para depois.

A contribuição defensável ficou **mais estreita e mais bem delimitada** que a
da primeira rodada. Está na seção 7.

## 4. Método

| | |
|---|---|
| **Base** | Consensus (`consensus.app`), agregador de literatura revisada por pares |
| **Data** | 06/10/2026 |
| **Consultas** | 12, uma pergunta por consulta |
| **Filtros** | nenhum — sem recorte de ano, tipo de estudo, país ou área |
| **Devolvidos** | 20 de 20 em todas as consultas |

As consultas, na forma exata em que foram feitas:

| # | Consulta | O que testa |
|---|---|---|
| 1 | *semantic matching of item descriptions in public procurement for price comparison using text embeddings* | eixo novo: casamento de item |
| 2 | *large language models generation of public procurement documents terms of reference tender specification drafting* | lacuna de geração, no domínio exato |
| 3 | *natural language processing Brazilian public procurement bidding documents licitações* | produção brasileira |
| 4 | *data provenance and audit trail for reproducibility of price research in public procurement* | eixo pendente: proveniência em compras |
| 5 | *reference price estimation in Brazilian public procurement using open government purchasing data and item description similarity* | preço de referência no Brasil |
| 6 | *digital government and e-procurement capacity in small municipalities Brazil new public procurement law 14.133 planning phase* | eixo pendente: município pequeno |
| 7 | *retrieval-augmented generation applied to government documents and public administration* | reexecução do eixo 1, que havia mostrado metade |
| 8 | *pesquisa de preços e valor estimado nas contratações públicas municipais estudo técnico preliminar termo de referência* | literatura de administração sobre a fase preparatória |
| 9 | *hybrid lexical and dense retrieval with structured metadata filtering for short noisy product descriptions* | técnica: busca híbrida com filtro |
| 10 | *Portal Nacional de Contratações Públicas PNCP dados abertos análise de contratações* | uso do portal nacional como fonte |
| 11 | *reconstructing past query results with temporal versioning for auditability and reproducibility of search systems* | técnica: reconstituição de consulta |
| 12 | *sistema de apoio à elaboração de estudo técnico preliminar e termo de referência com inteligência artificial generativa* | lacuna de objeto: as duas peças |

Não foram reexecutados os eixos 3, 4 e 5 da primeira rodada, que já haviam
devolvido 20 de 20. O eixo 2 foi coberto pelas consultas 1 e 5, mais
específicas.

### Buscas que voltaram vazias

Registradas de propósito: lacuna afirmada sem busca registrada não se sustenta.

- **Consulta 12.** Nenhum dos vinte resultados trata de estudo técnico
  preliminar ou termo de referência. A base devolveu trabalhos genéricos sobre
  inteligência artificial generativa em revisão de literatura, saúde e
  engenharia. **Não foi encontrado trabalho que gere essas duas peças.**
- **Consulta 8.** Nenhum resultado sobre pesquisa de preços na fase
  preparatória municipal brasileira. Vieram estudos de formação de preço em
  obras na Rússia, República Tcheca e Turquia, e um estudo de custo de
  modalidades num município do Paraná.
- **Consulta 4.** Dezenove dos vinte resultados tratam de proveniência em
  biomedicina, de bases abertas de contratação ou de detecção de fraude. **Um
  só une proveniência e compras públicas** — [6] —, e não trata de preço.
- **Consulta 10.** Nenhum trabalho empírico usa o portal nacional brasileiro
  como fonte de dados. Há dois ensaios jurídicos sobre o portal e bases abertas
  de França, Portugal, Espanha, Romênia e União Europeia.

Limite destas ausências: uma base só, consultas em inglês e português, sem
teses e dissertações brasileiras, que a base cobre mal. "Não encontrado" aqui
quer dizer não encontrado nesta base, com estas consultas.

## 5. Triagem

### Lidas por inteiro e conferidas — onze

| # | Trabalho | Onde foi lido | Entra no quadro |
|---|---|---|---|
| [1] | Brandão et al., 2024 | PDF da editora | sim |
| [2] | Siciliani et al., 2023 | PDF da editora, em repositório institucional | sim |
| [3] | Faria, Silva e Soares, 2025 | PDF nos anais | sim |
| [4] | Silva et al., 2024 | PDF no periódico | sim |
| [5] | Brum et al., 2024 | PDF nos anais | no texto, não no quadro |
| [6] | Sampaio et al., 2026 | PDF nos anais | sim |
| [7] | Musumeci et al., 2024 | preprint | não — ver seção 6 |
| [8] | Van der Meer e Rossi, 2026 | preprint | sim |
| [9] | Gao et al., 2026 | preprint | sim |
| [10] | Zhao e Li, 2024 | preprint | sim |
| [11] | Staudinger, Piroi e Rauber, 2024 | versão dos autores | fundamentação, não quadro |

Quatro foram lidos em preprint. Para três deles existe versão publicada que não
foi aberta; a situação de cada um está no fichamento e na seção 10.

### Cortadas por falta de acesso ao texto completo

A regra manda cortar e buscar outra.

| Trabalho | Por que interessava | Situação |
|---|---|---|
| Laolugsanalerd et al., 2025 — petições jurídicas tailandesas | Era o [23] da primeira rodada: formulário estruturado para documento, com linha de base de tempo medida | Anais de acesso fechado; sem preprint localizado. **Cortado.** O papel de precedente com tempo medido passa a [8] |
| Sofat et al., 2024 — fluxos de compras governamentais na Índia | Avaliação de propostas com modelo de linguagem | Capítulo de acesso fechado. Cortado |
| Mehrbod et al., 2018 — casamento semântico de produto em mercados de licitação | Precedente antigo de busca semântica sobre item | Periódico de acesso fechado. Cortado |
| Felizzola et al., 2024 — análise visual de dado aberto de compras | Contexto | Acesso fechado. Cortado |

### Exceção nominal, autorizada pela orientação

**Billedo et al., 2026** — o [4] da primeira rodada, recuperação e geração sobre
documentos de licitação das Filipinas. Tentativa de acesso refeita em
06/10/2026: a base de busca só tem o resumo; não há preprint; o registro de
acesso aberto o classifica como fechado, sem cópia em repositório; busca pelo
título não achou versão dos autores. **Continua fechado.**

Entra no quadro, e só no quadro, com o que o resumo sustenta, atribuído ao
resumo e não ao trabalho. As células que o resumo não sustenta vão como "não
informado". Nada dele fundamenta afirmação deste TCC. A exceção vale para este
trabalho e não abre precedente.

### Texto disponível, ainda não lido — fila

Acesso aberto confirmado nas quatro primeiras linhas; na última, ainda não
verificado. Faltou tempo para ler. Nenhum pode ser citado antes de lido.

| Trabalho | Por que ler |
|---|---|
| Lima et al., 2026 — modelo de linguagem pré-treinado em documentos de licitação em português (*Journal of the Brazilian Computer Society*) | Pesa diretamente na escolha do modelo de representação. PDF já salvo em `TCC/papers/` |
| Lima et al., 2025 — similaridade entre descrições de objeto contratado (*Procedia Computer Science*) | Mesmo grupo; similaridade semântica sobre objeto de licitação brasileira |
| Montequín et al., 2026 — o [6] da primeira rodada (*Procedia Computer Science*) | Precedente publicado de avaliação com documentos sintéticos. O veículo, que estava "não identificado", é este |
| Nai et al., 2024 — recomendação e geração em compras públicas italianas | Há cópia em repositório institucional |
| Belmiro et al., 2026; Correia et al., 2026 | Extração de informação e conformidade em editais e contratos brasileiros sob a nova lei |

### Devolvidas e descartadas por tangência

Detecção de fraude e conluio; previsão de preço de adjudicação por aprendizado
de máquina; casamento de produto em comércio eletrônico; bases abertas de
contratação de outros países; proveniência em biomedicina. Ficam fora por não
tocarem nem a fase preparatória nem a comparabilidade de item.

A consulta 6 devolveu um conjunto de artigos descritivos brasileiros sobre a
dificuldade de municípios pequenos em implantar a nova lei — falta de
capacitação, de estrutura e de pessoal. Não são trabalhos correlatos, mas são
**candidatos à fundamentação** sobre prefeituras. Vários saem em periódicos de
publicação rápida, cujo rigor precisa ser avaliado um a um antes de qualquer
uso. Nenhum foi lido.

## 6. Três afirmações da primeira rodada que caíram

### 6.1 "Nenhum trabalho de proveniência toca compras públicas"

**Caiu.** [6] toca: é brasileiro, de 2026, e usa um modelo de proveniência para
documentar como indicadores de risco em compras públicas são derivados de bases
abertas federais.

O que resta é mais estreito. Lá, a proveniência serve ao controle, depois da
contratação, e rastreia a derivação de um indicador. Não trata de preço por
item, não está na fase preparatória e não demonstra a reconstituição de um
resultado numa data passada. Os próprios autores apontam, como trabalho futuro,
levar a proveniência a sistemas de apoio à decisão do serviço público.

### 6.2 "Musumeci et al. cobrem geração de documento em administração pública com recuperação"

**Superestimado.** Lido inteiro, [7] descreve um fluxo de três agentes que segue
um documento-modelo seção por seção. Os exemplos são trechos de carta genérica
para uma universidade fictícia; não há documento administrativo real, não há
avaliação quantitativa e não há base de conhecimento — a "recuperação" é busca
dentro do que o usuário já digitou. Sai do quadro e fica como precedente do
desenho de geração por seção.

A hipótese de lacuna de geração **continua derrubada**, mas por outra fonte:
[8], que está em produção numa prefeitura.

### 6.3 O precedente com linha de base de tempo medida

O [23] da primeira rodada sustentava que havia precedente metodológico direto
para a avaliação: tempo de redação medido antes e depois. **O texto completo não
foi obtido, e ele foi cortado.**

O papel é assumido por [8], que foi lido: mede o tempo por carta contra
estimativa histórica — seis horas reduzidas a duas ou três — e quanto da minuta
sobrevive à revisão (81%).

### Duas correções menores de metadado

- O [11] da primeira rodada, com "veículo não identificado", saiu no **SBSI
  2025** [3].
- O [6] da primeira rodada saiu em *Procedia Computer Science*, volume 278.

## 7. Onde sobra espaço, depois da leitura

| # | Lacuna | Como ficou |
|---|---|---|
| 1 | ~~Geração de minuta~~ | **Continua derrubada**, agora por fonte lida [8]. Em documento de licitação há protótipos [9][10] |
| 2 | Reprodutibilidade temporal da pesquisa de preços | **De pé, reformulada.** Não se pode mais dizer que proveniência não chegou às compras públicas [6]. Pode-se dizer que não chegou à pesquisa de preços na fase preparatória, e que reconstituir resultado de busca por proximidade de significado é problema declarado em aberto na literatura de recuperação [11] |
| 3 | Busca vetorial filtrada sob seletividade restritiva | **Não reexaminada nesta rodada.** Ganhou apoio indireto: [5] mostra que número e unidade decidem se dois itens são o mesmo, e [4] que produto e serviço têm de ser separados antes de comparar preço — as duas coisas que o filtro estruturado resolve |
| 4 | Município de pequeno porte | **De pé, média.** Todos os sistemas lidos operam em escala estadual, nacional ou em capital [1][2][8]. A consulta 6 só devolveu estudos descritivos |
| 5 | Estudo técnico preliminar e termo de referência como objeto | **Reforçada por busca vazia.** A consulta 12 não devolveu nenhum trabalho sobre as duas peças |
| 6 | **Nova: triagem de comparabilidade na composição da pesquisa de preços** | **Forte.** Os trabalhos de preço lidos ou partem das cotações já reunidas [3] ou agrupam itens para apontar sobrepreço depois [1][4][5]. Nenhum apoia a decisão, item por item, de quem monta a cotação. E nenhum tem gabarito: [5] declara a falta de referência como limitação; este trabalho tem as escolhas reais de quem cotou |

**Inferência, declarada como tal.** A contribuição defensável é a junção de 6,
2 e 3: recuperar candidatos a preço por proximidade de significado sob filtro
estruturado obrigatório, na fase preparatória, registrando o que estava
disponível e o que foi escolhido de modo que a pesquisa possa ser reconstituída
— e **avaliando isso contra cotações reais**, o que nenhum dos correlatos de
preço faz. As lacunas 4 e 5 dão o recorte de aplicação. Gerar as peças entra
como funcionalidade necessária, com o diferencial de redigir a partir da
evidência do processo em vez de adaptar texto anterior.

O que **não** se pode reivindicar: ser o primeiro a usar busca semântica em
compras públicas [2]; ser o primeiro a tratar preço de licitação brasileira
com computação [1][3][4]; ser o primeiro a gerar documento em prefeitura [8];
ser o primeiro a levar proveniência às compras públicas [6].

## 8. Quadro comparativo — rascunho

Colunas pedidas pela orientação. Cada célula traz o que o texto lido sustenta;
"não nomeada" quer dizer que a norma de contratação não é identificada no
artigo.

| Trabalho | Objeto documental | Etapa do processo | País e norma de referência | Tratamento de preço | Trilha de auditoria reproduzível |
|---|---|---|---|---|---|
| Siciliani et al., 2023 [2] | Editais e anexos; registros estruturados de contratos | Ciclo inteiro, como consulta a casos anteriores; monitoramento | Itália, região da Apúlia. Cita a diretiva europeia de dados abertos; norma de contratação não nomeada | Não trata. Um indicador compara valor adjudicado e valor estimado | Não |
| Brandão et al., 2024 [1] | Documentos de licitação — edital, ata, homologação | Controle, depois da contratação | Brasil, Minas Gerais. Cita a lei de acesso à informação; lei de licitações não nomeada | Banco de preços de referência por agrupamento de descrição; alerta por desvio da média do grupo | Não. "Trilha de auditoria", ali, é regra de investigação de indício de fraude |
| Silva et al., 2024 [4] | Itens licitados — descrição, unidade, valor | Controle, depois da contratação | Brasil, Minas Gerais. Cita a Lei nº 14.133/2021 | Limiar de sobrepreço por intervalo interquartil, dentro de grupo de itens padronizados; separa produto de serviço | Não |
| Faria, Silva e Soares, 2025 [3] | Conjunto de cotações já coletadas | Fase preparatória — cálculo do preço de referência | Brasil, dado federal. Norma não nomeada no corpo do texto | Seletor de tratamento estatístico e modelo para sinalizar sobrepreço e subpreço | Não |
| Sampaio et al., 2026 [6] | Bases abertas federais — contratos, empresas, sanções, eleitoral | Controle e fiscalização | Brasil, esfera federal. Norma não nomeada | Não trata preço por item | **Parcial.** Proveniência da derivação de cada indicador e dado bruto preservado; reconstituição em data passada não demonstrada |
| Van der Meer e Rossi, 2026 [8] | Carta de parecer jurídico em resposta a objeção de cidadão | Fora de compras: revisão administrativa de multa e remoção | Países Baixos, Amsterdã. Direito administrativo local; discute o regulamento europeu de inteligência artificial | Não trata | **Parcial.** Registra fontes, instrução e edições de cada carta; não trata de dado que muda |
| Gao et al., 2026 [9] | Catálogo de critérios de sustentabilidade para o edital | Fase preparatória — redação de critérios do instrumento convocatório | Suíça. Legislação suíça de compras, acordo de compras governamentais da OMC e guia europeu de compras verdes | Não trata | **Parcial.** Endereço de fonte oficial exigido por critério; sem registro de decisão |
| Zhao e Li, 2024 [10] | Documento de licitação, por adaptação de documento anterior | Fase preparatória — redação do instrumento convocatório | China, área médica. Norma não nomeada | Não trata | Não |
| Billedo et al., 2026 — **só pelo resumo** | Documentos de licitação em PDF | Consulta a documentos e regulamentos | Filipinas, lei de compras públicas do país | Não informado | Não informado |
| **Este trabalho** | Documento de formalização de demanda, estudo técnico preliminar, termo de referência, mapa de cotação | **Fase preparatória — redação das peças e triagem de preço candidato** | **Brasil, município de pequeno porte. Lei nº 14.133/2021** | **Recuperação de candidatos por proximidade de significado sob filtro de unidade, quantidade, natureza, região e janela temporal; cálculo pelo critério escolhido pelo operador** | **Sim, por requisito: registro de candidatos disponíveis e escolhidos, autor e critério; reconstituição da pesquisa na data** |

**Recorte sugerido para o artigo**, que tem vinte a vinte e cinco páginas: seis
linhas mais a deste trabalho — Siciliani, Brandão e Silva fundidos numa linha
por serem o mesmo grupo e o mesmo sistema, Faria, Sampaio, Van der Meer e Gao.
Zhao e Billedo ficam para a versão longa.

**Cuidado com a última coluna.** Marcar "sim" para este trabalho descreve
requisito, não resultado: a trilha ainda não foi implementada nem demonstrada.
Na fase de projeto o texto precisa dizer "previsto", e a célula só vira "sim"
sem ressalva depois da demonstração de reconstituição.

## 9. O que a leitura trouxe além do quadro

1. **Sinal lexical é forte em descrição de item.** Em [5], juntar itens pela
   primeira palavra organiza a maior parte de dois milhões de descrições, e
   método simples fica perto de modelo sofisticado. Isso pesa contra decidir o
   modelo de representação sem testar, e a favor de combinar sinal lexical e
   semântico.
2. **Descrição municipal tem mediana de seis palavras** [4]. É a restrição já
   registrada nos requisitos, agora com número publicado sobre doze milhões de
   itens.
3. **Geração livre erra onde documento de licitação não tolera erro** [9]:
   paráfrase no lugar de texto literal, e limiar numérico inventado. Sustenta a
   exigência de fonte conferível e de destaque do trecho a revisar.
4. **Fonte visível e aprovação obrigatória constroem confiança** [8] — o mesmo
   que a usuária declarou como condição de aceitação.
5. **Há duas formas de reconstituir uma pesquisa** [11]: reexecutar a consulta
   sobre o estado antigo do índice, ou guardar o resultado como foi
   apresentado. Os requisitos atuais apontam para a segunda. Se a primeira
   também será exigida é decisão em aberto, e muda o desenho do armazenamento.
6. **O critério de avaliação de [3] contraria a prática observada.** Mede-se lá
   a proximidade ao preço homologado; a usuária entrevistada preserva margem
   acima dele de propósito, porque o valor estimado é teto.

## 10. O que ficou em aberto

- **Versões publicadas não abertas** de três preprints: [7] tem registro de
  capítulo em série de anais, páginas 98-117; [9] tem registro em simpósio de
  2026 com **lista de autores diferente** da do preprint; [10] tem registro em
  conferência de acesso fechado. [8] traz bloco de referência de conferência
  com identificador ainda em branco. Enquanto isso, citam-se os preprints.
- **Cidade do evento de [6]**, que o PDF não informa.
- **Paginação de [4]**, que o PDF não imprime, e de [11], cuja versão dos
  autores não traz a dos anais.
- **Fila de leitura** da seção 5, a começar pelo modelo de linguagem para
  licitação em português.
- **Segunda base.** Continua valendo: uma base só não triangula, e teses e
  dissertações brasileiras ficaram de fora.
- **Sistemas que não são literatura.** O quadro compara trabalhos acadêmicos. A
  orientação falou em "sistemas existentes", o que também abrange sistema de
  governo e produto comercial — o módulo federal de elaboração de estudo
  técnico, o painel federal de preços, os bancos de preços comerciais. Isso
  pede outra fonte, que é documentação oficial e não artigo. Foi tentado em
  06/10/2026 e **não foi possível conferir**: as páginas do portal federal de
  compras com o manual do módulo de estudo técnico e com a descrição do módulo
  de pesquisa de preços responderam "conteúdo restrito", exigindo autenticação.
  Nada sobre esses sistemas entra no quadro enquanto a documentação oficial não
  for lida — descrevê-los de memória seria o mesmo erro que a regra de metadado
  existe para evitar.

## 11. Referências

### Lidas por inteiro e conferidas

Numeração desta nota. Fichamento de cada uma em `TCC/papers/`.

| # | Referência | Identificador |
|---|---|---|
| 1 | Brandão, M. A. et al. PLUS: A Semi-automated Pipeline for Fraud Detection in Public Bids. *Digital Government: Research and Practice*, v. 5, n. 1, art. 5, 2024 | doi:10.1145/3616396 |
| 2 | Siciliani, L. et al. AI-based decision support system for public procurement. *Information Systems*, v. 119, art. 102284, 2023 | doi:10.1016/j.is.2023.102284 |
| 3 | Faria, E. M. B. de; Silva, G. J. F. da; Soares, M. S. Intelligent Methodologies for Preparing Reference Prices in Brazilian Public Biddings. Anais do XXI SBSI, 2025, p. 241-249 | doi:10.5753/sbsi.2025.246450 |
| 4 | Silva, M. O. et al. Overpricing Analysis in Brazilian Public Bidding Items. *Journal on Interactive Systems*, v. 15, n. 1, p. 130-142, 2024 | doi:10.5753/jis.2024.3831 |
| 5 | Brum, P. P. V. et al. Unsupervised Grouping of Public Procurement Similar Items: Which Text Representation Should I Use? Anais da LREC-COLING 2024, p. 17176-17185 | aclanthology.org/2024.lrec-main.1492 |
| 6 | Sampaio, I. et al. Public procurement risk indicators from open government data and provenance model. Anais da EGOV-CeDEM-ePart 2026 | doi:10.59490/6a91adc10fd2bd55cd254870 |
| 7 | Musumeci, E. et al. LLM Based Multi-Agent Generation of Semi-structured Documents from Semantic Templates in the Public Administration Domain. Preprint, 2024 | arXiv:2402.14871v1 |
| 8 | Van der Meer, V.; Rossi, J. LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters. Preprint, 2026 | arXiv:2605.12012v2 |
| 9 | Gao, Y. et al. Generating and Evaluating Sustainable Procurement Criteria for the Swiss Public Sector using In-Context Prompting with Large Language Models. Preprint, 2026 | arXiv:2603.22513v1 |
| 10 | Zhao, Y.; Li, D. A Large Language Model-based Framework for Semi-Structured Tender Document Retrieval-Augmented Generation. Preprint, 2024 | arXiv:2410.09077v1 |
| 11 | Staudinger, M.; Piroi, F.; Rauber, A. Reproducible Hybrid Time-Travel Retrieval in Evolving Corpora. Anais da SIGIR-AP 2024 | doi:10.1145/3673791.3698421 |

### Devolvidas pela base e não lidas

> **Metadados como a base os devolveu, não conferidos. Nada aqui é citável.**

| Título | Autoria informada | Ano | Veículo informado | Identificador |
|---|---|---|---|---|
| Optimizing Retrieval-Augmented Generation for Querying Locally Stored Public Procurement Documents using Small Language Models | Billedo et al. | 2026 | 2nd ICCIAA | doi:10.1109/icciaa68481.2026.11543573 |
| HelBERT: A BERT-Based Pretraining Model for Public Procurement Tasks in Portuguese | Lima et al. | 2026 | J. Braz. Comput. Soc. | doi:10.5753/jbcs.2026.5511 |
| A Deep Learning Approach for Identifying Similarities in Contracted Object Description in Public Procurement | Lima et al. | 2025 | Procedia Computer Science | doi:10.1016/j.procs.2025.07.124 |
| A Dual-Mode Retrieval-Augmented Generation System for Interactive Question Answering of Public Tender Documents | Montequín et al. | 2026 | Procedia Computer Science | doi:10.1016/j.procs.2026.03.134 |
| Large Language Models and Recommendation Systems: A Proof-of-Concept Study on Public Procurements | Nai et al. | 2024 | não identificado | doi:10.1007/978-3-031-70242-6_27 |
| A Comparative Study of Traditional Machine Learning and Large Language Models for Information Extraction in Public Procurement Notices | Belmiro et al. | 2026 | não identificado | doi:10.5220/0014818100004018 |
| An Automated Approach to Contractual Compliance Analysis in Public Bidding Contracts | Correia et al. | 2026 | Journal of Public Administration and Governance | doi:10.5296/jpag.v16i1.23671 |
| BidCorpus: A multifaceted learning dataset for public procurement | Lima et al. | 2024 | Data in Brief | doi:10.1016/j.dib.2024.111202 |
| Evaluating Contextualized Embeddings for Topic Modeling in Public Bidding Domain | Hott et al. | 2023 | não identificado | doi:10.1007/978-3-031-45392-2_27 |
| Reducing Drafting Backlogs with LLMs: A Feasibility Study on Thai Legal Petitions | Laolugsanalerd et al. | 2025 | iSAI-NLP | doi:10.1109/isai-nlp66160.2025.11320533 |
| Speeding up Government Procurement Workflows with LLMs | Sofat et al. | 2024 | não identificado | doi:10.1007/978-3-031-68211-7_3 |
| Application of a semantic product matching mechanism in open tendering e-marketplaces | Mehrbod et al. | 2018 | Journal of Public Procurement | doi:10.1108/jopp-03-2018-002 |
| Software Procurement Duplicate Detection Using Fuzzy Matching and LLM Verification | Liao et al. | 2026 | IEEE ICCT-Pacific | doi:10.1109/icct-pacific69083.2026.11518888 |
| More Information, Lower Price? Access Market-based Reference Prices and Gains in Public Procurement Efficiency | Martinez-Carrasco et al. | 2023 | não identificado | doi:10.18235/0004794 |
| Red flag algorithms for Brazilian electronic invoices: outlier detection and price risk classification | Interian et al. | 2023 | Int. Trans. Oper. Res. | doi:10.1111/itor.13323 |
| Query Attribute Modeling: Improving Search Relevance with Semantic Search and Meta Data Filtering | Menon et al. | 2025 | IEEE ICDMW | doi:10.1109/icdmw69685.2025.00131 |
| An Analysis of Fusion Functions for Hybrid Retrieval | Bruch et al. | 2022 | ACM Trans. Inf. Syst. | doi:10.1145/3596512 |
| Overview of the TREC 2023 Product Search Track | Campos et al. | 2023 | ArXiv | doi:10.48550/arxiv.2311.07861 |
| Temporal JSON Keyword Search | Dyreson et al. | 2024 | Proc. ACM on Management of Data | doi:10.1145/3654980 |
| O Portal Nacional de Contratações Públicas como ruptura paradigmática na governança das contratações públicas brasileiras | D'Almeida | 2026 | International Integralize Scientific | doi:10.63391/bvf0a595 |
| Os impactos da nova lei de licitações em pequenos municípios | Paula | 2024 | Revista ft | doi:10.69849/revistaft/ar10202410240934 |
| Challenges to the Implementation of the new public procurement law in municipal management: the case of Pontal do Paraná | Abreu et al. | 2024 | Caderno Pedagógico | doi:10.54033/cadpedv21n12-126 |
| A nova Lei de Licitações para novos prefeitos | Pironti et al. | 2024 | Revista da Procuradoria do Tribunal de Contas do Estado do Pará | doi:10.52028/tce-pa.v04i07_art.08_pr |
| Cost management in the supply chain: An analysis of the costs of different types of municipal procurement | Pereira et al. | 2022 | Social Sciences & Humanities Open | doi:10.1016/j.ssaho.2022.100260 |
