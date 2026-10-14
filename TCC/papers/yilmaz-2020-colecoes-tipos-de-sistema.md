---
tipo: paper
autores: ["Emine Yilmaz", "Nick Craswell", "Bhaskar Mitra", "Daniel Campos"]
ano: 2020
titulo: "On the Reliability of Test Collections for Evaluating Systems of Different Types"
venue: "Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval"
tags: [avaliacao, recuperacao-de-informacao, gabarito-incompleto, ameaca-a-validade]
citacao_abnt: "YILMAZ, Emine; CRASWELL, Nick; MITRA, Bhaskar; CAMPOS, Daniel. On the reliability of test collections for evaluating systems of different types. In: INTERNATIONAL ACM SIGIR CONFERENCE ON RESEARCH AND DEVELOPMENT IN INFORMATION RETRIEVAL, 43., 2020. Proceedings [...]. New York: ACM, 2020. p. 2101-2104. DOI: 10.1145/3397271.3401317."
arquivo_local: "TCC/papers/yilmaz-2020-colecoes-tipos-de-sistema.pdf"
verificado: true
---

# On the Reliability of Test Collections for Evaluating Systems of Different Types

> Lido o preprint arXiv:2004.13486v1. Título, autores e evento conferidos no preprint; páginas e DOI no registro do DOI, em 14/10/2026. O preprint traz DOI de modelo, não o real. Local de publicação do ACM vem do próprio preprint.

## Síntese

Simula coleções de avaliação montadas só com sistemas tradicionais e só com sistemas neurais, e mede quão bem cada uma avalia os dois tipos.

## Contribuições

- Primeiro teste de reuso de coleção montada com um tipo de sistema para avaliar outro tipo.

## Resultados-chave

- Sistemas neurais acham mais relevantes nos primeiros postos.
- Com poço só tradicional, a correlação da ordem dos neurais cai muito — chega perto de zero, e negativa, numa medida — e a coleção tende a subestimá-los.
- Poço neural avalia bem os dois tipos.

## Limitações

Poços rasos (profundidade 10), 43 consultas, uma trilha de avaliação. Os autores reconhecem que poços mais variados poderiam dar outro resultado.

## Relevância para este TCC

Apoia diretamente a ameaça do gabarito: avaliação feita com relevantes vindos de busca por palavra tende a subestimar a busca por significado. Ler junto com [[voorhees-2022-colecoes-trec-neurais]], que limita o alcance.

## Citáveis

> "one might incorrectly infer that the neural model is performing worse than the traditional model" (Yilmaz et al., 2020, p. 3 do preprint)

## Backlinks

- [[../../docs/pesquisas/metodologia-dsr-e-modelagem-de-processo]]
