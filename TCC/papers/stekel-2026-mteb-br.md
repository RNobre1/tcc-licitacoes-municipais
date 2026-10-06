---
tipo: paper
autores: ["Tardelli Ronan Coelho Stekel"]
ano: 2026
titulo: "MTEB-BR: A Text Embedding Benchmark for Brazilian Portuguese"
venue: "arXiv, preprint arXiv:2607.04581v2 [cs.CL]"
tags: [fundamentacao, representacao-de-texto, benchmark, portugues, decisao-a2, preprint]
citacao_abnt: "STEKEL, Tardelli Ronan Coelho. MTEB-BR: a text embedding benchmark for Brazilian Portuguese. arXiv, 7 jul. 2026. Preprint arXiv:2607.04581v2. Disponível em: https://arxiv.org/abs/2607.04581. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/stekel-2026-mteb-br.pdf"
verificado: true
---

# MTEB-BR: A Text Embedding Benchmark for Brazilian Portuguese

> **`verificado: true` vale para o preprint.** Conferido em 06/10/2026 contra o
> PDF: autor único, afiliação (Instituto Federal de São Paulo), título,
> identificador, versão 2 e data (07/07/2026).
>
> **Dois cuidados ao usar.** É preprint de três meses, **sem revisão por pares**.
> E o que ele ordena — modelos — envelhece rápido: a tabela vale como retrato de
> meados de 2026, não como ordem permanente. Foram lidos o corpo do artigo e a
> seção de limitações; os apêndices, não.

## Síntese

Primeiro conjunto de avaliação de modelos de representação vetorial montado só
com texto originalmente em português do Brasil, sem tradução. São 22 tarefas em
sete categorias — seis delas de recuperação — e 93 modelos avaliados, 73 de
pesos abertos e 20 serviços comerciais. O diferencial declarado é relatar a
classificação com incerteza: intervalo por reamostragem, teste pareado entre
modelos, e uma análise de quais tarefas de fato separam os modelos.

## Contribuições

- Conjunto de tarefas nativo, excluindo por construção as bases traduzidas.
- Painel de 93 modelos, de 23 milhões a 27 bilhões de parâmetros.
- Camada estatística: intervalos, significância pareada, agrupamento em faixas
  de modelos indistinguíveis.
- Comparação com a classificação multilíngue mais usada.

## Método

Cada modelo é usado congelado. Recuperação medida por ganho acumulado
descontado nos dez primeiros; similaridade por correlação de postos com
julgamento humano; classificação por um classificador linear sobre os vetores.
Entrada limitada a 512 unidades de texto para todos os modelos.

As seis tarefas de recuperação cobrem domínio aberto, jurisprudência de
tribunal de contas, tributário, perguntas frequentes bancárias e medicina.

## Resultados-chave

1. **Os seis primeiros são estatisticamente indistinguíveis.** Entre eles há um
   modelo de pesos abertos e licença permissiva, com média 0,670 contra 0,682 do
   líder comercial.
2. **Um modelo de 308 milhões de parâmetros fica em 13º de 93**, a 0,033 do
   líder. A qualidade sobe rápido com o tamanho até aí e depois quase não sobe.
3. **A classificação multilíngue prevê só moderadamente a ordem em português:**
   correlação de 0,75 sobre 55 modelos em comum. Um modelo que é 3º lá é 49º
   aqui.
4. **Modelos específicos de português perdem em recuperação** — média 0,331
   contra 0,517 dos multilíngues —, **mas a causa é o objetivo de treino, não a
   língua.** Os que só foram treinados para prever palavra mascarada têm média
   0,258. Os que foram ajustados para recuperação empatam com os multilíngues
   (0,516 contra 0,517).
5. **A imagem no espelho:** os mesmos modelos de palavra mascarada que vão mal
   em recuperação estão entre os primeiros em classificação. Ter boa
   informação para classificar não é ter boa geometria para buscar.
6. Recuperação é a categoria que mais separa os modelos; agrupamento, a que
   menos.

## Limitações

Declaradas pelo autor, e são várias: documentos curtos e entrada cortada em 512
unidades; conjuntos de recuperação pequenos — um deles com 50 consultas; **viés
de registro para texto institucional e jurídico**, que responde por seis das 22
tarefas; **texto de avaliação de produto e conversa não estão representados**;
serviços comerciais mudam sem aviso; parte do material pode estar no treino dos
modelos; e o painel é amostra de conveniência.

O autor também declara que não afirma que sua classificação esteja mais perto
da qualidade em uso real.

Da leitura: **não há nenhuma tarefa com descrição de item ou de produto.**

## Relevância para este TCC

Dá a lista de candidatos para a bateria de testes e, mais importante, **muda o
que se espera do modelo de domínio**.

### O que muda

1. **O modelo treinado em licitação tem contra si a evidência mais direta
   disponível.** [[lima-2026-helbert]] foi treinado só para prever palavra
   mascarada. Aqui, sobre texto brasileiro nativo, essa classe de modelo fica em
   último na recuperação — e a causa apontada é justamente o objetivo de treino.
   A hipótese de que "domínio ganha" tem de ser trocada por uma mais precisa:
   **domínio só ajuda se vier junto com ajuste para similaridade.**
2. **A classificação internacional não serve de atalho.** Escolher modelo pela
   tabela multilíngue é a decisão que este artigo mostra ser pouco confiável
   para o português.
3. **O candidato não precisa ser grande.** Há modelo de centenas de milhões de
   parâmetros perto do topo — cabe na máquina de trabalho, sem depender da que
   tem placa dedicada.
4. **Serviço comercial tem um custo que só aparece neste projeto.** O artigo
   registra que esses serviços mudam sem aviso. Um vetor que muda de um mês
   para o outro impede reconstituir uma pesquisa de preços como estava na data.
   Isso liga a escolha do modelo ao requisito de trilha: **modelo de pesos
   abertos, com versão fixada, é condição de reprodutibilidade**, não só de
   custo.

### O que não muda

**Nada aqui dispensa o teste próprio.** O conjunto não tem descrição de item, é
enviesado para prosa jurídica, e os primeiros colocados são indistinguíveis.
Serve para escolher **quem entra** na bateria, não quem ganha.

### Candidatos que saem desta leitura

Por classe, para que a bateria teste hipóteses e não só nomes:

| Classe | O que testa | Exemplo no artigo |
|---|---|---|
| Multilíngue de uso geral, tamanho médio | A linha de base de vetor | família multilíngue de uso geral, de 118 a 560 milhões; outro multilíngue de 568 milhões |
| Pequeno perto do topo | Se o tamanho importa neste dado | modelo de 308 milhões, 13º de 93 |
| Português ajustado para recuperação | Se a língua ajuda quando o objetivo é o certo | família de codificadores de sentença em português, variante de recuperação |
| Português só de palavra mascarada | O contraste negativo previsto | modelo geral de português; modelo de licitação |
| Grande, de pesos abertos | O teto alcançável sem serviço pago | modelo de 7,6 bilhões, 2º de 93. Se cabe na máquina de trabalho ou pede a que tem placa dedicada, é coisa a medir |

A camada estatística é aproveitável tal qual: reamostrar os 231 itens, relatar
intervalo e teste pareado, e **declarar empate quando for empate**.

## Citáveis

> "the gap reflects training objective and domain, not language specialization"
> (Stekel, 2026, p. 5 do preprint)

> "An encoder can thus carry probeable class signal without the metric geometry
> open-domain retrieval demands" (Stekel, 2026, p. 6 do preprint)

> "The multilingual leaderboard remains a useful first filter [...], but it
> cannot substitute for native evaluation." (Stekel, 2026, p. 7 do preprint)

> "closed APIs evolve silently" (Stekel, 2026, p. 10 do preprint)

## Backlinks

- [[lima-2026-helbert]]
- [[justino-2025-recuperacao-precedentes]]
- [[rassin-2024-anotacao-parcial-recuperacao]]
- [[staudinger-2024-recuperacao-reprodutivel]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
