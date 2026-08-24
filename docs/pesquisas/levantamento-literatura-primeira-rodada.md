---
tipo: pesquisa
titulo: "O que a literatura já cobre do tema, e onde sobra espaço para este trabalho?"
status: parcial
criado: 2026-08-24
autor: Rafael Nobre de Souza
relacionado:
  - docs/projeto.md
  - docs/pesquisas/prompt-levantamento-literatura.md
  - docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md
tags: [pesquisa, literatura, trabalhos-relacionados, rag, pesquisa-de-precos]
---

# Primeira rodada do levantamento de literatura

> ⚠️ **NENHUM METADADO DESTA NOTA FOI CONFERIDO NA FONTE PRIMÁRIA.** Tudo aqui é
> o que a base de busca devolveu. Ano, veículo, volume, páginas e ordem dos
> autores precisam ser verificados no PDF ou na página oficial antes de qualquer
> entrada em `refs.bib` e antes de qualquer citação no texto. A regra existe
> porque o erro já foi cometido neste projeto, e ela morde de verdade aqui:
> quatro dos itens mais aderentes têm veículo que a base não identificou.

## 1. Contexto

A orientação delimitou a fundamentação teórica a três temas — administração
pública, prefeituras e licitação — e fixou o texto em 20 a 25 páginas. Isso
inviabiliza uma revisão sistemática com protocolo completo, e torna a seção de
trabalhos relacionados um quadro comparativo enxuto.

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
composição de pesquisa de preços a partir do PNCP —, o que a literatura revisada
por pares já cobre, e que recorte permanece não atendido?

## 3. Resposta curta

**O tema não é virgem, e um trabalho de 2026 chega perto o bastante para ser
tratado como concorrência direta.** RAG sobre documento de licitação pública já
foi publicado [4][6]; estimativa de preço de referência em licitação brasileira
por método estatístico e por aprendizado de máquina já foi publicada [11];
extração de informação de documento de licitação com apoio à decisão já foi
publicada [15].

**O que não apareceu em nenhum dos vinte resultados: geração de minuta.** Todo o
corpus recuperado é de *consulta* a documento existente — pergunta e resposta
sobre edital, lei ou processo. Nenhum trata de *redigir* documento novo a partir
de formulário guiado. Esse é o espaço mais defensável do trabalho, e é uma
ausência observada, não uma lacuna provada — ver a seção 7.

## 4. Método

| | |
|---|---|
| **Base** | Consensus (`consensus.app`), agregador de literatura revisada por pares |
| **Data** | 24/08/2026 |
| **Eixos planejados** | 4 |
| **Eixos executados** | 2 |
| **Filtros aplicados** | **nenhum** — só a consulta textual, sem recorte de ano, tipo de estudo ou domínio |
| **Resultados por eixo** | 20 encontrados, 10 devolvidos (limite da conta gratuita) |
| **Interrupção** | Cota mensal esgotada no meio do lote |

Os eixos:

| # | Eixo | Estado |
|---|---|---|
| 1 | RAG aplicada a documento governamental e administração pública | executado |
| 2 | Automação de compras públicas, incluindo estimativa de preço de referência | executado |
| 3 | Desempenho de bancos vetoriais dedicados contra `pgvector` | **não executado** |
| 4 | Geração assistida de documento jurídico-administrativo com modelo de linguagem | **não tentado** |

Mensagem exata do servidor ao interromper:

```
You've used all 30 searches this month; resets on September 1st.
```

**Os eixos 3 e 4 não são lacuna de literatura — são lacuna de execução.** A
distinção importa: tratar eixo não executado como ausência de trabalho publicado
seria inventar resultado. Ficam pendentes até 1º de setembro de 2026.

## 5. Achados do eixo 1 — RAG em documento governamental

Eixo forte, e com dois trabalhos que atingem o alvo do projeto.

**Concorrência direta.** [4] faz RAG sobre documentos de licitação pública das
Filipinas, com fragmentação que preserva a hierarquia do documento jurídico
(256 a 512 tokens), recuperação híbrida com filtragem em três níveis —
documento, seção, fragmento — e modelos pequenos ajustados por QLoRA em 4 bits
para caber em 4 GB de memória de vídeo. Relata 89,3% de acurácia contra 71,3%
de linha de base, sobre 2.088 pares de pergunta e resposta derivados da lei de
licitações filipina, com validação por cinco servidores da área. É precedente
metodológico e concorrente ao mesmo tempo.

**Precedente para a política de dados sintéticos.** [6] faz RAG sobre o conjunto
documental de uma licitação, com recuperação semântica e lexical em paralelo.
Interessa por duas razões: os documentos avaliados **foram gerados
sinteticamente**, o que dá precedente publicado à regra de nunca versionar
documento real deste projeto; e a arquitetura prioriza fidelidade ao documento e
interpretabilidade para usuário não técnico, que é o perfil da secretaria
demandante.

**Linha de base em corpus jurídico brasileiro.** [3] indexa mais de 7.000
documentos legislativos brasileiros e avalia nove configurações de RAG com
*recall*, MRR, BERTScore e METEOR. Melhor recuperação: Mistral com embeddings
`bge-m3`, *recall* de 0,852. Serve de referência nacional e de fonte para a
escolha do modelo de embedding.

**Sustentação do recorte de auditoria.** [7] descreve arquitetura de fundamentação
em quatro camadas — recuperação, verificação de citação, calibração de confiança
e escalonamento com humano no circuito — com controle de acesso por atributo em
nível de documento, em agência governamental real, oito meses em operação.
Recuperação híbrida com precisão de 91,3% em k=10; a verificação de citação por
inferência de linguagem natural reduziu afirmações sem suporte de 23% para 4,1%
em produção. É o trabalho que melhor articula proveniência obrigatória como
requisito de governo, e é o mais próximo do recorte de trilha de auditoria.

**Contra-argumento a considerar.** [2] sustenta que RAG plano sobre documento não
estruturado limita raciocínio de múltiplos saltos e interpretabilidade quando os
dados de governo são estruturados, e propõe GraphRAG modular. [5], o mais citado
do eixo com 130 citações, critica recuperação por similaridade e propõe indexação
com relações semânticas explícitas. Os dois juntos são a resposta a "basta um
índice vetorial", e a modelagem de dados deste trabalho vai ter que responder a
eles.

**Fonte de método de avaliação.** [10] é revisão sistemática PRISMA de 2021 a
2025: 7.947 artigos filtrados para 100 em Q1 e Q2. Conclui que há fragmentação
conceitual na definição e na medição de fundamentação, com predomínio de métricas
de similaridade textual inadequadas ao contexto regulatório. Útil como
mapeamento do campo e como justificativa para métrica de avaliação própria.

Demais devolvidos, de contexto: [1] comunicação de política pública ao cidadão,
22 citações, PLOS ONE; [8] chatbot com banco vetorial em agência de serviço
público, com similaridade de cosseno média de 0,404 — número baixo, e o trabalho
serve mais como exemplo de avaliação frágil que como referência de desempenho;
[9] RAG e modelo ajustado para governo eletrônico grego, língua de poucos
recursos.

## 6. Achados do eixo 2 — Compras públicas e preço de referência

Eixo forte, e com o achado mais valioso de toda a rodada.

**Alvo direto, e brasileiro.** [11] trata da construção de preço de referência em
licitação pública **brasileira**, combinando técnica estatística e aprendizado de
máquina para detectar sobrepreço e subpreço. Critica explicitamente a média
aritmética e o menor preço como causa de distorção — que é exatamente a prática
que o módulo de pesquisa de preços deste projeto pretende substituir. Metodologia
Design Science Research, com experimento quantitativo sobre dados reais de
licitação. Resultados relatados: desvio médio de 2,53% na versão estatística
contra 15,58% dos métodos tradicionais, e 70% de acurácia na detecção de
irregularidade na versão com TensorFlow.

⚠️ Zero citações, 2025, **veículo não identificado pela base**. É a referência
mais próxima do problema e a que mais precisa de conferência antes de ser citada.

**Precedente de escala sobre dados abertos de portal nacional.** [14] analisa
58.337 licitações espanholas de 2012 a 2018, 31,426 bilhões de euros, e propõe
estimador de preço de adjudicação por *random forest*. 22 citações, revista
Complexity. É o análogo europeu do que o PNCP permite fazer aqui. [12], dos
mesmos autores, compara regressão linear, *random forest*, regressão isotônica e
redes neurais para o mesmo fim.

**Referência de arquitetura para dado semiestruturado.** [15] é o mais citado com
aderência real ao recorte — 37 citações, revista Information Systems: sistema de
apoio à decisão com processamento de linguagem natural extraindo informação de
dados estruturados **e** não estruturados de documento de licitação, com busca
semântica, sumarização e extração aberta de triplas.

**Problema que o módulo vai enfrentar, com número.** [19] valida sobre 847.392
registros de compras: casamento difuso de produto com F1 de 93,4%, detecção de
anomalia com F1 de 90,8%, previsão com MAPE de 4,2%. O casamento difuso é
exatamente o problema de agrupar itens equivalentes vindos do PNCP com descrições
divergentes.

**Evidência de campo de que a necessidade existe.** [17] é qualitativo, vinte
participantes, e registra que automação já é usada na preparação de documentação
de compras e na simplificação de linguagem técnica. Amostra fraca, mas é
evidência empírica de que o módulo de minutas responde a necessidade observada.

**Risco de desenho, e vale registrar.** [13] é o mais citado do eixo (123
citações, Manufacturing & Service Operations Management), mas o objeto é outro:
experimento de campo sobre como fornecedores mudam a cotação quando o comprador é
um agente automatizado. Achado relevante como risco: há discriminação de preço
contra comprador automatizado, que recebe cotação mais alta que comprador humano
quando não há sinalização. Não afeta o módulo que consulta o PNCP, mas afetaria
qualquer extensão futura que cotasse junto a fornecedor.

Contexto adicional: [16] software de análise de mercado em compras públicas
russas; [18] revisão sobre contribuição da IA a compras públicas; [20]
modernização de compras com aprendizado de máquina, citando compras públicas
como 16,9% do PIB europeu.

## 7. Onde sobra espaço, e com que força de evidência

Separado de propósito entre o que está provado e o que é leitura.

**Provado pelos resultados** — a literatura cobre e o trabalho não deve
reivindicar como novidade:

- RAG sobre corpus jurídico e regulatório, inclusive brasileiro [3]
- RAG sobre documento de licitação [4][6]
- Estimativa de preço de referência por estatística e por aprendizado de
  máquina, inclusive no Brasil [11][12][14]
- Extração de informação de documento de licitação [15]
- Arquitetura de fundamentação com proveniência para governo [7]

**Inferência, com a força de cada uma declarada:**

| # | Lacuna candidata | Força da evidência |
|---|---|---|
| 1 | **Geração de minuta**, não consulta a documento. Nenhum dos vinte devolvidos trata de redigir ETP ou TR a partir de formulário guiado | **Fraca a média.** É ausência em 20 resultados de **uma** base, com o eixo 4 — o que buscaria justamente geração — **não executado**. Não afirmar lacuna no texto antes de rodar o eixo 4 |
| 2 | **Reprodutibilidade temporal da pesquisa de preços.** Nenhum dos trabalhos de preço [11][12][14][19] menciona trilha que permita reconstituir a cotação como ela era na data de execução | **Média.** É o recorte de banco de dados do trabalho, e a ausência é consistente nos quatro |
| 3 | **Município de pequeno porte.** O corpus é de escala nacional (58 mil licitações [14], 847 mil registros [19]) ou de agência central [7] | **Média.** Contexto genuinamente ausente nos devolvidos |
| 4 | **Lei nº 14.133/2021 como objeto.** [11] é brasileiro e trata de preço, mas nada ancora ETP e TR como artefatos exigidos pela fase preparatória | **Média.** Reforça 1 e 3 |

A combinação de 2, 3 e 4 é mais defensável que qualquer uma isolada: trilha de
auditoria reproduzível, em prefeitura pequena, sobre os artefatos que a 14.133
exige.

## 8. Riscos que a rodada revelou

1. **[4] é concorrência direta e é de 2026.** Precisa ser lido inteiro e
   posicionado explicitamente no quadro comparativo. Ignorá-lo é o pior desfecho
   possível na banca.
2. **Quatro dos itens mais aderentes têm zero citações**, e três têm veículo não
   identificado pela base — inclusive [11], o mais próximo do problema. Sem
   conferência na fonte, nenhum deles entra no texto.
3. **[2] e [5] contestam a suficiência do índice vetorial.** A decisão de
   modelagem de dados vai ter que responder, e não por omissão.
4. **O corpus recuperado é dominado por pergunta e resposta.** Se o eixo 4
   mostrar que geração de minuta também já foi publicada, a lacuna 1 cai e o
   argumento de contribuição precisa se apoiar em 2, 3 e 4.

## 9. O que ficou em aberto

- **Eixos 3 e 4**, até 1º de setembro de 2026, quando a cota da base volta.
- **Reformular a consulta do eixo 4** para separar geração de recuperação. A
  formulação original arriscava devolver os mesmos trabalhos de pergunta e
  resposta que o eixo 1 já trouxe.
- **Conferir na fonte primária** todos os metadados, com prioridade para [4],
  [6], [7] e [11].
- **Ler [4] inteiro** antes de escrever qualquer linha de trabalhos relacionados.
- **Segunda base.** Uma base só não triangula. Sobreposição entre respostas
  independentes é o sinal mais barato de que uma referência é central, e é o que
  o protocolo em `prompt-levantamento-literatura.md` recomenda.
- **Eixo 3 talvez não deva ser resolvido por literatura.** Comparação de
  desempenho entre `pgvector` e bancos vetoriais dedicados vive em *benchmark* de
  engenharia, e a Iniciação Científica em andamento no PET-EG produz dado
  primário próprio sobre exatamente isso. Se a decisão se apoiar em medição
  própria em vez de literatura, o texto tem de declarar isso — não é evidência
  revisada por pares, e apresentá-la como tal seria erro.

## 10. Conclusão

A rodada cumpriu o que precisava cumprir: mostrou que o tema tem literatura,
identificou um concorrente direto, e trouxe uma referência brasileira exatamente
sobre preço de referência em licitação. Nenhuma delas derruba o trabalho, e duas
delas — [4] e [11] — melhoram o projeto ao dar precedente metodológico.

A lacuna mais provável não é "usar IA em licitação", que já existe, e sim
**reconstituir uma pesquisa de preços exatamente como ela era na data em que foi
feita, em município de pequeno porte, sobre os artefatos que a Lei nº 14.133/2021
exige**. Isso é o recorte de banco de dados, e é o que justifica a orientação.

Meia rodada, portanto, e nenhuma citação liberada para o texto até a conferência
na fonte.

## 11. Referências devolvidas pela base

> Lista bruta, na numeração usada acima. **Metadados não conferidos.** A ordem
> das iniciais dos autores, o ano e o veículo são o que a base informou, e é
> exatamente esse tipo de campo que a regra de rigor manda verificar.

| # | Título | Autoria informada | Ano | Veículo informado | Citações |
|---|---|---|---|---|---|
| 1 | Improving citizen-government interactions with generative artificial intelligence | Lixin Yun et al. | 2024 | PLOS ONE | 22 |
| 2 | Hybrid Multi-Agent GraphRAG for E-Government: Towards a Trustworthy AI Assistant | George Papageorgiou et al. | 2025 | Applied Sciences | 19 |
| 3 | Using Retrieval-Augmented Generation to Improve Access to Legal Documents | Eniedson Fabiano Pereira da Silva Júnior et al. | 2026 | Int. Conference on Semantic Computing (ICSC) | 1 |
| 4 | Optimizing Retrieval-Augmented Generation for Querying Locally Stored Public Procurement Documents using Small Language Models | Dean Reight F. Billedo et al. | 2026 | 2nd ICCIAA | 0 |
| 5 | KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation | Lei Liang et al. | 2024 | Companion Proc. ACM Web Conference 2025 | 130 |
| 6 | A Dual-Mode Retrieval-Augmented Generation System for Interactive Question Answering of Public Tender Documents | V. R. Montequín et al. | 2026 | **não identificado** | 0 |
| 7 | RAG-grounded Advisory Systems for Government Decision-making | Zeki Emre Tekin | 2026 | SSRN Electronic Journal | 0 |
| 8 | Implementing Retrieval-Augmented Generation and Vector Databases for Chatbots in Public Services Agencies Context | Ibnu Pujiono et al. | 2024 | JITK | 11 |
| 9 | Legal Assistance in Low-Resource Languages: Evaluating RAG and Fine-Tuned LLMs for Greek e-Governance | M. Tsourma et al. | 2025 | 3rd FLLM | 1 |
| 10 | Groundedness in Government Document Chatbots: A Systematic Literature Review and Metric Oriented Analysis | Frendy Rumambi et al. | 2026 | Systematic Literature Review Journal | 0 |
| 11 | Intelligent Methodologies for Preparing Reference Prices in Brazilian Public Biddings | Eduardo Marques Braga Faria et al. | 2025 | **não identificado** | 0 |
| 12 | Award Price Estimator for Public Procurement Auctions Using Machine Learning Algorithms: Case Study with Tenders from Spain | Manuel J. García Rodríguez et al. | 2021 | Studies in Informatics and Control | 9 |
| 13 | AI and Procurement | Ruomeng Cui et al. | 2020 | Manufacturing & Service Operations Management | 123 |
| 14 | Public Procurement Announcements in Spain: Regulations, Data Analysis, and Award Price Estimator Using Machine Learning | M. Rodríguez et al. | 2019 | Complexity | 22 |
| 15 | AI-based decision support system for public procurement | Lucia Siciliani et al. | 2023 | Information Systems | 37 |
| 16 | The use of software to support management decisions in public procurement | A. Rada et al. | 2022 | **não identificado** | 2 |
| 17 | The Impact of Automation and AI on Public Procurement Performance in Tanzania | Godfrey Fabia Mbondo | 2026 | Asian Journal of Education and Social Studies | 0 |
| 18 | The Artificial Intelligence and Public Procurement | Berraida Riyad et al. | 2024 | IEEE 15th LOGISTIQUA | 3 |
| 19 | A Rigorous Multi-Agent Framework for Procurement Optimization | S. Mujtaba et al. | 2025 | International Journal of Applied Mathematics | 0 |
| 20 | Modernizing Procurement in Supply Chain with AI and Machine Learning Techniques | Goli Mallesham | 2024 | International Journal of Engineering and Computer Science | 0 |
