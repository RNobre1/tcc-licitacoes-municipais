---
tipo: pesquisa
titulo: "O que as bases novas acrescentam, e o que a leitura muda na escolha do modelo de representação e no desenho da avaliação?"
status: três bases novas consultadas; cinco fontes lidas integralmente e conferidas; duas decisões afetadas
criado: 2026-10-06
autor: Rafael Nobre de Souza
relacionado:
  - docs/pesquisas/levantamento-literatura-segunda-rodada.md
  - docs/pesquisas/sistemas-existentes.md
  - docs/arquitetura/README.md
  - docs/tasks/backlog.md
  - TCC/papers/
tags: [pesquisa, literatura, representacao-de-texto, avaliacao, ameaca-a-validade, teses, sbc]
---

# Ampliação de bases e escolha do modelo de representação

> ## Como ler esta nota
>
> A segunda rodada do levantamento usou uma base só e declarou isso como
> limite. Esta nota consulta três outras e lê por inteiro cinco trabalhos,
> escolhidos por um critério: **mudar alguma decisão**, e não aumentar a lista.
>
> Valem as duas regras de sempre. Fonte só entra lida por inteiro; metadado só
> vale conferido na fonte primária. Cada leitura tem fichamento em `TCC/papers/`.
>
> Uma afirmação da segunda rodada é corrigida na seção 8.

## 1. Contexto

Duas coisas mudaram desde a segunda rodada.

A decisão em aberto mais importante da arquitetura é o modelo de representação
das descrições de item. E foi confirmado que o conjunto de avaliação pode ser
montado dos documentos já recebidos: 231 itens reais, com os preços que a
servidora escolheu para cada um. Com gabarito na mão, a pergunta deixa de ser
"qual modelo a literatura recomenda" e passa a ser **quais modelos vale a pena
testar, e o que o teste vai poder concluir**.

## 2. Pergunta

Consultadas bases fora da já usada, o que aparece de novo — e, lidos os
trabalhos que tocam a escolha do modelo e a avaliação, que candidatos entram na
bateria de testes e que cuidados o desenho da avaliação precisa ganhar?

## 3. Resposta curta

**Três achados mudam decisão. Um corrige afirmação anterior.**

1. **O gabarito favorece a busca por palavra, e isso tem de ser dito.** Os
   preços escolhidos pela servidora foram encontrados numa ferramenta que busca
   por palavra. A literatura de avaliação mede esse caso: quando os relevantes
   anotados foram escolhidos por um sistema de busca, sistemas parecidos com
   ele saem favorecidos, e quase um em cada cinco pares de sistemas aparece na
   ordem errada [2]. Consequência: se a busca por significado ganhar, ganhou em
   desvantagem; se perder, não está refutada. A sessão de validação com a
   usuária deixa de ser complemento e vira condição do desenho — seção 6.

2. **O modelo treinado em licitação brasileira não é o favorito.** Existe um,
   publicado e aberto [1]. Mas ele foi treinado só para prever palavra
   mascarada, descartou no treino as sentenças curtas e apagou os números. E a
   evidência mais ampla disponível sobre texto brasileiro mostra que essa classe
   de modelo vai mal em recuperação, por causa do objetivo de treino e não da
   língua [3]; um experimento revisado por pares, em português, não distinguiu
   modelos de domínio de um modelo geral [4]. Ele entra na bateria como
   candidato e como contraste — seção 5.

3. **A escolha do modelo está amarrada à trilha de auditoria.** Serviço
   comercial de vetores muda sem aviso [3]. Um vetor que muda impede
   reconstituir uma pesquisa como estava na data. Modelo de pesos abertos com
   versão fixada é condição de reprodutibilidade, não só de custo.

**A correção:** existe um banco de preços brasileiro, descrito em artigo, que
oferece consulta de preço de referência para abrir licitação [5]. A lacuna de
triagem de comparabilidade continua de pé, mas mais estreita — seção 8.

**O que as bases novas confirmaram:** a produção brasileira de computação sobre
licitação é numerosa e está quase toda do lado do controle — fraude, conluio,
sobrepreço. Nenhum título encontrado trata de gerar as peças da fase
preparatória nem de apoiar a triagem de preço candidato.

## 4. Método

Consultas feitas em 06/10/2026.

### 4.1 Base de literatura já usada, três consultas novas

Sem filtro, 20 de 20 devolvidos em cada uma.

| Consulta | O que testa |
|---|---|
| *information retrieval evaluation with incomplete relevance judgments* | como avaliar com gabarito incompleto |
| *Portuguese text embedding models benchmark for semantic textual similarity and retrieval* | candidatos de modelo para português |
| *entity matching of product offers with pretrained language models short textual descriptions* | casamento de descrição curta de produto |

### 4.2 Biblioteca digital brasileira de teses e dissertações

Pela interface de busca para programas, em todos os campos.

| Consulta | Registros |
|---|---|
| "pesquisa de preços" licitação | 19 |
| "preço de referência" "compras públicas" | 10 |
| "termo de referência" "linguagem natural" | 3 |
| "banco de preços" licitação | 2 |
| "compras públicas" "processamento de linguagem natural" | 1 |
| "estudo técnico preliminar" "inteligência artificial" | 1 |
| licitação "mineração de texto" | 1 |
| "pesquisa de preços" licitação "aprendizado de máquina" | **0** |
| "compras públicas" "aprendizado de máquina" | **0** |
| "sobrepreço" licitação "descrição" | **0** |
| licitação itens descrição similaridade semântica preços | **0** |

### 4.3 Publicações da Sociedade Brasileira de Computação

Por um índice aberto de publicações, restrito ao prefixo de identificador da
SBC, com busca em título e resumo.

| Consulta | Registros |
|---|---|
| licitação OU licitações | 32 |
| "public procurement" OU "public bidding" OU "bidding" | 19 |
| "pesquisa de preços" | 2 |
| "preço de referência" | **0** |
| "termo de referência" geração | **0** |
| "compras públicas" semântica | **0** |
| licitação descrição itens similaridade | **0** |

### 4.4 Repositório de preprints

| Consulta | Registros |
|---|---|
| "public procurement" com casamento de item, descrição de item, preço de referência ou estimativa de preço | 1, fora do tema |
| "public procurement" com busca semântica, recuperação densa ou vetores | 1, sobre detecção de linguagem acusatória |

### Limite

A busca por título e resumo perde trabalho cujo resumo está só em inglês quando
a consulta é em português, e vice-versa — por isso as consultas à SBC foram
feitas nas duas línguas. Não foi consultado o catálogo de teses da agência
federal de pós-graduação. "Zero registros" aqui quer dizer zero nesta base, com
esta consulta.

## 5. O que cada base acrescentou

| Base | Acrescentou | Confirmou |
|---|---|---|
| Base de literatura, consultas novas | A literatura de avaliação com gabarito incompleto, que a rodada anterior não tinha buscado; dois conjuntos de avaliação de modelos para português, ambos de 2026 | — |
| Teses e dissertações | Um corpo de dissertações de **administração** sobre a fase interna e sobre o efeito da regulamentação da pesquisa de preços — material para a fundamentação, não para o quadro | Nenhuma tese une pesquisa de preços a aprendizado de máquina ou a processamento de linguagem, nas consultas feitas |
| Publicações da SBC | **Um sistema existente descrito em artigo** [5]; cerca de cinquenta trabalhos sobre licitação nos eventos e periódicos da sociedade | A concentração no controle: pelos títulos, a quase totalidade trata de fraude, conluio, sobrepreço, classificação de documento e qualidade de dado |
| Repositório de preprints | Nada | Ausência de trabalho sobre casamento de item ou busca semântica em compras públicas fora do que já se tinha |

**Leitura da distribuição.** A comunidade brasileira de computação produz
bastante sobre licitação, publica nos eventos de banco de dados e de sistemas
de informação, e olha para o processo **depois** que ele aconteceu. Isso
sustenta duas afirmações: o tema cabe nesses eventos, e a fase preparatória é o
lado pouco atendido.

## 6. Avaliação: a ameaça que a leitura expôs, e o que muda no desenho

### 6.1 O problema

O conjunto de avaliação tem, para cada item, os preços que a servidora
escolheu. Tudo o mais na base é tratado como não relevante. Isso é anotação
parcial, e a literatura a contesta há décadas.

O estudo lido [2] mede o tamanho do problema num conjunto em que quase todos os
relevantes são conhecidos. Com um só relevante anotado por consulta:

| Como o relevante anotado foi escolhido | Pares de sistemas na ordem errada |
|---|---|
| Ao acaso | 3,2% |
| O mais popular, ou o mais curto | 15,1% |
| **Por um sistema de busca existente** | **19,2%** |
| O mais longo | 22,8% |

E a direção do erro é conhecida: quando quem escolheu foi um sistema de busca
por palavra, outro sistema por palavra aparece como o melhor; quando foram
sistemas de vetor, esse mesmo sistema aparece como o pior.

### 6.2 Por que é exatamente este caso

A servidora chegou aos preços digitando palavras num banco de preços que busca
por palavra. Os relevantes do gabarito são, por construção, os que uma busca
por palavra alcança. Há ainda dois filtros dela sobre o que a busca devolveu,
ambos documentados no levantamento de requisitos: o preço esperado e a
prioridade geográfica.

Um método por significado que encontre item comparável descrito com outras
palavras — que é o que ele promete — será contado como erro.

### 6.3 O que se pode concluir, em cada desfecho

| Desfecho no gabarito | Leitura permitida |
|---|---|
| Busca por significado ganha da busca por palavra | Resultado conservador. Ganhou em desvantagem |
| Empata ou perde | **Não refuta.** Não se distingue "é pior" de "achou comparáveis que o gabarito não registra" |
| Dois modelos de vetor diferem por pouco | Não se lê. Com poucos relevantes por consulta, só diferença grande sobrevive [2] |

### 6.4 O que muda no desenho

1. **A sessão de validação com a usuária vira condição, com forma definida.**
   Juntar os primeiros resultados de todos os métodos comparados, inclusive a
   busca por palavra; embaralhar; pedir o julgamento sem indicar a origem.
   Julgar só os resultados de um método repetiria o viés com o sinal trocado.
2. **Busca por palavra é linha de base obrigatória**, sabendo-se que parte em
   vantagem.
3. **Guardar a lista curta.** A validação de setembro mostrou que ela marca
   mais candidatos antes de filtrar os três. Cada relevante a mais por item é o
   que estabiliza a ordem dos sistemas.
4. **Teste pareado sobre os itens, com intervalo.** Reamostrar os 231 itens e
   relatar a diferença com incerteza; declarar empate quando for empate. O
   conjunto de avaliação para português lido faz exatamente isso e mostra que
   seus seis primeiros modelos são indistinguíveis [3].
5. **Separar o subconjunto de ajuste.** Qualquer limiar ou parâmetro escolhido
   nos mesmos itens em que se mede o resultado infla o número — foi o que
   ocorreu na tarefa de similaridade do modelo de licitação [1].
6. **Declarar a ameaça no texto**, com a referência.

A avaliação em duas condições, com e sem o preço esperado, não é afetada: ela
compara cada método consigo mesmo.

## 7. Modelo de representação: o que a leitura permite afirmar

### 7.1 Três afirmações, com a força de cada uma

| Afirmação | Força | Apoio |
|---|---|---|
| Modelo treinado só para prever palavra mascarada vai mal em recuperação, qualquer que seja o domínio | **Forte, com ressalva** — 93 modelos, texto nativo; mas é preprint sem revisão | [3] |
| Especializar o modelo no domínio por pré-treino rende pouco em recuperação | **Média** — duas fontes independentes, uma delas sem teste de significância | [3][4] |
| Ajustar o modelo para similaridade é o que mais pesa | **Média** — claro em [3]; em [4] a diferença é menor que o ruído provável | [3][4] |

### 7.2 O que isso diz do modelo de licitação

Ele existe, é aberto, é pequeno na versão podada, e ganhou de modelos gerais e
jurídicos nas tarefas em que foi testado [1]. Quatro coisas, porém, saem do
próprio método dele:

- foi treinado só para prever palavra mascarada;
- **descartou no treino as sentenças com menos de dez unidades** — e descrição
  de item municipal tem mediana de seis palavras;
- **trocou todo número por um marcador** — e número é o que separa caixa de cem
  de caixa de mil;
- a tarefa de similaridade em que foi medido compara dois objetos de licitação
  acima de um limiar, e só funcionou depois de reduzir o texto ao núcleo.

Nada disso o exclui. Tudo isso impede escolhê-lo sem medir.

### 7.3 Bateria proposta

Por classe, para que o teste responda a perguntas e não só ordene nomes. Os
nomes são exemplos presentes nas fontes lidas.

| # | Classe | Pergunta que responde | Exemplos |
|---|---|---|---|
| 1 | Busca por palavra, com e sem agrupamento pela primeira palavra | Há diferencial? | BM25; a heurística dos trabalhos de Minas Gerais |
| 2 | Português, só palavra mascarada, uso geral | Contraste negativo previsto | BERTimbau |
| 3 | Português, só palavra mascarada, domínio de licitação | O domínio compensa o objetivo de treino? | HelBERT, base e podado |
| 4 | Português, ajustado para similaridade | O objetivo de treino é o que pesa? | SBERT-pt; família Serafim, variante de recuperação |
| 5 | Multilíngue de uso geral, tamanho médio | A linha de base de vetor | multilingual-E5; BGE-M3 |
| 6 | Pequeno perto do topo do conjunto de avaliação em português | Tamanho importa neste dado? | EmbeddingGemma de 308 milhões |
| 7 | Grande, de pesos abertos | Qual o teto sem serviço pago? | Qwen3-Embedding |
| 8 | Combinação de palavra e vetor | Os sinais se somam? | fusão das classes 1 e a melhor de 4 a 6 |

Variantes de entrada a cruzar com as classes 3 a 7: descrição integral, e
descrição reduzida ao núcleo do item.

**Fora da bateria, de propósito:** serviço comercial de vetores. Pode entrar
como referência de teto numa medição isolada, mas não como candidato a
componente do sistema, pela razão da seção 3, item 3.

**Filtro estruturado fica fora do vetor em todas as classes.** Unidade,
quantidade, natureza, região e período são condição, não sinal a aprender. As
leituras desta rodada e da anterior apontam para o mesmo lado: o modelo de
licitação apaga número [1], e os trabalhos de Minas Gerais mostram que número e
unidade decidem a identidade do item.

### 7.4 O que continua em aberto

- Se vale ajustar um modelo da classe 4 ou 5 com pares do próprio domínio.
  As fontes sugerem que é o caminho mais promissor [3], mas exige pares de
  treino separados dos 231 itens de avaliação.
- Qual máquina roda a classe 7.
- Como fixar e registrar a versão do modelo junto de cada pesquisa, para que a
  reconstituição seja possível.

## 8. Correção à segunda rodada

A segunda rodada afirmava, ao descrever a lacuna de triagem de comparabilidade,
que os trabalhos de preço lidos ou partem das cotações já reunidas ou agrupam
itens para apontar sobrepreço depois, e que **nenhum apoia a decisão de quem
monta a cotação**.

**Um apoia, em parte.** O banco de preços de Minas Gerais [5] descreve, como
um de seus dois usos, obter preço de referência para abrir uma licitação. O
exemplo dado é o de um palco de seis por quatro metros: o usuário escreve uma
consulta que exige uma palavra, exige um padrão com caractere curinga para
cobrir as formas de escrever a medida, e exclui outra palavra para tirar da
lista os itens de iluminação.

A afirmação correta:

> Há ferramenta brasileira que oferece consulta de preço de referência para a
> fase preparatória. Ela busca por palavra, devolve estatística sobre tudo o que
> a consulta trouxe e deixa com o usuário o trabalho de decidir o que é
> comparável — a ponto de ele ter de programar a comparabilidade na própria
> consulta. Está disponível só para usuários internos do órgão que a mantém.

A lacuna fica mais estreita e, ao mesmo tempo, mais bem ilustrada: o exemplo do
palco é a descrição, feita pelos autores de um banco de preços acadêmico, do
custo que este trabalho mediu em campo.

## 9. Fila de leitura

Encontrados nesta rodada, **não lidos**. Metadados como a base os devolveu.

**Para a fundamentação sobre a fase preparatória — dissertações de
administração**

| Título | Autoria informada | Ano | Instituição |
|---|---|---|---|
| A eficiência nas contratações públicas: uma análise da fase interna das licitações | Maciel | 2022 | UnB |
| Inovação em compras públicas: análise e proposições para a etapa preliminar do processo licitatório do executivo catarinense | Bayestorff | 2024 | UDESC |
| Aplicação de métodos estatísticos na definição de preços de referência em compras públicas | Costa Júnior | 2026 | UERJ |
| Análise da metodologia de pesquisa de preços e o impacto nas compras do Instituto Federal de Minas Gerais | Oliveira | 2023 | IFMG |
| A busca da eficiência nas licitações públicas: o efeito da regulamentação da pesquisa de preço sobre as compras no Instituto Federal de Pernambuco | Silva Neto | 2020 | UFPE |

A primeira é a que mais interessa: se medir a duração da fase interna, dá um
segundo número, independente, para pôr ao lado dos nove a vinte e oito dias
medidos neste trabalho.

**Para a avaliação**

| Título | Por que |
|---|---|
| One-Shot Labeling for Automatic Relevance Estimation (2023) | Como preencher as lacunas de julgamento quando há um só relevante por consulta. Cópia aberta localizada |
| Retrieval evaluation with incomplete information (2004) | A referência fundadora do problema. **Acesso fechado**; sem cópia aberta localizada |

**Para o casamento de item**

| Título | Por que |
|---|---|
| An Approach for Product Record Linkage Using Cross-Lingual Learning and Large Language Models (2025) | Descrição curta e variada de produto em nota fiscal eletrônica brasileira |
| Sobrepreço em compras públicas: metodologia baseada na identificação de valores discrepantes (2024) | Mesmo evento e mesmo ano do banco de preços de Minas Gerais |

## 10. O que não foi conferido

- **Versão publicada de [2]**, se houver: o preprint não diz onde saiu.
- **[3] é preprint sem revisão por pares**, e seus apêndices não foram lidos.
- **Os exemplos de modelo da seção 7.3** vêm das fontes lidas; não foi
  verificado, um a um, se cada modelo continua disponível, sob que licença, e se
  roda na máquina de trabalho. Só o modelo de licitação teve a disponibilidade
  e a licença conferidas no repositório público.
- **Os cerca de cinquenta títulos da SBC** foram lidos só como títulos. A
  afirmação de concentração no controle descreve os títulos.
- **As teses** da seção 9 não foram abertas.
- **Catálogo de teses da agência federal:** não consultado.

## 11. Referências

### Lidas por inteiro e conferidas nesta rodada

| # | Referência | Identificador |
|---|---|---|
| 1 | Lima, W. E. M. et al. HelBERT: A BERT-Based Pretraining Model for Public Procurement Tasks in Portuguese. *Journal of the Brazilian Computer Society*, v. 32, n. 1, p. 145-158, 2026 | doi:10.5753/jbcs.2026.5511 |
| 2 | Rassin, R. et al. Evaluating D-MERIT of Partial-annotation on Information Retrieval. Preprint, 2024 | arXiv:2406.16048v2 |
| 3 | Stekel, T. R. C. MTEB-BR: A Text Embedding Benchmark for Brazilian Portuguese. Preprint, 2026 | arXiv:2607.04581v2 |
| 4 | Justino, A. F.; Jacob Junior, A. F. L.; Lobato, F. M. F. A Comparative Study of BERT Models for Semantic Retrieval of Brazilian Legal Precedents. Anais do XIII KDMiLe, 2025, p. 65-72 | doi:10.5753/kdmile.2025.247782 |
| 5 | Costa, L. G. L. et al. Quanto Custa: Banco de Preços de Compras Públicas do Estado de Minas Gerais. Anais Estendidos do XXXIX SBBD, 2024, p. 239-245 | doi:10.5753/sbbd_estendido.2024.243804 |

Lida por inteiro e descartada por tangência: uma nota de três páginas sobre uma
plataforma estadual de consulta de preços de varejo a partir de notas fiscais
(Anais Estendidos do SBSI 2023, p. 84-86, doi:10.5753/sbsi_estendido.2023.229243).
É voltada ao consumidor, guarda os preços por dez dias e não trata de compra
pública.

### Devolvidas e não lidas

> **Metadados como as bases os devolveram, não conferidos. Nada aqui é citável.**

| Título | Autoria informada | Ano | Veículo informado | Identificador |
|---|---|---|---|---|
| Retrieval evaluation with incomplete information | Buckley et al. | 2004 | não identificado | doi:10.1145/1008992.1009000 |
| On information retrieval metrics designed for evaluation with incomplete relevance assessments | Sakai et al. | 2008 | Information Retrieval | doi:10.1007/s10791-008-9059-7 |
| One-Shot Labeling for Automatic Relevance Estimation | MacAvaney et al. | 2023 | SIGIR 2023 | doi:10.1145/3539618.3592032 |
| Beyond Multilingual Averages: MTEB-PT, a Benchmark for Portuguese Sentence Encoders | Okamura et al. | 2026 | ArXiv | doi:10.48550/arxiv.2607.04071 |
| Open Sentence Embeddings for Portuguese with the Serafim PT* encoders family | Gomes et al. | 2024 | ArXiv | doi:10.48550/arxiv.2407.19527 |
| BERTimbau: Pretrained BERT Models for Brazilian Portuguese | Souza et al. | 2020 | não identificado | doi:10.1007/978-3-030-61377-8_28 |
| Measuring Brazilian Portuguese Product Titles Similarity using Embeddings | Romualdo et al. | 2021 | não identificado | doi:10.5753/stil.2021.17791 |
| An Approach for Product Record Linkage Using Cross-Lingual Learning and Large Language Models | Alves et al. | 2025 | não identificado | doi:10.5220/0013285000003929 |
| Deep entity matching with pre-trained language models | Li et al. | 2020 | Proc. VLDB Endow. | doi:10.14778/3421424.3421431 |
| JointMatcher: Numerically-aware entity matching using pre-trained language models with attention concentration | Ye et al. | 2022 | Knowl. Based Syst. | doi:10.1016/j.knosys.2022.109033 |
| Pre-trained Embeddings for Entity Resolution: An Experimental Analysis | Zeakis et al. | 2023 | Proc. VLDB Endow. | doi:10.14778/3598581.3598594 |
| Sobrepreço em compras públicas: Metodologia baseada na identificação de valores discrepantes | não informada | 2024 | Anais Estendidos do SBBD | doi:10.5753/sbbd_estendido.2024.244291 |
| Uma Metodologia para Coleta e Mapeamento de Dados de Licitações Públicas dos Portais da Transparência dos Municípios | não informada | 2025 | ERBD | doi:10.5753/erbd.2025.7267 |
| Ferramenta para Auxílio à Auditoria de Editais Municipais para Compra de Medicamentos | não informada | 2024 | Anais Estendidos do SBSI | doi:10.5753/sbsi_estendido.2024.238796 |
