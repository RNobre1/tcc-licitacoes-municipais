---
tipo: decisão
data: 2026-11-24
status: aceita
tags: [decisão-relevante, avaliação, limiar, c11, c15, recuperação, r1, r2]
---

# Critério de aceitação de R1 e R2, fixado antes de medir

## Contexto

A classificação da pesquisa, *Design Science Research*, exige que o limiar de
aceitação de cada resultado esperado seja fixado **antes** da medição (C11). Os
limites das faixas de comparabilidade do RF23 também precisam sair de um
subconjunto separado daquele em que se mede (C15). Nesta semana o conjunto de
avaliação e o arnês da bateria ficam prontos. Com o espaço de busca nacional,
decidido no mesmo dia, a medição sai na virada do ano.

Duas condições pesaram:

- a observação de uso com a servidora e o julgamento às cegas (C5 e C6) passam
  para o início do TCC II, então o que a pesquisa sugeria calibrar nessa sessão
  precisa ser fixado agora, ou a medição espera até 2027;
- o conjunto vem de **três** relatórios de cotação, o que impede dividir ou
  reamostrar por relatório.

A investigação está em `docs/pesquisas/limiares-de-aceitacao-r1-r2.md`.

## Opções consideradas

| Ponto | Opções | Escolha |
|---|---|---|
| Critério de R1 | Absoluto fixo; relativo sem margem; relativo com margem | Relativo com margem de 0,05 |
| Corte k | 10 agora; 20 agora; esperar a observação de 2027 | 10, fixado agora |
| Partição | 40/60 por item; 25/75 por item; validação cruzada aninhada como principal | 40% ajuste e 60% medição, por item |
| Estratos da partição | Relatório e material ou serviço; mais o número de relevantes; só o relatório | Relatório e material ou serviço |
| Escolha do finalista | Maior Recall\@10 no ajuste, com desempate pelo MRR\@20; dois finalistas com correção; o multilingual-E5 fixado agora | Maior Recall\@10 no ajuste, com desempate pelo MRR\@20 |
| Definição de Recall\@10 | Fração dos escolhidos entre os dez primeiros; ao menos um entre os dez primeiros | Fração dos escolhidos |
| Aceite de R2 | Nível de referência de 25% de erro; R2 só descritivo até 2027; nível de 50% | Nível de referência de 25% |
| Leitura de R2 | Grade fixa com linha de base só-preço e partição fácil/difícil; só a curva; esperar o erro real da servidora | Grade fixa, só-preço e fácil/difícil |

## Decisão

**R1.**

- **Recall\@10** é, em cada item, a fração dos preços escolhidos pela servidora
  que aparece entre os dez primeiros resultados, com média sobre os itens. "Ao
  menos um entre os dez primeiros" é descritivo.
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

- 40% para ajuste e 60% para medição, **por item**, sobre os 231 itens com ao
  menos um preço escolhido reencontrado no PNCP, estratificada por relatório e
  por material ou serviço, com semente fixa. Os 40 itens sem relevante no PNCP
  ficam fora do escopo de R1, e isso é dito com o número.
- A lista de itens e o seu resumo SHA-256 são gravados **antes** de qualquer
  método rodar sobre itens rotulados. O arnês recusa ler a medição se o resumo
  não bater.
- No ajuste se fixam no máximo quatro parâmetros: os dois limites de faixa do
  finalista, e o k1 e o b do BM25. O resto usa valor padrão declarado.
- **A partição congelada**, gerada pelo comando versionado com semente 42 e
  fração 0,40 sobre os 231 itens, tem 92 itens de ajuste, 139 de medição e o
  resumo SHA-256
  `2c2e7bd50913b30ad3ab1b4f336178e19a3c0514c2f4acdf2a6007d3606eb6ad`. A lista
  de itens fica fora do repositório, com o dado de domínio. O resumo fica aqui,
  e o arnês recusa medir se a partição não bater com ele.

**R2.**

- A âncora é exp(média de ln(preços escolhidos) + σ·Z), com σ em {0; 0,10;
  0,25; 0,50; 1,00}, mais a condição sem âncora. σ = 0 é rotulado como limite
  superior, porque é o oráculo.
- Uma **linha de base só-preço** ordena o mesmo espaço de busca por
  |ln(p/âncora)|, sem texto. Se ela empatar com o sistema, o ganho é do preço.
- Uma **partição fácil/difícil**: o item é fácil quando o só-preço já põe um
  relevante entre os dez primeiros. O ganho de R1 tem de persistir nos difíceis.
- Relata-se G(σ) = Recall\@10 com σ − Recall\@10 sem âncora, em todos os
  níveis.
- **R2 é aceito** se as três condições valerem: R1 aceito; com a âncora em
  σ = 0,25, o sistema supera a linha de base só-preço, com o limite inferior do
  intervalo de 95% acima de zero; e o ganho do finalista sobre o BM25 persiste
  nos itens difíceis, também com o limite inferior acima de zero. A sessão de
  2027 confere se 25% de erro é realista para a servidora.

**Constantes de execução.** 200 sorteios de ruído por item e nível, com os
mesmos sorteios em todos os níveis; 10.000 reamostras no intervalo; sementes
fixas, gravadas na saída de cada execução.

## Justificativa

- **Não há fonte para um Recall\@10 absoluto "razoável".** Ele depende do espaço
  de busca e do gabarito, e escolhê-lo olhando a linha de base é o que o C11
  proíbe.
- **Vencer a busca por palavra é conservador**, porque o gabarito a favorece.
  A margem separa a significância da importância prática.
- **Com cerca de 139 itens na medição, só se detectam diferenças de cerca de
  dez pontos.** Somada à margem de 0,05, a barra prática é mais alta: para ter
  80% de chance de aceitar o R1, o sistema precisa superar o BM25 por algo entre
  12 e 18 pontos, conforme os métodos discordem mais ou menos. Com ganho
  moderado, "inconclusivo" é o desfecho provável, e isso é dito antes de medir.
  A conta supõe acerto binário por item; com Recall\@10 como fração, a variância
  por item não é maior, então a conta vale como limite conservador.
- **O k fixado agora** permite medir na virada do ano, sem esperar 2027. Se a observação de 2027
  mostrar que a servidora examina outro número de candidatos, isso vira
  limitação declarada, e não mudança do k depois de medir.
- **A grade de ruído é escolha de projeto**, porque nenhuma fonte prescreve
  níveis. A sessão de 2027, com o preço visível ou oculto sorteado por item,
  serve de validação externa.

## Consequência

- O arnês implementa exatamente estes parâmetros. Mudar qualquer um depois de
  rodar sobre a medição invalida o R1.
- O espaço de busca foi decidido no mesmo dia, em nota própria:
  [[2026-11-24-espaco-de-busca-e-preco-do-candidato]].
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
- [[2026-11-24-espaco-de-busca-e-preco-do-candidato]]
