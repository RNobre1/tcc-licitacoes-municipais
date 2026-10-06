---
tipo: paper
autores: ["Pedro P. V. Brum", "Mariana O. Silva", "Gabriel P. Oliveira", "Lucas G. L. Costa", "Anisio Lacerda", "Gisele L. Pappa"]
ano: 2024
titulo: "Unsupervised Grouping of Public Procurement Similar Items: Which Text Representation Should I Use?"
venue: "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)"
tags: [trabalhos-relacionados, descricao-de-item, representacao-de-texto, busca-semantica, brasil]
citacao_abnt: "BRUM, Pedro P. V. et al. Unsupervised grouping of public procurement similar items: which text representation should I use? In: JOINT INTERNATIONAL CONFERENCE ON COMPUTATIONAL LINGUISTICS, LANGUAGE RESOURCES AND EVALUATION (LREC-COLING), 2024, Torino. Proceedings [...]. [S. l.]: ELRA: ICCL, 2024. p. 17176-17185. Disponível em: https://aclanthology.org/2024.lrec-main.1492/. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/brum-2024-agrupamento-itens-similares.pdf"
verificado: true
---

# Unsupervised Grouping of Public Procurement Similar Items: Which Text Representation Should I Use?

> **`verificado: true`** — conferido em 06/10/2026. Autores, evento, datas e
> páginas 17176-17185, no rodapé do PDF dos anais. Título completo dos anais,
> cidade (Torino) e editoras, no registro bibliográfico oficial da ACL
> Anthology. O DOI que a base de busca devolveu (10.63317/45au7zjcrwfb) resolve
> para a página do evento, mas não aparece no PDF — foi deixado fora da
> referência.

## Síntese

Terceiro trabalho do grupo da UFMG, e o mais próximo da decisão técnica central
deste TCC. A pergunta é direta: para agrupar itens de compra pública que são o
mesmo produto escrito de formas diferentes, que representação de texto usar? Os
autores comparam oito representações, de saco de palavras a modelos de sentença
baseados em BERT, sobre mais de dois milhões de descrições em português, e
propõem uma variante que dá peso aos componentes que definem um item:
substantivo, unidade de medida e número.

## Contribuições

- Arcabouço em três etapas: limpeza, extração de informação e representação.
- Adaptação, para descrições de item, de um método que combina o vetor da
  sentença inteira com o vetor de seus componentes mais importantes.
- Comparação de oito representações em texto que não segue gramática formal.
- Conjunto sintético de 100 mil descrições com unidades convertidas, para
  ensinar ao modelo que medidas equivalentes descrevem o mesmo objeto.

## Método

Dados: 196.747 licitações de 2015 a 2018, de onde saem 2.149.533 itens cuja
descrição tem número ou unidade de medida.

Números são normalizados em notação científica. A extração usa etiquetagem
gramatical e reconhecimento de entidades.

O agrupamento tem duas etapas: primeiro, uma heurística junta os itens que
começam pela mesma palavra; depois, um algoritmo de agrupamento por densidade
refina cada grupo usando a representação vetorial.

Sem gabarito, a avaliação usa métricas internas de agrupamento — coeficiente de
silhueta e dois índices de separação — mais o percentual de itens deixados sem
grupo e análise qualitativa.

## Resultados-chave

- **Sem a heurística da primeira palavra, 43% a 45% dos itens ficam sem
  grupo.** Com ela, de 18% a 28%.
- Melhor silhueta, 0,685, com o modelo de sentença ajustado no conjunto
  sintético do domínio. Média ponderada simples de vetores de palavra chega a
  0,679; saco de palavras, a 0,621.
- A variante proposta não superou o modelo de sentença ajustado quando
  combinada à heurística.
- O ajuste no conjunto sintético melhorou todas as métricas.
- Num grupo de 2.331 máscaras, o refinamento separou 16 subgrupos, e em quatro
  deles um número está entre os termos mais frequentes.

## Limitações

- Não há gabarito: as métricas medem coesão do agrupamento, não se os itens
  agrupados são de fato o mesmo produto.
- Análise qualitativa pequena, reconhecida pelos autores.
- Generalização para outros domínios e idiomas não testada.
- Busca semântica aparece só como trabalho futuro.

## Relevância para este TCC

Informa diretamente a decisão em aberto sobre o modelo de representação das
descrições.

**O sinal lexical é forte nesse tipo de texto.** A primeira palavra da descrição
sozinha organiza a maior parte dos itens, e método simples chega perto de modelo
sofisticado. Isso é evidência contra apostar só em representação densa, e a
favor de combinar sinal lexical com semântico — e de testar antes de escolher.

**Número e unidade decidem se dois itens são o mesmo.** Caixa de cem e caixa de
mil máscaras são itens diferentes, e modelo de linguagem genérico lida mal com
magnitude. É o argumento para tratar unidade e quantidade como filtro
estruturado obrigatório, em vez de esperar que a similaridade as resolva.

**Ajuste no domínio compensa.** Reforça a suposição de que as descrições reais
da base pública precisam ser testadas antes de fechar o modelo.

A diferença de tarefa: lá, agrupamento não supervisionado, sem gabarito. Aqui,
recuperação de candidatos para um item consultado, avaliada contra as escolhas
de quem fez a cotação — o que dá a este trabalho o gabarito que falta lá.

## Citáveis

> "Given the lack of uniformity in naming items and the absence of a common
> information system spanning all levels of government procurement, identifying
> whether two item descriptions are the same becomes crucial." (Brum et al.,
> 2024, p. 17176)

> "For instance, distinguishing between boxes containing 1,000 or 100 masks
> requires attention to numbers." (Brum et al., 2024, p. 17176)

> "using sophisticated supervised methods [...] to derive vectors for
> unsupervised tasks may not offer significant advantages" (Brum et al., 2024,
> p. 17182)

## Backlinks

- [[brandao-2024-plus]]
- [[silva-2024-sobrepreco-itens-licitacao]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
