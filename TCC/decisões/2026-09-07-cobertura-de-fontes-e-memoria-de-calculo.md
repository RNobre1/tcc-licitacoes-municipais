---
tipo: decisão
data: 2026-09-07
status: aceita
tags: [escopo, fontes-de-preço, etp, memória-de-cálculo, avaliação]
---

# Cobertura de fontes de preço e tratamento da memória de cálculo ausente

Duas decisões forçadas pela mesma coisa: a análise de quinze documentos reais
mostrou que a prática diverge do que a especificação supunha, nos dois pontos.

## Contexto

A decisão de 06/09 fixou pipeline próprio sobre a API pública, e apoiou-se numa
observação que **estava errada**: a de que a fonte efetiva dos preços seria o
portal nacional sozinho. Isso valia para o processo mais simples dos três — um
item, uma fonte —, e não vale em geral.

Medido nos dois processos grandes:

| | Processo B, 120 itens | Processo C, 150 itens |
|---|---|---|
| Preços no relatório | 360 | 448 |
| Portal Nacional de Contratações Públicas | 47,5% | 62,3% |
| Plataformas privadas de pregão | 35,0% | 23,3% |
| Base federal de compras | 5,8% | 7,6% |
| Tribunais de contas | 8,3% | 4,1% |
| Fontes distintas listadas no relatório | 15 | 18 |

O portal nacional é a maior fonte isolada, mas está longe de responder pelo
conjunto: **entre 38% e 52% dos preços vêm de outro lugar**, sobretudo de
plataformas privadas de pregão eletrônico. Esta medida é bem menos favorável
que a primeira que apurei, que dizia 85% e 93% — aquele número saiu de calcular
a proporção só entre os preços que trazem endereço completo, que são justamente
os do portal nacional. O erro de denominador inflava o resultado a favor da
decisão que eu estava recomendando, e isso precisa ficar registrado.

O segundo ponto veio dos Documentos de Formalização de Demanda. **Nenhum dos
seis traz memória de cálculo.** A justificativa é prosa sobre a logística do
município e a quantidade aparece só como número em tabela. Ainda assim, os ETPs
derivados afirmam que os quantitativos consideraram histórico de consumo de
contratações anteriores. A regra existe, e é descumprida de forma sistemática.

## Decisão 1 — Cobertura de fontes

### Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — Somente o portal nacional | Uma API pública, oficial e documentada; cobre de 47,5% a 62,3% do que ela usa hoje; a lacuna é mensurável e vira resultado | Perde entre 38% e 52% dos preços de referência. Em item raro, onde a cobertura mais importa, pode faltar candidato |
| B — Portal nacional mais o painel do tribunal de contas do estado | Acrescenta preço regional, que ataca direto o viés de preço de outros estados; é a base do próprio órgão que fiscaliza o município | Segunda integração, sem API documentada conhecida; provavelmente exigiria raspagem, com fragilidade e discussão ética no texto |
| C — Portal nacional mais a base federal de compras | As duas bases federais | Sobreposição grande entre elas; ganho de cobertura menor que o esforço, e não cobre o preço regional, que é onde está a dor relatada |

### Decisão

**Escolhida: A.** Somente o portal nacional. A cobertura que fica de fora — 7% a
15% — vira **limite declarado e medido**, reportado como resultado.

### Justificativa

Uma fonte pública, oficial e com API é o que torna o trabalho reprodutível por
outro município e por outro pesquisador. Raspar painel de tribunal de contas
resolveria 6,5% num processo e 0,3% no outro, ao custo de uma dependência frágil
e de uma discussão que desviaria o texto do que ele tem a dizer.

E há uma razão metodológica: **a lacuna medida é ela própria um resultado.** Ao
reportar quanto da cotação real não se reproduz com fonte pública única, o
trabalho informa um município que pensa em abrir mão do sistema comercial. Isso
vale mais que esconder o número atrás de uma integração improvisada.

## Decisão 2 — Memória de cálculo ausente

### Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — Gerar assim mesmo, marcando a lacuna | Menos atrito na adoção; o documento sai utilizável | Preserva o defeito: basta ignorar a marcação e o texto volta a afirmar o que não aconteceu |
| B — Não escrever a afirmação sem o dado | Elimina o defeito por construção | O documento gerado fica visivelmente mais fraco que o atual, e alguém pode ler isso como piora |
| C — Bloquear até a secretaria preencher | O mais correto perante a norma | Hoje ninguém preenche; um sistema que trava seria abandonado no primeiro uso |

### Decisão

**Escolhida: A**, por decisão do orientando, com o custo assumido e uma
mitigação obrigatória.

### Justificativa e mitigação

A escolha é de adoção: um sistema recusado no primeiro uso não melhora processo
nenhum, e o defeito que ele evitaria continuaria acontecendo sem ele. É
preferível um documento que sai com a lacuna visível a um documento que não sai.

O custo é real e está registrado: **marcação pode ser ignorada.** A mitigação
adotada é o requisito RF33 — a marca tem de **sobreviver ao arquivo exportado**,
não viver só na tela. Um `.docx` que chega ao processo com a lacuna visível
obriga quem for removê-la a fazer isso conscientemente, e deixa rastro. Marcação
que só existe na interface é decoração.

Fica registrado para revisão: se a medição de uso mostrar que a marca é removida
sem preenchimento na maioria dos casos, a decisão vira B.

## Consequência

**Entra em escopo:**

- Coleta e indexação restritas ao portal nacional.
- Medição e relato da cobertura perdida em relação à prática atual.
- Geração do documento na ausência de memória de cálculo, sem afirmar histórico
  de consumo que não existe, com marca persistente no arquivo exportado.

**Fica fora de escopo:**

- Painéis de tribunais de contas e plataformas privadas de pregão como fonte de
  preço.
- Bloqueio do fluxo por ausência de memória de cálculo.

## Critério de revisão

- Se a medição mostrar que a cobertura de fonte única derruba a recuperação
  abaixo do utilizável em itens raros, reabrir a opção B — e aí a discussão sobre
  raspagem precisa acontecer por inteiro, inclusive a parte ética.
- Se a marca de lacuna for removida sem preenchimento na maioria dos usos
  observados, a decisão 2 vira a opção B.

## Backlinks
- [[2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
- [[../requisitos/2026-09-06-analise-dos-documentos-recebidos]]
- [[../sessões/2026-09-07]]
