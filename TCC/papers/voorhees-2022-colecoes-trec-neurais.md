---
tipo: paper
autores: ["Ellen M. Voorhees", "Ian Soboroff", "Jimmy Lin"]
ano: 2022
titulo: "Can Old TREC Collections Reliably Evaluate Modern Neural Retrieval Models?"
venue: "arXiv, preprint arXiv:2201.11086v1"
tags: [avaliacao, recuperacao-de-informacao, gabarito-incompleto, contraprova, preprint]
citacao_abnt: "VOORHEES, Ellen M.; SOBOROFF, Ian; LIN, Jimmy. Can old TREC collections reliably evaluate modern neural retrieval models? arXiv, 26 jan. 2022. Preprint arXiv:2201.11086v1. Disponível em: https://arxiv.org/abs/2201.11086. Acesso em: 14 out. 2026."
arquivo_local: "TCC/papers/voorhees-2022-colecoes-trec-neurais.pdf"
verificado: true
---

# Can Old TREC Collections Reliably Evaluate Modern Neural Retrieval Models?

> `verificado: true` vale para o preprint, conferido em 14/10/2026. Versão publicada, se houver, não localizada nem lida.

## Síntese

Mandaram julgar os documentos inéditos que sistemas neurais e de linha de base encontraram numa coleção clássica de 1999, e compararam a ordem dos sistemas antes e depois.

## Contribuições

- Teste direto, com avaliadores humanos, do reuso de uma coleção antiga para sistemas neurais.

## Resultados-chave

- 3.842 documentos novos julgados; 158 relevantes.
- Ordem dos 134 sistemas quase idêntica: correlação de 0,9933 e 0,9991.
- A divergência com [[yilmaz-2020-colecoes-tipos-de-sistema]] é atribuída à qualidade da coleção: profundidade, diversidade e eficácia dos sistemas que a montaram, inclusive buscas manuais.
- Sem as buscas manuais, os sistemas neurais recuperaram parte dos relevantes que só elas tinham achado — algum apoio à ideia de que acham documentos diferentes.

## Limitações

Uma coleção, construída com orçamento grande; modelos neurais usados sem ajuste ao domínio. Os autores dizem que o conselho "use poços profundos de sistemas eficazes" é pouco acionável.

## Relevância para este TCC

É a contraprova obrigatória. E, pelos critérios que ela mesma dá, o gabarito deste trabalho — raso e de um só tipo — é o caso em que a robustez não vale.

## Citáveis

> "The quality of a pooled collection is strongly dependent on the effectiveness of the runs from which the pools were taken, the diversity of those runs, and the pool depth" (Voorhees; Soboroff; Lin, 2022, p. 4 do preprint)

## Backlinks

- [[../../docs/pesquisas/metodologia-dsr-e-modelagem-de-processo]]
