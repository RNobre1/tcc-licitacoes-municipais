---
tipo: paper
autores: ["Yingqiang Gao", "Veton Matoshi", "Luca Rolshoven", "Tilia Ellendorff", "Judith Binder", "Jeremy Austin Jann", "Gerold Schneider", "Matthias Stürmer"]
ano: 2026
titulo: "Generating and Evaluating Sustainable Procurement Criteria for the Swiss Public Sector using In-Context Prompting with Large Language Models"
venue: "arXiv, preprint arXiv:2603.22513v1 [cs.SE]"
tags: [trabalhos-relacionados, geracao-de-documento, licitacao, fase-preparatoria, alucinacao, suica, preprint]
citacao_abnt: "GAO, Yingqiang et al. Generating and evaluating sustainable procurement criteria for the Swiss public sector using in-context prompting with large language models. arXiv, 23 mar. 2026. Preprint arXiv:2603.22513v1. Disponível em: https://arxiv.org/abs/2603.22513. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/gao-2026-criterios-sustentaveis-suica.pdf"
verificado: true
---

# Generating and Evaluating Sustainable Procurement Criteria for the Swiss Public Sector using In-Context Prompting with Large Language Models

> **`verificado: true` vale para o preprint.** Conferido em 06/10/2026 contra o
> PDF: oito autores, título, identificador e data (23/03/2026). **Há divergência
> com a versão publicada, que não foi lida**: o registro do DOI
> 10.1145/3820755.3821484, de um simpósio de engenharia de documentos de 2026,
> lista sete autores, sem Judith Binder. Antes de citar a versão dos anais, abrir
> o PDF da editora e conferir autoria e páginas.

## Síntese

Grupo de Zurique e Berna. Na Suíça, a lei exige que o edital traga critérios de
sustentabilidade — de habilitação, de julgamento e de especificação técnica — e
redigi-los, setor por setor, a partir de guias oficiais, é trabalho manual de
especialista. O artigo apresenta um software que usa modelos de linguagem
ancorados nesses guias para gerar catálogos de critérios, com três níveis de
ambição cada, e avalia o resultado contra catálogos feitos à mão.

## Contribuições

- Software de mesa que encadeia leitura dos guias, instrução estruturada e
  exportação em planilha.
- Exigência de que cada critério gerado venha com endereço de fonte oficial.
- Avaliação automática por alinhamento entre tabela gerada e tabela de
  referência, e por um modelo de linguagem no papel de avaliador.
- Relato dos modos de falha observados.

## Método

Padrão-ouro montado por uma especialista para sete setores, de 60 a 144
critérios cada, a partir do guia europeu de compras verdes e do guia suíço.

Três modelos comerciais com busca em arquivo. A geração é repetida até cinco
vezes quando viola a estrutura ou a exigência de fonte.

Avaliação qualitativa: dois cientistas de dados comparam 50 critérios gerados
com 60 de referência no setor de mobiliário. Avaliação automática: casamento
ótimo entre linhas e medida de qualidade, cobertura e média harmônica. Estudo
de uso com **uma** especialista em compras sustentáveis.

## Resultados-chave

- Critérios gerados com, em média, 149 caracteres contra 484 dos de referência:
  **mais curtos e mais genéricos**.
- Oito critérios de referência ficaram sem correspondente gerado.
- Concordância bruta entre anotadores de 94,67%, mas kappa de 0,520 —
  concordância apenas moderada além do acaso.
- O modelo de melhor equilíbrio chegou a média harmônica de 0,74 no setor de
  mobiliário.
- Na avaliação da especialista: o sistema **parafraseia em vez de reproduzir o
  texto da fonte**, omite critérios e níveis, e **inventou limiares numéricos**.

## Limitações

Declaradas com franqueza incomum: a qualidade depende da cobertura dos guias; a
repetição de tentativas introduz não determinismo; a exigência de fonte reduz,
mas não elimina, referência inventada; e o sistema depende de modelos fechados.
O estudo de uso tem uma única participante.

## Relevância para este TCC

É o correlato que mais se aproxima da **etapa do processo**: redigir, antes da
publicação, uma parte do instrumento convocatório exigida por lei. E o que ele
relata é a principal evidência externa a favor do desenho escolhido aqui.

**A conclusão dos autores é um aviso.** Geração livre e exigência de precisão
de um documento de licitação não combinam: o modelo parafraseia onde se
precisava de texto literal e inventa número onde se precisava de fonte. Isso
sustenta três decisões já registradas:

- toda base legal citada tem de ser rastreável até referência conferível
  (RNF04);
- trecho gerado com base legal, prazo ou valor é destacado para conferência
  humana (RF09);
- seção que descreve método é redigida a partir do resultado efetivo do
  processo, e não de texto padrão (RF11).

É também o que a servidora entrevistada disse com outras palavras: o texto vem
bem escrito, mas é preciso conferir se as leis citadas são mesmo aquelas.

Diferenças: o produto lá é um catálogo de critérios reutilizável, não a peça de
um processo concreto; a norma é a suíça e a europeia; não há preço; e a
rastreabilidade é o endereço da fonte de cada critério, sem registro de decisão.

O método de avaliação — casar linha gerada com linha de referência — pode servir
de inspiração para medir a minuta gerada contra a versão assinada.

## Citáveis

> "The expert evaluation highlights a fundamental mismatch between generative AI
> and procurement requirements for precision and traceability, as models tend to
> paraphrase or hallucinate instead of reproducing source text verbatim." (Gao
> et al., 2026, p. 10 do preprint)

> "the system occasionally hallucinated numerical thresholds or ambition levels,
> which is especially problematic in compliance-critical procurement contexts"
> (Gao et al., 2026, p. 10 do preprint)

> "SwissSPC is best positioned as a decision-support system rather than a fully
> autonomous procurement tool" (Gao et al., 2026, p. 10 do preprint)

## Backlinks

- [[vandermeer-2026-legalcheck]]
- [[zhao-2024-geracao-documento-licitacao]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
