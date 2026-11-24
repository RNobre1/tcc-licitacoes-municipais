---
tipo: decisão
data: 2026-11-24
status: aceita
tags: [decisão-relevante, modelo-de-representação, busca-semântica, a2, auditoria]
---

# multilingual-E5 como modelo provisório da busca, até a bateria escolher

## Contexto

A reunião de 10/11 pediu a busca semântica funcionando e a integração entre o
banco relacional e o vetorial testada. O modelo definitivo (A2) sai da bateria
de modelos (C3), por medição, e a medição só fecha na virada do ano. Para a
triagem buscar candidatos reais antes disso, a busca precisa de um modelo agora.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A. multilingual-E5 base, pesos abertos, local | Está na bateria proposta, na classe 5; versão fixada, como a trilha de auditoria exige; roda na máquina de trabalho, sem custo, e o dado não sai dela | Não é a escolha medida; pode perder na bateria |
| B. Manter os dados fictícios até a bateria | Nenhuma escolha provisória | A integração só se prova com modelo falso; não há busca real para mostrar |
| C. Serviço comercial de vetores | Nada a instalar | O vetor pode mudar sem aviso, o que quebra a reconstituição de uma pesquisa; exige chave e tem custo |

## Decisão

**Escolhida: A.** O `intfloat/multilingual-e5-base`, com a revisão fixada no
comando de indexação e no nome da coleção, até a bateria escolher o definitivo.

## Justificativa

Modelo de pesos abertos com versão fixada é condição para reconstituir uma
pesquisa como ela estava na data (RN08), e não só uma questão de custo, como
registra `docs/pesquisas/ampliacao-de-bases-e-escolha-do-modelo-de-representacao.md`.
Entre os de pesos abertos, o multilingual-E5 é a linha de base de vetor da
bateria.

## Consequência

- A busca roda com ele desde 24/11. Cada coleção leva o nome do modelo e da
  revisão, então trocar de modelo cria outra coleção e não mistura vetores.
- A A2 continua aberta, e esta escolha não antecipa o resultado da bateria.

## Critério de revisão

Trocar assim que a bateria escolher o finalista, ou antes, se a revisão fixada
deixar de estar disponível no repositório público do modelo.

## Backlinks

- [[2026-11-24-limiares-de-aceitacao-r1-r2]]
- [[2026-10-18-pilha-tecnologica]]
