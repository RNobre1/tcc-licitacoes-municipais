---
tipo: pesquisa
titulo: "Como tratar escores empatados no cálculo de Recall@k e MRR da bateria"
status: decidida em 26/11/2026 — opção C; ver TCC/decisões/2026-11-26-empates-na-avaliacao.md
criado: 2026-11-26
autor: Rafael Nobre de Souza
relacionado:
  - TCC/decisões/2026-11-24-limiares-de-aceitacao-r1-r2.md
  - TCC/decisões/2026-11-24-espaco-de-busca-e-preco-do-candidato.md
  - docs/pesquisas/limiares-de-aceitacao-r1-r2.md
tags: [pesquisa, avaliação, empate, recall, mrr, r1, r2, c17]
---

# Escores empatados na bateria de avaliação

## A pergunta

Cada método da bateria ordena o espaço de busca de um item, e o Recall\@10 conta
quantos preços escolhidos pela servidora caem entre os dez primeiros. Quando
dois candidatos recebem exatamente o mesmo escore, a ordem entre eles não vem do
método. Ela vem da regra de desempate. Se um grupo empatado atravessa a décima
posição, é a regra que decide quem entra no Recall\@10.

Hoje o arnês desempata de duas formas:

- na busca por palavra e na linha de base só-preço, pelo menor identificador do
  item;
- na busca semântica sobre os itens públicos, pela ordem em que o Qdrant
  devolve os pontos. Essa ordem nem é estável entre reconstruções do índice.

A revisão da terceira rodada da frente de avaliação mostrou o efeito numa sonda
sintética. Sem palavra em comum com a consulta, os relevantes de menor
identificador dão Recall\@10 de 1,00, e os de maior identificador dão 0,00.

A pergunta é qual regra a bateria usa, fixada antes de medir.

## Por que não é caso de borda

Contagem no banco local em 26/11/2026, sobre as páginas de itens buscadas até
19:12 UTC. Usei a cópia mais recente de cada página, por endpoint e parâmetros.
A descrição foi posta em minúsculas, sem espaço nas pontas e com os espaços
internos colapsados. Só contagens, sem nenhuma descrição impressa:

- 59.207 compras e 791.694 itens;
- 582.167 descrições distintas;
- **262.792 itens (33,2%) têm a descrição idêntica à de pelo menos outro
  item**;
- o maior grupo de descrições idênticas tem 1.796 itens;
- 3.547 grupos têm dez itens ou mais, e somam 137.757 itens (17,4%). São esses
  os grupos capazes de ocupar sozinhos os dez primeiros lugares;
- respeitando maiúsculas e minúsculas, a fração de itens com duplicata é de
  32,1%, e o maior grupo tem 1.556 itens.

O banco continua recebendo a coleta nacional. Repetida em outro instante, a
contagem dá outros números, mas a mesma ordem de grandeza: uma contagem
anterior, refeita pela revisão, deu 32,8%.

O que esses números medem e o que não medem:

- **Duplicata gera empate nos dois métodos.** Descrição idêntica dá escore
  idêntico no BM25, que só olha o texto, e vetor idêntico no modelo de
  representação, que também só recebe o texto.
- **Duplicata não é a única fonte de empate.** O BM25 também empata entre
  descrições distintas com o mesmo comprimento e as mesmas contagens dos termos
  da consulta. Numa sonda **sintética** da revisão, com 8.000 descrições todas
  distintas, um grupo empatado atravessou a décima posição em 74% das
  consultas. É só ilustração, não medida sobre os dados.
- **A contagem é sobre a lista de descrições, não sobre o topo de cada
  ordenação.** Quantos itens do conjunto de avaliação têm um empate que decide
  o Recall\@10 só se sabe rodando os métodos no ajuste.

## O que a literatura diz

Todas as fontes abaixo foram lidas **só no resumo**. Servem para orientar a
decisão e não podem ser citadas no texto do TCC antes da leitura integral. O
texto completo de [1] não foi encontrado até 26/11.

- **Desempate por identificador é parâmetro não controlado.** Desempatar pelo
  nome ou identificador do documento é um parâmetro não controlado da avaliação.
  Num estudo de 22 edições do TREC, essa regra deu diferenças significativas em
  relação a regras mais justas [2].
- **O valor esperado sobre as ordens empatadas.** Há uma forma exata e barata de
  calcular precisão, revocação, F1, precisão média, posto recíproco e nDCG na
  presença de empates. O valor é o esperado sobre todas as ordens possíveis
  dentro dos grupos empatados, calculado sem enumerar as permutações [1]. O
  resumo não trata dos cortes (\@k, MRR\@20). A revisão conferiu por conta
  própria, por enumeração exaustiva em 300 casos pequenos, que as fórmulas do
  Recall\@k, do posto recíproco truncado e do acerto em k batem com a média
  sobre todas as ordens. Essa conferência não substitui a leitura de [1].
- **Em recomendação, a regra de desempate muda muito o número.**
  - O cenário tem um item relevante contra negativos amostrados.
  - Com desempate pela ordem de entrada, o relevante vence todo empate, e o
    nDCG\@10 é 0,85. Com desempate por *hash*, o mesmo nDCG\@10 cai para 0,17
    [3].
  - A média sobre 100 sementes de *hash* se aproxima de perto do valor esperado
    exato [3].
  - A magnitude não se transfere para a bateria deste trabalho, que tem outro
    cenário.
- **Empates espúrios em baixa precisão numérica.** Eles surgem quando o escore é
  calculado em baixa precisão. A proposta tem duas partes [4]:
  - calcular em precisão maior a etapa final de pontuação;
  - relatar o valor esperado, a faixa e o viés com métricas conscientes de
    empate.

  A primeira parte importa aqui, porque o Qdrant devolve o escore em 32 bits.

## Alternativas

| Opção | Prós | Contras |
|---|---|---|
| A. Identificador ou ordem do índice, como hoje | Simples | Viés documentado [2]; o identificador acompanha a ordem de coleta, e a ordem do Qdrant não é estável |
| B. *Hash* estável com uma semente fixa | Simples, determinística e sem viés sistemático | Uma única ordem sorteada; o resultado de cada item carrega a variância do sorteio |
| C. Valor esperado sobre as ordens dos grupos empatados | Exato, sem parâmetro e sem semente; proposto em [1] e usado como referência em [3] | Exige a lista inteira com os escores, e não só os primeiros |
| D. Média de *hash* sobre muitas sementes | Aproxima C [3] e serve a qualquer etapa | Mais custo, e um parâmetro a fixar: o número de sementes |

## Recomendação

**C nas métricas do R1, e D dentro do R2, sempre.** Quando não há empate, C e
D dão o mesmo número que B, então a recomendação não depende de quantos empates
houver.

- **No R1.** Recall\@1, \@5, \@10 e \@20, acerto em 10 e MRR\@20 de cada item são o
  valor esperado sobre as ordens dos grupos empatados. O intervalo por
  reamostragem e o teste pareado continuam iguais e passam a usar esses valores
  por item.
- **No R2.** O RF23 reordena os 20 primeiros do finalista. Em cada um dos 200
  sorteios de ruído que já existem, a ordem dentro de cada grupo empatado é
  sorteada de novo **na lista inteira**, antes de tirar os 20. A semente é
  gravada e não depende do rótulo. A média sobre os sorteios já integra o
  desempate, sem parâmetro novo.
- **Na linha de base só-preço e na partição fácil/difícil.** Vale o mesmo. Elas
  empatam ainda mais, porque preços iguais são comuns.
- **Em todo resultado se relata a fração de itens sensíveis ao desempate:**
  - no Recall\@10, item com um grupo empatado atravessando a décima posição e
    com parte, mas não todos, dos seus membros relevantes;
  - no MRR\@20, item cujo primeiro grupo com relevante, dentro dos 20 primeiros,
    tem mais de um membro;
  - no R2, item com grupo empatado atravessando a vigésima posição.

O motivo: a regra de hoje favorece um método por acaso de identificador ou de
ordem do índice. Com um terço dos itens em grupos de descrição idêntica, isso
pode decidir o R1.

## O que a implementação precisa, se C e D forem adotados

- **Escores.** "Empate" é igualdade exata do escore como o método o devolve. No
  Qdrant, isso é em 32 bits.
- **Métricas.** Elas recebem a lista inteira com os escores, e não só os
  identificadores dos primeiros, porque o tamanho de cada grupo e o número de
  relevantes nele contam inteiros.
- **Busca semântica na avaliação:**
  - busca exata (`exact=True`), sem a aproximação do índice;
  - limite de pelo menos o tamanho do espaço de busca do item;
  - filtro de modalidade no próprio Qdrant.
- **Teste metamórfico.** Ele passa a cobrir os grupos: com o gabarito trocado
  por identificadores inexistentes, a lista de grupos e os escores ficam
  idênticos. Isso reforça a regra de nenhum método ver o rótulo.

## Fora desta decisão

**Equivalência de descrição.** Um item com descrição idêntica à de um preço
escolhido, mas que a servidora não escolheu, conta hoje como distrator. Com
grupos de até 1.796 itens idênticos, o Recall\@10 fica limitado por construção,
porque só cabem dez. Isso não é regra de desempate: é definição de relevância,
e muda o gabarito. Fica aberto à parte, como C18, e não se adota em silêncio.

## Referências

1. [Computing information retrieval performance measures efficiently in the presence of tied scores](https://consensus.app/papers/details/w:acae1b1c-60bb-4cdf-b5ac-7fdbf6e16dd2/) — McSherry, F.; Najork, M. European Conference on Information Retrieval, 2008. Lido no resumo.
2. [Tie-Breaking Bias: Effect of an Uncontrolled Parameter on Information Retrieval Evaluation](https://consensus.app/papers/details/w:d1b5c4f8-87e6-4055-95e5-f5ee90468b3e/) — Cabanac, G. et al. Lecture Notes in Computer Science, 2010. Lido no resumo.
3. [Tie Handling Is Part of the Evaluation Protocol: An Order-Invariance Audit for Tie-Heavy Recommender Scores](https://consensus.app/papers/details/w:9290f9b7-c18b-497b-a131-ea0161a0cc1c/) — Guo, C. et al. arXiv, 2026. Pré-publicação, lida no resumo.
4. [Reliable Evaluation Protocol for Low-Precision Retrieval](https://consensus.app/papers/details/w:6a8f0945-5bd2-4c1c-8858-ddcb4c3a2de7/) — Yang, K. et al. Association for Computational Linguistics, 2026. Lido no resumo.

Os metadados acima vêm do mecanismo de busca e não foram conferidos na fonte
primária. Nenhum entra em `refs.bib` antes dessa conferência.
