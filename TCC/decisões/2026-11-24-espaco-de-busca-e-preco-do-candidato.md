---
tipo: decisão
data: 2026-11-24
status: aceita
tags: [decisão-relevante, avaliação, corpus, pncp, preço, rf23, rn07, in-65]
---

# O espaço de busca é o PNCP nacional de doze meses, e o candidato mostra o preço homologado

## Contexto

Duas perguntas ficaram abertas depois do critério de aceitação de R1 e R2
([[2026-11-24-limiares-de-aceitacao-r1-r2]]): sobre que espaço de itens a busca
e a bateria rodam, e que preço cada candidato mostra e usa no cálculo.

A extração dos três relatórios de cotação respondeu a primeira com dados. Dos
452 preços escolhidos pela servidora que se reencontram no PNCP:

- vêm de **24 unidades da federação**: o Pará responde por 10,6%, e a região
  Norte inteira por cerca de 16%;
- vêm de três modalidades: pregão eletrônico (68,1%), dispensa (25,7%) e pregão
  presencial (5,3%). As duas restantes somam 0,8%;
- todos foram publicados nos doze meses anteriores à data da pesquisa;
- em 95,1% deles, a unidade escrita difere da unidade pedida.

Em junho de 2026, o PNCP recebeu, no país todo, cerca de 31 mil pregões
eletrônicos, 59 mil dispensas e 750 pregões presenciais. Doze meses dessas três
modalidades somam a ordem de doze milhões de itens.

A investigação está em `docs/pesquisas/limiares-de-aceitacao-r1-r2.md`, seção
6.4.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A. Nacional, doze meses, as três modalidades do gabarito | É o espaço em que o sistema buscaria; alcança 99% dos relevantes; é o cenário da contribuição declarada, descrição curta sobre milhões de itens | Coleta de dias e indexação de horas a um dia por modelo; a medição passa para a virada do ano |
| B. Nacional, doze meses, só pregão eletrônico | Um terço das requisições | 32% dos relevantes ficam inalcançáveis: o teto de R1 cai para 68% |
| C. Só a região Norte | Cabe numa semana | Só cerca de 16% dos relevantes estão lá; R1 mediria quase nada |
| D. Um mês nacional, com os relevantes inseridos | Cabe numa semana | É o *pool* que a pesquisa desaconselha: os relevantes têm presença garantida, e os vizinhos de outros meses não |

Para o preço do candidato na triagem: o homologado quando existe, com o
estimado marcado no lugar; só o homologado; ou sempre o estimado.

## Decisão

**Espaço de busca: opção A.** Para cada item pedido, o espaço C(q) é o conjunto
dos itens publicados no PNCP nos doze meses anteriores à data da pesquisa
daquele item (RN07), em todas as unidades da federação, nas modalidades pregão
eletrônico, dispensa e pregão presencial. É o mesmo para todos os métodos. A
unidade não filtra, porque a grafia diverge em 95% dos relevantes. A conversão
de unidade segue aberta, no D11.

**Preço do candidato:**

- a triagem mostra o **preço unitário homologado** quando ele existe;
- sem ele, mostra o **estimado**, marcado como tal, e esse preço **não entra**
  no valor estimado;
- item com orçamento sigiloso aparece sem preço;
- o homologado é buscado no PNCP sob demanda, para os candidatos exibidos,
  porque buscar o de doze milhões de itens custaria uma requisição por item.

O preço usado na medição de R2 fica aberto: decide-se ao desenhar a execução
nacional da bateria, com o custo medido.

## Justificativa

- O gabarito mostra que a servidora busca no país inteiro. Um espaço regional
  cortaria os relevantes antes de qualquer método rodar.
- Doze meses vem da RN07, e todos os relevantes cabem nessa janela.
- A IN 65/2021 aceita como referência o preço de contratação, o homologado. O
  estimado é a previsão do órgão, costuma ser maior e vem zerado no orçamento
  sigiloso.

## Consequência

- A coleta passa a ser nacional, por dia e retomável, e roda em lotes ao longo
  de dezembro. Esta semana o arnês roda num corpus-piloto só para validar o
  caminho, sem ajustar nada.
- A medição de R1 e R2 sai na virada do ano, antes do prazo estimado do SBBD.
- O índice precisa servir a doze milhões de pontos por modelo: índices de carga
  nos campos filtrados e armazenamento em disco com quantização.

## Critério de revisão

- Se a coleta nacional se mostrar inviável no tempo (por instabilidade da API
  ou capacidade da máquina), voltar a esta nota antes de recortar o espaço, e
  nunca recortar olhando o resultado.
- Se a sessão de 2027 mostrar que a servidora limita a região, rever o filtro.

## Backlinks

- [[2026-11-24-limiares-de-aceitacao-r1-r2]]
- [[2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
