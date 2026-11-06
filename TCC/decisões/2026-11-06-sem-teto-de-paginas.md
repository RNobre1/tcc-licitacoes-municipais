---
tipo: decisão
data: 2026-11-06
status: aceita
tags: [texto, formato, artigo, sbc, páginas, orientação]
---

# O teto de 25 páginas deixa de barrar o texto

## Contexto

Na reunião de 19/08, a orientação fixou o texto principal como artigo de 20 a
25 páginas. A decisão [[2026-08-24-formato-do-texto-artigo-sbc]] transformou
isso em restrição de projeto, e `tests/test_conformidade_sbc.py` passou a falhar
quando a entrega da SBC passasse de 25 páginas.

O alvo da SBC chegou a 25 de 25 em 18/10, quando a subseção da pilha
tecnológica consumiu a última página livre. Desde então, cada parágrafo novo
precisava tirar outro do lugar. Em 06/11 entraram no texto o diagrama geral de
casos de uso e o parágrafo que o apresenta, que a própria orientação pediu em
24/10. A entrega apresentável ficou em 25 páginas na SBC, 28 no layout do curso
e 35 no do SIBI, e a versão de trabalho, com os marcadores de pendência, em 28,
30 e 37.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A. Manter o teto e cortar texto | Segue o número fixado em 19/08 | Corta o que a orientação pediu depois, e o texto ainda não tem resultados nem conclusão: o corte se repetiria a cada seção |
| B. Retirar o teto da guarda | O texto cresce com o que é pedido | Precisa de confirmação da orientação, que foi quem fixou o número |

## Decisão

**Escolhida: a opção B.** O autor a tomou em 06/11/2026. Para ele, as 25 páginas
eram uma ideia inicial, e não um limite a defender.

## Justificativa

O número veio antes do conteúdo: em 19/08 o texto ainda não tinha arquitetura,
casos de uso nem avaliação. Mantê-lo como teste que barra obrigaria a decidir o
conteúdo pela contagem, e não pelo que a orientação pede.

## Consequência

- `tests/test_conformidade_sbc.py` deixa de falhar acima de 25 páginas. Os
  demais testes da entrega da SBC continuam valendo.
- A decisão de 24/08 continua valendo no resto: o formato é artigo da SBC, e o
  layout do SIBI é o alvo do depósito. Só o orçamento de página deixa de ser
  restrição de projeto.
- **A confirmação com a orientadora fica para a reunião de 07/11.** O número foi
  fixado por ela, e por isso a mudança é levada a ela.

## Critério de revisão

Reabrir se a orientadora mantiver o limite, ou se um veículo de submissão
escolhido para o artigo impuser um teto próprio.

## Backlinks

- [[2026-08-24-formato-do-texto-artigo-sbc]]
- [[../sessões/2026-08-19]]
- [[../sessões/2026-10-18]]
