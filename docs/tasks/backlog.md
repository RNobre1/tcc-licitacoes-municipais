# Backlog

Fonte única do que falta. Atualizado a cada sessão de trabalho.

As pendências **não** são repetidas em `docs/projeto.md` nem na especificação de
requisitos: os dois apontam para cá. Lista duplicada envelhece em um dos lados e
ninguém descobre qual.

Última revisão: 27/10/2026, depois da reunião de 24/10.

## Como ler

Cada item diz **quem resolve**, porque isso determina o que pode andar em
paralelo e o que está bloqueado em outra pessoa.

| Dono | Significado |
|---|---|
| Autor | Trabalho técnico, sem dependência externa |
| Fonte de domínio | Depende da servidora do setor de licitações |
| Orientação | Depende da orientadora |
| Instituição | Depende de secretaria, colegiado ou calendário |
| Externo | Depende de terceiro sem compromisso conosco |

Estado: `aberto`, `em andamento`, `bloqueado`, `fechado`.

---

## Caminho crítico

O que destrava mais coisa adiante, em ordem.

| # | O que | Dono | Estado | Destrava |
|---|---|---|---|---|
| C1 | Medir volume, ritmo de publicação e formato das descrições da base pública | Autor | aberto | Decisão A3, e dimensiona o índice |
| C2 | Montar o conjunto de avaliação a partir dos relatórios de cotação já recebidos | Autor | aberto | Decisão A2, que é a que mais afeta o resultado |
| C3 | Levantar candidatos a modelo de representação e rodar a bateria contra C2 | Autor | aberto | Fecha A2 |
| C4 | ~~Escrever a seção de resultados esperados~~ | Autor | **fechado** | R1 a R8 escritos, um indicador cada; os limiares ficam em C11 |
| C5 | Sessão de julgamento às cegas com a fonte de domínio | Fonte de domínio | aberto | **Condição** para a medição ter conclusão nos dois sentidos |
| C6 | **Escrever o roteiro da sessão de observação do banco de preços** | Autor | aberto | É o pré-requisito de C5, e precisa existir antes de marcar a sessão |
| C7 | ~~Decidir a classificação da pesquisa~~ | Autor | **fechado 15/10** | DSR adotada. Abre C10 a C13 |
| C10 | ~~Escrever a subseção de classificação da pesquisa~~ | Autor | **fechado 15/10** | Classificação, ciclos, posicionamento e contribuição escritos |
| C11 | **Fixar limiar de aceitação de cada resultado esperado, antes de medir** | Autor | aberto | Exigência da classificação adotada; muda a ordem de trabalho |
| C15 | Fixar os limites de faixa de comparabilidade do RF23, hoje provisórios (0,80 e 0,60), num subconjunto de ajuste e antes de medir | Autor | aberto | Parte de C11: limite escolhido olhando o resultado invalida a medição |
| C16 | Explicar no texto a decisão do RF23 e incorporar as emendas ao protocolo. Na arquitetura: a ordenação por faixa, a proximidade pelo logaritmo da razão e por que não um escore único. Na metodologia: P1, o R2 como curva; P2, o preço esperado antes dos candidatos na C5; P3, o preço visível ou oculto sorteado por item. **A justificativa é o que sustenta a escolha diante da orientação e da banca**, então cada afirmação aponta a fonte ou declara que é inferência | Autor | aberto | Texto e roteiro de C6. Decidido em 28/10, e a orientação é informada em 07/11 |
| C12 | ~~Declarar o artefato que é a contribuição e o tipo dela~~ | Autor | **fechado 15/10** | Dois níveis declarados; o protocolo de avaliação é a contribuição principal |
| C13 | ~~Declarar a classe de problemas~~ | Autor | **fechado 15/10** | Escrita na metodologia |
| C14 | Conferir a política de declaração de ferramenta de geração em cada veículo | Autor | aberto | Obrigação do veículo; precisa ser verificada antes de submeter |
| C8 | ~~Modelar o processo de licitação em BPMN~~ | Autor | **fechado 18/10** | Raias verticais, página retrato, desenho em TikZ gerado do modelo; geometria e tamanho verificados por teste |
| C9 | ~~Conferir o prazo do simpósio de sistemas de informação~~ | Autor | **fechado 14/10** | Não houve prorrogação; apareceu a trilha de indústria, com prazo em 11/12/2026 |

Sobre C2: foi confirmado em 06/10/2026 que o gabarito pode ser montado do
material já entregue. Os relatórios de cotação trazem, por item, a descrição do
que foi pedido e as descrições dos preços escolhidos com procedência. Medido:
271 itens no total, 231 deles com ao menos um preço reencontrável na base
pública — 85%. **A antiga pendência "planilha de entrada de cotações encerradas"
deixou de existir**, e com ela a afirmação de que sem esse par a avaliação não
existiria.

### Sobre C6: o roteiro que ainda não existe

A sessão de C5 não é entrevista, é **observação de uso** com uma tarefa de
julgamento ao fim. São dois momentos distintos, e o roteiro precisa separá-los.

**Primeiro momento — observar.** Ela abre o banco de preços e cota alguns itens
enquanto narra o que está fazendo. O que se registra é o que hoje não existe em
documento nenhum: que termo ela digitou, quantos candidatos voltaram, quais ela
olhou, **quais descartou e por quê**, e em que ordem aplicou os filtros. O
registro do descarte é o que falta no gabarito atual, e é o produto principal.

**Segundo momento — julgar às cegas.** Apresentar a ela uma lista de candidatos
para alguns itens, misturando resultados de métodos diferentes, embaralhados e
sem indicar a origem de cada um, e pedir que diga quais aceitaria. É o que
corrige o viés descrito em C5 — e precisa ser cego, senão repete o viés com o
sinal trocado.

O que o roteiro precisa resolver antes de ser escrito:

| Questão | Por quê |
|---|---|
| Quantos itens cabem na sessão | Observação é lenta; o número realista define o tamanho da amostra |
| Como registrar sem atrapalhar | Gravar tela, anotar, ou as duas. Interromper a cada descarte muda o comportamento observado |
| Que itens escolher | Precisam cobrir o fácil e o difícil — o item de consumo cotidiano e o de dezoito atributos técnicos |
| Como formular a pergunta do descarte | "Por que não esse?" sugere que havia razão. Pergunta aberta descobre quando não havia |
| De onde vêm os candidatos do segundo momento | Antes da bateria rodar, só há a busca por palavra. Pode ser necessário dividir em duas sessões |

Observação sobre a última linha, que é a que mais pesa: o segundo momento só tem
sentido completo depois que houver pelo menos dois métodos a comparar. O primeiro
momento pode acontecer **agora** e já entrega o registro dos descartes.

### Sobre C5: por que virou condição, e não complemento

Levantado em 06/10/2026, antes de qualquer medição.

Os preços que formam o gabarito foram escolhidos pela servidora **dentro de uma
ferramenta que busca por palavra**. Os relevantes anotados são, por construção,
os que uma busca por palavra alcança. Um método por significado que encontre
item comparável descrito com outras palavras será contado como erro.

| Desfecho na medição | Leitura permitida |
|---|---|
| Busca por significado ganha | Resultado conservador — ganhou em desvantagem |
| Empata ou perde | **Não refuta.** Não se distingue "é pior" de "achou comparáveis que o gabarito não registra" |
| Dois modelos diferem por pouco | Não se lê: com poucos relevantes por consulta, só diferença grande sobrevive |

**Forma que a sessão precisa ter:** reunir os primeiros resultados de todos os
métodos comparados, inclusive a busca por palavra; embaralhar; pedir o julgamento
sem indicar a origem. Julgar os resultados de um método só repetiria o viés com
o sinal trocado.

Decorre daí mais quatro exigências de desenho: busca por palavra é linha de base
obrigatória, sabendo-se que parte em vantagem; a lista curta que ela marca antes
de filtrar deve ser guardada, porque cada relevante a mais estabiliza a
comparação; o teste é pareado sobre os itens, com intervalo, declarando empate
quando for empate; e qualquer limiar é ajustado em subconjunto separado daquele
em que se mede.

~~A avaliação em duas condições, com e sem o preço esperado, não é afetada: ela
compara cada método consigo mesmo.~~ **Corrigido em 28/10/2026.** Isso vale para o
viés da busca por palavra, mas não para o viés de **seleção por preço**. O gabarito
foi montado por quem descarta pelo preço antes de ler a descrição, então o
candidato perto do preço dela está super-representado, e a condição com
estimativa o favorece. As emendas P1, P2 e P3, adotadas na decisão de ordenação
do RF23 (`TCC/decisões/2026-10-28-ordenacao-rf23.md`), tratam disso. A
explicação do viés é inferência, e é testável.

### Sobre C7, C8 e C9: o que a reunião de 09/10/2026 mudou

A orientação leu o texto e não pediu alteração nele. O foco sai da redação e vai
para três coisas.

**C7 — classificação da pesquisa.** O texto não declara a classificação, e a
orientação sugeriu Design Science Research, com estudo de caso como alternativa
mais simples. A razão dada: o trabalho gera um artefato para intervir num
problema real, e DSR descreve exatamente isso; além disso, dá mais força para
aceitação em evento.

Antes de adotar, é preciso saber **o que DSR cobra**: que seções, que rigor de
avaliação, que forma de relatar a contribuição. Adotar uma metodologia é assumir
as exigências dela, e o custo precisa ser conhecido antes da escolha.

**C8 — BPMN.** O argumento da orientação é de público: administração pública e
governo digital falam em "processos", e o diagrama do processo de compras
valoriza o artigo nos dois destinos. A ferramenta indicada foi o Bizagi; o
diagrama precisa ser versionável, então o formato de saída importa.

**C9 — divergência de prazo, fechada em 14/10/2026.** Não houve prorrogação: a
trilha principal venceu em 30/09, com prazo marcado como rígido na própria
chamada. O "até fevereiro" lido na reunião vem do resumo da página inicial, que
diverge da chamada da trilha de novas ideias — ali 22/02/2027 é a **notificação**,
e o prazo de arquivos é 18/12/2026. Essa trilha também exclui graduação em
andamento.

Em compensação apareceu a **trilha de indústria e inovação**, que não estava no
levantamento: submissão em **11/12/2026**, texto de duas a quatro páginas sobre
experiência prática, com estudantes de graduação no público declarado. É o único
formato aberto do evento que acolhe o estágio atual.

**A decisão não é só de prazo.** Pela própria descrição, aquela trilha é vitrine
de experiência e não de contribuição científica — o oposto do que a orientação
recomendou buscar, com o caso concreto de um trabalho recusado por apresentar
sistema. Levar a ela, junto da pergunta sobre o estrato valer para anais
estendidos, que é a mesma dúvida do workshop do simpósio de banco de dados.

### A lacuna da tabela de verificação

Apontada na mesma reunião, e distinta das três acima porque é conserto de texto,
não trabalho novo.

A pergunta de pesquisa promete reduzir esforço sem comprometer conformidade, e o
objetivo específico 5 fala em esforço de triagem, conformidade e usabilidade. A
tabela de verificação **não mede nenhum dos três diretamente** — mede
recuperação, estrutura do documento, valor estimado, desempenho, esforço
residual e trilha.

O argumento de que a melhora é implícita não se sustenta num texto avaliado:
implícito não é medido. Conserta-se acrescentando linhas à tabela.

### Contribuição científica, e por que ela precisa ficar explícita

A orientação foi enfática: evento científico recusa trabalho que apresenta
sistema. Citou um TCC recusado por isso, com os pareceristas perguntando qual
era a contribuição científica.

As três candidatas deste trabalho, nenhuma dependente de o sistema existir:

| Candidata | Por que é científica |
|---|---|
| O viés do gabarito e o protocolo de julgamento às cegas que o corrige | Achado metodológico sobre avaliação de recuperação, não implementação |
| Recuperação sob filtro restritivo em descrição curta e ruidosa | Mediana de seis palavras sobre doze milhões de itens |
| Avaliação em duas condições, com e sem a âncora de preço | Separa compreender o item de já conhecer o preço |

---

## Texto

| O que | Dono | Estado |
|---|---|---|
| ~~Seção de resultados esperados~~ | Autor | fechado — R1 a R8; falta o instrumento de usabilidade |
| Trabalhos relacionados: escrever o quadro com quatro referências citadas | Autor | em andamento |
| ~~Figuras dos diagramas~~ | Autor | fechado — exportadas e guardadas por teste de frescor |
| Reduzir a subseção da pilha tecnológica a uma declaração: a orientação dispensou justificar a linguagem (24/10). Recupera folga no alvo da SBC, hoje em 25 de 25 | Autor | aberto |
| Diagrama geral de casos de uso no texto; os demais por link ao repositório (orientação, 24/10) | Autor | aberto — depende de D1 |
| Resultados no TCC II com teste de aceitação com usuário e estatística descritiva (orientação, 24/10) | Autor | TCC II |
| Fonte publicada para a afirmação sobre municípios de pequeno porte | Autor | bloqueado em pesquisa |
| Reescrever "domínio pouco explorado" como observação até o quadro fechar | Autor | aberto |
| Organização do trabalho, na introdução — escrever por último | Autor | aberto |
| Resumo, palavras-chave e versão em inglês | Autor | aberto |
| Protocolo da medição de persistência da iniciação científica, em detalhe | Autor | aberto |
| Referência primária do modelo de arquitetura em níveis, antes de citá-lo | Autor | aberto |

### Ritmo de citação, decidido em 06/10/2026

A bibliografia tem catorze entradas; o texto cita duas. O `biblatex` só imprime
o que é citado, então a base pode crescer sem inflar a lista de referências.

A decisão é citar **quatro** nesta semana, e crescer semanalmente. O motivo é
que cada referência citada precisa ser defensável diante da banca, e saltar de
três para catorze de uma vez não é sustentável — nem honesto quanto ao que foi
de fato lido no período.

---

## Desenvolvimento

Aberto pela reunião de 24/10, quando a orientação deu a metodologia por
concluída. Cada item aqui é **o quê**; a ordem e as datas são do plano do ciclo,
não deste arquivo.

| # | O que | Dono | Estado |
|---|---|---|---|
| D1 | Diagrama geral de casos de uso, com cada caso ligado aos requisitos que cobre | Autor | aberto |
| D2 | Documentar cada caso de uso no repositório **quando ele for implementado**, não antes nem depois | Autor | permanente |
| D3 | Protótipo navegável das telas principais, com dados fictícios e layout pronto, antes do modelo de dados | Autor | aberto |
| D4 | Ambiente local: banco relacional e banco vetorial em contêiner, com a aplicação apontando para eles | Autor | aberto |
| D5 | Conferir que os modelos `.bpmn` abrem na ferramenta indicada pela orientação. Foi afirmado na reunião e não testado: ela não roda no sistema da máquina de trabalho, e raia vertical é o recurso menos uniforme entre editores | Autor | aberto — exige outra máquina |
| D6 | Repositório acessível na entrega: a orientação conta com o link para código e casos de uso | Autor | fechado em 28/10 — repositório público por decisão do autor, depois da auditoria do histórico e da correção do `code/README.md`, conferida num clone novo |
| D7 | Fuso de referência da data de uma pesquisa de preços. O sistema guarda o instante em UTC, mas "a data em que a pesquisa foi realizada", que a RN08 exige reproduzir, depende do fuso em que a data é lida. É **decisão relevante**, porque afeta a trilha de auditoria. Levantada na revisão do dia 03 | Autor | aberto — decidir ao implementar a trilha, pelo protocolo de decisões relevantes |
| D8 | A integração contínua roda só a suíte do texto. A de `code/` precisa entrar como portão obrigatório. Até 28/10 ela não rodava nada: o workflow disparava em `main`, e a branch do repositório é `master` | Autor | aberto — fase 6 do ciclo de desenvolvimento. O disparo foi corrigido em 28/10 |
| D9 | Endurecimento para implantação: `check --deploy` aponta envio de e-mail, HSTS, SSL e cookies, e não há `STATIC_ROOT`, de modo que os arquivos estáticos só são servidos pelo servidor de desenvolvimento. Precisa de dono **antes** de qualquer implantação, nunca depois | Autor | aberto — sem implantação prevista neste ciclo |
| D10 | Sessão do protótipo em cookie assinado: as decisões de triagem ficam no navegador, assinadas mas **não cifradas**. Serve para dado fictício; antes de qualquer dado real, voltar para sessão no banco, que chega no dia 07 | Autor | aberto — revisar quando o PostgreSQL entrar |
| D11 | Conversão de unidade na proximidade de valor do RF23. O protótipo compara a unidade do candidato com a do item por igualdade exata, e unidade diferente deixa a proximidade indefinida. A nota da decisão fala em unidade que "não converte", mas não define conversão: os dados de demonstração só têm pares sem fator, como pacote e unidade. É decisão relevante, porque muda quais candidatos têm proximidade e, com isso, a ordem que o R1 e o R2 medem | Autor | aberto — aguarda os dados reais, a partir do dia 07, para ver que pares de unidade aparecem e se há fator na descrição |
| D12 | Formato do preço esperado digitado na triagem. Hoje vírgula ou ponto são separador decimal, e qualquer outra forma conta como sem preço, com aviso na tela. Um preço com separador de milhar, como `1.234,50`, é ignorado, e `1.500` vira 1,5 para o sistema e 1500 para quem digitou. É decisão relevante se a servidora digitar o preço esperado no sistema durante a sessão C5, porque um erro de leitura muda a condição "com estimativa" do R2 | Autor | aberto — aguarda o roteiro da C5 (emenda P2), que define como o preço esperado é pedido e registrado |

**Convenção de citação daqui em diante**, fixada em 24/10: biblioteca usada é
mencionada no texto com link para a documentação técnica dela. Não exige a
leitura integral que vale para artigo — é referência de uso, não de argumento.

---

## Sistema

| # | O que | Dono | Estado |
|---|---|---|---|
| A1 | ~~Linguagem, arcabouço e banco relacional~~ | Autor | **fechado 18/10** — Python, Django, HTMX e PostgreSQL |
| A2 | Modelo de representação das descrições | Autor | aberto — depende de C2 e C3 |
| A3 | Estratégia de atualização da ingestão | Autor | aberto — depende de C1 |
| A4 | Onde reside a geração dos documentos | Autor | aberto |
| A5 | ~~Mecanismo concreto de autenticação~~ | Autor | **fechado 18/10** — o do próprio arcabouço, com o perfil único de 22/09 |
| A6 | Proporção entre tipos de processo no setor | Fonte de domínio | aberto — limita o alcance do que se pode afirmar |

**A1 e A5, fechadas em 18/10.** Nota em `TCC/decisões/2026-10-18-pilha-tecnologica.md`.
A escolha não foi precedida de pesquisa comparativa, e isso é deliberado: o que a
metodologia cobra é o registro das alternativas descartadas naquilo que **muda o
resultado medido**. Linguagem e arcabouço não mudam — o mesmo experimento daria o
mesmo número em qualquer um deles. Só o banco relacional tem razão técnica ligada
ao problema, e ela está declarada no texto. A5 cai junto porque autenticação
passa a ser recurso do arcabouço.

### A2 e A3 não bloqueiam o TCC I

Para a qualificação basta o desenho e o método de decisão declarado, que a seção
de arquitetura já faz ao registrar cada decisão como aberta e dizer o que ela
aguarda. Fechar A2 com número é resultado de TCC II.

---

## Questões em aberto que não são tarefas

Decisões que alguém precisa tomar, e que mudam desenho.

### Q1 — Que sentido de "reproduzir uma pesquisa passada" o trabalho entrega?

Há dois, e custam coisas diferentes:

1. **Guardar o resultado.** Salvar o que foi apresentado — candidatos, ordem,
   dados do momento, escolhas. Reconstituir é abrir o registro. Barato.
2. **Reexecutar a consulta sobre o estado antigo do índice.** Exige o índice
   versionado no tempo. Caro, e a literatura resolve isso para busca por palavra,
   declarando a busca por significado como trabalho futuro.

**DECIDIDO em 06/10/2026: forma 1**, guardar o resultado. Decisão do autor, com
dois motivos. O que o órgão de controle cobra — que o preço existia, veio de onde
se diz e estava válido — é inteiramente respondido por ela. E a orientação
recomendou não ampliar escopo, por o trabalho já ser complexo.

A forma 2 fica como **trabalho futuro**, declarada no texto como limite conhecido
do que foi entregue. Não é omissão: a literatura resolve a reexecução no tempo
apenas para busca por palavra, e declara a busca por significado como problema
em aberto. Dizer isso no texto é mais forte que silenciar.

### Q2 — Critério de avaliação da recuperação

Um trabalho correlato brasileiro avalia pela proximidade ao preço homologado.
A prática observada preserva margem acima dele de propósito, porque o valor
estimado é teto. Adotar aquele critério mediria o sistema contra um alvo que o
domínio diz estar errado. **Decidido: não adotar**, e explicar a diferença no
texto.

---

## Dependências externas

| O que | Dono | Estado | Observação |
|---|---|---|---|
| Titulação da orientadora, para a folha de rosto | Orientação | aberto | Pedido mais de uma vez |
| Parecer sobre o texto atualizado, em especial a classificação da pesquisa | Orientação | aberto | Prometido até 07/11 |
| Informar a orientação da decisão de ordenação do RF23 e das emendas P1 a P3 ao protocolo de avaliação | Autor | aberto | Reunião de 07/11. O autor decidiu e informa, em vez de pedir aval antes |
| Texto da natureza do trabalho conforme o colegiado | Instituição | aberto | |
| **Datas do calendário acadêmico de 2026.2 e 2027.1** | Instituição | aberto | Trava o cronograma do texto **e decide quais prazos de publicação servem**: para substituir o TCC, o aceite precisa sair antes da defesa |
| Modelo de TCC usado por orientando anterior | Orientação | em andamento | Pedido de novo em 06/10. Até chegar, segue o alvo atual |
| Designação exata do órgão de controle externo competente | Autor | aberto | Conferir em fonte oficial. Nunca preencher de memória |
| Texto da instrução normativa que ampara a pesquisa de preços | Autor | aberto | Identificada com evidência primária; o texto não foi lido na fonte |
| Acesso ao artigo correlato de acesso fechado | Externo | bloqueado | Pedido em 24/08, sem resposta. A orientação autorizou usar o resumo, declarando a limitação |
| Modelo em branco de estudo técnico e termo de referência, com marcação do que é fixo | Fonte de domínio | aberto | Incluir o cabeçalho e o brasão em uso: a geração vai usar layout pronto com esses campos (orientação, 24/10) |
| Documento de formalização de demanda ainda não visto em alguma modalidade | Fonte de domínio | aberto | |

---

## Pesquisa

| O que | Dono | Estado |
|---|---|---|
| Quadro dos sistemas existentes que não são literatura | Autor | em andamento |
| Teses e dissertações brasileiras | Autor | em andamento |
| Anais de eventos brasileiros não varridos | Autor | em andamento |
| Ler o artigo de modelo de linguagem para licitação em português | Autor | em andamento — pesa em A2 |
| Oito entradas da bibliografia com verificação pendente | Autor | aberto — cada uma declara o campo que falta |
| Cinco perguntas sobre veículos de publicação | Orientação | aberto — decidem mais que as tabelas de prazo |

---

## Fechados recentemente

Mantidos por um ciclo, para que não voltem por engano.

| O que | Quando | Como fechou |
|---|---|---|
| Versão para celular | 24/10/2026 | Não: só interface web. O setor não usaria |
| Justificar a escolha da linguagem no texto | 24/10/2026 | Não é preciso, segundo a orientação |
| Planilha de entrada de cotações encerradas | 06/10/2026 | Deixou de ser necessária: o gabarito está nos relatórios já recebidos |
| Perfil de usuário: um ou dois | 22/09/2026 | Um só, com autenticação mantida. Decisão registrada |
| O município usa catálogo federal de materiais? | 21/09/2026 | Não |
| Escolha entre persistência vetorial dedicada e extensão do relacional | setembro/2026 | Dedicada, por medição própria sob filtro restritivo |
