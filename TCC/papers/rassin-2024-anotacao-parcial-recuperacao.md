---
tipo: paper
autores: ["Royi Rassin", "Yaron Fairstein", "Oren Kalinsky", "Guy Kushilevitz", "Nachshon Cohen", "Alexander Libov", "Yoav Goldberg"]
ano: 2024
titulo: "Evaluating D-MERIT of Partial-annotation on Information Retrieval"
venue: "arXiv, preprint arXiv:2406.16048v2 [cs.IR]"
tags: [fundamentacao, avaliacao, recuperacao-de-informacao, gabarito-incompleto, ameaca-a-validade, preprint]
citacao_abnt: "RASSIN, Royi et al. Evaluating D-MERIT of partial-annotation on information retrieval. arXiv, 13 out. 2024. Preprint arXiv:2406.16048v2. Disponível em: https://arxiv.org/abs/2406.16048. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/rassin-2024-anotacao-parcial-recuperacao.pdf"
verificado: true
---

# Evaluating D-MERIT of Partial-annotation on Information Retrieval

> **`verificado: true` vale para o preprint.** Conferido em 06/10/2026 contra o
> PDF: sete autores na ordem, título, identificador, versão 2 e data
> (13/10/2024). O PDF não informa onde o trabalho foi publicado; se houver
> versão em anais, não foi localizada nem lida. Cita-se o preprint.

## Síntese

Grupo de pesquisa de uma empresa de tecnologia com a Universidade Bar-Ilan.
A pergunta: quando um conjunto de avaliação de busca só registra **alguns** dos
textos relevantes de cada consulta, e trata todo o resto como irrelevante, a
comparação entre sistemas ainda é confiável? Para responder, os autores montam
um conjunto em que quase todos os relevantes estão anotados e depois o
"estragam" de propósito, deixando só parte das anotações, para ver quanto a
ordem dos sistemas muda.

A resposta é que depende de **como os relevantes anotados foram escolhidos** — e
que a forma mais comum de escolher é a pior.

## Contribuições

- Conjunto de avaliação com 1.196 consultas e 60.333 passagens relevantes,
  média de 50 por consulta, sobre 6,5 milhões de passagens de enciclopédia.
- Estudo do efeito de anotar um só relevante por consulta, sob cinco formas de
  escolhê-lo.
- Curva de quanto anotar para que a ordem dos sistemas se estabilize.

## Método

Doze sistemas de busca prontos para uso: cinco por palavra, quatro por vetor e
três híbridos. Medida: revocação nos vinte primeiros. A ordem dos doze sob
anotação completa é o padrão; a ordem sob anotação parcial é comparada a ela por
correlação de postos, lida também como taxa de pares de sistemas invertidos.

A escolha do relevante único é simulada de cinco modos: ao acaso; o mais
popular; o mais longo; o mais curto; e **o primeiro que um sistema de busca
existente devolve** — repetido para cada um dos doze sistemas no papel de quem
escolhe.

## Resultados-chave

| Como o relevante anotado foi escolhido | Correlação com a ordem verdadeira | Pares de sistemas invertidos |
|---|---|---|
| Ao acaso | 0,936 | 3,2% |
| O mais popular | 0,696 | 15,1% |
| O mais curto | 0,696 | 15,1% |
| **Por um sistema de busca existente** | **0,616** | **19,2%** |
| O mais longo | 0,545 | 22,8% |

- **Quem escolhe os relevantes favorece seus parentes.** Quando o relevante foi
  escolhido por um sistema de busca por palavra, outro sistema por palavra
  aparece como o melhor dos demais; quando foi escolhido por sistemas de vetor,
  esse mesmo sistema aparece como o pior.
- Só diferença muito grande entre sistemas resiste: com um relevante por
  consulta, mesmo pares de sistemas com diferença altamente significativa são
  invertidos em 17% dos casos; pares com diferença apenas significativa, em 33%.
- Para sistemas claramente distintos, anotar cerca de 20% dos relevantes já dá
  ordem razoável. Para sistemas próximos, é preciso anotar quase tudo.
- A técnica usual de juntar os primeiros resultados de vários sistemas para
  julgar encontrou só uma parte dos relevantes.

## Limitações

Declaradas: o método de montagem depende da estrutura da enciclopédia e não se
transporta a outros acervos; a anotação foi feita por modelo de linguagem, com
85% de concordância com avaliadores humanos; e as consultas pedem muitas
respostas, o que difere do caso de resposta única.

Da leitura: os doze sistemas são de 2020 a 2022, e o domínio é texto
enciclopédico em inglês.

## Relevância para este TCC

**É a leitura que mais mexe no desenho da avaliação**, porque descreve com
número exatamente a situação do gabarito que este trabalho tem.

### O que o gabarito é, nos termos deste artigo

O conjunto de avaliação previsto sai dos relatórios de cotação: para cada item,
os cerca de três preços que a servidora escolheu. Isso é anotação **parcial** —
há outros preços comparáveis na base, que ela não escolheu ou nem viu — e é
anotação **escolhida por um sistema de busca existente**: ela chegou a esses
preços digitando palavras numa ferramenta que busca por palavra.

É o pior caso da tabela acima, e o viés tem direção conhecida.

### A consequência, que tem de estar no texto

**O gabarito favorece a busca por palavra.** Os preços escolhidos são, por
construção, aqueles que uma busca por palavra alcança. Um método por
significado que traga um item comparável descrito com outras palavras — que é
precisamente o que ele promete — será contado como erro.

Daí três leituras, que mudam o que se pode concluir:

1. Se a busca por significado **ganhar** da busca por palavra neste gabarito, o
   resultado é conservador: ganhou jogando no campo do adversário.
2. Se **perder ou empatar**, o resultado não refuta a hipótese. Não é possível
   distinguir "é pior" de "achou comparáveis que o gabarito não registra".
3. Diferença **pequena** entre dois modelos de vetor não deve ser lida de jeito
   nenhum: com poucos relevantes por consulta, só diferença grande sobrevive.

### O que isso muda no desenho

- A **sessão de validação com a usuária**, já prevista como complemento, deixa
  de ser complemento e vira condição. E precisa ter uma forma específica: juntar
  os primeiros resultados de **todos** os métodos comparados, inclusive a busca
  por palavra, embaralhar, e pedir o julgamento sem dizer de onde veio cada um.
  Julgar só os resultados de um método repetiria o viés com o sinal trocado.
- A **busca por palavra entra como linha de base obrigatória**, já sabendo que
  parte em vantagem.
- **Capturar a lista curta** — os candidatos que ela marca antes de filtrar os
  três — aumenta o número de relevantes por item, e é isso que estabiliza a
  ordem.
- Comparação entre modelos com **teste pareado sobre os itens**, relatando
  intervalo, e não só a média.
- A ameaça vai declarada na seção de avaliação, com esta referência.

A avaliação em duas condições, com e sem o preço esperado, não é afetada: ela
compara o mesmo método consigo mesmo.

## Citáveis

> "models that successfully retrieve falsely labeled negatives are punished in
> evaluation" (Rassin et al., 2024, p. 1 do preprint)

> "the selection technique, used to pick which passages are annotated, has a
> major effect on the systems' measured performance and on the ranking of the
> different systems" (Rassin et al., 2024, p. 7 do preprint)

> "evaluation based on queries with a single annotated relevant passage is
> highly dependent on the passages selected for annotation, unless one system is
> significantly superior to all others" (Rassin et al., 2024, p. 8 do preprint)

## Backlinks

- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
- [[brum-2024-agrupamento-itens-similares]]
- [[stekel-2026-mteb-br]]
