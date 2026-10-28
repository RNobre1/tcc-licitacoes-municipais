---
tipo: pesquisa
titulo: "Como ordenar candidatos por comparabilidade e proximidade de valor sem fundi-las, como medir a proximidade, e o que a estimativa exibida faz com o julgamento do operador?"
status: recomendação, pendente de decisão do Rafael e, na parte que toca o protocolo de avaliação, de aval da orientação
criado: 2026-10-28
autor: Rafael Nobre de Souza
relacionado:
  - docs/requisitos/README.md
  - texto/tcc1/secoes/04-desenvolvimento.tex
  - texto/tcc1/secoes/05-resultados-esperados.tex
  - docs/tasks/backlog.md
tags: [pesquisa, ordenação, ranqueamento, preferências, ancoragem, avaliação, decisão]
---

# Ordenação por duas dimensões: comparabilidade e proximidade de valor

> **O que esta nota é.** Uma decisão relevante, tratada pelo protocolo do
> projeto: para, pesquisa, justifica, sobe. Nada aqui altera código, texto do
> TCC ou backlog. O que depende de decisão está marcado como **decisão**, e o que
> é raciocínio meu, e não achado de fonte, está marcado como **inferência**.
>
> **O que a literatura lida não resolve.** Nenhuma fonte lida mede se o
> operador *entende melhor* uma ordenação do que outra, nem se mostrar uma
> estimativa de preço enviesa um julgamento de *comparabilidade* (categórico).
> A recomendação da seção 7 se apoia em propriedades formais e no encaixe com o
> protocolo de avaliação, e propõe medir o efeito de ancoragem em vez de
> presumi-lo.

## 1. Resumo

| Pergunta | Recomendação | Estado da evidência |
|---|---|---|
| Como ordenar sem fundir | **Ordem lexicográfica sobre faixas de comparabilidade**: a comparabilidade decide a faixa, a proximidade de valor desempata *dentro* da faixa, e as duas colunas aparecem sempre | Formal (Chomicki) e de revisão (Latifis); sem evidência de usuário |
| Como medir a proximidade | **Razão logarítmica**, d = \|ln(p/e)\|, exibida como fator ("1,35× acima") | Propriedades demonstradas (Tofallis, Morley), em previsão, não em preços; transferência é inferência |
| Sem preço esperado | A coluna some e a ordem se reduz à comparabilidade. **Nada é imputado** | Raciocínio de projeto (inferência) |
| Efeito de mostrar a estimativa | **Desconhecido para julgamento de comparabilidade.** Ancoragem em estimativa numérica é grande e vale para especialistas; o que não se sabe é se transborda para um julgamento categórico | Schley, Kazak, Azzopardi |
| Afeta R1, R2, protocolo? | **Sim.** R1 precisa fixar a chave de ordenação; R2 mistura dois efeitos que o texto trata como um; o protocolo ganha três emendas (seção 8) | Inferência sobre o desenho, com base no que o projeto já registra |
| Sobe à orientação? | **Sim, o pacote do protocolo** (seção 8). A regra de ordenação em si é reversível e fica com o Rafael | Regra do projeto para decisão relevante: a que afeta método ou avaliação vai também à orientação |

## 2. Contexto e o que está em jogo

O requisito RF23 manda aceitar uma estimativa de preço esperado e ordenar os
candidatos "considerando tanto a comparabilidade do item quanto a proximidade a
essa estimativa, exibindo as duas dimensões separadamente"
(`docs/requisitos/README.md:624`). A seção de arquitetura proíbe o escore único
"para que o operador saiba qual das duas puxou cada candidato para cima"
(`texto/tcc1/secoes/04-desenvolvimento.tex:526-529`). A origem é uma observação
de campo: a servidora descarta candidato por valor implausível antes de ler a
descrição (`docs/requisitos/README.md:634-646`).

Três coisas nunca foram definidas: a regra de ordenação, a medida de
proximidade e o que fazer sem preço esperado. E há uma quarta, que o texto
atual trata como resolvida: o efeito de exibir o preço sobre o próprio
operador.

Por que é relevante. O R1 mede se os candidatos certos aparecem "entre os
primeiros resultados", e a ordenação define o que é "primeiro". O R2 separa
compreender o item de já conhecer o preço, em duas condições
(`texto/tcc1/secoes/05-resultados-esperados.tex`, tabela de resultados).
O backlog afirma que essa avaliação em duas condições "não é afetada" pelo viés
do gabarito, porque compara cada método consigo mesmo
(`docs/tasks/backlog.md:115`). A seção 8 examina o alcance dessa afirmação.

## 3. Método e limites da busca

Nove consultas ao Consensus, sem filtro de ano, desenho ou periódico, sobre:
ancoragem em estimativa de preço; ordenação multicritério sem agregação
(Pareto); medidas de similaridade de preço; consultas de preferência em bancos
de dados; ancoragem em julgamento de relevância; razão logarítmica de acurácia;
semiordem lexicográfica; exibição de escore do sistema a quem julga;
detecção de preço anormal em compras públicas. A busca devolve resumo, não
texto: **só entrou na síntese o que teve o texto completo lido** e as citações
conferidas por busca literal no texto extraído. Metadado conferido por
Crossref e pelo registro do arXiv, nunca de memória.

Não houve mensagem de assinatura nem contador nos resultados do Consensus. O
único bloco final foi a instrução de citação, que reproduzo na resposta ao
coordenador.

## 4. Fontes lidas por inteiro

| # | Fonte | Versão lida | Sustenta |
|---|---|---|---|
| C | Chomicki, J. *Preference Queries*. arXiv:cs/0207093 (27 jul 2002), 34 p. | **Preprint**, "versão expandida" de um artigo da EDBT 2002. A versão publicada é Chomicki, J. *Preference formulas in relational queries*. ACM TODS 28(4):427–466, 2003 (DOI 10.1145/958942.958946). **Conferir o publicado antes de citar** | Composição de preferências, ordem lexicográfica como composição priorizada, camadas por iteração, limite do escore único |
| L | Latifis, K.; Sidiropoulos, A.; Evangelidis, G. *International university rankings: composite indicators and methodological approaches*. Front. Res. Metr. Anal. 11:1828850, 25 maio 2026. DOI 10.3389/frma.2026.1828850 | Publicada, acesso aberto, 30 p. Revisão narrativa, declarada como tal | Críticas ao escore composto; alternativas sem agregação |
| T | Tofallis, C. *A better measure of relative prediction accuracy for model selection and model estimation*. J. Oper. Res. Soc. 66(8):1352–1362, 2015. DOI 10.1057/jors.2014.103 | **Preprint do autor**, 25 p. | Razão logarítmica, assimetria do erro percentual |
| M | Morley, S. K.; Brito, T. V.; Welling, D. T. *Measures of model performance based on the log accuracy ratio*. Space Weather 16(1):69–88, 2018. DOI 10.1002/2017SW001669 | **Manuscrito aceito**, repositório do LANL, 55 p. | Razão logarítmica, leitura em fator e em percentual |
| S | Schley, D. R.; Weingarten, E. *50 Years of Anchoring Effects: A Theoretical Re-Integration and Meta-Analysis*. Publicado como *Fifty Years of Anchoring Effects: A Theoretical Reintegration and Meta-Analysis*, Management Science, 19 maio 2026. DOI 10.1287/mnsc.2023.03238 | **Manuscrito em revisão**: o texto traz `[Blinded for review, 2025]`. Título e números podem diferir do publicado. **Conferir os números na versão final antes de citar** | Ancoragem: tamanho do efeito e moderadores |
| A | Azzopardi, L. *Cognitive Biases in Search: A review and reflection of cognitive biases in Information Retrieval*. CHIIR '21, p. 27–37. DOI 10.1145/3406522.3446023 | Versão do repositório da Universidade de Strathclyde, 11 p. Artigo de perspectiva, "not a systematic review" | Ancoragem e vieses no julgamento de relevância |
| K | Kazak, J. K.; Zarębska, W.; Sadowski, A.; Kamińska, J. A. *The anchoring effect in real estate decisions*. Real Estate Management and Valuation 34(1):53–62, 2026. DOI 10.2478/remav-2026-0005 | Publicada, acesso aberto, 10 p. | Ancoragem em profissionais, em tarefa de valoração de preço |

Duas correções de metadado vindas da conferência. O Consensus lista Kazak como
2025; o cabeçalho do artigo traz volume 34, número 1, **2026** (recebido em
2025-07-02, aceito em 2025-11-25). E o Consensus lista Schley com o título
publicado, "Fifty Years", enquanto o manuscrito lido diz "50 Years".

## 5. Achados

### 5.1 Ordenar por duas dimensões sem fundi-las

**O escore único não é neutro, e para uma preferência com duas dimensões nem
sempre é possível.** Chomicki mostra que uma relação de preferência só pode ser
representada por uma função de escore se for uma *ordem fraca*, o que exige que
a indiferença seja transitiva: "in order for a preference relation to be
representable using scoring functions the relation has to be a weak order"
(C, seção 3.2; ver também o exemplo 1.2 e o teorema 6.1). A composição de Pareto
(C, definição 4.2) não é ordem fraca em geral.

> **Inferência.** Exemplo mínimo, com as duas dimensões a maximizar: A = (2,2),
> B = (1,1), C = (3,0). A domina B. C é incomparável com A e com B. Logo
> "A ∼ C" e "C ∼ B" valem, mas "A ∼ B" não: a indiferença não é transitiva e
> nenhum escore reproduz essa ordem. É aritmética, não achado, mas é o que dá
> base formal à proibição do escore único que a seção de arquitetura já faz por
> outra razão (rastrear a origem do puxão).

**O que Latifis acrescenta, no domínio dele (rankings de universidades).**
- Crítica ao composto: a posição é "sensitive to seemingly technical design
  decisions" e as tabelas "encourage over-interpretation of small score
  differences" (L, p. 2); pesos fixos e agregação compensatória "implicitly
  authorize trade-offs between dimensions that are rarely justified as
  universally valid" (L, p. 26).
- Pareto: "(i) they avoid arbitrary weighting and normalization, (ii) they
  preserve the structure of multidimensional data, (iii) they enhance
  interpretability" (L, p. 11). Preço a pagar: "Dominance induces a partial
  order … allowing incomparability" (L, p. 11), e o conjunto não dominado pode
  ficar grande, o que o artigo liga a espaços de muitas dimensões: "skyline sets
  can become very large" (L, p. 12).
- Camadas: "a tiered classification scheme, by partial order rather than strict
  total ranking", com os pontos da mesma camada ainda incomparáveis (L, p. 13).
- Faixas: "tiering and banding reduce false precision" (L, p. 19), mas "grouping
  thresholds still affect interpretive outcomes, even if explicit weights are
  avoided" (L, p. 20).
- Ressalva dos autores, que vale para toda a seção: "weight-free" não é
  "value-neutral"; escolher o método e os indicadores "is itself a normative
  decision and therefore not neutral" (L, p. 2–3).
- Recomendação final: acompanhar qualquer ranking escalar de "complementary
  representations (fronts, layers, groups, and profiles)" (L, p. 28).
- **Ordem lexicográfica entre critérios com prioridade: não consta.** A única
  menção é lexicográfica sobre (profundidade de Pareto, desempate), L, p. 13.

**O que Chomicki dá para a ordem lexicográfica.** Ela aparece como *composição
priorizada* (definição 5.1): "prefer according to ≻C2 unless ≻C1 is
applicable". Duas notas técnicas. A composição priorizada de relações
transitivas não precisa ser transitiva (exemplo 5.2), mas isso vale para
relações arbitrárias; sobre ordens fracas ela se comporta como a ordem
lexicográfica usual (**inferência**). E a iteração do operador de seleção
(definição 7.1) gera *camadas*: a primeira é a fronteira de Pareto, a segunda é
a fronteira do que sobrou, e assim por diante (seção 7).

**Veto não comuta com ordenação.** Chomicki mostra que aplicar um filtro antes
ou depois da seleção das preferidas dá resultados diferentes, salvo condição
verificável (teorema 4.3; exemplo 6.1, "selecting the most desirable affordable
car will not give the same result as selecting the most desirable cars if they
are affordable"). Isso importa porque o comportamento observado da servidora é
um *veto* por valor, e RF23 pede *ordenação*.

**Tolerância.** Chomicki define, no §6.1.2, o conjunto dos que diferem do topo
"by at most d" (ω com f − d). Pela aritmética, tolerância *par a par* ("empata
se a diferença é ≤ δ") não é transitiva (0, δ e 2δ: o primeiro empata com o
segundo, o segundo com o terceiro, o primeiro não empata com o terceiro).
Luce (1956) e Pirlot & Vincke (1992) tratam disso como semiordens, mas só li os
resumos, e eles ficam fora da sustentação. **Consequência de projeto
(inferência):** faixa tem de ser *partição fixa* (faixas com cortes), nunca
tolerância par a par, senão a ordenação é mal definida.

**Lacuna.** Latifis não traz evidência de usuário: nenhum teste de compreensão,
estudo de usabilidade ou experimento com decisores. A demanda por tabela simples
é afirmada, citando Moed (2017), e não medida (L, p. 27). Nenhuma fonte lida
compara formatos pela compreensão de quem decide.

### 5.2 Medir a proximidade de valor

Seja p o preço unitário do candidato e e o preço esperado, ambos positivos.

| Medida | Propriedade, com fonte | Problema, com fonte |
|---|---|---|
| \|p − e\| | Simples | Depende da escala: "an error of ε = 100 is penalized equally at x = 103 and x = 106" (M) |
| \|p − e\| / e | Independe da escala | **Assimétrica**: previsto 10 e real 100 dá 90%; previsto 100 e real 10 dá 900% (T, citando Shepperd e MacDonell). Um fator 2 acima dá 100%, um fator 2 abaixo dá 50% (M). Indefinida com referência zero (M) |
| \|ln(p / e)\| | "This measure is symmetric in the sense that interchanging f and g merely alters the sign"; adimensional (T); simétrica e aditiva, atribuídas a Törnqvist (T); em fator, `exp(\|ln Q\|)`, e `exp(\|ln Q\|) − 1` é o erro relativo com o *menor* valor no denominador (M, eqs. 9 e 12) | Exige valores estritamente positivos: "the quantity of interest is strictly positive, and we shall make this assumption throughout" (T); indefinida com zero (M) |

**O que as duas fontes não são.** Tofallis trata de previsão de esforço de
software; Morley, de fluxo de elétrons em cinturões de radiação. Nenhuma trata
de preço de mercado nem de comparabilidade item a item. Que a dispersão de preço
cresça com o nível (heterocedasticidade multiplicativa, o caso em que a medida é
"far superior" em T) é **hipótese a verificar nos dados do PNCP**, e não achado.
Tofallis também avisa que o log tem viés para baixo quando o ruído é *aditivo*.
Nenhuma das duas propõe limiar por item: ambas agregam. Que "razão máx/mín ≤ τ"
equivalha a "\|ln(p/e)\| ≤ ln τ" decorre da equação 9 de Morley
(**inferência**).

### 5.3 O efeito de mostrar a estimativa ao operador

**O que se sabe sobre ancoragem numérica.** Schley e Weingarten meta-analisam
1.280 tamanhos de efeito: g = 0,825 (IC 95% 0,765–0,884), com I² de 93,7%
(S, p. 23). Moderadores relevantes (S, tabelas 5 e 6, **números do manuscrito**):

| Moderador | Leitura |
|---|---|
| Âncora incidental (priming) contra paradigma típico | g de 0,16 contra 0,97. Maior moderador |
| Pergunta de comparação explícita | Sem moderação significativa (g de 0,88 contra 0,76), confundida com outros moderadores |
| Âncora de **outra dimensão** | g de 0,38 (n = 48) contra 0,84. Cai, não zera |
| Âncora implausível ou extrema | Sem moderação (β de −0,02) |
| Expertise do julgador | Sem moderação significativa (g de 0,66, n = 62, contra 0,83) |
| Incentivo à acurácia | **O único efeito consistente** nas quatro especificações (β de −0,23; g de 0,59 contra 0,84) |
| Debiasing | Não significativo nos modelos multivariados (β de −0,15); mesmo a estimativa pontual (g de 0,63 contra 0,83) deixa o efeito grande |

**Os limites de transferência, e eles são decisivos.** O critério de inclusão é
"at least one judgment in the form of a numeric estimate" (S, p. 16). **O artigo
não cobre julgamento categórico, de relevância ou de escolha** (busca pelo
termo não encontra desenho desse tipo). Exclui âncora em faixa e várias âncoras
por julgamento (S, p. 17), e a nossa tela mostra duas grandezas por candidato
(estimativa e distância). Predomina psicologia de laboratório (742 dos 1.280
efeitos), e a tabela de descrição do manuscrito registra só 20 de campo. E o artigo não traz recomendação de *mitigação*:
as orientações da seção 5.3 dele são para quem quer *usar* âncoras.

**Especialistas não escapam em tarefa de preço.** Kazak et al. mediram 170
profissionais do mercado imobiliário (avaliadores, corretores, gestores,
acadêmicos): índice de ancoragem de 46%, sem efeito significativo de
experiência, escolaridade ou sexo (K). Duas ressalvas: não há braço sem âncora,
e as âncoras estavam a ±6σ da estimativa de especialistas. É evidência sobre
*estimar valor*, o que o operador faz com o preço, não com a comparabilidade.

**Julgamento de relevância e informação mostrada a quem julga.** Azzopardi
relata, sem tamanhos de efeito ("the above findings are tendencies"), que
quem julga ancora no próprio julgamento anterior (A4); que uma porcentagem
fabricada de "outros avaliadores que acharam relevante" arrastou o julgamento
(A6); que quando a informação era verdadeira a probabilidade de marcar relevante
cresceu com ela e a acurácia melhorou (A7, A8); e que uma interface neutra
rendeu rótulos melhores que as indutoras de viés (A9). Pontuação, ranking ou
sugestão *do sistema* mostrados a quem julga: **não consta**. O próprio autor
admite que seguir o indicador pode ser regra racional, não viés, e que os dois
mecanismos são empiricamente indistinguíveis. Além disso o artigo não traz
orientação de randomização nem de cegamento.

> **Inferência.** A distância ao preço esperado se parece, para quem julga, com
> o indicador de A6 a A8: um número que carrega informação *possivelmente
> válida*. Se a estimativa é boa, ela ajuda (A8). Se é ruim, arrasta (A6). A
> origem declarada da estimativa na demonstração de campo (consumo cotidiano,
> cotação a fornecedor local, mecanismo de busca comum) sugere validade
> heterogênea. Nenhuma fonte lida testa isso para comparabilidade.

## 6. Opções

### 6.1 Regra de ordenação

| # | Opção | Prós | Contras | Custo de implementação |
|---|---|---|---|---|
| A | **Lexicográfica sobre faixas de comparabilidade**: faixa, depois proximidade, depois escore de comparabilidade | Determinística; a estimativa só reordena *dentro* da faixa e nunca promove candidato de faixa inferior, o que limita o ganho atribuível ao preço; sem estimativa, reduz-se exatamente à comparabilidade; mantém as duas colunas separadas | Exige cortes de faixa (parâmetro); com faixa larga a proximidade manda demais, com faixa estreita não conta; borda de faixa é artificial | Baixo na ordenação (um `ORDER BY`). Médio no desenho: calibrar o escore em faixas num subconjunto de ajuste, com limiar fixado antes de medir (C11) |
| B | **Escolhida pelo operador** (clique na coluna) | Não pressupõe nada; mostra as duas | Entrega a escolha a quem pode estar ancorado; R1 passa a depender do operador; a trilha (RF32) precisa registrar a ordem | Baixo na tela. **Alto no protocolo**: é preciso fixar uma ordem padrão para medir |
| C | **Fronteira de Pareto em camadas** | Sem pesos; mostra exatamente quem não é dominado; formalmente justificada (seção 5.1) | Camada pode ficar grande; dentro dela só há incomparabilidade, então "primeiros" deixa de ser "k primeiros"; recall@k do R1 perde comparabilidade com a linha de base lexical | Baixo no algoritmo (duas dimensões: ordenar e varrer). **Alto na avaliação**: exige métrica nova |
| D | **Grade de faixas nas duas dimensões** | Casa com o gesto da servidora (descartar por valor, depois ler); interpretável | Dois conjuntos de cortes; mais parâmetros a fixar antes de medir | Médio |
| E | Escore ponderado | Ordem total | **Proibido pela arquitetura**; não representa a preferência de duas dimensões (seção 5.1) | Baixo, e descartada |
| F | **Veto por valor** (filtro de implausibilidade) | É o comportamento observado | Remove candidato, o que afeta o recall do R1 e o gabarito; filtro e seleção não comutam (Chomicki, teorema 4.3); RF23 pede ordenação, não filtro | Baixo. Só como *marcação visual*, não como remoção |

### 6.2 Medida de proximidade

| Opção | Prós | Contras | Custo |
|---|---|---|---|
| Absoluta | Trivial | Escala-dependente; inutilizável entre itens de R$ 2 e R$ 2.000 | Nulo |
| Relativa | Familiar ao operador | Assimétrica; indefinida com referência zero | Nulo |
| **Logarítmica** | Simétrica, adimensional, lida como fator; dá limiar por fator | Só para positivos; evidência em previsão, não em preço; trata acima e abaixo como iguais (o sinal é exibido à parte) | Baixo: uma função e uma regra de entrada válida |

## 7. Recomendação

**Decisão 1, regra de ordenação: opção A**, com a opção F apenas como marca
visual e a opção B como reordenação manual *fora do que R1 e R2 medem*.

Motivo, em três linhas. A mantém as duas dimensões visíveis e separadas, como
RF23 e a arquitetura exigem. Dá ao R2 uma propriedade que as outras não dão: a
condição *com* estimativa é a condição *sem* estimativa reordenada dentro das
faixas, então o efeito do preço fica limitado e interpretável. E o R1 continua
sendo recall nos k primeiros. Custo: o corte das faixas é um parâmetro que tem de
ser fixado antes de medir e ajustado num subconjunto separado (C11).

**O que faria a recomendação mudar.**
1. Se o escore de comparabilidade for pouco calibrado, de modo que as faixas
   fiquem instáveis: ir para a opção C, aceitando a métrica nova.
2. Se a sessão C5 mostrar que o que a servidora aceita costuma estar em faixa
   inferior, mas perto do preço: aumentar o peso da proximidade, o que aponta
   para C ou D.
3. Se o experimento de ancoragem (seção 8) mostrar que exibir a proximidade
   desloca o julgamento: ocultar a coluna até o operador marcar a comparabilidade
   (divulgação sequencial). **Isso muda a interface, e nenhuma fonte lida
   sustenta essa mitigação.**
4. Se Shokouhi et al. (2015) ou Carter et al. (2025), que não pude ler, forem de
   encontro ao desenho (seção 10).

**Decisão 2, proximidade de valor.** Para candidato com preço unitário p > 0 e
preço esperado e > 0, na mesma unidade e na mesma base de tempo:

- s = ln(p / e) (com sinal) e **d = \|s\|**.
- A tela mostra o fator `exp(d)` e o sentido: "1,35× acima" ou "1,35× abaixo".
  Ordenar por d crescente.
- Faixas de proximidade, se usadas, são cortes de fator (≤ τ₁, ≤ τ₂, acima),
  ou seja, cortes de d em ln τ. Os valores de τ são **decisão para C11**, e não
  entram aqui.
- Candidato cuja unidade não converte para a de e, ou com p ≤ 0: **d indefinido**,
  mostrado como "sem comparação de valor". Na ordenação, vai para o fim da
  faixa. Nunca recebe d = 0 nem d = ∞.
- **Sem preço esperado:** a coluna de proximidade não existe, e a chave de
  ordenação é (faixa, escore de comparabilidade). **Não se imputa estimativa**,
  nem a mediana dos candidatos. **Inferência:** imputar a partir dos candidatos
  premiaria o consenso de preços, mostraria ao operador um número que ela não
  informou, e duplicaria o RF24 (preço discrepante), que é outro recurso.
- Estimativa em **intervalo** fica fora desta recomendação: a literatura lida
  exclui âncora em faixa (S, p. 17).

## 8. Efeito sobre R1, R2 e o protocolo

**R1.** Passa a precisar declarar a chave de ordenação. Com a opção A, R1 sem
estimativa é o recall por similaridade que já estava previsto, e R1 com
estimativa só difere dele pela reordenação dentro das faixas. Com a opção C,
"primeiros resultados" deixaria de significar k posições.

**R2.** O texto atual trata "com e sem a estimativa" como um único contraste. Há
pelo menos dois efeitos nele, e a diferença entre as condições os soma.

1. **Efeito do sistema** (o que se quer isolar): quanto o preço ajuda a achar o
   que ela usou.
2. **Efeito do gabarito** (**inferência**): os preços do gabarito foram
   escolhidos por ela depois de descartar por implausibilidade de valor, e esse
   descarte está registrado em campo. Candidato perto do preço dela está
   *enriquecido* no gabarito por construção, e a condição com estimativa favorece
   exatamente esse candidato. É um viés de seleção por preço, **distinto do viés
   lexical** que o backlog trata. A afirmação "ela compara cada método consigo
   mesmo" (`docs/tasks/backlog.md:115`) cancela o viés que é constante entre as
   condições. Este não é constante: ele se correlaciona com a característica que só
   a condição com estimativa usa. Nenhuma fonte lida mede isso, e isso é teste
   empírico, não argumento.

**Emendas propostas ao protocolo (vão à orientação):**

- **P1. Origem da estimativa na avaliação.** O gabarito não traz a estimativa
  que a servidora tinha. Se ela for derivada dos preços do próprio gabarito,
  vira *oráculo* e infla a condição favorável. Proposta: reportar R2 como
  **curva**: sem estimativa (piso) e com estimativa = preço do gabarito
  perturbado por ruído multiplicativo log-normal, em vários níveis de σ, com σ = 0
  rotulado como **limite superior**. A escala logarítmica é a mesma da
  proximidade, o que mantém o experimento coerente. Os níveis de σ são decisão
  de C11.
- **P2. Calibrar σ com dado real.** No primeiro momento de C5 (observar),
  pedir o preço esperado *antes* de ela ver os candidatos, e registrar a origem
  (consumo, cotação local, busca). A razão logarítmica entre essa estimativa e o
  preço que ela acaba escolhendo mede a qualidade real das estimativas e fixa σ
  em dado, não em palpite. Custo: uma pergunta por item no roteiro de C6.
- **P3. Julgamento às cegas com e sem preço visível.** No segundo momento de C5,
  parte dos itens é julgada com o preço do candidato oculto, sorteada por item.
  O conjunto julgado às cegas de preço serve de gabarito livre do viés de
  seleção por preço (efeito 2). A diferença de aceitação entre preço visível e
  oculto estima, de graça, o efeito de ancoragem do preço sobre a comparabilidade.
  **Custo e limite:** reduz o número de itens julgados por sessão, e com uma
  única participante o resultado é evidência de caso, não de população. Se a
  sessão não comportar o desenho, o mínimo é registrar P2 e declarar o limite.

**Vai à orientadora?** O pacote P1 a P3 e a definição de "primeiros" em R1: sim,
porque tocam "o que é medido, ou como". A regra de ordenação em si e a medida de
proximidade são decisão de arquitetura do Rafael, reversíveis e sem custo de
retrabalho no texto, salvo o parágrafo das duas dimensões.

## 9. O que esta nota não estabelece

- Que a opção A é mais bem compreendida que as outras: **não há evidência de
  usuário** nas fontes lidas. Latifis não a traz, e nenhuma das demais compara
  formatos de apresentação.
- Que mostrar a estimativa enviesa, ou não, o julgamento de comparabilidade.
- Que a razão logarítmica é a medida certa para *preço de licitação*: as duas
  fontes são de previsão em outros domínios, e a hipótese de dispersão
  proporcional ao nível precisa ser verificada nos dados.
- Os números de Schley (manuscrito) e a forma publicada de Chomicki (preprint).

## 10. Fontes encontradas e não lidas

Fora da síntese, por falta de texto completo. Cada uma tem relevância declarada.

| Fonte | Por que importa | Por que não entrou |
|---|---|---|
| Shokouhi, White & Yilmaz. *Anchoring and adjustment in relevance estimation*. SIGIR 2015. DOI 10.1145/2766462.2767841 | **O estudo mais específico** de ancoragem em julgamento de relevância; Azzopardi o cita | ACM bloqueia o download direto; sem cópia aberta. **Não tentei o navegador** |
| Carter et al. *How was my performance? Exploring the role of anchoring bias in AI-assisted decision making*. Int. J. Inf. Manag., 2025. DOI 10.1016/j.ijinfomgt.2025.102875 | Âncora vinda de recomendação do sistema; propõe "consider the opposite" como mitigação | Texto aberto na editora, mas bloqueado ao download direto. **Não tentei o navegador** |
| Pirlot & Vincke (1992); Luce (1956) | Semiordens e agregação lexicográfica | Só resumo |
| Vartia (1985), *How should relative changes be measured?* | Único indicador de mudança relativa simétrico, aditivo e normado | Sem cópia aberta |
| Pan et al. (2023), Pareto multinível para ranking multiatributo | Tem estudo com usuários | Sem cópia aberta |
| Kießling (2002), *Foundations of Preferences in Database Systems* | Linha de pesquisa citada por Chomicki (seção 8.1) com construtores de preferência e composições Pareto e lexicográfica; pode trazer medida de distância a um alvo, **o que não verifiquei** | O repositório não respondeu ao download |
| Agai (2026), ancoragem em licitações com preço de abertura e estimativa oficial | Mesmo domínio | Só resumo; amostra pequena (65, 22 e 21 por grupo); veículo não avaliado |

**Próximo passo de leitura**, se a decisão for aprovada: Shokouhi e Carter, pelo
navegador, antes de redigir o parágrafo de ancoragem no texto.
