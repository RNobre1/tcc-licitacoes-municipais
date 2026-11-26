---
tipo: decisão
data: 2026-11-26
status: aceita
tags: [decisão-relevante, avaliação, empate, recall, mrr, r1, r2, c17, c11]
---

# Empates contam pelo valor esperado no R1 e por sorteio no R2

## Contexto

O arnês da bateria desempata escores iguais pelo menor identificador do item,
na busca por palavra e na linha de base só-preço, e pela ordem em que o Qdrant
devolve os pontos, na busca semântica. A revisão da frente de avaliação mostrou,
numa sonda sintética, que essa regra decide o Recall\@10. Os relevantes de
menor identificador dão 1,00, e os de maior dão 0,00.

Na fatia coletada do PNCP, 33,2% dos itens têm descrição idêntica à de outro
item, em minúsculas, como o BM25 a vê. Respeitando maiúsculas, como o modelo de
representação a vê, são 32,1%. E 3.547 grupos têm dez itens idênticos ou mais.
A contagem é de 26/11/2026, às 19:12 UTC, sobre a cópia mais recente de cada
página; o critério está na pesquisa. Descrição idêntica gera empate nos dois
métodos, e o BM25 empata também entre descrições distintas. A regra de desempate muda o que se mede, então precisa
estar fixada antes da medição, como as demais da C11.

A investigação está em `docs/pesquisas/empates-na-avaliacao.md`.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A. Identificador ou ordem do índice, como hoje | Nenhum trabalho | Viés documentado; o identificador acompanha a ordem de coleta, e a ordem do Qdrant não é estável entre reconstruções |
| B. *Hash* com uma semente fixa | Simples e sem viés sistemático | Uma única ordem sorteada: cada item carrega a variância do sorteio, e, por inferência, o intervalo do R1 se alarga |
| C. Valor esperado sobre as ordens dos grupos empatados, no R1, e sorteio a cada sorteio de ruído, no R2 | Exato no R1, sem parâmetro novo; sem empate, dá o mesmo número que B | O arnês passa a guardar a lista inteira com os escores, e a busca semântica da avaliação passa a ser exata |

## Decisão

**Escolhida: C.** Decidida pelo autor em 26/11/2026, antes de qualquer medição.

- **R1.** Recall\@1, \@5, \@10 e \@20, acerto em 10 e MRR\@20 de cada item são o
  valor esperado sobre todas as ordens possíveis dentro dos grupos empatados. O
  intervalo por reamostragem e o teste pareado usam esses valores por item,
  sem outra mudança.
- **R2.** Em cada um dos 200 sorteios de ruído, a ordem dentro de cada grupo
  empatado é sorteada de novo na lista inteira do finalista, **antes** de tirar
  os 20 primeiros que o RF23 reordena. A semente é gravada e não depende do
  rótulo.
- **Desempate final do RF23.** O RF23 ordena por faixa, proximidade,
  semelhança e, por último, identificador. No R2, esse último critério também é
  sorteado: a cada sorteio, cada candidato recebe um posto aleatório que
  substitui o identificador. Sem isso, o identificador desfaria o sorteio entre
  candidatos de descrição e preço idênticos. A ordenação de `pricing/` não muda.
- **Linha de base só-preço.** No R2, a ordem dentro de cada grupo de preço igual
  também é sorteada de novo a cada sorteio de ruído.
- **Partição fácil/difícil.** Seguem duas escolhas do autor, de 26/11, antes de
  medir:
  - a âncora é a exata: a média geométrica dos preços escolhidos, sem ruído
    (σ = 0);
  - com ela, *p* é a chance de o só-preço pôr um relevante entre os dez
    primeiros, como valor esperado sobre as ordens dos grupos de preço igual.

  O item é **fácil se *p* > 0** e **difícil se *p* = 0**. Difícil é, então, o
  item em que nem o preço exato tem chance de achar o relevante, e o ganho
  medido nesse grupo não pode vir do preço.
- **Empate** é igualdade exata do escore como o método o devolve. No Qdrant,
  isso é em 32 bits.
- **Todo resultado relata a fração de itens sensíveis ao desempate:**
  - no Recall\@10, item com grupo empatado atravessando a décima posição, com
    ao menos um membro relevante e ao menos um não relevante;
  - no MRR\@20, item cujo primeiro grupo com relevante, dentro dos 20 primeiros,
    tem mais de um membro, e nem todos relevantes;
  - no R2, item com grupo empatado atravessando a vigésima posição.

## Justificativa

- Desempatar pelo identificador é um parâmetro não controlado da avaliação.
  Isso está documentado na literatura de recuperação de informação. A fonte foi
  lida só no resumo e ainda não é citável no texto.
- O valor esperado sobre as ordens empatadas não tem parâmetro nem semente, e é
  calculado sem enumerar as permutações. A conferência por enumeração exaustiva,
  feita na revisão, bateu com as fórmulas do Recall\@k e do posto recíproco
  truncado.
- No R2, o sorteio já existe: os 200 sorteios de ruído integram o desempate sem
  acrescentar parâmetro.
- Sem empate, C dá o mesmo número que B. A escolha não depende de quantos
  empates houver.

## Consequência

- **O arnês muda antes da medição:**
  - as métricas recebem a lista inteira com os escores;
  - a busca semântica da avaliação é exata, com limite de pelo menos o tamanho
    do espaço de busca do item e o filtro de modalidade no próprio Qdrant;
  - o sorteio do R2 embaralha os grupos antes do corte nos 20;
  - o teste metamórfico passa a cobrir os grupos.
- Mudar esta regra depois de rodar sobre a medição invalida o R1 e o R2, como
  qualquer parâmetro da [[2026-11-24-limiares-de-aceitacao-r1-r2]].
- A definição de relevância **não** muda. Um item com descrição idêntica à de um
  preço escolhido, que a servidora não escolheu, segue como distrator. Essa
  questão é a C18, aberta à parte.

## Critério de revisão

- Antes de medir: se a leitura integral da fonte do valor esperado contradisser
  a conferência por enumeração.
- Depois de medir: nada muda. Uma nova regra exige um novo conjunto de medição.

## Backlinks

- [[2026-11-24-limiares-de-aceitacao-r1-r2]]
- [[2026-11-24-espaco-de-busca-e-preco-do-candidato]]
