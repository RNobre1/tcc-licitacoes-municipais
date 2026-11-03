---
tipo: pesquisa
titulo: "Com quantas casas decimais exibir o fator de proximidade de valor na tela de triagem?"
status: decidida em 03/11/2026 — duas casas; ver TCC/decisões/2026-11-03-precisao-do-fator-de-proximidade.md
criado: 2026-11-03
autor: Rafael Nobre de Souza
relacionado:
  - TCC/decisões/2026-10-28-ordenacao-rf23.md
  - docs/pesquisas/ordenacao-por-duas-dimensoes.md
tags: [pesquisa, rf23, exibição, precisão numérica, ancoragem, avaliação]
---

# Precisão do fator de proximidade na tela de triagem

## A pergunta

A tela de triagem mostra a proximidade de valor como um fator, por exemplo
"1,35× acima", com duas casas decimais. A ordem dos candidatos usa a distância
exata, *d* = |ln(*p*/*e*)|, e não o número exibido. A revisão da T05.3 apontou
dois efeitos visíveis do arredondamento nos dados de demonstração:

- 27,90 contra 28,00 aparece como "1,00× abaixo";
- no item 2, "1,07× acima" vem antes de "1,07× abaixo", e o menos parecido fica
  em cima, porque as distâncias diferem na terceira casa.

A ordem está certa nos dois casos, mas o que se vê parece contradizer a regra de
desempate. A pergunta é se a tela deve mostrar duas ou três casas.

## O que a escolha muda e o que não muda

- **Não muda a ordem.** A chave de ordenação é a distância exata, arredondada
  só na nona casa para neutralizar ruído de ponto flutuante. R1 e R2 não
  dependem da exibição.
- **Muda o que o operador vê.** Com três casas, uma diferença de 0,05% já
  aparece; com duas, só a partir de 0,5%. Três casas reduzem os empates
  aparentes, mas não os eliminam.
- **Pode mudar como o operador julga.** É aqui que a literatura entra, porque a
  tela é usada na sessão C5, e o protocolo existe justamente para controlar o
  peso que o preço tem no julgamento (emendas P1 a P3).

## Busca

Duas consultas ao Consensus, sem filtro, em 03/11/2026:

1. *precision of numeric anchors (number of decimal places) influences judgment and adjustment*
2. *number of decimal places displayed in decision support interfaces effect on user comparison accuracy*

Não houve mensagem de assinatura nem contador nos resultados.

**Limite desta nota: só os resumos foram lidos.** Pela regra do projeto, nenhuma
destas fontes entra no texto do TCC antes da leitura integral, e os metadados
abaixo saem do Consensus, sem conferência na fonte primária. Elas servem aqui
como indício para uma decisão de exibição, que é reversível.

## O que os resumos indicam

| Fonte | O que o resumo diz | Peso para esta tela |
|---|---|---|
| Pena-Marin et al., 2026, *Journal of Marketing* | Atributos exibidos com mais precisão, quando menor é melhor, recebem mais peso na comparação entre opções, porque a precisão orienta a atenção para os valores menores | **Alto.** O fator é um atributo em que menor é melhor. Mais casas puxariam o peso para o preço, que é o viés que o protocolo tenta conter |
| Janiszewski e Uy, 2008, *Psychological Science*; Frech et al., 2020, *Social Cognition* | Âncoras precisas produzem ajuste menor do que âncoras redondas | Médio. O operador não estima um número a partir do fator; ele julga comparabilidade |
| Zhang e Schwarz, 2013, *Journal of Experimental Social Psychology* | O efeito da precisão some quando o número vem de um procedimento automático, sem intenção comunicativa | Atenua o anterior: o fator é calculado pelo sistema |
| Witteman et al., 2011, *Journal of Medical Internet Research* | Casas decimais a mais em calculadoras de risco trazem pouco ou nenhum benefício, reduzem a credibilidade e pioram a lembrança do número | Médio. O contexto é outro, mas a tela também é de apoio à decisão |
| Kok et al., 2019, *Physical Review Physics Education Research* | Estudantes que viram dados com mais casas compararam pior os conjuntos | Baixo. A população é de estudantes, e a tarefa é outra |
| Cole, 2015, *Archives of Disease in Childhood* | Recomenda apresentar números com duas a três casas significativas | Baixo. É orientação editorial. "1,07" já tem três casas significativas |

**Nenhuma fonte mede esta tela:** um fator de razão de preços, numa triagem de
comparabilidade em compras públicas. O que existe são indícios de outros
contextos, e todos apontam na mesma direção: precisão a mais tem custo, e o
benefício é pouco.

## Inferência

O efeito visual que motivou a pergunta é real, mas pequeno: nos dados de
demonstração, ele aparece uma vez. O custo provável de três casas atinge o que
o protocolo de avaliação mais quer proteger, que é o julgamento de
comparabilidade não ser puxado pelo preço. Entre um artefato visual raro e
explicável e um risco, ainda que só indicado, sobre o que se mede, a escolha
conservadora é manter duas casas.
