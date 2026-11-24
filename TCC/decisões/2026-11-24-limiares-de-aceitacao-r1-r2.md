---
tipo: decisão
data: 2026-11-24
status: aceita
tags: [avaliação, limiar, c11, c15, recuperação, r1, r2]
---

# Critério de aceitação de R1 e R2, fixado antes de medir

## Contexto

A classificação da pesquisa, *Design Science Research*, exige que o limiar de
aceitação de cada resultado esperado seja fixado **antes** da medição (C11). Os
limites das faixas de comparabilidade do RF23 também precisam sair de um
subconjunto separado daquele em que se mede (C15). Nesta semana o conjunto de
avaliação e o arnês da bateria ficam prontos, e a medição pode acontecer ainda
em dezembro.

Duas condições pesaram:

- a observação de uso com a servidora e o julgamento às cegas (C5 e C6) passam
  para o início do TCC II, então o que a pesquisa sugeria calibrar nessa sessão
  precisa ser fixado agora, ou a medição espera até 2027;
- o conjunto vem de **três** relatórios de cotação, o que impede dividir os
  itens ou reamostrar por relatório.

A investigação está em `docs/pesquisas/limiares-de-aceitacao-r1-r2.md`.

## Opções consideradas

| Ponto | Opções | Escolha |
|---|---|---|
| Critério de R1 | Absoluto fixo; relativo sem margem; relativo com margem | Relativo com margem de 0,05 |
| Corte k | 10 agora; 20 agora; esperar a observação de 2027 | 10, fixado agora |
| Partição | 40/60 por item; 25/75 por item; validação cruzada aninhada como principal | 40% ajuste e 60% medição, por item |
| Leitura de R2 | Grade fixa com linha de base só-preço e partição fácil/difícil; só a curva; esperar o erro real da servidora | Grade fixa, só-preço e fácil/difícil |

## Decisão

**R1.**

- Um único contraste confirmatório: o finalista contra o BM25 ajustado, em
  Recall\@10, no subconjunto de medição. O finalista é o de maior Recall\@10 no
  subconjunto de ajuste, e o empate se desfaz pelo MRR\@20.
- **R1 é aceito** se o limite inferior do intervalo de 95% da diferença pareada
  passar de **0,05**: um relevante a mais a cada vinte itens.
- **Empate** só se declara se o intervalo de 90% couber em ±0,08. Fora disso, o
  resultado é **inconclusivo**. Empate ou perda **não refutam**, por causa do
  viés do gabarito a favor da busca por palavra.
- O intervalo é por reamostragem dos itens, com semente fixa. O p-valor por
  permutação pareada entra como conferência. O resultado por relatório é
  relatado ao lado.
- Recall\@1, \@5 e \@20 e MRR\@20 são descritivos.

**Partição.**

- 40% para ajuste e 60% para medição, **por item**, estratificada por relatório
  e por material ou serviço, com semente fixa.
- A lista de itens e o seu resumo SHA-256 são gravados **antes** de qualquer
  método rodar sobre itens rotulados. O arnês recusa ler a medição se o resumo
  não bater.
- No ajuste se fixam no máximo quatro parâmetros: os dois limites de faixa do
  finalista, e o k1 e o b do BM25. O resto usa valor padrão declarado.

**R2.**

- A âncora é exp(média de ln(preços escolhidos) + σ·Z), com σ em {0; 0,10;
  0,25; 0,50; 1,00}, mais a condição sem âncora. σ = 0 é rotulado como limite
  superior, porque é o oráculo.
- Uma **linha de base só-preço** ordena o mesmo espaço de busca por
  |ln(p/âncora)|, sem texto. Se ela empatar com o sistema, o ganho é do preço.
- Uma **partição fácil/difícil**: o item é fácil quando o só-preço já põe um
  relevante entre os dez primeiros. O ganho de R1 tem de persistir nos difíceis.
- Relata-se G(σ) = Recall\@10 com σ − Recall\@10 sem âncora.

## Justificativa

- **Não há fonte para um Recall\@10 absoluto "razoável".** Ele depende do espaço
  de busca e do gabarito, e escolhê-lo olhando a linha de base é o que o C11
  proíbe.
- **Vencer a busca por palavra é conservador**, porque o gabarito a favorece.
  A margem separa a significância da importância prática.
- **Com cerca de 139 itens na medição, só se detectam diferenças de cerca de
  dez pontos.** Por isso o empate exige uma margem larga, e "inconclusivo" é
  resposta prevista.
- **O k fixado agora** permite medir em dezembro. Se a observação de 2027
  mostrar que a servidora examina outro número de candidatos, isso vira
  limitação declarada, e não mudança do k depois de medir.
- **A grade de ruído é escolha de projeto**, porque nenhuma fonte prescreve
  níveis. A sessão de 2027, com o preço visível ou oculto sorteado por item,
  serve de validação externa.

## Consequência

- O arnês implementa exatamente estes parâmetros. Mudar qualquer um depois de
  rodar sobre a medição invalida o R1.
- O espaço de busca **continua aberto**. Ele depende da distribuição real dos
  relevantes (UF, modalidade, data) e é decidido em nota própria.
- A C11 fica fechada para R1 e R2. Os limiares de R3 a R8 vêm com as medições
  deles.

## Critério de revisão

- Antes de medir: se o subconjunto de ajuste mostrar discordância entre métodos
  acima de 30%, a diferença mínima detectável passa de cerca de treze pontos, e
  o R1 é relatado como descritivo, em vez de testado.
- Depois de medir: nada destes parâmetros muda. Uma nova escolha exige um novo
  conjunto de medição.

## Backlinks

- [[2026-10-28-ordenacao-rf23]]
- [[2026-10-15-classificacao-da-pesquisa-dsr]]
- [[2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
