---
tipo: decisão
data: 2026-11-27
status: aceita
tags: [decisão, índice-semântico, ingestão, coleta-nacional, a3, a7]
---

# O índice definitivo é construído uma vez, depois da coleta nacional

## Contexto

A coleta nacional do PNCP, de doze meses, roda desde 24/11. Em 27/11 havia
cerca de 95 mil compras e 878 mil itens públicos construídos. A previsão é de
seis a sete dias de máquina para o resto, com pausas.

A indexação do comando atual não é incremental. Cada execução recalcula o vetor
de todos os itens: cerca de 73 itens por segundo, ou 3,5 horas para 878 mil
itens. Com os cerca de 20 milhões de itens do corpus completo, uma passada leva
uns três dias. Se for interrompida, recomeça do zero.

Em 27/11, com a reindexação e a coleta rodando juntas, a coleta quase parou por
três horas: as duas disputam o mesmo banco.

E a configuração da coleção nacional ainda depende da decisão A7, que trata dos
vetores em disco ou da quantização. Se ela mudar a configuração, o índice
precisa ser refeito.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A. Indexar tudo de novo durante a coleta, a cada etapa | A tela acompanha a coleta | Dias de máquina repetidos; disputa pelo banco atrasa a coleta; pode ser refeito de novo depois da A7 |
| B. Indexar uma vez no fim, com fatias por data só quando for preciso mostrar algo | Uma única passada completa, já na configuração definitiva; a coleta não disputa o banco | A tela fica com o índice parcial até o fim da coleta, e avisa isso |
| C. Indexação incremental contínua, só dos itens novos | Índice sempre próximo do banco | Exige a opção de pular os itens já indexados, ainda não revisada nem integrada, e continua sujeita à A7 |

## Decisão

**Escolhida: B.** Decidida pelo autor em 27/11/2026.

- A reindexação em curso em 27/11 termina. Ela leva ao índice as compras do
  gabarito, para a tela e para o piloto.
- Durante o resto da coleta, nenhuma reindexação completa. Se a tela ou o piloto
  precisarem de dados novos, indexa-se só a fatia de datas (`--start` e
  `--end`), que leva minutos.
- Com a coleta completa e a A7 decidida, o índice inteiro é construído uma vez,
  na coleção definitiva. **Esse é o índice sobre o qual se mede o R1.**
- Antes dessa passada, revisa-se e integra-se o caminho acelerado de indexação,
  que reaproveita o vetor das descrições repetidas, um terço dos itens, sem
  mudar nenhum vetor. A precisão FP32 e o limite de 512 tokens foram mantidos em
  26/11.

## Justificativa

- Uma passada completa no fim custa uns três dias de máquina; refeita a cada
  etapa, custaria isso várias vezes.
- Medido em 27/11: indexar e coletar ao mesmo tempo atrasa a coleta, que é o
  caminho crítico até a medição.
- A configuração da coleção pode mudar com a A7. Construir o índice completo
  antes disso arrisca refazê-lo.

## Consequência

- O índice da tela fica parcial até o fim da coleta, com o aviso que mostra
  quantos itens estão indexados.
- Uma pausa durante a coleta não perde nada: a coleta retoma de onde parou. Uma
  pausa durante a indexação completa a faz recomeçar. Por isso, ela é agendada
  para quando a máquina puder ficar ligada.
- A estratégia de atualização da ingestão em uso (A3) continua aberta. Esta
  decisão trata só da construção do corpus da avaliação.

## Critério de revisão

- Se a passada completa, mesmo acelerada, passar de uns três dias, considerar a
  opção C, com retomada, antes de recomeçar do zero.
- Se a A7 mantiver a configuração atual da coleção, os pontos já indexados podem
  ser aproveitados, desde que o modelo e a revisão sejam os mesmos.

## Backlinks

- [[2026-11-24-espaco-de-busca-e-preco-do-candidato]]
- [[2026-11-24-modelo-provisorio-da-busca]]
