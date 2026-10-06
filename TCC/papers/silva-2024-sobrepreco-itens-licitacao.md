---
tipo: paper
autores: ["Mariana O. Silva", "Lucas G. L. Costa", "Larissa D. Gomide", "Guilherme Bezerra", "Gabriel P. Oliveira", "Michele A. Brandão", "Anisio Lacerda", "Gisele Pappa"]
ano: 2024
titulo: "Overpricing Analysis in Brazilian Public Bidding Items"
venue: "Journal on Interactive Systems, v. 15, n. 1"
tags: [trabalhos-relacionados, pesquisa-de-precos, descricao-de-item, produto-e-servico, brasil]
citacao_abnt: "SILVA, Mariana O. et al. Overpricing analysis in Brazilian public bidding items. Journal on Interactive Systems, [s. l.], v. 15, n. 1, p. 130-142, 2024. DOI: 10.5753/jis.2024.3831."
arquivo_local: "TCC/papers/silva-2024-sobrepreco-itens-licitacao.pdf"
verificado: true
---

# Overpricing Analysis in Brazilian Public Bidding Items

> **`verificado: true`** — conferido em 06/10/2026. Autores, periódico, ano,
> volume e número, no cabeçalho do PDF; páginas 130-142 e data de publicação
> (18/01/2024), nos metadados da página do artigo na biblioteca da SBC.
> **O PDF não imprime número de página**: nas citações diretas abaixo a página
> foi inferida da faixa 130-142 e precisa ser reconferida se a citação for usada.

## Síntese

Trabalho do mesmo grupo do [[brandao-2024-plus]], versão estendida de artigo
anterior. Propõe uma metodologia para padronizar a descrição de itens licitados
e um método estatístico, baseado no intervalo interquartil, para apontar
sobrepreço. Compara três formas de agrupar itens e valida contra preços de
combustível publicados pela agência reguladora do setor.

## Contribuições

- Padronização de descrição em três fases: limpeza textual, estruturação de
  atributos e separação entre produto e serviço.
- Heurística por palavras-chave que classifica o item como produto ou serviço.
- Quatro faixas de preço — normal, alto, sobrepreço e anomalia — definidas por
  limiares interpretáveis.
- Comparação de três estratégias de agrupamento, com validação contra dado
  externo.

## Método

Dados: licitações de 853 municípios de Minas Gerais — 12.805.984 itens
municipais (2014 a 2021) e 1.361.523 estaduais (2009 a 2021).

A limpeza inclui correção ortográfica e lematização. A estruturação rotula cada
termo em sete categorias: unidade de medida, cor, material, número, tamanho,
tipo ou quantidade, e palavra. O agrupamento usa a descrição original, todas as
palavras da categoria "palavra", ou só a primeira delas — sempre dentro da mesma
comarca, ano e mês.

O limite de sobrepreço é o terceiro quartil mais 1,5 vez o intervalo
interquartil; anomalia é cem vezes esse limite.

Validação: cruzamento com a série de preços máximos de cinco combustíveis em 67
municípios, por casamento aproximado de texto com limiar de 90%.

## Resultados-chave

- **Descrições curtas: mediana de 6 palavras nos itens municipais** e de 15 nos
  estaduais.
- 33,8% dos itens municipais sem categoria de despesa identificável.
- A heurística classificou 84,9% dos itens como produto e 15,1% como serviço;
  2,88% foram descartados por descrição ausente ou inconsistente.
- Agrupar por todas as palavras teve o melhor ajuste ao dado externo: R² de 95%
  e erro percentual médio de 4%, contra R² de 80% da descrição original.
- Só no combustível comum, a descrição original aparece de 211 formas
  distintas; após a padronização, 59.

## Limitações

- A separação entre produto e serviço erra: um item de exames laboratoriais foi
  classificado como produto.
- A validação cobre só combustível, que é um produto de descrição simples.
- O agrupamento é por igualdade de termos padronizados, sem medida de
  proximidade de significado. Os autores apontam o uso de vetores de palavras
  como trabalho futuro.
- Casos sinalizados não foram submetidos a especialistas do domínio.

## Relevância para este TCC

Dá número publicado a três coisas que o levantamento de campo encontrou em
pequena escala:

1. **Descrição de item municipal é curta e ruidosa.** Mediana de seis palavras.
   É a restrição que este TCC registra ao dizer que a qualidade da
   correspondência é limitada pela descrição disponível, e pesa na escolha do
   modelo de representação.
2. **Unidade de medida precisa ser separada da descrição.** O artigo trata
   unidade como categoria própria de atributo, o que converge com a regra de
   vocabulário fechado de unidades.
3. **Produto e serviço têm de ser distinguidos antes de comparar preço.** É o
   requisito de excluir candidato cuja natureza não corresponde à do item
   (RF18), aqui com precedente publicado e com a taxa de erro da heurística
   declarada.

A diferença de posição é a mesma do PLUS: o trabalho serve à detecção de
sobrepreço depois da contratação, não à composição da pesquisa de preços. E o
agrupamento por termos é exatamente a busca por palavra cujo limite motivou este
trabalho.

Cita a Lei nº 14.133/2021 ao tratar de itens dispensados de licitação.

## Citáveis

> "we identified a notable gap in the existing research: the lack of studies
> specifically addressing the challenges of standardizing input data and
> comparing statistical parameters between analogous items in depth" (Silva et
> al., 2024, p. 132 — página inferida)

> "municipal items feature shorter descriptions than state items (with a median
> of 6 words for municipal items and 15 words for state items)" (Silva et al.,
> 2024, p. 133 — página inferida)

> "clustering without distinguishing between products and services can result in
> an unbalanced estimation of overpricing" (Silva et al., 2024, p. 134 — página
> inferida)

## Backlinks

- [[brandao-2024-plus]]
- [[brum-2024-agrupamento-itens-similares]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
