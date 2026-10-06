---
tipo: paper
autores: ["Weslley Emmanuel Martins Lima", "Victor Ribeiro da Silva", "Jasson Carvalho da Silva", "Ricardo de Andrade Lira Rabêlo", "Anselmo Cardoso de Paiva"]
ano: 2026
titulo: "HelBERT: A BERT-Based Pretraining Model for Public Procurement Tasks in Portuguese"
venue: "Journal of the Brazilian Computer Society, v. 32, n. 1"
tags: [fundamentacao, representacao-de-texto, modelo-de-linguagem, licitacao, portugues, brasil, decisao-a2]
citacao_abnt: "LIMA, Weslley Emmanuel Martins et al. HelBERT: a BERT-based pretraining model for public procurement tasks in Portuguese. Journal of the Brazilian Computer Society, [s. l.], v. 32, n. 1, p. 145-158, 2026. DOI: 10.5753/jbcs.2026.5511."
arquivo_local: "TCC/papers/lima-2026-helbert.pdf"
verificado: true
---

# HelBERT: A BERT-Based Pretraining Model for Public Procurement Tasks in Portuguese

> **`verificado: true`** — conferido em 06/10/2026. Autores, periódico, ano,
> volume e número, no cabeçalho do PDF; páginas 145-158 e data de publicação
> (21/02/2026), nos metadados da página do artigo na biblioteca da SBC. O PDF não
> imprime número de página: citação direta precisa de reconferência.
>
> **Atenção ao resumo.** Ele anuncia ganho de 5% e 4% em F1 na classificação
> sobre os dois principais modelos de comparação. As tabelas do corpo do artigo
> mostram ganho menor — ver "Resultados-chave". Citar os números das tabelas, não
> os do resumo.

## Síntese

Grupo da Universidade Federal do Piauí, com a Federal do Maranhão e o tribunal
de contas do estado. Treina do zero um modelo de linguagem do tipo BERT sobre
documentos de compras públicas em português — editais, contratos e leis — e
mostra que ele supera modelos de uso geral e modelos jurídicos em três tarefas
do domínio. Publica três variantes: a base, uma para texto longo e uma podada,
com metade das camadas. Os modelos estão disponíveis em repositório público, sob
licença permissiva.

## Contribuições

- Primeiro modelo de linguagem pré-treinado em grande volume de documentos de
  compras públicas em português, segundo os autores.
- Variante para documentos de até 4.096 unidades de texto, com mecanismo de
  atenção local, esparsa e global.
- Variante podada, com seis camadas, quase duas vezes mais rápida.
- Comparação com quatro modelos: dois de uso geral e dois jurídicos, todos em
  português ou multilíngues.

## Método

**Corpus de pré-treino:** 460 mil documentos, 47 GB brutos — editais do portal
federal de compras (278.739) e do tribunal de contas do Piauí (142.374),
contratos (38.902) e 21 leis. Segmentado em 9.827.103 sentenças de até 128
unidades.

Três decisões de preparação que importam para quem for usar o modelo em
descrição de item:

- **sentenças com menos de dez unidades foram descartadas**, por serem
  consideradas fragmento ruidoso;
- **números, datas, endereços e horários foram trocados por marcadores
  padronizados**;
- tudo em caixa baixa e sem acento.

Pré-treino só por modelagem de linguagem mascarada, seis épocas, 72 horas numa
única placa de 8 GB.

**Avaliação intrínseca:** perplexidade sobre um conjunto de documentos de Minas
Gerais não visto no treino; fertilidade do tokenizador; previsão de palavras do
domínio mascaradas.

**Avaliação extrínseca,** com validação cruzada em cinco partes:

1. classificar o objeto de uma licitação em quatro naturezas — obra, serviço,
   bem de consumo, bem permanente — sobre 2.137 amostras;
2. apontar sete tipos de cláusula restritiva em 1.818 editais;
3. **similaridade semântica** entre objetos de contratação, sobre 1.754 pares
   anotados por especialistas como semelhantes ou não, medida por similaridade de
   cosseno com um limiar escolhido para cada modelo.

## Resultados-chave

| Tarefa | Melhor variante do modelo | Modelo geral em português | Melhor modelo jurídico |
|---|---|---|---|
| Perplexidade (menor é melhor) | 10,37 | 49,89 | 41,48 |
| Fertilidade do tokenizador (ideal: 1) | 1,17 | 1,83 | 1,33 |
| Natureza do objeto, F1 ponderado | 96,96 (podada) | 95,80 | 94,68 |
| Cláusula restritiva, F1 | 94,91 (texto longo) | 92,06 | 92,40 |
| Similaridade de objetos, F1 | 97,20 (podada) | 93,53 | 95,70 |

- A variante podada ganha da base na classificação e na similaridade, com 68
  milhões de parâmetros e 263 MB.
- **A similaridade sobre o texto integral do objeto deu resultado
  "decepcionante"**, nas palavras dos autores. Só funcionou depois de extrair,
  com reconhecimento de entidades, a expressão central do objeto.
- Em reconhecimento de entidades, o modelo **não** superou um modelo
  multilíngue de uso geral.

## Limitações

Declaradas: todas as tarefas usam editais; em reconhecimento de entidades não
houve ganho; só cerca de 1% do material foi anotado; recurso computacional
restringiu tamanho de lote e de sentença.

Da leitura:

- O limiar de similaridade foi escolhido, para cada modelo, **no mesmo conjunto
  em que o F1 é relatado**. O número é otimista e a comparação entre modelos
  fica frouxa.
- O artigo não diz como o vetor da sentença é obtido a partir do modelo.
- O ganho na classificação de natureza é de cerca de um ponto, não de cinco.
- A tarefa de similaridade é decidir se **dois objetos de licitação** são
  semelhantes — o objeto é a frase que resume a contratação inteira. Não é
  recuperar, entre milhares de itens, os comparáveis a um item pedido.

## Relevância para este TCC

É a leitura que mais pesa na decisão sobre o modelo de representação das
descrições, e ela **acrescenta um candidato sem encerrar a decisão**.

### O que muda

1. **Entra um candidato de domínio, publicado e pequeno.** Há modelo treinado em
   documento de licitação brasileira, disponível sob licença permissiva, com
   variante podada que roda com folga na máquina de trabalho. Deixá-lo fora da
   bateria de testes seria difícil de justificar diante da banca.
2. **Dá a comparação mínima que a bateria precisa ter:** um modelo de uso geral
   em português, um jurídico e o de domínio. A ordem que o artigo encontrou —
   domínio acima de jurídico, jurídico acima de geral — é a hipótese a testar
   sobre itens.

### O que não muda, e por quê

O artigo **não autoriza escolher esse modelo sem medir**, por quatro razões que
saem do próprio método:

1. **O corpus exclui o tipo de texto que interessa.** Sentença com menos de dez
   unidades foi descartada no pré-treino. Descrição de item municipal tem
   mediana de seis palavras ([[silva-2024-sobrepreco-itens-licitacao]]). O
   modelo viu prosa de edital, não lista de itens.
2. **Número foi apagado.** Trocar todo número por um marcador elimina
   exatamente o que [[brum-2024-agrupamento-itens-similares]] mostrou decidir se
   dois itens são o mesmo: caixa de cem não é caixa de mil. Isso reforça tratar
   unidade e quantidade como **filtro estruturado**, fora do vetor.
3. **Não é modelo de recuperação.** Foi treinado para prever palavra mascarada,
   não para aproximar textos de mesmo sentido. Os próprios autores só obtiveram
   similaridade útil depois de extrair a expressão central. Modelo treinado
   para similaridade de sentença pode ganhar dele nesta tarefa mesmo sem
   conhecer o domínio.
4. **A tarefa medida é outra.** Par de objetos acima de um limiar não é lista
   ordenada de candidatos para um item.

### Consequência prática para a bateria

Como o gabarito de 231 itens com as escolhas de quem cotou pode ser montado, a
pergunta deixa de ser "qual modelo a literatura recomenda" e passa a ser "qual
ganha no nosso dado". Das fontes lidas saem, como candidatos a testar:

| Candidato | De onde vem a indicação | O que testa |
|---|---|---|
| Busca por palavra, com e sem a heurística da primeira palavra | [[brum-2024-agrupamento-itens-similares]] | Linha de base. Se o modelo denso não ganhar dela, não há diferencial |
| Modelo de uso geral em português | comparação deste artigo | Quanto custa não ter domínio |
| Este modelo, base e podado | este artigo | Quanto vale o domínio |
| Modelo de sentença ajustado para similaridade | [[brum-2024-agrupamento-itens-similares]] | Quanto vale ser treinado para similaridade |
| Modelo multilíngue de vetores de uso geral | usado como instrumento em [[gao-2026-criterios-sustentaveis-suica]] e em [[vandermeer-2026-legalcheck]] | O que se obtém sem nenhum ajuste |
| Combinação de palavra e vetor | apontada em [[siciliani-2023-apoio-a-decisao-licitacoes]] | Se os sinais se somam |

Dois cuidados de método que este artigo ensina pelo que deixou de fazer:
escolher qualquer limiar ou parâmetro **num subconjunto separado** do que mede o
resultado; e testar, além do texto integral, a descrição reduzida ao núcleo do
item, já que a redução foi o que fez a similaridade funcionar lá.

O mesmo grupo publica, no mesmo repositório, modelos de reconhecimento de
características de produto e de vínculo com o catálogo federal. Não fazem parte
do artigo e não foram avaliados aqui; ficam como pista para o requisito de
apontar especificação não verificável.

## Citáveis

> "Sentences shorter than ten tokens were excluded, as concise sentences
> typically represent noisier or incomplete text fragments." (Lima et al., 2026,
> seção 4.1)

> "applying semantic similarity techniques to the full text of contract objects
> yielded disappointing results" (Lima et al., 2026, seção 5.2.3)

> "the results obtained by the proposed model in the named entity recognition
> tasks were not superior to those obtained by general-purpose models" (Lima et
> al., 2026, seção 6)

## Backlinks

- [[brum-2024-agrupamento-itens-similares]]
- [[silva-2024-sobrepreco-itens-licitacao]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
