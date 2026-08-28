---
tipo: pesquisa
titulo: "O que a literatura já cobre do tema, e onde sobra espaço para este trabalho?"
status: cinco eixos executados; nenhuma fonte lida integralmente
criado: 2026-08-24
autor: Rafael Nobre de Souza
relacionado:
  - docs/projeto.md
  - docs/pesquisas/prompt-levantamento-literatura.md
  - docs/pesquisas/escolha-do-banco-vetorial.md
  - docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md
tags: [pesquisa, literatura, trabalhos-relacionados, rag, pesquisa-de-precos]
---

# Levantamento de literatura — primeira rodada

> ## Duas regras que valem para tudo nesta nota
>
> **1. Nenhum metadado foi conferido na fonte primária.** Tudo aqui é o que a
> base de busca devolveu. Ano, veículo, volume, páginas e ordem dos autores
> precisam ser verificados antes de qualquer entrada em `refs.bib`.
>
> **2. Nada aqui é citável, porque nada aqui foi lido.** Fonte só entra como
> referência do trabalho **se o texto completo for obtido e lido por inteiro**.
> Resumo não basta. Sem acesso — paywall, instituição sem assinatura, pedido de
> acesso negado —, a fonte é **cortada** e se busca outra no lugar.
>
> Consequência: esta nota é **fila de leitura**, não bibliografia. O que ainda é
> permitido sem o texto completo é mencionar em conversa com a orientação, com
> base no resumo, dizendo que só o resumo foi lido.

## 1. Contexto

A orientação delimitou a fundamentação a três temas — administração pública,
prefeituras e licitação — e fixou o texto em 20 a 25 páginas. Isso inviabiliza
revisão sistemática com protocolo completo, e torna a seção de trabalhos
relacionados um quadro comparativo enxuto.

Mas o corte de páginas não dispensa saber o que já existe. Duas perguntas
dependem disso e nenhuma pode ser respondida por opinião: **o trabalho já foi
feito por alguém?** e **qual é exatamente a lacuna que ele ocupa?** Chegar à
banca reivindicando novidade que a literatura já cobre é o risco que esta nota
existe para eliminar.

O protocolo usado está em `prompt-levantamento-literatura.md`, escrito antes
desta rodada.

## 2. Pergunta central

Dado o tema — apoio computacional à fase preparatória de contratações públicas
municipais sob a Lei nº 14.133/2021, com geração assistida de ETP e TR e
composição de pesquisa de preços a partir do PNCP —, o que a literatura já cobre,
e que recorte permanece não atendido?

## 3. Resposta curta

**O tema não é virgem, e a primeira hipótese de lacuna caiu durante o próprio
levantamento.**

Já foi publicado: RAG sobre documento de licitação pública [4][6]; RAG sobre
corpus jurídico brasileiro [3]; estimativa de preço de referência em licitação
brasileira [11]; extração de informação de documento de licitação com apoio à
decisão [15]; arquitetura de proveniência para governo [7]; **geração de
documento semiestruturado em administração pública** [21]; **geração assistida em
prefeitura, em produção** [22]; e **geração a partir de formulário estruturado,
com linha de base medida** [23].

O que **não** aparece em nenhum dos cem resultados: a **junção**. Gerar a minuta
e compor a pesquisa de preços **com trilha que permita reconstituir a cotação
exatamente como ela era na data**, sob a Lei nº 14.133/2021, em município de
pequeno porte. É aí que sobra espaço, e a seção 8 mede a força dessa afirmação.

## 4. Método

| | |
|---|---|
| **Base** | Consensus (`consensus.app`), agregador de literatura revisada por pares |
| **Data** | 24/08/2026 |
| **Eixos executados** | 5 |
| **Filtros aplicados** | **nenhum** — só a consulta textual, sem recorte de ano, tipo de estudo ou domínio |
| **Resultados** | 20 encontrados por eixo; 10 devolvidos nos dois primeiros, 20 nos três seguintes |

Os dois primeiros eixos rodaram sob conta gratuita e devolveram 10 de 20. A cota
mensal esgotou entre o segundo e o terceiro, e os três últimos rodaram depois da
assinatura, devolvendo 20. **Os eixos 1 e 2, portanto, mostraram metade do que a
base tinha** — vale reexecutá-los quando houver motivo.

| # | Eixo | Devolvidos |
|---|---|---|
| 1 | RAG aplicada a documento governamental e administração pública | 10 de 20 |
| 2 | Automação de compras públicas e estimativa de preço de referência | 10 de 20 |
| 3 | Bancos vetoriais dedicados contra `pgvector` | 20 de 20 |
| 4 | Geração assistida de documento jurídico-administrativo | 20 de 20 |
| 5 | Trilha de auditoria, proveniência e reprodutibilidade de consulta | 20 de 20 |

## 5. Eixo 1 — RAG em documento governamental

**Concorrência direta.** [4] faz RAG sobre documentos de licitação pública das
Filipinas, com fragmentação que preserva a hierarquia do documento jurídico
(256 a 512 tokens), recuperação híbrida em três níveis e modelos pequenos
ajustados por QLoRA em 4 bits para caber em 4 GB de memória de vídeo. Relata
89,3% de acurácia contra 71,3% de linha de base, sobre 2.088 pares de pergunta e
resposta derivados da lei de licitações filipina, com validação por cinco
servidores da área.

⚠️ **Acesso ao texto completo não obtido.** Pedido de acesso feito via
ResearchGate em 24/08/2026, sem resposta. Enquanto não for lido, não é citável —
só mencionável.

**Precedente para a política de dados sintéticos.** [6] faz RAG sobre o conjunto
documental de uma licitação, com recuperação semântica e lexical em paralelo. Os
documentos avaliados **foram gerados sinteticamente**, o que dá precedente
publicado à regra de nunca versionar documento real deste projeto.

**Linha de base em corpus jurídico brasileiro.** [3] indexa mais de 7.000
documentos legislativos brasileiros e avalia nove configurações de RAG com
*recall*, MRR, BERTScore e METEOR. Melhor recuperação: Mistral com embeddings
`bge-m3`, *recall* de 0,852.

**Sustentação do recorte de auditoria.** [7] descreve arquitetura de fundamentação
em quatro camadas — recuperação, verificação de citação, calibração de confiança
e escalonamento com humano no circuito — com controle de acesso por atributo em
nível de documento, em agência governamental real, oito meses em operação.
Recuperação híbrida com precisão de 91,3% em k=10; a verificação de citação por
inferência de linguagem natural reduziu afirmações sem suporte de 23% para 4,1%.

**Contra-argumento a responder.** [2] sustenta que RAG plano sobre documento não
estruturado limita raciocínio de múltiplos saltos quando os dados são
estruturados, e propõe GraphRAG modular. [5], o mais citado do eixo com 130
citações, critica recuperação por similaridade e propõe indexação com relações
semânticas explícitas. Juntos são a resposta a "basta um índice vetorial", e a
modelagem de dados deste trabalho vai ter que responder a eles.

**Fonte de método de avaliação.** [10] é revisão sistemática PRISMA de 2021 a
2025: 7.947 artigos filtrados para 100 em Q1 e Q2. Conclui que há fragmentação
conceitual na medição de fundamentação, com predomínio de métricas de similaridade
textual inadequadas ao contexto regulatório.

Demais devolvidos, de contexto: [1] comunicação de política pública ao cidadão,
22 citações, PLOS ONE; [8] chatbot com banco vetorial em agência de serviço
público, com similaridade de cosseno média de 0,404 — número baixo, e o trabalho
serve mais como exemplo de avaliação frágil que como referência; [9] RAG para
governo eletrônico grego, língua de poucos recursos.

## 6. Eixo 2 — Compras públicas e preço de referência

**Alvo direto, e brasileiro.** [11] trata da construção de preço de referência em
licitação pública **brasileira**, combinando técnica estatística e aprendizado de
máquina para detectar sobrepreço e subpreço. Critica explicitamente a média
aritmética e o menor preço como causa de distorção — a prática que o módulo de
pesquisa de preços pretende substituir. Design Science Research, com experimento
quantitativo sobre dados reais. Resultados relatados: desvio médio de 2,53% na
versão estatística contra 15,58% dos métodos tradicionais, e 70% de acurácia na
detecção de irregularidade.

⚠️ Zero citações, 2025, **veículo não identificado pela base**. É a referência
mais próxima do problema e a que mais precisa de conferência.

**Precedente de escala sobre dados abertos de portal nacional.** [14] analisa
58.337 licitações espanholas de 2012 a 2018 e propõe estimador de preço de
adjudicação por *random forest*. 22 citações, revista Complexity. [12], dos
mesmos autores, compara regressão linear, *random forest*, regressão isotônica e
redes neurais.

**Referência de arquitetura para dado semiestruturado.** [15] — 37 citações,
revista Information Systems: apoio à decisão com processamento de linguagem
natural extraindo informação de dados estruturados **e** não estruturados de
documento de licitação, com busca semântica, sumarização e extração de triplas.

**Problema que o módulo vai enfrentar, com número.** [19] valida sobre 847.392
registros de compras: casamento difuso de produto com F1 de 93,4%, detecção de
anomalia com F1 de 90,8%, previsão com MAPE de 4,2%. O casamento difuso é
exatamente o problema de agrupar itens equivalentes vindos do PNCP com descrições
divergentes.

**Evidência de campo de que a necessidade existe.** [17] é qualitativo, vinte
participantes, e registra que automação já é usada na preparação de documentação
de compras e na simplificação de linguagem técnica. Amostra fraca, mas é
evidência empírica.

**Risco de desenho.** [13] — 123 citações, Manufacturing & Service Operations
Management — é experimento de campo sobre como fornecedores mudam a cotação
quando o comprador é agente automatizado: há discriminação de preço contra
comprador automatizado. Não afeta o módulo que consulta o PNCP, mas afetaria
extensão futura que cotasse junto a fornecedor.

Contexto adicional: [16], [18] e [20].

## 7. Eixo 3 — Persistência vetorial dedicada contra `pgvector`

Eixo com literatura robusta, e o mais consequente para a arquitetura. A análise
completa e a recomendação estão em `escolha-do-banco-vetorial.md`; aqui fica o
que a base devolveu.

**Praticamente o desenho da Iniciação Científica em andamento.** [24] compara
sete sistemas — FAISS, Chroma, Qdrant, Weaviate, Milvus, OpenSearch e `pgvector`
— de 175 a 2,2 milhões de vetores, com dez ensaios por configuração e remoção de
*outlier* de partida a frio. Achado central: `pgvector` com HNSW abaixo de 10 ms
e acima de 100 consultas por segundo na escala de 50 mil, superando todos os
dedicados exceto o Chroma.

Isso importa **antes** de a IC fechar, não depois: é a linha de base contra a
qual o experimento próprio vai ser lido. Não invalida a medição própria — que é
sobre outro dado e outro hardware —, mas obriga posicionamento.

**Favorece `pgvector` sob restrição de recurso.** [25] compara Chroma e
`pgvector` em 4 GB de RAM, 119 ensaios sobre Deep1M: overhead de armazenamento de
3 a 4 vezes contra 395 do Chroma, e *recall* de 99,6 a 99,8% contra 91 a 95%.
Conclui que `pgvector` é mais viável para produção dinâmica.

**A pergunta arquitetural de fundo.** [26] — ICDE 2024, 29 citações — investiga se
as limitações do PostgreSQL para dado vetorial são fundamentais ou de
implementação, comparando PASE com Faiss. [27] mostra o mesmo movimento no
sentido inverso: banco relacional distribuído que alcança paridade com Milvus e
supera `pgvector`.

**E o que nenhum deles mede.** Nenhum dos vinte devolvidos avalia **busca
vetorial combinada com filtro de metadados sob seletividade restritiva**, que é
justamente a operação da composição de pesquisa de preços e o eixo em que os
sistemas se separam na medição própria. [28] e [29] são os que mais se aproximam —
propõem arcabouços de avaliação de busca filtrada e de consulta composta — e
ambos apontam a ausência de referência padronizada nesse cenário.

Demais devolvidos, de contexto: surveys [30][31][32], a biblioteca Faiss [33] com
835 citações, otimização de `pgvector` sobre SSD moderno com ganho de 11,1 vezes
em *throughput* [34], e sistemas comerciais [35][36].

## 8. Eixo 4 — Geração de documento jurídico-administrativo

**Este eixo derrubou a hipótese de lacuna** que a primeira leitura desta nota
sustentava. Fica registrado como caiu, não apagado.

A hipótese era: nenhum trabalho trata de **gerar** minuta — todo o corpus dos
eixos 1 e 2 era consulta a documento pronto. O eixo que buscava geração não havia
rodado. Rodou, e há literatura no domínio exato:

- [21] gera **documento semiestruturado em Administração Pública** a partir de
  template semântico, com multi-agente e recuperação para substituir a construção
  manual de instrução. 24 citações.
- [22] é **municipal**: prefeitura de Amsterdam, recuperação aumentada por geração
  e por contexto para redigir carta de resposta a objeção, em produção, capturando
  80% a 100% do raciocínio jurídico exigido, com revisão por especialista no
  circuito.
- [23] é o mais parecido com o módulo de minutas: **entrada estruturada mapeada
  para campos de template → documento gerado**, avaliado por dois servidores
  públicos em sete casos reais. **Tem linha de base medida**: 9,75 para 6,41
  minutos de redação, dois ajustes por documento em média. É precedente
  metodológico direto para a avaliação deste trabalho.
- [37] propõe geração em duas etapas — planeja a estrutura das seções, depois gera
  cada seção com prompts baseados em recuperação — com dataset de 133 categorias
  de documento jurídico.
- [38] e [39] tratam de redação de documento jurídico com modelo ajustado
  localmente, com privacidade da informação como requisito declarado.

**O risco central do eixo, e é grande.** [40] — 317 citações — mede alucinação
jurídica em modelos de linguagem: ao menos 58% das tarefas testadas, com os
modelos falhando em prever suas próprias alucinações e aceitando premissa
jurídica incorreta do usuário sem contestar. [41] acrescenta o lado humano:
profissionais do direito preferem documento que acreditam ser de autoria humana,
mesmo quando o conteúdo é idêntico.

Os dois juntos são argumento **a favor** do desenho com proveniência obrigatória
e revisão humana no circuito, não contra o trabalho. Mas precisam aparecer no
texto: prometer geração sem tratar alucinação é o que a banca vai cobrar.

Contexto adicional: surveys de modelos de linguagem no direito [42][43],
sumarização de decisão judicial com inconsistência documentada [44], geração de
termo de consentimento [45], e um modelo de linguagem ajustado por governo para
sumarizar proposta legislativa [46].

## 9. Eixo 5 — Proveniência, auditoria e reprodutibilidade

Técnica madura, domínio virgem — e é a combinação mais favorável ao trabalho.

**A literatura de proveniência é sólida e antiga.** [47] é survey com 337
citações classificando para que serve, que formas assume e de onde vem. [48]
resolve o problema de armazenar proveniência de granularidade fina de forma
**resistente a adulteração**, com compressão e encadeamento criptográfico — que é
tecnicamente o que uma trilha de pesquisa de preços auditável precisa. [49]
captura proveniência por **reescrita de consulta SQL**, independente do SGBD,
cobrindo 93% das consultas do TPC-H contra 86%, 50% e 14% das alternativas. [50]
extrai proveniência de log de eventos do banco, em produção.

**E há trilha de auditoria específica para modelo de linguagem.** [51] propõe
registro cronológico, resistente a adulteração e rico em contexto, ligando
proveniência técnica a registro de governança, com implementação aberta.

**Nenhum dos vinte toca compras públicas.** Nem licitação, nem preço de
referência, nem processo administrativo. Os domínios de aplicação são biomédico
[52][53][54], serviço público em geral com foco em acessibilidade [55], auditoria
contábil [56][57], dado espacial [58] e rede social [59].

Isso reposiciona a contribuição: não é inventar trilha de auditoria — a técnica
existe e é madura. É **aplicá-la ao domínio de pesquisa de preços**, onde ninguém
aplicou, com a exigência específica de reproduzir a cotação na data.

## 10. Onde sobra espaço, e com que força

Separado de propósito entre o que os resultados mostram e o que é leitura minha.

**O que a literatura cobre** — não reivindicar como novidade:

| Coberto | Onde |
|---|---|
| RAG sobre corpus jurídico e regulatório, inclusive brasileiro | [3] |
| RAG sobre documento de licitação | [4][6] |
| Estimativa de preço de referência, inclusive no Brasil | [11][12][14] |
| Extração de informação de documento de licitação | [15] |
| Proveniência com resistência a adulteração e reprodutibilidade | [47][48][49] |
| Arquitetura de fundamentação com proveniência para governo | [7] |
| **Geração de documento administrativo a partir de template** | [21][23][37] |
| **Geração assistida em prefeitura, em produção** | [22] |

**Lacunas candidatas, com a força de cada uma:**

| # | Lacuna | Força |
|---|---|---|
| 1 | ~~Geração de minuta~~ | **DERRUBADA.** [21], [22] e [23] cobrem geração em administração pública, em prefeitura e a partir de formulário estruturado |
| 2 | **Reprodutibilidade temporal da pesquisa de preços.** Nenhum trabalho de preço [11][12][14][19] menciona trilha que reconstitua a cotação na data; nenhum trabalho de proveniência [47]–[51] toca compras públicas | **Forte.** Ausência consistente nos dois eixos, e são vinte resultados cada. A técnica existe e o domínio não foi atendido |
| 3 | **Busca vetorial filtrada sob seletividade restritiva em índice de preços.** Nenhum dos vinte do eixo 3 mede esse cenário, e [28][29] registram a ausência de referência padronizada | **Média a forte.** Confirmada por medição própria, e é o recorte de banco de dados |
| 4 | **Município de pequeno porte.** O corpus é de escala nacional ou agência central; [22] é municipal, mas é capital europeia com departamento jurídico próprio | **Média.** Enfraquecida por [22], não eliminada |
| 5 | **Lei nº 14.133/2021 como objeto.** [11] é brasileiro e trata de preço, mas nada ancora ETP e TR como artefatos da fase preparatória | **Média** |

**Inferência, declarada como tal:** a contribuição defensável é a **junção de 2 e
3** — compor pesquisa de preços com trilha reproduzível, sobre índice vetorial
que sustente filtro restritivo —, com 4 e 5 como recorte de aplicação. Gerar
minuta entra como funcionalidade necessária, não como novidade, e o texto tem de
dizer isso.

## 11. Riscos que o levantamento revelou

1. **[4] é concorrência direta, é de 2026, e não há acesso ao texto completo.**
   Pedido feito via ResearchGate, sem resposta. Se o acesso não vier, a regra do
   projeto manda cortar — e aí é preciso outra fonte que cubra o mesmo ponto.
2. **A hipótese de lacuna mais atraente caiu.** Serve de aviso: as outras quatro
   também podem cair quando cada texto for lido de fato.
3. **[24] é linha de base para a IC** e precisa ser posicionado antes do relatório
   final de dezembro.
4. **[40] mede 58% de alucinação em tarefa jurídica.** Tem de aparecer no texto.
5. **Os eixos 1 e 2 mostraram metade dos resultados**, por limite da conta na
   ocasião. Reexecutar se algum deles voltar a ser decisivo.
6. **Quatro dos itens mais aderentes têm zero citações** e três têm veículo não
   identificado — inclusive [11].

## 12. O que ficou em aberto

- **Obter e ler o texto completo** de tudo que se pretende citar. É a regra, e
  hoje **nenhuma** das fontes desta nota a cumpre.
- **Conferir metadados na fonte primária**, com prioridade para [4], [7], [11],
  [21], [22], [23] e [24].
- **Segunda base.** Uma base só não triangula. Sobreposição entre respostas
  independentes é o sinal mais barato de que uma referência é central.
- **Dois eixos ainda não buscados:** proveniência aplicada especificamente a
  compras públicas, e governo digital em município de pequeno porte. Os dois
  testariam as lacunas 2 e 4 diretamente.

## 13. Referências devolvidas pela base

> Lista bruta, na numeração usada acima. **Metadados não conferidos, e nenhuma
> fonte lida.** Nada aqui é citável até que o texto completo seja obtido e lido.

| # | Título | Autoria informada | Ano | Veículo informado | Cit. |
|---|---|---|---|---|---|
| 1 | Improving citizen-government interactions with generative artificial intelligence | Lixin Yun et al. | 2024 | PLOS ONE | 22 |
| 2 | Hybrid Multi-Agent GraphRAG for E-Government | George Papageorgiou et al. | 2025 | Applied Sciences | 19 |
| 3 | Using Retrieval-Augmented Generation to Improve Access to Legal Documents | Eniedson F. P. da Silva Júnior et al. | 2026 | Int. Conf. on Semantic Computing | 1 |
| 4 | Optimizing RAG for Querying Locally Stored Public Procurement Documents using Small Language Models | Dean Reight F. Billedo et al. | 2026 | 2nd ICCIAA | 0 |
| 5 | KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation | Lei Liang et al. | 2024 | Companion Proc. ACM Web Conf. 2025 | 130 |
| 6 | A Dual-Mode RAG System for Interactive QA of Public Tender Documents | V. R. Montequín et al. | 2026 | **não identificado** | 0 |
| 7 | RAG-grounded Advisory Systems for Government Decision-making | Zeki Emre Tekin | 2026 | SSRN Electronic Journal | 0 |
| 8 | Implementing RAG and Vector Databases for Chatbots in Public Services Agencies Context | Ibnu Pujiono et al. | 2024 | JITK | 11 |
| 9 | Legal Assistance in Low-Resource Languages: RAG and Fine-Tuned LLMs for Greek e-Governance | M. Tsourma et al. | 2025 | 3rd FLLM | 1 |
| 10 | Groundedness in Government Document Chatbots: A Systematic Literature Review | Frendy Rumambi et al. | 2026 | Systematic Literature Review Journal | 0 |
| 11 | Intelligent Methodologies for Preparing Reference Prices in Brazilian Public Biddings | Eduardo M. B. Faria et al. | 2025 | **não identificado** | 0 |
| 12 | Award Price Estimator for Public Procurement Auctions Using Machine Learning | Manuel J. García Rodríguez et al. | 2021 | Studies in Informatics and Control | 9 |
| 13 | AI and Procurement | Ruomeng Cui et al. | 2020 | Manufacturing & Service Operations Mgmt. | 123 |
| 14 | Public Procurement Announcements in Spain | M. Rodríguez et al. | 2019 | Complexity | 22 |
| 15 | AI-based decision support system for public procurement | Lucia Siciliani et al. | 2023 | Information Systems | 37 |
| 16 | The use of software to support management decisions in public procurement | A. Rada et al. | 2022 | **não identificado** | 2 |
| 17 | The Impact of Automation and AI on Public Procurement Performance in Tanzania | Godfrey F. Mbondo | 2026 | Asian J. of Education and Social Studies | 0 |
| 18 | The Artificial Intelligence and Public Procurement | Berraida Riyad et al. | 2024 | IEEE 15th LOGISTIQUA | 3 |
| 19 | A Rigorous Multi-Agent Framework for Procurement Optimization | S. Mujtaba et al. | 2025 | Int. J. of Applied Mathematics | 0 |
| 20 | Modernizing Procurement in Supply Chain with AI and ML Techniques | Goli Mallesham | 2024 | Int. J. of Eng. and Computer Science | 0 |
| 21 | LLM Based Multi-Agent Generation of Semi-structured Documents from Semantic Templates in the Public Administration Domain | Emanuele Musumeci et al. | 2024 | **não identificado** | 24 |
| 22 | LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters | Virgill van der Meer et al. | 2026 | ArXiv | 0 |
| 23 | Reducing Drafting Backlogs with LLMs: A Feasibility Study on Thai Legal Petitions | Sathana Laolugsanalerd et al. | 2025 | iSAI-NLP | 0 |
| 24 | Benchmarking Open Source Vector Databases | J. Patel et al. | 2026 | J. of Big Data and Artificial Intelligence | 0 |
| 25 | Comparative Analysis of Performance Aspects Between Chroma and Pgvector as a Vector Database | Ali Zaenal Abidin et al. | 2025 | bit-Tech | 1 |
| 26 | Are There Fundamental Limitations in Supporting Vector Data Management in Relational Databases? A Case Study of PostgreSQL | Yunan Zhang et al. | 2024 | IEEE ICDE | 29 |
| 27 | SingleStore-V: An Integrated Vector Database System in SingleStore | Cheng Chen et al. | 2024 | Proc. VLDB Endow. | 53 |
| 28 | VecBench: A Controllable Benchmark for Filtered Vector Search | Xiangkun Zhang et al. | 2026 | Proc. ACM on Management of Data | 3 |
| 29 | BigVectorBench: Heterogeneous Data Embedding and Compound Queries | Guoxin Kang et al. | 2025 | Proc. VLDB Endow. | 6 |
| 30 | Survey of vector database management systems | J. Pan et al. | 2023 | The VLDB Journal | 206 |
| 31 | Vector Database Management Techniques and Systems | J. Pan et al. | 2024 | Companion of SIGMOD 2024 | 76 |
| 32 | A Brief Survey of Vector Databases | Xingrui Xie et al. | 2023 | 9th BigDIA | 26 |
| 33 | The Faiss Library | Matthijs Douze et al. | 2024 | IEEE Trans. on Big Data | 835 |
| 34 | Turbocharging Vector Databases using Modern SSDs | Joobo Shim et al. | 2025 | Proc. VLDB Endow. | 16 |
| 35 | BlendHouse: A Cloud-Native Vector Database System in ByteHouse | Zhaojie Niu et al. | 2025 | IEEE ICDE | 9 |
| 36 | Cost-Effective, Low Latency Vector Search with Azure Cosmos DB | Nitish Upreti et al. | 2025 | ArXiv | 7 |
| 37 | Structured Legal Document Generation in India: VidhikDastaavej | S. Nigam et al. | 2025 | ArXiv | 2 |
| 38 | Legal Documents Drafting with Fine-Tuned Pre-Trained Large Language Model | Chun-Hsien Lin et al. | 2024 | ArXiv | 12 |
| 39 | Assisting Drafting of Chinese Legal Documents Using Fine-Tuned Pre-trained LLMs | Chun-Hsien Lin et al. | 2025 | The Review of Socionetwork Strategies | 4 |
| 40 | Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models | Matthew Dahl et al. | 2024 | J. of Legal Analysis | 317 |
| 41 | It Cannot Be Right If It Was Written by AI | Jakub Harasta et al. | 2024 | Artificial Intelligence and Law | 32 |
| 42 | Large Language Models in Legal Systems: A Survey | Fatemeh Dehghani et al. | 2025 | Humanities and Social Sciences Comm. | 28 |
| 43 | Large Language Models in Law: A Survey | Jinqi Lai et al. | 2023 | ArXiv | 250 |
| 44 | Applicability of large language models and generative models for legal case judgement summarization | A. Deroy et al. | 2024 | Artificial Intelligence and Law | 67 |
| 45 | Large language models for automated consent form generation | Tanna L. Nelson et al. | 2025 | JCO Oncology Practice | 0 |
| 46 | LLaMandement: Large Language Models for Summarization of French Legislative Proposals | Joseph Gesnouin et al. | 2024 | ArXiv | 12 |
| 47 | A survey on provenance: What for? What form? What from? | Melanie Herschel et al. | 2017 | The VLDB Journal | 337 |
| 48 | Compact, Tamper-Resistant Archival of Fine-Grained Provenance | Nan Zheng et al. | 2020 | Proc. VLDB Endow. | 6 |
| 49 | A DBMS-Independent Approach for Capturing Provenance Polynomials Through Query Rewriting | Paulo Pintor et al. | 2025 | IEEE Access | 0 |
| 50 | OneProvenance: Efficient Extraction of Dynamic Coarse-Grained Provenance from Database Query Event Logs | Fotis Psallidas et al. | 2022 | Proc. VLDB Endow. | 6 |
| 51 | Audit Trails for Accountability in Large Language Models | Victor Ojewale et al. | 2026 | ArXiv | 14 |
| 52 | Provenance Information for Biomedical Data and Workflows: Scoping Review | Kerstin Gierend et al. | 2024 | J. of Medical Internet Research | 26 |
| 53 | Data Provenance in Biomedical Research: Scoping Review | Marco Johns et al. | 2023 | J. of Medical Internet Research | 16 |
| 54 | Embedding data provenance into the Learning Health System | V. Curcin | 2016 | Learning Health Systems | 34 |
| 55 | Audit data governance for disability-inclusive public services | Sitthisak Chaiyasuk et al. | 2026 | PLOS One | 0 |
| 56 | Securing Big Data Provenance for Auditors | Deniz Appelbaum | 2016 | J. of Emerging Technologies in Accounting | 72 |
| 57 | From Tracking Lineage to Enhancing Data Quality and Auditing: ProvETL | Matheus Vieira et al. | 2024 | **não identificado** | 6 |
| 58 | GeoPROV: A Domain-Specialised Provenance Model for Spatial Data Supply Chains | Muhammad A. Sadiq et al. | 2026 | ISPRS Int. J. of Geo-Information | 0 |
| 59 | Social data provenance framework based on zero-information loss graph database | A. Rani et al. | 2022 | Social Network Analysis and Mining | 3 |
