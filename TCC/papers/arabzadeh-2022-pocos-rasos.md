---
tipo: paper
autores: ["Negar Arabzadeh", "Alexandra Vtyurina", "Xinyi Yan", "Charles L. A. Clarke"]
ano: 2022
titulo: "Shallow pooling for sparse labels"
venue: "Information Retrieval, v. 25, n. 4 (lido o preprint arXiv:2109.00062v2)"
tags: [avaliacao, recuperacao-de-informacao, rotulo-esparso, julgamento-por-preferencia]
citacao_abnt: "ARABZADEH, Negar; VTYURINA, Alexandra; YAN, Xinyi; CLARKE, Charles L. A. Shallow pooling for sparse labels. Information Retrieval, v. 25, n. 4, p. 365-385, 2022. DOI: 10.1007/s10791-022-09411-0."
arquivo_local: "TCC/papers/arabzadeh-2022-pocos-rasos.pdf"
verificado: true
---

# Shallow pooling for sparse labels

> Lido o preprint v2, de 28/02/2022. Periódico, volume, número e páginas da versão publicada vêm do índice aberto de publicações, consultado em 14/10/2026; **a versão publicada não foi aberta** — VERIFICAR antes de citar página.

## Síntese

Numa coleção em que quase toda consulta tem um único relevante anotado, compara, por julgamento lado a lado, o primeiro resultado de sistemas neurais com o relevante anotado.

## Contribuições

- Mostra que, com rótulo esparso, um sistema pode ser "melhor que perfeito".
- Propõe manter o rótulo como melhor resposta conhecida, por comparação lado a lado.

## Resultados-chave

- 94% das consultas de desenvolvimento têm um só relevante.
- Quando sistema e rótulo discordam no primeiro posto, avaliadores preferem o resultado do sistema em 58,6% dos pares.
- Com rótulos refeitos por preferência, a ordem do topo da classificação muda.

## Limitações

Avaliadores recrutados por plataforma de tarefas, com erro estimado de um terço; uma coleção; 500 consultas na segunda etapa.

## Relevância para este TCC

Dá a forma barata da sessão de julgamento: mostrar lado a lado o preço que a servidora escolheu e o primeiro candidato de outro método, sem identificar qual é qual.

## Citáveis

> "we suggest that sparse labels should explicitly represent the best known items, with preference judgments employed to determine and maintain these best known items." (Arabzadeh et al., 2022, p. 3 do preprint)

## Backlinks

- [[../../docs/pesquisas/metodologia-dsr-e-modelagem-de-processo]]
