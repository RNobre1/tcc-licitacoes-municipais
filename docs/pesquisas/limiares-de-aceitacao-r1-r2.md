---
tipo: pesquisa
titulo: "Fixar R1 e R2 antes de medir: limiar, curva, partição e espaço de busca (C11, C15)"
status: decidida em 24/11/2026 — ver TCC/decisões/2026-11-24-limiares-de-aceitacao-r1-r2.md; o espaço de busca segue aberto
criado: 2026-11-24
autor: Rafael Nobre de Souza
relacionado:
  - TCC/decisões/2026-10-28-ordenacao-rf23.md
  - TCC/decisões/2026-10-15-classificacao-da-pesquisa-dsr.md
  - docs/pesquisas/ampliacao-de-bases-e-escolha-do-modelo-de-representacao.md
tags: [pesquisa, avaliação, limiar, c11, c15, recuperação, estatística]
---

# Fixar R1 e R2 antes de medir: limiar, curva, partição e espaço de busca

> **Como ler.** Cada pergunta tem: o que está **provado na fonte** (marcado **\[Fonte n]**), o que é **inferência** minha (marcado **\[Inf.]**), as opções com prós, contras e custo, uma recomendação com motivo, e o que a faria mudar. A decisão é do autor. Nenhum número de limiar, margem ou fração abaixo é decisão; são propostas.
>
> Duas ressalvas de método. Primeira: as cifras de poder estatístico (§6.1) são **cálculo meu**, com premissas explícitas, e não resultado de fonte. Segunda: quase toda a literatura de avaliação de recuperação lida é de coleções TREC, com cerca de 50 consultas e muitos relevantes por consulta. O caso daqui (cerca de 230 itens, poucos relevantes por item, descrição curta, gabarito vindo de outra ferramenta) é diferente em três pontos, e cada transposição está marcada.

## Resumo das recomendações

| # | Pergunta | Recomendação (propostas, não decisões) |
| --- | --- | --- |
| 1 | Limiar de R1 | **Relativo decide, absoluto descreve.** Aceitar R1 se o limite inferior do IC 95% da diferença pareada de Recall\@10 contra o BM25 ajustado ficar acima de uma margem mínima declarada. O piso absoluto só entra se a observação da C6 fornecer âncora. Um único contraste confirmatório (o finalista escolhido no ajuste). Empate só se declara com margem de equivalência de pelo menos ±8 a ±10 pontos. |
| 2 | R2 como curva | Curva de ruído log-normal com **níveis calibrados no erro real da servidora** (P2), mais uma **linha de base só-preço** e a **partição de itens fácil/difícil**. O ganho "não decorre só do preço" quando o sistema vence o BM25 sem preço **e** vence o só-preço com preço. |
| 3 | Partição | **Uma partição única, congelada antes de qualquer execução**, em torno de 40% ajuste / 60% medição, estratificada e **dividida por relatório de cotação** (não por item). Validação cruzada aninhada como robustez, não como decisão. A fração importa pouco (menos de 1,5 ponto de diferença mínima detectável entre 25% e 40%); o que importa é a disjunção, o congelamento e o agrupamento. |
| 4 | Corpus | **Corpus operacional inteiro sob os filtros que o sistema aplica em produção, com janela "a partir da data da pesquisa"**, igual para todos os métodos. Amostra aleatória de distratores: não. *Pool* só como protocolo de julgamento da C5, não como corpus de recuperação. |

---

## 1. Contexto

A classificação DSR exige critério de aceitação fixado antes da medição (C11), e os limites de faixa do RF23 hoje são provisórios (0,80 e 0,60, C15). O conjunto de avaliação tem 271 itens, dos quais 231 têm ao menos um preço escolhido pela servidora que se reencontra no PNCP. O arnês calcula Recall\@1/5/10/20 e MRR\@20, compara pares por reamostragem dos itens com IC de 95%, separa subconjunto de ajuste e de medição, e trata o R2 como curva de ruído log-normal sobre a âncora de preço. A linha de base obrigatória é o BM25, que parte em vantagem porque o gabarito veio de uma ferramenta que busca por palavra.

Decidir errado custa caro de duas formas. Um limiar escolhido olhando o resultado invalida a medição. Um limiar sem poder para detectar a diferença que importa produz um R1 inconclusivo, e a banca lê isso como ausência de resultado.

## 2. Pergunta central

Para um conjunto de cerca de 230 itens, com poucos relevantes por item e gabarito escolhido por uma ferramenta de busca por palavra, **o que a literatura de avaliação de recuperação permite fixar, antes de medir, sobre o limiar de R1, a leitura de R2 como curva, a partição ajuste/medição e o espaço de busca, e o que fica sem respaldo?**

## 3. Subperguntas

| # | Subpergunta | Escopo da busca |
| --- | --- | --- |
| 3.1 | Limiar de R1: absoluto, relativo ou ambos; qual k; qual teste; poder e diferença mínima detectável | Testes de significância em recuperação; tamanho de conjunto de consultas e poder; equivalência e não inferioridade; múltiplas comparações; métricas de corte |
| 3.2 | R2 como curva: níveis de ruído e critério para "o ganho não vem só do preço" | Robustez a ruído; linha de base de entrada parcial; dispersão de preços |
| 3.3 | Partição ajuste/medição | Fração ótima; validação aninhada; ajuste e teste disjuntos em recuperação |
| 3.4 | Espaço de busca quando o gabarito vem de outra ferramenta | Viés de *pool*; relevantes escolhidos por sistema; amostragem de negativos; efeito do tamanho do índice |

## 4. Metodologia aplicada

- **Nível**: L2. A decisão afeta o que é medido (critério 1 da regra de decisões relevantes), então a nota propõe e não decide.
- **Ferramentas**: busca em base de literatura revisada por pares (22 buscas, 3 resultados cada, no plano gratuito); OpenAlex e a API do arXiv **só para localizar cópia aberta e conferir metadado**; leitura de PDF por extração de texto. **Busca web geral não foi usada.**
- **Texto integral**: 17 fontes lidas: 14 por PDF obtido hoje (com as exceções de leitura parcial indicadas no §5) e 3 pelos fichamentos de rodadas anteriores, com os números citados reconferidos hoje contra o PDF. Os PDFs da ACM foram obtidos pela sessão de navegador do autor. Duas fontes foram lidas só nas conclusões e **não sustentam nenhuma afirmação** desta nota; outras ficam na fila, com só o resumo visto (§5).
- **Cálculo próprio**: fórmulas de poder e uma simulação do IC por reamostragem, descritas no §6.1. Os scripts não estão versionados; os parâmetros estão na nota, e o cálculo se refaz em minutos.
- **Revisão adversarial**: não executada por revisor independente. Há um registro de autocrítica no §12 e a recomendação de que alguém releia antes da reunião.

## 5. Fontes consultadas

Todas primárias (artigo ou preprint). Metadado conferido **no PDF**, salvo onde a coluna "Pendência" diz outra coisa.

**Lidas (texto integral obtido; exceções indicadas na própria linha).** As de \[1] a \[14] foram lidas por extração de texto; figuras e tabelas só no que o texto descreve. Em \[13] e \[14] foram lidos os parágrafos corridos, e linhas curtas de tabelas e legendas ficaram de fora.

| # | Referência | Pendência de metadado |
| --- | --- | --- |
| 1 | Smucker, M. D.; Allan, J.; Carterette, B. A comparison of statistical significance tests for information retrieval evaluation. *CIKM'07*, Lisboa, 6–8 nov. 2007. ACM, a partir da p. 623, 10 p. | DOI (10.1145/1321440.1321528) vem do registro do DOI, não impresso no PDF; página final a conferir |
| 2 | Urbano, J.; Lima, H.; Hanjalic, A. Statistical significance testing in information retrieval: an empirical analysis of Type I, Type II and Type III errors. *SIGIR '19*, Paris, 21–25 jul. 2019. ACM, 10 p. doi:10.1145/3331184.3331259 (impresso). Lido o preprint arXiv:1905.11096v2 | páginas a conferir |
| 3 | Sakai, T. My system is as effective as yours: reproducibility, sustainability, and more. *SIGIR '25*, Pádua, 13–18 jul. 2025. ACM, 11 p. doi:10.1145/3726302.3730345 (impresso) | — |
| 4 | Ferro, N.; Sanderson, M. Uncontextualized significance considered dangerous. *SIGIR '24*, Washington, 14–18 jul. 2024. ACM, 10 p., a partir da p. 261. doi:10.1145/3626772.3657827 (impresso) | — |
| 5 | Webber, W.; Moffat, A.; Zobel, J. Statistical power in retrieval experimentation. *CIKM'08*, Napa Valley, 26–30 out. 2008. ACM, a partir da p. 571, 10 p. | DOI (10.1145/1458082.1458158) do registro, não impresso |
| 6 | Fuhr, N. Some common mistakes in IR evaluation, and how they can be avoided. *ACM SIGIR Forum*, v. 51, n. 3, dez. 2017, p. 32–41 | DOI (10.1145/3190580.3190586) do registro; o registro data a publicação de 2018 |
| 7 | Büttcher, S.; Clarke, C. L. A.; Yeung, P. C. K.; Soboroff, I. Reliable information retrieval evaluation with incomplete and biased judgements. *SIGIR'07*, Amsterdã, 23–27 jul. 2007. ACM, p. 63–70 | DOI (10.1145/1277741.1277755) do registro |
| 8 | Krichene, W.; Rendle, S. On sampled metrics for item recommendation. *KDD '20*, 23–27 ago. 2020. ACM, p. 1748–1757. doi:10.1145/3394486.3403226 (impresso). **Lido em parte**: resumo, introdução, seção 6 (experimentos) e conclusão. A derivação (seções 4–5) foi lida na versão preliminar de um só autor, arXiv:1912.02263v1 (Rendle) | seções 4–5 da versão publicada não lidas |
| 9 | Reimers, N.; Gurevych, I. The curse of dense low-dimensional information retrieval for large index sizes. *ACL-IJCNLP 2021* (artigos curtos). Lido o arXiv:2012.14210v2, 9 jun. 2021 | páginas da versão publicada a conferir |
| 10 | Gururangan, S.; Swayamdipta, S.; Levy, O.; Schwartz, R.; Bowman, S. R.; Smith, N. A. Annotation artifacts in natural language inference data. *NAACL-HLT 2018*. Lido o arXiv:1803.02324v2, 16 abr. 2018 | páginas da versão publicada a conferir |
| 11 | Vabalas, A.; Gowen, E.; Poliakoff, E.; Casson, A. J. Machine learning algorithm validation with a limited sample size. *PLOS ONE*, v. 14, n. 11, e0224365, 7 nov. 2019. doi:10.1371/journal.pone.0224365 | — |
| 12 | Joseph, V. R. Optimal ratio for data splitting. Preprint arXiv:2202.03326v1, 7 fev. 2022 | versão publicada (*Statistical Analysis and Data Mining*, 2022) não lida; volume e páginas a conferir |
| 13 | Dror, R.; Baumer, G.; Shlomov, S.; Reichart, R. The hitchhiker's guide to testing statistical significance in natural language processing. *ACL 2018* (artigos longos), Melbourne, p. 1383–1392 | — |
| 14 | Berg-Kirkpatrick, T.; Burkett, D.; Klein, D. An empirical investigation of statistical significance in NLP. *EMNLP-CoNLL 2012*, Jeju, 12–14 jul. 2012, p. 995–1005 | — |

**Lidas em rodada anterior (fichamento em `TCC/papers/`), com os números citados aqui reconferidos hoje contra o PDF**

| # | Referência | O que foi reconferido |
| --- | --- | --- |
| 15 | Rassin, R. et al. Evaluating D-MERIT of partial-annotation on information retrieval. Preprint arXiv:2406.16048v2, 2024 | Tabela 3: erro de 3,20%, 15,10%, 22,75% e 19,20% (relevante escolhido ao acaso, mais popular, mais longo, por sistema existente); τ de 0,616 para o caso por sistema |
| 16 | Voorhees, E. M.; Soboroff, I.; Lin, J. Can old TREC collections reliably evaluate modern neural retrieval models? Preprint arXiv:2201.11086v1, 2022 | τ de 0,9933 (MAP) e 0,9991 (P\@10) entre qrels original e expandido; 134 sistemas |
| 17 | Yilmaz, E.; Craswell, N.; Mitra, B.; Campos, D. On the reliability of test collections for evaluating systems of different types. *SIGIR 2020*, p. 2101–2104 | coleção com *pools* de profundidade 10 e 43 consultas; τ de Kendall das Tabelas 1 e 2 (MRR dos sistemas neurais com *pool* tradicional: −0,12 em documentos e 0,004 em passagens; nDCG\@10: 0,68 e 0,574) |

**Lidas só em parte (resumo e conclusões). Não sustentam afirmação; servem para dizer onde a literatura não é unânime**

- Parapar, J. et al. Using score distributions to compare statistical significance tests for information retrieval evaluation. *JASIST*, 2019 (arXiv:1901.10696). Conclui que Wilcoxon e sinal são os mais potentes, o oposto de \[1] e \[2].
- Otero, D.; Parapar, J.; Barreiro, Á. Towards reliable testing for multiple information retrieval system comparisons. *LNCS*, 2025 (arXiv:2501.03930). Recomenda Wilcoxon com correção de Benjamini-Hochberg para comparar todos os pares de sistemas.

**Fila de leitura: só o resumo foi visto. Metadado como a base devolveu; nada citável**

Sakai (2016), revisão sistemática de poder em SIGIR e TOIS; Wellek (2010), livro sobre testes de equivalência; Tomek et al. (2026, PNAS), equivalência prática; Webber e Park (2009), ajuste de escore para viés de *pool*; MacAvaney et al. (2023, SIGIR), preenchimento de lacunas de julgamento com um relevante conhecido; Moffat (2022) e Ferrante et al. (2021, ambos IEEE Access), debate sobre escala de medida das métricas; Thakur et al. (2021), BEIR; Kamphuis et al. (2020), variantes do BM25; Ji et al. (2023, TOIS), Le et al. (2025, RecSys) e Gusak et al. (2025, RecSys), vazamento temporal em avaliação; Liu et al. (2023, RecSys), amostragem de negativos; Kaplan et al. (2015, *International Economic Review*), dispersão de preços; Wilson et al. (1996) e Kazak et al. (2025), ancoragem; Brown et al. (2025), auditoria de atalhos em *benchmarks*.

**Cobertura.** O plano gratuito devolve 3 resultados por busca. "Não achei" significa não achei nesta base com estas consultas. Em particular, **não achei fonte que prescreva níveis de ruído ou critério para uma curva de sensibilidade do tipo do R2** (duas buscas dedicadas devolveram trabalhos fora do assunto).

## 6. Síntese

### 6.1 Pergunta 1: como formular o limiar de R1

**Provado na fonte**

- **O que o teste estatístico faz com \~50 consultas de TREC.** O teste *t* pareado e o de permutação mantêm o erro tipo I no nível nominal, para várias métricas e para 25, 50 e 100 consultas; o *bootstrap-shift* é liberal (0,059 com α de 0,05 e 50 consultas), e o viés diminui com a amostra; Wilcoxon e sinal erram mais quanto maior a amostra \[2]. Em outro estudo, permutação, *bootstrap* e *t* quase coincidem com 50 consultas, e o *bootstrap* tem pequeno viés para p menores; os autores recomendam a permutação e descartar Wilcoxon e sinal \[1]. **A literatura não é unânime**: um terceiro trabalho, lido só nas conclusões, chega à conclusão oposta sobre a potência (§5).
- **Métricas de corte têm mais variância.** As diferenças de P\@10 e de recíproca do posto têm de 2 a 4 vezes o desvio padrão das de AP e nDCG\@20, e o erro tipo III chega a 2% para essas métricas ou com poucas consultas \[2].
- **Poder depende de efeito, variância e n.** A potência de um teste *t* pareado unilateral é aproximadamente Φ(√n·δ/σ − z₁₋α); reduzir à metade a diferença detectável, ou dobrar o desvio, exige quadruplicar a amostra. Não há um σ único: o desvio das diferenças varia muito entre pares de sistemas, e estimá-lo com experiência prévia ou piloto deixa margens largas \[5]. Com 50 consultas, só se detectam diferenças de AP de 0,06 a 0,08 \[5].
- **Piloto e medição têm de ser disjuntos.** Reusar os itens do piloto no experimento principal enviesa; acrescentar itens até atingir potência também enviesa (o desvio é subestimado em cerca de 3,5%, e a taxa de falso positivo sobe 7%) \[5].
- **Ausência de significância não é empate.** "Não rejeitei H₀" só permite dizer que não se sabe. Para afirmar equivalência ou não inferioridade, é preciso declarar antes uma zona de indiferença, e a potência exige muito mais amostra: com a margem derivada de preferências de usuário, 80% de potência pedia 101 consultas para nDCG e 460 para iRBU \[3]. Para vários contra um, se a conclusão só vale quando **todos** passam, não há correção; se basta **algum**, aplica-se α/K \[3].
- **Múltiplas comparações.** Sem correção, 40% a 50% dos resultados significativos de coleções TREC são provavelmente erro tipo I (todos os pares de sistemas); o erro sobe quando o conjunto de consultas diminui, e a inconsistência entre sistemas parecidos é de 2 a 3 vezes maior \[4]. O conjunto completo de hipóteses tem de ser conhecido antes do experimento; efeito e intervalo de confiança devem ser relatados; o MRR não está em escala intervalar, e a alternativa é o posto do primeiro relevante \[6].
- **Limiar de ganho não substitui teste.** O ganho necessário para significância depende do tamanho do conjunto de teste e da semelhança entre sistemas; a significância se calibra bem em amostras i.i.d. do mesmo domínio e se degrada em outro domínio \[14]. Observações dependentes violam o pressuposto dos testes \[13].
- **Poucos relevantes por consulta.** Com um relevante anotado por consulta, só diferenças grandes entre sistemas resistem \[15]. Para a mesma verba de julgamento, avaliar muitas consultas de forma rasa dá mais potência que poucas de forma funda \[5]. Medidas de precisão nos primeiros postos estão entre as mais sensíveis a julgamentos incompletos e enviesados (P\@20: perda média de 2,1 posições no sistema excluído, até 12; nDCG\@20: 2,1 e até 14), com o MRR entre as menos sensíveis (0,9) \[7].
- **Os primeiros postos importam mais.** A maioria dos usuários para cedo na lista \[6].

**Inferência**

- **\[Inf.] k = 10 como único corte confirmatório.** Nenhuma fonte fixa k para este domínio. O argumento é que o R1 diz "entre os primeiros resultados", que o usuário para cedo \[6] e que a C6 mede quantos candidatos a servidora examina. Recall\@1/5/20 e MRR\@20 ficam como descrição, declarados como tal, para não multiplicar hipóteses \[6].
- **\[Inf.] Poder para este caso.** O resultado é binário por item no caso mais simples (sucesso\@10), e o desvio da diferença pareada é ≈ √pd, com pd a fração de itens em que os dois métodos discordam. Com α de 0,05 bilateral e potência de 0,80, a menor diferença detectável é ≈ 2,80·√(pd/n).

| Itens na medição | pd = 10% | pd = 20% | pd = 30% |
| --- | --- | --- | --- |
| 231 (sem partição, só referência) | 5,8 | 8,2 | 10,1 |
| 173 (ajuste 25%) | 6,7 | 9,5 | 11,7 |
| 155 (ajuste 33%) | 7,1 | 10,1 | 12,3 |
| 139 (ajuste 40%) | 7,5 | 10,6 | 13,0 |
| 115 (ajuste 50%) | 8,3 | 11,7 | 14,3 |

Valores em pontos de sucesso\@10. Com quatro contrastes e Bonferroni, multiplicar por ≈ 1,19. Efeito de agrupamento (itens do mesmo relatório não independentes) multiplica por √deff: deff de 1,5 dá ≈ ×1,22. Uma simulação do IC percentil por reamostragem de itens (n de 231, 154 e 115; pd de 20%; diferença verdadeira de +8 pontos) deu cobertura de 0,95 e probabilidade de o limite inferior ficar acima de zero de 0,79, 0,62 e 0,46; sob diferença nula (pd de 10% e 20%, n de 154), 0,02 e 0,03 (nominal 0,025). **O pd é suposto**: só se conhece depois de rodar os métodos, e o conjunto de ajuste serve para estimá-lo antes de tocar a medição \[5].

- **\[Inf.] Equivalência é cara.** Pela fórmula de \[3], na aproximação normal (reproduz a potência de 0,364 publicada para n=50 com 0,33), com pd de 20%: margem de ±5 pontos pede ≈ 690 itens; ±8 pede ≈ 270; ±10 pede ≈ 170. Com 139 itens a potência é 0,36 para ±8 e 0,68 para ±10. **Com a amostra daqui, "empate" só é declarável com margem larga.**

**Opções**

| Opção | Prós | Contras | Custo |
| --- | --- | --- | --- |
| A. Só absoluto (Recall\@10 ≥ x) | Simples; diz se serve | Não há fonte para x; o valor depende do corpus, do tamanho do conjunto e do gabarito \[14, 9]; escolher x olhando o BM25 é exatamente o que C11 proíbe | Baixo |
| B. Só relativo (limite inferior do IC da diferença pareada > 0 contra o BM25) | Casa com o arnês; neutraliza o fato de o gabarito favorecer o BM25 (vencer é conservador); pareado controla dificuldade do item | "> 0" aceita ganho sem importância prática \[6]; não diz nada sobre empate \[3] | Baixo |
| C. Relativo com margem mínima (limite inferior > Δmin) e piso absoluto só se houver âncora no domínio | Separa significância de importância \[6]; o piso ancora o texto na tarefa real | Δmin e piso são decisões relevantes do autor; sem âncora, o piso volta a ser arbitrário | Médio: depende da C6 |
| D. C mais zona de equivalência para declarar empate | Distingue "empata" de "inconclusivo" \[3] | Margem ≥ ±8 pontos pela potência disponível; tentação de escolher a margem olhando o resultado | Médio; margem declarada antes |

**Recomendação: C, com D como regra de leitura do que não passa.** Motivo: o R1 precisa de um critério que o gabarito enviesado a favor do BM25 não desmonte (vencer em desvantagem é conservador), que a banca leia como efeito e não como mero p-valor, e que declare de antemão o que se conclui quando não passa. O texto do critério proposto:

1. **Confirmatório**: um contraste, finalista contra BM25 ajustado, Recall\@10, conjunto de medição, **o finalista escolhido por regra declarada sobre o conjunto de ajuste** \[Inf.; ajuste e teste disjuntos: 5, 6, 11]. Os demais contrastes do C3 são exploratórios, com Bonferroni se forem relatados como testes \[3, 4, 6].
2. **Aceitar R1** se o limite inferior do IC de 95% (reamostragem por relatório) da diferença pareada for **> Δmin**. Δmin é do autor; um ponto de partida defensável é 0,05, "um relevante a mais a cada 20 itens", na lógica do exemplo de Fuhr (0,02 de P\@10 = um relevante a mais a cada 5 consultas) \[6].
3. **Declarar empate** só se o IC de 90% ficar dentro de (−M, +M), com M ≥ 0,08. Fora disso, "inconclusivo". Empate ou perda **não refutam**, por causa do viés do gabarito (C5); quem decide a leitura é a sessão cega.
4. **Teste**: IC por reamostragem de relatórios (percentil) como regra de decisão; p-valor por permutação como conferência. Com cerca de 140 itens os testes *t*, permutação e *bootstrap* coincidem na prática \[1, 2], então a escolha é por o que se quer relatar, não por poder.
5. **Piso absoluto**: só se a C6 der âncora (por exemplo, a fração de itens em que o preço escolhido apareceu entre os candidatos que ela de fato examinou). Sem âncora, o nível absoluto é **relatado com IC e não decide**.
6. **Antes de tocar a medição**: calcular pd e a diferença mínima detectável no conjunto de ajuste. Se ela passar de Δmin, registrar que R1 não tem poder para esse contraste, em vez de medir e interpretar \[5].

**O que mudaria a recomendação**

- A C6 mostrar que a servidora examina bem mais ou bem menos que 10 candidatos: muda o k, **antes** de medir.
- pd ≥ 30% no ajuste (as diferenças só são detectáveis acima de ≈ 13 pontos): trocar para Recall\@20 ou relatar R1 como descritivo.
- Relatórios grandes e muito homogêneos (efeito de agrupamento alto): menos observações efetivas; a diferença mínima detectável sobe.
- A orientação preferir critério só absoluto: aceitar, desde que x venha de âncora externa e não do BM25.

---

### 6.2 Pergunta 2: como ler o R2 como curva (P1)

**Provado na fonte**

- A técnica de **linha de base de entrada parcial**: um classificador que vê só a hipótese, sem a premissa, acerta 67% dos pares no SNLI e 53% no MultiNLI; dividindo o teste em "fácil" (o classificador de entrada parcial acerta) e "difícil" (erra), os modelos completos caem muito no difícil (por exemplo, de 84,7% para 69,4% no SNLI para um deles). A lição declarada é que o sucesso dos modelos foi superestimado por atalhos do protocolo de anotação \[10]. **É o análogo exato do risco do R2**: o gabarito foi montado por quem descarta pelo preço antes de ler a descrição, e a condição "com estimativa" pode estar colhendo esse atalho.
- Sistemas muito correlacionados atingem significância com ganhos menores \[14]. O R2 compara o mesmo sistema consigo mesmo com e sem preço, então os ganhos detectáveis podem ser menores que os do R1. Em sentido contrário, a inconsistência entre sistemas parecidos é de 2 a 3 vezes maior \[4]. As duas coisas valem e a leitura tem de declarar ambas.
- Seleção do relevante por sistema existente distorce a ordem entre sistemas \[15, 7]. A seleção por preço é um mecanismo análogo, mas **nenhuma fonte lida mede o efeito do preço**; isso é inferência já registrada na decisão de 28/10.

**Não encontrado**

- Fonte que prescreva níveis de ruído, ou critério de aceitação, para uma curva de sensibilidade sobre uma âncora. Os níveis são, portanto, **escolha de projeto**, e devem ser justificados pelos dados da própria pesquisa.

**Inferência**

- **\[Inf.] Âncora**: ê = exp(média de ln(preços escolhidos) + σ·Z), Z normal padrão; σ = 0 é o oráculo e fica rotulado como limite superior (P1). Níveis de σ em unidades de ln: 0,1 (≈ ±10%), 0,25 (+28% / −22%), 0,5 (+65% / −39%), 1,0 (+172% / −63%).
- **\[Inf.] Calibração**: o melhor ancoradouro para σ é o erro real da servidora, medido na C5 pela emenda P2 (preço esperado pedido **antes** dos candidatos): σ̂ = desvio padrão de ln(estimativa / preço escolhido). Sem a C5 a tempo, o substituto é o desvio padrão de ln(preço) entre candidatos comparáveis do mesmo item, medido **no conjunto de ajuste**. Níveis sugeridos: {0, σ̂/2, σ̂, 2σ̂, sem estimativa}. A grade fixa acima é o plano B.
- **\[Inf.] Sorteio**: R = 200 sorteios de ruído por item e nível, com os mesmos Z em todos os níveis (curva monótona por construção); média dos sorteios dentro do item, IC por reamostragem de relatórios.
- **\[Inf.] Teto do ganho**: como a ordenação só reordena dentro da faixa, o ganho atribuível ao preço é limitado. Vale relatar o *headroom*: fração de itens em que o relevante está na faixa certa, mas fora do top 10 sem preço.

**Opções**

| Opção | Prós | Contras | Custo |
| --- | --- | --- | --- |
| A. Duas condições (com e sem estimativa) | Simples | O "com" é um oráculo; mistura efeito do sistema e viés de seleção (decisão de 28/10) | Baixo |
| B. Curva de ruído (P1 já adotada) | Mostra a dependência do preço; o oráculo vira limite superior | Sozinha não diz se o ganho é do preço ou do texto; os níveis são arbitrários se não calibrados | Baixo |
| C. B mais **linha de base só-preço** mais **partição fácil/difícil** | Responde ao R2 diretamente (analogia \[10]): se o só-preço iguala o sistema, o ganho é do preço | Linha de base nova a implementar; análise em três camadas | Médio |
| D. Só o experimento cego de P3 (preço visível ou oculto sorteado por item) | Livre do viés de seleção do gabarito | Poucos itens (depende da C5); caro; não substitui a curva | Alto, em tempo da servidora |

**Recomendação: C, com D como validação externa quando a C5 existir.** Critério proposto (todos declarados antes):

1. **Não é só o preço, parte 1**: a vantagem do sistema sobre o BM25 **sem estimativa** (R1) tem limite inferior do IC acima de Δmin. Se o ganho existe sem preço, ele não vem do preço.
2. **Não é só o preço, parte 2**: com estimativa, nos níveis σ ≤ σ̂, o sistema supera a **linha de base só-preço** (rankear os candidatos do mesmo C(q) por |ln(p/ê)|, sem texto), limite inferior do IC > 0. Se o só-preço empata, o ganho é do preço.
3. **Onde mora o ganho**: dividir os itens em "fáceis" (o só-preço já põe o relevante no top 10) e "difíceis" (não põe). O ganho de R1 tem de persistir nos difíceis; se ele estiver concentrado nos fáceis, decorre do preço \[10].
4. **Leitura da curva**: relatar G(σ) = R\@10(com, σ) − R\@10(sem), o nível σ\* em que G deixa de se distinguir de zero, e G(σ̂). Relatar o nível sem ruído como limite superior.
5. **Validação externa (D)**: se a C5 produzir julgamentos com preço oculto, a diferença entre G no gabarito e G nesses julgamentos estima o quanto o gabarito está ancorado no preço.

**O que mudaria a recomendação**

- O só-preço já empatar com o sistema: o R2 muda de "o ganho não decorre do preço" para "o gabarito não permite separar", e a conclusão sai da C5.
- O σ̂ medido na C5 ficar fora da grade acima: reescalar os níveis, não manter os fixos.
- |C(q)| pequeno depois dos filtros (o só-preço funciona de graça): o R2 mede pouco; reportar como limite.
- A ancoragem estimada pela P3 na C5: se for pequena, o gabarito é menos suspeito e a curva sobre ele pesa mais; se for grande, a curva sobre o gabarito só se lê como limite superior.

---

### 6.3 Pergunta 3: partição entre ajuste e medição (C15 e §6.4 item 5)

**Provado na fonte**

- **Ajuste e medição têm de ser disjuntos.** Validação que usa os mesmos dados para ajustar e medir dá estimativas inflacionadas; divisão treino/teste e validação cruzada aninhada dão estimativas não viesadas, mesmo com amostra pequena; a validação cruzada comum (a seleção usa tudo) é viesada, e a seleção de atributos feita antes da divisão pesa mais que o ajuste de parâmetros \[11]. O conjunto do piloto não deve voltar para o experimento principal \[5].
- **O *holdout* simples é frágil.** Fuhr o lista entre os erros: o resultado pode depender muito da divisão (cita um estudo em que o desempenho nas duas metades da coleção diferiu em 20%, que **não li**), e pede validação cruzada como mínimo; o conjunto de ajuste tem de ser disjunto do de teste, com três subconjuntos ou laço interno \[6].
- **Não há fração universal.** Para regressão linear, com p parâmetros, o ótimo é treino : teste = √p : 1, ou seja, fração de teste de 1/(√p+1): 0,50 com p=1, 0,41 com p=2, 0,33 com p=4, 0,25 com p=9. O critério é o erro quadrático da estimativa do erro de generalização, e a própria fonte diz que a regra de 80/20 não tem justificativa geral \[12].
- **Observações dependentes** violam o pressuposto dos testes \[13].

**Inferência**

- **\[Inf.] O critério de \[12] não é o nosso.** Ele minimiza o erro de prever o desempenho de um modelo com p coeficientes. Aqui o "treino" só fixa 2 a 4 escalares (limites de faixa, parâmetros do BM25), e o que interessa é a **potência da comparação confirmatória**. Por isso a fórmula aponta para uma fração de medição *menor* do que a que a potência pede. Fica como âncora formal de que 80/20 não é lei, não como regra.
- **\[Inf.] A fração pesa pouco no poder** (tabela do §6.1): de 25% a 40% de ajuste, a diferença mínima detectável sobe cerca de 1 ponto (pd 20%).
- **\[Inf.] Unidade de divisão = relatório de cotação (ou processo)**, não item. Itens do mesmo relatório compartilham a servidora, a época e o universo do PNCP, e o RF19 já trata candidatos do mesmo evento como não independentes. Dividir por item deixaria o mesmo relatório dos dois lados.
- **\[Inf.] Variáveis de estratificação**: só as observáveis **sem rodar nenhum método**: grupo de material/serviço, número de relevantes (1, 2, ≥3), tamanho de C(q) (tercis), UF e modalidade do relevante, comprimento da descrição. Não estratificar por "dificuldade para o BM25", porque isso exige ver o rótulo na medição.
- **\[Inf.] Congelamento**: gerar a partição com semente registrada, gravar a lista de identificadores e um resumo criptográfico **antes** de rodar qualquer método sobre itens rotulados, e deixar o arnês recusar-se a ler a medição se o resumo não bater.
- **\[Inf.] O BM25 recebe o mesmo orçamento de ajuste** (k1, b, tokenização) que os candidatos. Há literatura sobre linhas de base fracas que **não localizei** nesta busca; fica como pendência de leitura, sem nome nem ano (§11).

**Opções**

| Opção | Prós | Contras | Custo |
| --- | --- | --- | --- |
| A. *Holdout* único congelado (ajuste ≈ 40% / medição ≈ 60%) | Um valor de limiar fixo, como C11 e C15 pedem; teste não viesado \[11]; simples de declarar | Frágil à divisão \[6]; menos itens na medição | Baixo |
| B. Validação cruzada aninhada sobre os 231 | Usa todos os itens na medição \[11]; atende a \[6] | Limiares diferentes por dobra: o que se mede é o **procedimento**, não o valor que o sistema vai usar; foge de "fixar o limiar antes de medir" | Baixo em computação (os vetores se calculam uma vez); alto de explicação |
| C. *Holdout* repetido (muitas divisões aleatórias) | Mostra a dependência da divisão; responde a \[6] | Qual divisão é "a" medição? Sem uma registrada, volta o problema de escolher o resultado | Baixo |
| D. Ajuste fora do gabarito: calibrar as faixas com os julgamentos de comparabilidade da C5 e fixar o BM25 em valores padrão | Todos os 231 vão para a medição; as faixas são de **comparabilidade** e a C5 mede exatamente isso | Depende da servidora e do calendário da C5; menos itens para escolher finalista | Alto em tempo da servidora; depende da C5 |

**Recomendação: A como medição primária, B e C como robustez declarada, D se a C5 chegar a tempo.** Concretamente: ≈ 92 itens de ajuste e ≈ 139 de medição, por relatório, estratificado, congelado. A fração é um julgamento entre \[12] (mais ajuste) e a potência (mais medição); com 40% a diferença mínima detectável fica ≈ 0,5 ponto acima de 33%, e o ajuste tem o que precisa para estimar pd, escolher o finalista e fixar 2 a 4 parâmetros. **O ponto de apoio é limitar o que se ajusta no gabarito a p ≤ 4**: limites de faixa do finalista, k1 e b do BM25. Todo o resto vai com valor padrão declarado. Com B e C relatadas, quem ler \[6] vê que a conclusão não depende de uma divisão sorteada.

**O que mudaria a recomendação**

- A C5 entregar julgamentos de comparabilidade a tempo: calibrar as faixas ali (opção D) e baixar o ajuste para ≈ 25% (≈ 58 / 173 itens).
- Poucos relatórios (menos de \~20): a divisão por relatório fica desbalanceada; passar a estratificar por relatório em vez de sortear.
- O estudo de estabilidade (reamostrar o ajuste e ver quanto os limites oscilam) mostrar que 92 itens não estabilizam os limites: mais ajuste, ou menos parâmetros.
- A orientação exigir validação cruzada como critério principal: promover B e redefinir C15 como "fixar o procedimento".

---

### 6.4 Pergunta 4: o espaço de busca (corpus)

**Provado na fonte**

- **Viés de *pool*.** A avaliação por *pool* é enviesada contra sistemas que não contribuíram para ele. Em TREC GOV2 com 42 execuções, remover do *pool* as contribuições exclusivas de um grupo derruba a execução desse grupo em média 2,1 posições em P\@20 (até 12), e remover todas as execuções manuais derruba as manuais em média 6,4 posições (até 18), com τ de Kendall abaixo de 0,9 para todas as medidas. Uma medida desenhada para julgamentos incompletos, a bpref, erra no sentido contrário (superestima). Completar os julgamentos por um classificador reduziu o erro (τ de P\@20 de 0,828 para 0,951) \[7]. O método usual do TREC (união dos primeiros k = 20 de 12 sistemas) deixou de achar parte importante dos relevantes de uma coleção em que quase todos eram conhecidos \[15].
- ***Pools* rasos de um só tipo de sistema subestimam o outro tipo.** Com *pools* de profundidade 10 de sistemas tradicionais, a ordem dos sistemas neurais se correlaciona mal com a verdadeira: τ de Kendall de −0,12 (documentos) e 0,004 (passagens) para o MRR, e de 0,68 e 0,57 para o nDCG\@10 \[17]. Com *pools* profundos, diversos e de sistemas eficazes, uma coleção antiga avalia bem sistemas novos (τ de 0,9933 e 0,9991, 134 sistemas) \[16]. **O nosso gabarito é raso e de um só tipo**: cai no caso ruim.
- **Relevante escolhido por sistema existente** inverte 19,2% dos pares de sistemas (contra 3,2% ao acaso), e o sistema "parente" aparece como melhor \[15].
- **Amostrar negativos ao acaso quebra a métrica.** Métricas calculadas sobre uma amostra de itens são inconsistentes com a exata, **mesmo em expectativa**: o pior recomendador no exato pode aparecer como o melhor na amostra; encolhendo a amostra, todas as métricas convergem para a AUC; a conclusão é evitar amostragem, e, se for inevitável, corrigir (a correção custa variância) \[8].
- **O resultado denso × esparso depende do tamanho do índice.** Na mesma tarefa, um modelo denso treinado sem negativos difíceis vence o BM25 com índice de 10 mil a 1 milhão de entradas e perde com 8,8 milhões; os autores concluem que resultados de índice pequeno não se transferem para índice grande \[9].
- **Não sustentado**: vazamento temporal. Os trabalhos de recomendação que tratam disso (na fila) têm só o resumo visto; a janela *as-of* abaixo é, portanto, inferência apoiada na regra de validade temporal do próprio projeto.

**Inferência**

- **\[Inf.] O que "corpus" deve ser aqui.** O sistema nunca busca em todo o PNCP: aplica filtros obrigatórios (RF17: unidade, ordem de grandeza da quantidade, recorte geográfico, janela temporal; RF18: natureza) e só então rankeia. O corpus de avaliação é, por item, **C(q) = o que passa nesses filtros**, e deve ser **o mesmo para todos os métodos**; o filtro está fora da comparação, como já decidido ("filtro estruturado fica fora do vetor"). Isso faz a comparabilidade entre métodos valer por construção.
- **\[Inf.] Janela "a partir da data da pesquisa" (*as-of*).** A validade temporal é contada do início da pesquisa. Excluir candidatos publicados depois dessa data evita que um método seja premiado por achar preço que a servidora não poderia ter usado, e é a mesma lógica de reconstituição do RF30.
- **\[Inf.] Tetos e efeito do tamanho.** Reportar (a) o **teto do filtro** (fração de relevantes do gabarito que passam nos filtros; nenhum método passa de aí) e (b) Recall\@10 **por tercil de |C(q)|**. O segundo é uma curva análoga à do P1 e mostra o efeito de \[9] nos dados da própria pesquisa.
- **\[Inf.] O *pool* é protocolo de julgamento, não corpus.** Na C5, o *pool* de candidatos a julgar é a união dos primeiros k de todos os métodos mais o gabarito, embaralhado (\[7, 15, 17] mandam incluir sistemas de tipos diferentes). Esse conjunto julgado serve para **ampliar os relevantes** (um gabarito mais rico, relatado ao lado do original), não para restringir a recuperação.

**Opções**

| Opção | O que faz com o viés | Comparabilidade entre métodos | Prós | Contras | Custo |
| --- | --- | --- | --- | --- | --- |
| A. Corpus operacional inteiro C(q), janela *as-of*, igual para todos | Não elimina o viés do gabarito (relevantes não registrados contam como erro), mas não o agrava com um *pool* | Máxima: mesmo C(q) | Reproduz a produção; sem amostragem; mostra o efeito do tamanho \[9] | Relevantes não registrados inflam falsos negativos para todos, mais para quem acha o que o BM25 não acha | Médio: indexar o recorte e filtrar por consulta |
| B. *Pool* de documentos (união dos primeiros k dos métodos) como corpus | Viés contra quem não contribuiu e contra sistema novo \[7, 17]; o *pool* muda quando entra um método | Depende de quem entrou | Barato de julgar; é o padrão TREC | Re-rankear o próprio *pool* infla as métricas de topo; reuso frágil; o resultado vale só para o conjunto de métodos de hoje | Baixo |
| C. Corpus restrito à janela da norma e aos filtros, sem mais nada | É o caso A com os filtros mínimos | Máxima | Mais barato que A | Se for pequeno demais, favorece o denso \[9] | Baixo |
| D. Amostra aleatória de distratores | Inconsistente com a métrica exata, mesmo em expectativa \[8] | Boa, mas distorcida | Barato | Evitar; a literatura lida a desaconselha | Baixo |
| E. A como primário, mais C(q) alargado (sem janela, ou UF ampla) como sensibilidade, mais *pool* da C5 como julgamento | O alargado mostra a dependência do tamanho; o *pool* da C5 enriquece o gabarito | Mantida | Cobre as ameaças conhecidas | Mais análises | Médio |

**Recomendação: E, com A como corpus primário.** Motivo: o gabarito já está enviesado a favor do BM25 e não há como "consertar" isso escolhendo o corpus; o que o corpus pode fazer é não piorar (D e B piorariam, por razões de \[8] e \[7]) e deixar o efeito do tamanho visível (A e o alargado). Os relevantes que a C5 acrescentar entram como gabarito ampliado, relatado ao lado do original.

**O que mudaria a recomendação**

- A distribuição que chegar na quarta mostrar que os relevantes estão concentrados na mesma UF e nos mesmos meses do relatório: o C(q) é pequeno, o denso fica favorecido \[9], e o alargado deixa de ser sensibilidade e vira necessidade.
- Os relevantes espalhados por muitas UFs ou fora da janela: o filtro do RF17 corta relevantes do gabarito, e o teto do filtro cai; decidir se o filtro operacional muda ou se o gabarito é restringido ao que o filtro alcança (decisão relevante, do autor).
- A C5 não acontecer: nenhum julgamento cego, e o R1 fica só com o gabarito original, com a leitura de §6.1.

**O que cruzar na quarta**: fração dos relevantes que passa em cada filtro isolado e em todos juntos; distribuição de |C(q)|; idade do relevante na data da pesquisa; UF do relevante contra UF do órgão; modalidade; **número de relatórios e de itens por relatório**; número de relevantes por item.

---

## 7. Afirmações-chave e triangulação

| # | Afirmação | Fontes | Status | Grau |
| --- | --- | --- | --- | --- |
| 1 | Com \~50 a 100 consultas, *t* e permutação mantêm erro tipo I; *bootstrap-shift* é levemente liberal; Wilcoxon e sinal são pouco confiáveis para médias | \[1], \[2]; contestado por Parapar (só conclusões) | triangulado, contestado | B |
| 2 | Hipóteses e família de comparações têm de ser declaradas antes; sem correção, a taxa de erro tipo I explode (40–50% dos significativos, TREC, todos os pares) | \[4], \[6], \[3] | triangulado (o número 40–50% é fonte única) | B |
| 3 | Não rejeitar H₀ não prova empate; equivalência exige zona de indiferença declarada e muita amostra | \[3]; apoio parcial em \[5] | parcial | B |
| 4 | Piloto/ajuste tem de ser disjunto da medição; ajustar com os dados da medição infla | \[5], \[11], \[6] | triangulado | B |
| 5 | *Holdout* único é frágil à divisão, e validação aninhada ou divisão disjunta não é viesada | \[6] (cita estudo não lido), \[11] | parcial | C |
| 6 | A fração ótima de teste depende do número de parâmetros (√p : 1) | \[12] | fonte única (regressão linear, perda quadrática) | C |
| 7 | Relevantes escolhidos por sistema existente, ou *pools* rasos de um só tipo, distorcem a comparação; as medidas dos primeiros postos são das mais sensíveis | \[15], \[7], \[17]; limite em \[16] | triangulado | B |
| 8 | O resultado denso × esparso depende do tamanho do índice | \[9] | fonte única (uma tarefa, uma família de modelos) | C |
| 9 | Amostrar negativos ao acaso é inconsistente com a métrica exata | \[8] | fonte única (recomendação; o estudo adicional só no resumo) | B |
| 10 | Linha de base de entrada parcial e partição fácil/difícil revelam atalhos de um *benchmark* | \[10] | fonte única (outro domínio; analogia) | C |
| 11 | Limiar de ganho não substitui teste; a significância se degrada fora do domínio; observações dependentes violam o pressuposto | \[14], \[13] | parcial | B |
| 12 | Para a mesma verba, mais consultas rasas dão mais potência que poucas fundas | \[5] | fonte única | B |

Triangulados: 4 de 12 (0,33). **Cinco recomendações dependem de afirmação de fonte única ou de analogia** (itens 6, 8, 9, 10, 12); por isso estão marcadas como hipótese ou inferência e não como fato.

## 8. Alternativas consideradas e descartadas

| Alternativa | Por que não |
| --- | --- |
| Fixar um Recall\@10 absoluto "razoável" (por exemplo, 0,5) | Nenhuma fonte dá o número; ele depende do corpus e do gabarito \[9, 14] |
| Teste de hipótese com α = 0,05 sem margem (só "p < 0,05") | Aceita ganho irrelevante; não diz o que concluir quando falha \[3, 6] |
| Wilcoxon ou sinal como teste principal | Um estudo recomenda descontinuar \[1], outro encontra erro crescente com a amostra \[2]; um terceiro defende o contrário (parcial). Sem acordo, usar o teste que testa a média que se relata |
| Dividir por item | Itens do mesmo relatório dos dois lados; viola independência (RF19, \[13]) |
| Estratificar por dificuldade para o BM25 | Exige ver o rótulo na medição |
| Amostra aleatória de distratores | \[8] |
| *Pool* como corpus de recuperação | \[7, 17] |
| Preencher lacunas de julgamento por um modelo | Muda o que é medido (decisão relevante); só resumo lido (fila) |

## 9. Limitações conhecidas

- **Transposição de TREC.** As conclusões sobre testes estatísticos vêm de coleções com 50 a 250 consultas e sistemas de recuperação de documentos; aqui são \~230 itens, descrição curta, poucos relevantes. As conclusões podem não transferir.
- **pd e σ são supostos.** As cifras de poder dependem de pd (discordância entre métodos), que só se conhece depois de rodar. Não há dado de desvio de erro de estimativa de preço da servidora (σ̂ virá da C5).
- **Sem fonte para níveis de ruído** do R2 e para o k ideal.
- **Fonte de outro domínio**: \[8], \[9], \[10] e \[11] são de recomendação, de recuperação densa em MS MARCO, de inferência textual e de aprendizado de máquina clínico. Servem como analogia, não como prova para este caso.
- **Leitura de \[8] e \[13], \[14] parcial** nos pontos descritos no §5; \[12] é preprint.
- **Cobertura de busca limitada** (3 resultados por busca). Um trabalho que contradiga alguma afirmação pode estar fora do que vi.
- **Os 40 itens sem relevante no PNCP** ficam fora da medição; R1 vale para os itens com preço reencontrável (85%), e isso precisa constar como escopo.
- **Dois pontos do R2 e do corpus dependem de dados que chegam na quarta ou da C5.**

## 10. Decisão sugerida (não vinculante)

Adotar, **antes de rodar qualquer método no conjunto de medição**, um registro de avaliação com: contraste confirmatório único (finalista contra BM25 ajustado); métrica e corte (Recall\@10); critério de aceitação relativo com margem; regra de empate; partição congelada por relatório; corpus C(q) igual para todos com janela *as-of*; curva do R2 com níveis calibrados, linha de base só-preço e partição fácil/difícil. Todo o resto é descritivo e rotulado como tal.

**O que o autor precisa decidir** (cada item é decisão relevante pelo protocolo do projeto):

| Decisão | Opções | Aguarda |
| --- | --- | --- |
| Δmin (margem mínima de importância prática) | 0 / 0,05 / outra | A C6 (quanto a servidora tolera) |
| M (margem de equivalência) | ≥ 0,08, ou abrir mão de declarar empate | Nada |
| k confirmatório | 10 (proposto) ou outro | A C6 |
| Piso absoluto | não ter / ancorar na C6 | A C6 |
| Fração de ajuste | 25–40% (proposto ≈ 40%) | Contagem de relatórios |
| Níveis de σ do R2 | calibrar em σ̂ da C5 / grade fixa | A C5 |
| Filtros que definem C(q) e janela | os do RF17 / alargar | A distribuição da quarta |

## 11. Seguimentos

- [ ] Receber na quarta: relatórios e itens por relatório, relevantes por item, passagem nos filtros (§6.4).
- [ ] Com o arnês: calcular pd e a diferença mínima detectável **só no conjunto de ajuste**, antes de congelar o k.
- [ ] Implementar a linha de base só-preço e a partição fácil/difícil no arnês de R2.
- [ ] Implementar reamostragem por relatório no arnês e o p-valor por permutação como conferência.
- [ ] Gravar semente e resumo criptográfico da partição antes da primeira execução sobre itens rotulados.
- [ ] Ler por inteiro, para poder citar: Sakai (2016), Webber e Park (2009), Ji et al. (2023), a literatura sobre linhas de base fracas **(a localizar)** e os dois trabalhos lidos em parte.
- [ ] Conferir páginas das versões publicadas de \[9], \[10], \[12].
- [ ] Se o autor decidir: nota em `TCC/decisões/` com Δmin, M, k, fração e filtros; atualizar a C11 e a C15 no backlog.

## 12. Registro de autocrítica

Não houve revisão adversarial independente. Fraquezas que eu mesmo vejo:

| # | Classe | Fraqueza | Ação |
| --- | --- | --- | --- |
| 1 | Deve corrigir | Cinco recomendações apoiam-se em fonte única ou analogia (itens 6, 8, 9, 10, 12 do §7) | Rotuladas como hipótese; reler antes da reunião |
| 2 | Deve corrigir | A fração de ajuste tem apoio formal contrário (Joseph aponta mais ajuste); defendi mais medição por potência, que é critério meu | Declarado em §6.3; a decisão é do autor |
| 3 | Sugestão | Parapar e Otero lidos só nas conclusões; a divergência sobre o teste pode pesar mais do que mostrei | Deixar nota, ler antes de citar |
| 4 | Sugestão | O resultado de \[7] vem de uma só coleção (GOV2, 42 execuções) | Mantido como evidência qualitativa de direção, não de tamanho |
| 5 | Sugestão | A margem Δmin = 0,05 tem só o exemplo de Fuhr como apoio | Marcada como ponto de partida |

## 13. Referências

As referências numeradas estão no §5, com metadado conferido no PDF (ou a pendência dita). Nada em "fila de leitura" é citável.

## Registro de versão

| Data | Versão | Mudança | Autor |
| --- | --- | --- | --- |
| 2026-11-24 | 0.1 | Primeira versão, para decisão do autor | Rafael Nobre de Souza |
