---
tipo: paper
autores: ["Virgill van der Meer", "Julien Rossi"]
ano: 2026
titulo: "LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters"
venue: "arXiv, preprint arXiv:2605.12012v2 [cs.AI]"
tags: [trabalhos-relacionados, geracao-de-documento, prefeitura, trilha-de-auditoria, revisao-humana, paises-baixos, preprint]
citacao_abnt: "VAN DER MEER, Virgill; ROSSI, Julien. LegalCheck: retrieval- and context-augmented generation for drafting municipal legal advice letters. arXiv, 18 maio 2026. Preprint arXiv:2605.12012v2. Disponível em: https://arxiv.org/abs/2605.12012. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/vandermeer-2026-legalcheck.pdf"
verificado: true
---

# LegalCheck: Retrieval- and Context-Augmented Generation for Drafting Municipal Legal Advice Letters

> **`verificado: true` vale para o preprint.** Conferido em 06/10/2026 contra o
> PDF: autores, título, identificador, versão 2 e data (18/05/2026). O PDF traz
> o bloco de referência de uma conferência internacional de inteligência
> artificial e direito de 2026, **com o DOI ainda em branco**; não encontrei
> registro da versão publicada. Cita-se o preprint até que os anais sejam
> localizados. A entrada do sobrenome com partícula precisa seguir a regra que o
> estilo bibliográfico do texto adotar.

## Síntese

Sistema em uso no departamento jurídico da prefeitura de Amsterdã para redigir a
carta de parecer que responde a uma objeção de cidadão contra multa de lixo ou
remoção de veículo, bicicleta ou barco. Recupera pareceres anteriores e a
legislação pertinente, gera uma minuta com um modelo de linguagem, e passa por
revisão obrigatória de um jurista, que pode devolver anotações para uma segunda
geração. O jurista define de antemão o resultado — acolher ou rejeitar — e
continua sendo o autor da carta.

## Contribuições

- Arquitetura que combina recuperação sobre o acervo com contexto do caso em
  mais de uma etapa de geração.
- Avaliação em uso real, durante seis meses, com medidas de qualidade, tempo e
  aceitação.
- Relato do enquadramento de privacidade, risco e governança num órgão público.

## Método

Acervo de cerca de 23.500 pareceres de 2022 a 2025, com 150 a 14.000 casos por
domínio, segmentados por seção. A consulta é formada pela objeção — resumida
antes de virar vetor, o que melhorou a recuperação — e pelo relatório do
fiscal. Recuperam-se de 50 a 200 trechos por similaridade de cosseno, em
memória, sem banco vetorial dedicado. A geração roda com temperatura baixa.

Documentos anteriores são anonimizados antes de entrar em qualquer instrução.

Avaliação: cerca de 250 casos e 20 juristas. Mede-se quanto da minuta sobrevive
à edição, a presença dos fatos-chave, o tempo por carta comparado a estimativa
histórica, e a percepção por questionário e entrevista.

## Resultados-chave

- 81% do conteúdo gerado mantido literalmente na carta final; os juristas
  acrescentaram cerca de 8%.
- Fatos-chave presentes em mais de 99% das minutas.
- Redução de 50% a 70% no tempo total em casos simples: o que tomava seis horas
  passou a duas ou três.
- Minuta gerada em 20 a 25 segundos.
- Cartas geradas mais longas que as humanas em 68% dos casos, com 41% a mais de
  conteúdo em média.
- **Registro, para cada caso, das fontes usadas, da instrução e das alterações
  feitas** — o que os autores chamam de trilha de auditoria das entradas e
  saídas.

## Limitações

Declaradas: uma única organização, quatro domínios, grupo pequeno de
profissionais, dependência de modelo de terceiro, e nenhum estudo cego
comparando as etapas de geração.

Da leitura: a tabela de resultados traz revocação, precisão e F1 acima de 90%
sem definir contra o que foram calculadas; e a economia anual estimada supõe
implantação plena.

## Relevância para este TCC

**É o correlato mais forte do módulo de documentos, e o que de fato derruba a
hipótese de que geração assistida de documento em prefeitura seria novidade.**
Está em produção, é municipal, tem revisão humana obrigatória, exporta em
formato editável e registra as fontes de cada documento. O texto do TCC tem de
reconhecer isso sem rodeio.

O que distingue este trabalho:

1. **Tipo de documento.** Lá, resposta a um ato já praticado, redigida por
   analogia com casos anteriores. Aqui, peça de planejamento, cujo conteúdo vem
   dos dados da própria contratação.
2. **Tamanho do acervo.** Lá, 23.500 pareceres dão material para recuperar
   redação. No município estudado, a medição mostrou que o texto do estudo
   técnico não se repete entre processos — mediana de similaridade de 0,16 — e
   que copiar entre processos já produziu erro. A recuperação de redação
   anterior é, por isso, repertório de consulta aqui, e não a fonte do texto.
3. **Porte.** Capital com departamento jurídico e equipe de dados, contra setor
   de duas pessoas sem apoio de tecnologia.
4. **Preço.** Não há.
5. **Trilha.** Registra o que alimentou a geração. Não trata de reconstituir uma
   consulta sobre dado que mudou.

Três achados transferíveis: resumir a entrada antes de recuperar; fixar o
resultado como decisão humana antes de gerar; e a observação de que fonte
visível e aprovação obrigatória foram o que construiu a confiança dos juristas —
o mesmo que a servidora entrevistada apontou como condição.

O tempo medido por carta dá, além disso, um modelo de linha de base para a
medição cronometrada prevista na avaliação.

## Citáveis

> "We addressed this by logging the sources and the prompt for each case,
> effectively creating an audit trail of the AI's inputs and outputs." (Van der
> Meer; Rossi, 2026, p. 7 do preprint)

> "On average, 81% of AI-generated content was kept verbatim in the final
> letter, while jurists added only about 8% new content." (Van der Meer; Rossi,
> 2026, p. 6 do preprint)

> "LegalCheck always keeps a human in the loop and never sends a letter directly
> to citizens or decision-makers." (Van der Meer; Rossi, 2026, p. 5 do preprint)

## Backlinks

- [[musumeci-2024-geracao-documentos-semiestruturados]]
- [[gao-2026-criterios-sustentaveis-suica]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
