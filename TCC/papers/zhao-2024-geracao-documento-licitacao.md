---
tipo: paper
autores: ["Yilong Zhao", "Daifeng Li"]
ano: 2024
titulo: "A Large Language Model-based Framework for Semi-Structured Tender Document Retrieval-Augmented Generation"
venue: "arXiv, preprint arXiv:2410.09077v1 [cs.CL]"
tags: [trabalhos-relacionados, geracao-de-documento, licitacao, edital, china, preprint]
citacao_abnt: "ZHAO, Yilong; LI, Daifeng. A large language model-based framework for semi-structured tender document retrieval-augmented generation. arXiv, 4 out. 2024. Preprint arXiv:2410.09077v1. Disponível em: https://arxiv.org/abs/2410.09077. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/zhao-2024-geracao-documento-licitacao.pdf"
verificado: true
---

# A Large Language Model-based Framework for Semi-Structured Tender Document Retrieval-Augmented Generation

> **`verificado: true` vale para o preprint.** Conferido em 06/10/2026 contra o
> PDF: dois autores, título, identificador e data (04/10/2024). **Existe versão
> publicada com título em outra ordem, não lida**: o registro do DOI
> 10.1109/icsece61636.2024.10729522 aponta trabalho em conferência do IEEE de
> 2024, páginas 177-182, de acesso fechado. Cita-se o preprint.

## Síntese

Artigo curto, de cinco páginas, da Universidade Sun Yat-sen. Propõe gerar o
documento de licitação em dois passos: recuperar, no acervo de documentos
anteriores, o mais parecido com a necessidade atual, e adaptá-lo. A recuperação
combina índice vetorial e índice de vocabulário, e reordena pela semelhança
entre a lista de itens a comprar e as listas dos documentos anteriores. A
adaptação preenche marcadores num modelo de editor de texto. Um grafo de
conhecimento sobre itens de compras passadas serve para completar a lista
quando o comprador não a fornece.

## Contribuições

- Arcabouço de geração de documento de licitação semiestruturado.
- Recuperação em dois estágios, com reordenação pela lista de itens.
- Modelos com marcadores, preenchidos por agentes que perguntam ao usuário o
  que falta.
- Base de conhecimento de itens, com classificação de mercadoria e grafo.

## Método

Acervo de 1.406 documentos de licitação da área médica, cedidos por um grupo de
compras. Grafo com 4.536 entidades e 3.373 relações.

A semelhança entre itens combina distância de n-gramas, distância de edição e
distância de cosseno entre vetores, com penalidade pela diferença de tamanho das
listas.

Avaliação por similaridade vetorial entre o documento gerado e o documento que
a equipe de compras de fato produziu, separada em parágrafos e tabelas, sobre
"dezenas" de documentos sorteados.

## Resultados-chave

- Pontuação de 77,74 para o arcabouço completo, contra 12,55 do modelo de
  linguagem sozinho e 29,42 do modelo com recuperação.
- Tirar a recuperação de modelo reduz a pontuação para 73,47; tirar o
  preenchimento, para 76,54.

## Limitações

Não declaradas. Da leitura:

- **A métrica é semelhança de texto com um documento de referência.** Não diz se
  o documento gerado está juridicamente correto nem se serve.
- Nenhuma avaliação por pessoa do domínio.
- Tamanho da amostra de teste não informado com precisão.
- Nenhuma norma é citada, e não há verificação de conformidade.
- O texto traz referência cruzada quebrada a uma figura.

## Relevância para este TCC

Mostra que geração de documento de licitação por recuperação de documento
anterior já foi proposta — e que a ideia de usar **a lista de itens** como chave
de semelhança entre processos é precedente publicado. Isso conversa com o
requisito de recuperar, no acervo do próprio município, a redação de processos
de objeto semelhante.

Serve mais como contraste do que como apoio:

1. **Adaptar o documento mais parecido é a cópia entre processos** que a
   análise documental deste TCC mostrou produzir erro — texto idêntico para
   objetos diferentes, e afirmação de método que o processo não sustenta. O
   desenho daqui gera o conteúdo a partir da evidência do processo e usa o
   acervo só como repertório.
2. **A avaliação por semelhança com o original premia justamente a cópia.** A
   avaliação planejada aqui mede outra coisa: esforço de revisão e consistência
   verificável.
3. Não há tratamento de preço nem trilha de auditoria.

O documento gerado lá é o instrumento de convocação; aqui, as peças que o
antecedem.

## Citáveis

> "the task of generating government procurement documents presents a higher
> degree of rigor compared to other endeavors" (Zhao; Li, 2024, p. 1 do
> preprint)

> "Traditional manual methods of preparing tender documents are time-consuming,
> error-prone, and inconsistent, posing challenges for non-professional
> procurement personnel." (Zhao; Li, 2024, p. 1 do preprint)

## Backlinks

- [[musumeci-2024-geracao-documentos-semiestruturados]]
- [[gao-2026-criterios-sustentaveis-suica]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
