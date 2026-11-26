---
tipo: pesquisa
titulo: "Como tratar escores empatados no cálculo de Recall@k e MRR da bateria"
status: aberta — aguarda decisão do autor antes de qualquer medição (C17)
criado: 2026-11-26
autor: Rafael Nobre de Souza
relacionado:
  - TCC/decisões/2026-11-24-limiares-de-aceitacao-r1-r2.md
  - TCC/decisões/2026-11-24-espaco-de-busca-e-preco-do-candidato.md
  - docs/pesquisas/limiares-de-aceitacao-r1-r2.md
tags: [pesquisa, avaliação, empate, recall, mrr, r1, r2, c17]
---

# Escores empatados na bateria de avaliação

## A pergunta

Cada método da bateria ordena o espaço de busca de um item, e o Recall\@10 conta
quantos preços escolhidos pela servidora caem entre os dez primeiros. Quando dois
candidatos recebem exatamente o mesmo escore, a ordem entre eles não vem do
método: vem da regra de desempate. Se um grupo empatado atravessa a décima
posição, a regra decide quem entra no Recall\@10.

Hoje o arnês desempata pelo menor identificador do item. A revisão da terceira
rodada da frente de avaliação mostrou o efeito disso numa sonda sintética: sem
palavra em comum com a consulta, os relevantes de menor identificador dão
Recall\@10 de 1,00, e os de maior identificador dão 0,00, nos dois métodos.

A pergunta é qual regra de desempate a bateria usa, fixada antes de medir.

## Por que não é caso de borda

Na fatia coletada do PNCP até 26/11/2026 há 50.906 compras e 656.506 itens,
contando só a cópia mais recente de cada página. Com a descrição em minúsculas,
sem espaço nas pontas e com espaços internos colapsados:

- 487.284 descrições são distintas;
- **210.570 itens (32,1%) têm a descrição idêntica à de pelo menos outro item**;
- o maior grupo de descrições idênticas tem 1.625 itens.

Descrição idêntica dá escore idêntico no BM25, que só olha o texto, e vetor
idêntico no modelo de representação, que também só recebe o texto. Logo, empate
exato é frequente nos dois métodos. Esta medição é da fatia de dezembro de 2025
e de uma semana do Pará; o espaço nacional de doze meses deve ter grupos maiores,
mas isso é inferência.

## O que a literatura diz

Todas as fontes abaixo foram lidas **só no resumo**. Servem para orientar a
decisão, e não podem ser citadas no texto do TCC antes da leitura integral.

- Desempatar pelo nome ou identificador do documento é um parâmetro não
  controlado da avaliação. Num estudo de 22 edições do TREC, essa regra deu
  diferenças significativas em relação a regras mais justas [2].
- Existe uma forma exata e barata de calcular precisão, revocação, F1, precisão
  média, posto recíproco e nDCG na presença de empates. O valor é o **esperado
  sobre todas as ordens possíveis dentro dos grupos empatados**, calculado sem
  enumerar as permutações [1].
- Em recomendação com muitos empates, trocar só a regra de desempate muda o
  nDCG\@10 de 0,85 para 0,17 com os mesmos escores. A média sobre 100 sementes
  de desempate por *hash* coincide com o valor esperado exato sob desempate
  uniforme [3].
- Empates espúrios surgem também quando os escores são calculados em baixa
  precisão numérica. Métricas conscientes de empate, que relatam o valor
  esperado, a faixa e o viés, recuperam o valor correto [4].

## Alternativas

| Opção | Prós | Contras |
|---|---|---|
| A. Menor identificador, como hoje | Simples e determinística | Viés documentado [2]; o identificador acompanha a ordem de ingestão, que não tem relação com relevância |
| B. *Hash* estável com uma semente fixa | Simples, determinística e sem viés sistemático | Uma única ordem sorteada: o resultado de cada item carrega a variância do sorteio |
| C. Valor esperado sobre as ordens dos grupos empatados [1] | Exato, sem parâmetro, sem semente; é o padrão da literatura de RI | Implementação mais cuidadosa. O R2 reordena só os 20 primeiros, então o grupo empatado que atravessa a vigésima posição precisa de regra própria |
| D. Média de *hash* sobre muitas sementes | Aproxima C [3] e serve a qualquer métrica | Mais custo, e um parâmetro a fixar: o número de sementes |

## Recomendação

**C para o R1, com D embutido no R2.**

- **No R1**, o Recall\@k e o MRR\@20 de cada item são o valor esperado sobre as
  ordens dos grupos empatados [1]. O intervalo por reamostragem e o teste
  pareado continuam iguais: só passam a usar esses valores por item.
- **No R2**, a ordem dentro de cada grupo empatado é sorteada de novo em cada
  um dos 200 sorteios de ruído que já existem, com a semente gravada. A média
  sobre os sorteios já integra o desempate, sem parâmetro novo.
- **Em todo resultado**, relata-se a fração de itens em que um grupo empatado
  atravessa a décima posição.

O motivo: a regra de hoje favorece um método por acaso de identificador. Com um
terço dos itens em grupos de descrição idêntica, isso pode decidir o R1.

**O que mudaria a recomendação.** Se, no subconjunto de ajuste, quase nenhum
item tiver grupo empatado atravessando a décima posição, as opções B, C e D dão
o mesmo número. Nesse caso, B basta. A medição dessa fração é feita no ajuste,
antes de rodar a medição.

## Referências

1. [Computing information retrieval performance measures efficiently in the presence of tied scores](https://consensus.app/papers/details/w:acae1b1c-60bb-4cdf-b5ac-7fdbf6e16dd2/) — McSherry, F.; Najork, M. European Conference on Information Retrieval, 2008. Lido no resumo.
2. [Tie-Breaking Bias: Effect of an Uncontrolled Parameter on Information Retrieval Evaluation](https://consensus.app/papers/details/w:d1b5c4f8-87e6-4055-95e5-f5ee90468b3e/) — Cabanac, G. et al. Lecture Notes in Computer Science, 2010. Lido no resumo.
3. [Tie Handling Is Part of the Evaluation Protocol: An Order-Invariance Audit for Tie-Heavy Recommender Scores](https://consensus.app/papers/details/w:9290f9b7-c18b-497b-a131-ea0161a0cc1c/) — Guo, C. et al. arXiv, 2026. Pré-publicação, lida no resumo.
4. [Reliable Evaluation Protocol for Low-Precision Retrieval](https://consensus.app/papers/details/w:6a8f0945-5bd2-4c1c-8858-ddcb4c3a2de7/) — Yang, K. et al. Association for Computational Linguistics, 2026. Lido no resumo.

Os metadados acima vêm do mecanismo de busca e não foram conferidos na fonte
primária. Nenhum entra em `refs.bib` antes dessa conferência.
