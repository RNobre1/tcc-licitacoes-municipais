# Backlog

Fonte única do que falta. Atualizado a cada sessão de trabalho.

As pendências **não** são repetidas em `docs/projeto.md` nem na especificação de
requisitos: os dois apontam para cá. Lista duplicada envelhece em um dos lados e
ninguém descobre qual.

Última revisão: 06/10/2026.

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
| C4 | Escrever a seção de resultados esperados | Autor | aberto | Último vazio do texto |
| C5 | Sessão de tela com a fonte de domínio, registrando candidatos **descartados** | Fonte de domínio | aberto | Permite medir precisão, não só recuperação |

Sobre C2: foi confirmado em 06/10/2026 que o gabarito pode ser montado do
material já entregue. Os relatórios de cotação trazem, por item, a descrição do
que foi pedido e as descrições dos preços escolhidos com procedência. Medido:
271 itens no total, 231 deles com ao menos um preço reencontrável na base
pública — 85%. **A antiga pendência "planilha de entrada de cotações encerradas"
deixou de existir**, e com ela a afirmação de que sem esse par a avaliação não
existiria.

---

## Texto

| O que | Dono | Estado |
|---|---|---|
| Seção de resultados esperados — única ainda vazia | Autor | aberto |
| Trabalhos relacionados: escrever o quadro com quatro referências citadas | Autor | em andamento |
| Figuras dos diagramas: exportar as três páginas do editor para `texto/tcc1/figuras/` | Autor | aberto |
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

## Sistema

| # | O que | Dono | Estado |
|---|---|---|---|
| A1 | Linguagem e arcabouço | Autor | aberto — não afeta os níveis desenhados |
| A2 | Modelo de representação das descrições | Autor | aberto — depende de C2 e C3 |
| A3 | Estratégia de atualização da ingestão | Autor | aberto — depende de C1 |
| A4 | Onde reside a geração dos documentos | Autor | aberto |
| A5 | Mecanismo concreto de autenticação | Autor | aberto |
| A6 | Proporção entre tipos de processo no setor | Fonte de domínio | aberto — limita o alcance do que se pode afirmar |

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

**Posição atual: forma 1**, e os requisitos já apontam para ela. O que o órgão de
controle cobra — que o preço existia, veio de onde se diz e estava válido — é
inteiramente respondido por ela.

A forma 2 é pergunta de pesquisa, não de conformidade. Fica registrada como
desdobramento possível, e como limite conhecido do que foi entregue.

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
| Texto da natureza do trabalho conforme o colegiado | Instituição | aberto | |
| Datas do calendário acadêmico de 2026.2 e 2027.1 | Instituição | aberto | Trava o cronograma do texto |
| Modelo de TCC usado por orientando anterior | Orientação | em andamento | Pedido de novo em 06/10. Até chegar, segue o alvo atual |
| Designação exata do órgão de controle externo competente | Autor | aberto | Conferir em fonte oficial. Nunca preencher de memória |
| Texto da instrução normativa que ampara a pesquisa de preços | Autor | aberto | Identificada com evidência primária; o texto não foi lido na fonte |
| Acesso ao artigo correlato de acesso fechado | Externo | bloqueado | Pedido em 24/08, sem resposta. A orientação autorizou usar o resumo, declarando a limitação |
| Modelo em branco de estudo técnico e termo de referência, com marcação do que é fixo | Fonte de domínio | aberto | |
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
| Planilha de entrada de cotações encerradas | 06/10/2026 | Deixou de ser necessária: o gabarito está nos relatórios já recebidos |
| Perfil de usuário: um ou dois | 22/09/2026 | Um só, com autenticação mantida. Decisão registrada |
| O município usa catálogo federal de materiais? | 21/09/2026 | Não |
| Escolha entre persistência vetorial dedicada e extensão do relacional | setembro/2026 | Dedicada, por medição própria sob filtro restritivo |
