---
tipo: decisão
data: 2026-11-03
status: aceita
tags: [rf23, exibição, proximidade, avaliação, protocolo]
---

# O fator de proximidade é exibido com duas casas decimais

## Contexto

A tela de triagem exibe a proximidade de valor como fator, por exemplo "1,35×
acima", com duas casas. A ordem usa a distância exata. A revisão da T05.3
mostrou dois efeitos do arredondamento: "1,00× abaixo" para 27,90 contra 28,00,
e dois candidatos com "1,07×" na mesma faixa, o menos parecido em cima. A ordem
está certa, mas parece contradizer a regra de desempate. A decisão foi delegada
pelo autor ao coordenador, com a exigência de ser justificada. A investigação
está em `docs/pesquisas/precisao-do-fator-de-proximidade.md`.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| **A. Duas casas** | Já implementada, sem custo. Igual ao exemplo da nota do RF23. Os indícios da literatura são contra precisão a mais | Empates aparentes quando as distâncias diferem a partir da terceira casa |
| B. Três casas | Empates aparentes dez vezes mais raros | Não os elimina. Indício de que mais precisão desloca o peso para o atributo de preço, que é o viés que o protocolo tenta conter. Exige trocar formato e testes |
| C. Ordenar pelo fator exibido, arredondado | O que se vê passa a ser exatamente o que ordena | Muda a chave de ordenação do RF23 e, com isso, o que R1 e R2 medem. É outra decisão relevante, e não uma escolha de exibição |
| D. Exibir a distância *d* em vez do fator | Sem arredondamento aparente | Menos legível. A nota do RF23 escolheu o fator justamente pela leitura |

## Decisão

**Escolhida: a opção A.** O fator continua com duas casas decimais. Não há
mudança de código.

## Justificativa

1. **A ordem não depende da exibição.** A chave é a distância exata, e R1 e R2
   ficam iguais em qualquer das opções A, B e D. Por isso, esta decisão é de
   exibição, e a própria nota do RF23 diz que a exibição é reversível.
2. **O ganho de três casas é pequeno.** O efeito aparece uma vez nos dados de
   demonstração, e três casas só reduzem a frequência dele.
3. **O custo provável de três casas atinge o que se mede.** Pelo resumo de
   Pena-Marin et al. (2026), atributos em que menor é melhor recebem mais peso
   quando exibidos com mais precisão, e o fator é um desses atributos. A emenda
   P3 existe para estimar quanto o preço puxa o julgamento de comparabilidade,
   e aumentar a precisão do preço iria na direção contrária. Os outros resumos
   da nota de pesquisa apontam para o mesmo lado.
4. **Limite que precisa ser dito.** As fontes foram lidas só no resumo, e
   nenhuma mede esta tela. A decisão se apoia em indício, e por isso é a opção
   conservadora e sem custo, com critério de revisão explícito.

## Consequência

- O código e os testes ficam como estão.
- Na demonstração de 07/11 e no texto (C16), explica-se que a ordem usa a
  distância exata, e que dois fatores iguais na tela podem estar em ordem
  diferente da semelhança, porque diferem na terceira casa.
- As fontes da nota de pesquisa só entram no texto depois da leitura integral.

## Critério de revisão

Reabrir se:

1. na sessão C5, com o preço visível, o operador questionar ou ler errado a
   ordem de linhas com o mesmo fator exibido. Nesse caso, considerar a opção C,
   que exige o protocolo de decisão relevante, porque muda o RF23;
2. a leitura integral das fontes contradisser o que os resumos indicam;
3. a emenda P3 mostrar que a coluna de proximidade desloca o julgamento de
   comparabilidade. Esse já é um critério de revisão da decisão do RF23, e a
   resposta prevista é ocultar a coluna até o operador marcar a
   comparabilidade.

## Adendo de 27/11: a semelhança também com duas casas

Até 26/11, a coluna de semelhança mostrava o escore cru, com oito casas. Com a
busca semântica real na tela, o autor decidiu em 27/11 exibir a semelhança com
duas casas e vírgula decimal: 0,89, por exemplo. O arredondamento é para cima a
partir da metade.

Pesaram os mesmos motivos desta nota:

- a ordem usa o valor exato, então R1 e R2 não mudam;
- a precisão exibida pode dar a um número um peso que ele não tem no
  julgamento;
- a proximidade já aparece com duas casas, e as duas colunas ficam coerentes.

O percentual (89%) foi descartado, porque sugere uma probabilidade de ser o
mesmo item, e o escore de cosseno não é isso.

O critério de revisão 1 vale também aqui: dois candidatos com 0,89 na tela
podem estar em ordem diferente.

## Backlinks

- [[2026-10-28-ordenacao-rf23]]
