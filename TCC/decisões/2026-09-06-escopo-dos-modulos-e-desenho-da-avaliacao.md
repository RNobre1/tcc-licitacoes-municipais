---
tipo: decisão
data: 2026-09-06
status: aceita
tags: [escopo, arquitetura, avaliação, pesquisa-de-preços, etp, tr]
---

# Escopo dos dois módulos e desenho da avaliação

Três decisões tomadas juntas, no mesmo dia e pelo mesmo motivo: o levantamento
de requisitos derrubou premissas dos dois módulos ao mesmo tempo. Registradas
numa nota só porque separá-las esconderia que dependem umas das outras.

## Contexto

A entrevista de levantamento de 06/09/2026 trouxe três achados que a proposta
original não previa:

1. **O município já paga um banco de preços comercial** que agrega PNCP, Painel
   de Preços, Compras Governamentais e lojas da internet, e que já faz coleta,
   cálculo estatístico, memória de cálculo, mapa comparativo, registro de
   procedência por preço e exportação. Construir isso de novo não acrescenta
   nada.
2. **O gargalo medido não é coletar preço, é decidir se o preço é comparável.**
   A busca desses sistemas é por palavra: cotando maço de alface veio sanduíche
   natural, cotando urna funerária vieram serviços funerários, cotando trator de
   esteira vieram locações cobradas por hora. Quem separa é a pessoa, item por
   item — dois dias para cem itens, mais de uma semana para mil.
3. **O conteúdo mais valioso do ETP não está em API nenhuma.** A fonte foi
   explícita sobre o que precisa estar certo: consumo histórico, atas e contratos
   anteriores que justifiquem a quantidade, e as peculiaridades logísticas do
   município. E foi igualmente explícita sobre o que a faria não confiar: texto
   genérico e base legal citada de forma imprecisa.

## Decisão 1 — Módulo de pesquisa de preços

### Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — Pipeline próprio sobre a API do PNCP, posicionado para município sem banco comercial | Artefato autocontido, avaliável de ponta a ponta; atende o município que não paga ferramenta, que é a maioria das prefeituras pequenas; permite trilha de auditoria consultável, que nenhuma das ferramentas em uso oferece | Maior esforço de implementação; cobre menos fontes que o agregador comercial |
| B — Apenas a camada de triagem semântica, consumindo a planilha e devolvendo candidatos ranqueados | Escopo mínimo, ataque cirúrgico ao gargalo medido | Depende de um sistema pago continuar em uso; o mapa de cotação, que está na proposta, sai do entregável; não há artefato completo para avaliar |
| C — Manter a proposta original sem reposicionar | Nenhuma mudança de documentação | A banca perguntaria por que reconstruir algo que existe, funciona e está pago, e a resposta seria improvisada |

### Decisão

**Escolhida: A.** Pipeline próprio sobre a API do PNCP, com a correspondência
semântica de itens e a trilha de auditoria consultável como diferenciais
declarados — não a coleta.

### Justificativa

O reposicionamento não é retórico: muda quem é o usuário. A ferramenta comercial
é assinatura paga, e um município que não a tem começa de uma situação pior que
a descrita na entrevista. Esse é o caso em que o trabalho vale mais, e é
argumento de equidade além de técnico.

O diferencial fica preciso e defensável: a ferramenta em uso encontra por
palavra e deixa a comparação para a pessoa; e preserva a pesquisa antiga como
PDF estático de até duzentas e poucas páginas, não como dado consultável. Os
dois pontos são exatamente onde recuperação semântica com filtro estruturado e
persistência com versionamento resolvem — que é o recorte de banco de dados que
motiva a orientação.

## Decisão 2 — Módulo de documentos

### Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — TR completo, e ETP com as seções derivadas geradas e as de conhecimento local como preenchimento guiado com lacuna marcada | Nada é inventado; o gerado é rastreável; cabe no critério de aceitação declarado | Não entrega o ETP "pronto" no sentido ingênuo |
| B — ETP e TR gerados por inteiro | Escopo da proposta original | Para preencher justificativa de quantidade e peculiaridade do município, teria de produzir texto plausível sem lastro — que é o que a fonte nomeou como motivo para não confiar |
| C — Apenas o TR | O mais determinístico dos dois documentos | O ETP é onde está o trabalho pesado; deixá-lo fora reduz muito o ganho demonstrável |

### Decisão

**Escolhida: A.** Gera integralmente o que é derivável — tópicos fixos,
parcelamento, adequação orçamentária, justificativa do método de cotação, quadro
de itens e valores, e o TR inteiro. As seções que dependem de conhecimento local
viram preenchimento guiado, com a lacuna marcada de forma visível.

**Ajuste feito na revisão da transcrição: o gabarito é acervo, não formulário.**
Não existe modelo em branco com campos a substituir — a fonte declarou que não há
gabarito padronizado e que reaproveita um documento anterior, trocando o texto de
cada tópico. Os "tópicos fixos" que ela aponta estão marcados dentro de um
documento preenchido.

Isso muda a implementação e melhora o trabalho: recuperar a redação de um
processo anterior de objeto semelhante é **um segundo problema de recuperação**,
espelhando o do módulo de preços. Os dois módulos passam a ter a mesma natureza
técnica, e o recorte de banco de dados cobre os dois em vez de se dividir entre
eles.

### Justificativa

A opção B falha no critério que a própria fonte declarou. Ela já usa assistentes
de texto e descreveu o defeito com precisão: "às vezes ele enfeita demais e
coloca coisa que não é a nossa realidade", e "conferir as leis, quando ele coloca
leis, se realmente é aquela ou não é". Gerar texto sem lastro para justificar
quantidade é produzir exatamente o defeito que inviabiliza o uso.

A opção A ainda cabe no alvo: uma hora de revisão contra um dia dedicado hoje.
Boa parte do ETP é derivável de dado estruturado e do resultado da pesquisa de
preços, e a parte que não é fica marcada como lacuna em vez de preenchida com
plausibilidade.

## Decisão 3 — Desenho da avaliação

### Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — Usar cotações já realizadas como padrão-ouro de relevância | Julgamento já existe e é de quem faz o trabalho; barato; reaproveita a métrica da iniciação científica | Exige pedir material à fonte, com o cuidado da política de dados |
| B — Montar padrão-ouro do zero | Controle total sobre o conjunto | Caro, demorado, e o julgamento seria do autor, não de quem faz o trabalho |
| C — Medir apenas tempo | Simples | Mede velocidade, não qualidade. Um sistema rápido que traz candidato errado passaria |

### Decisão

**Escolhida: A.** Pedir de três a cinco cotações encerradas, com a planilha de
itens de entrada e o relatório de saída, e medir se o sistema recupera nos
primeiros resultados os preços que a servidora escolheu.

### Justificativa

Cada cotação encerrada carrega três preços que uma pessoa competente considerou
aceitáveis, cada um com chave precisa no portal nacional. Medir recuperação
contra essa escolha é a avaliação mais convincente disponível, e liga diretamente
com a métrica de recuperação usada na iniciação científica, o que dá continuidade
entre os dois trabalhos.

### Ressalvas, corrigidas na revisão da transcrição

A formulação inicial desta decisão supunha que a operadora montasse uma lista
curta de candidatos e depois filtrasse até três — o que produziria positivos e
negativos. **A demonstração de tela mostra que não é isso.** Ela escaneia os
resultados e marca diretamente os três que já são a resposta. A ferramenta
permite marcar mais e decidir depois; ela não usa assim.

Três consequências, todas a declarar no texto:

1. **O julgamento é positivo e incompleto.** Os descartados não ficam
   registrados. Mede-se **recuperação**, não precisão: um candidato que o sistema
   traga e ela não tenha escolhido pode ser igualmente aceitável.
2. **A escolha é evidência de aceitabilidade, não de otimalidade.** Recuperar o
   que ela escolheu prova concordância com julgamento humano competente; não
   prova que não haveria escolha melhor.
3. **A seleção dela é bidimensional.** Ela ranqueia por comparabilidade do item
   **e** por proximidade a um preço que já espera — verbalizado na demonstração
   como "eu vou chegar mais ou menos no que eu acho que deve ser", e descrito em
   outro momento como buscar preços que se aproximem de uma cotação de fornecedor
   local. Um ranqueador só de similaridade não reproduz isso, e medi-lo como se
   devesse seria medir contra um critério que ele não recebeu.

**Desenho que sai disso:** rodar a avaliação em duas condições, **sem âncora** e
**com âncora** de preço esperado. A diferença isola quanto do acerto vem de
entender o item e quanto vem de saber o preço. Isso vira resultado reportado.

**E uma medida de desfecho, independente da recuperação:** a distância entre o
valor estimado que o sistema produz e o que ela produziu. Não exige acertar os
mesmos itens, e é o que de fato importa para o processo.

**Complemento barato, se o incompleto incomodar:** mostrar a ela os primeiros k
resultados de alguns itens e pedir que diga quais aceitaria. Sessão curta, vai
para `TCC/validações/`, e fecha a medida de precisão.

## Consequência

**Entra em escopo:**

- Coleta e indexação de itens contratados a partir da API do PNCP.
- Correspondência semântica de descrição de item, com filtro por unidade de
  medida, ordem de grandeza da quantidade, recorte geográfico e janela temporal.
- Distinção entre produto e serviço, e agrupamento de candidatos originados do
  mesmo evento de contratação.
- Mapa de cotação com procedência por preço, e memória de cálculo.
- Trilha de auditoria que reconstitua uma pesquisa como ela era na data em que
  foi feita.
- Geração completa do TR, e do ETP nas seções deriváveis.
- Recuperação de redação no acervo de documentos anteriores do próprio município.
- Âncora de preço esperado como entrada do ranqueamento, com as duas dimensões
  exibidas separadas.
- Avaliação por recuperação contra cotações reais, em duas condições, mais a
  medida de desfecho sobre o valor estimado, além da medição de tempo.

**Fica fora de escopo:**

- Integração com o banco de preços comercial ou com qualquer sistema do
  município. Isso já estava fora e continua.
- Coleta de preços em lojas da internet e captura de tela como evidência.
- Geração de texto para as seções do ETP que dependem de conhecimento local sem
  lastro em dado fornecido.
- Verificação pelo órgão de controle, que a orientação já havia tirado do escopo
  obrigatório.

**Muda na documentação:** `docs/requisitos/README.md` fecha as questões Q1, Q2 e
Q3; `docs/projeto.md` sai com duas pendências a menos.

## Critério de revisão

Reabrir se:

- A API do PNCP não entregar cobertura suficiente de itens contratados para a
  correspondência funcionar. A viabilidade está investigada em
  `docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md`, mas contra a
  hipótese antiga; precisa ser reavaliada contra a correspondência semântica.
- As cotações pedidas não vierem em número suficiente para sustentar a medida de
  recuperação. Nesse caso a avaliação cai para a opção B ou C, e a decisão 3 é
  reescrita. O formato não é risco: o relatório já traz item, quantidade, unidade
  e os três escolhidos com chave rastreável.
- A recuperação medida **sem âncora** ficar tão baixa que o resultado só se
  sustente **com âncora**. Isso significaria que o trabalho depende de o operador
  já saber o preço — e aí a contribuição precisa ser reformulada com honestidade,
  não maquiada com a condição favorável.
- A revisão da orientadora apontar que o escopo não cabe no semestre de
  implementação.

## Backlinks
- [[../requisitos/2026-09-06-entrevista-fonte-de-dominio-relato]]
- [[2026-08-16-tema-e-recorte]]
- [[2026-08-16-politica-de-dados-de-dominio]]
- [[../sessões/2026-09-06]]
