---
tipo: paper
autores: ["Eduardo Marques Braga de Faria", "Gilton José Ferreira da Silva", "Michel S. Soares"]
ano: 2025
titulo: "Intelligent Methodologies for Preparing Reference Prices in Brazilian Public Biddings"
venue: "Anais do XXI Simpósio Brasileiro de Sistemas de Informação (SBSI 2025)"
tags: [trabalhos-relacionados, pesquisa-de-precos, preco-de-referencia, brasil, sbsi]
citacao_abnt: "FARIA, Eduardo Marques Braga de; SILVA, Gilton José Ferreira da; SOARES, Michel S. Intelligent methodologies for preparing reference prices in Brazilian public biddings. In: SIMPÓSIO BRASILEIRO DE SISTEMAS DE INFORMAÇÃO (SBSI), 21., 2025, Recife. Anais [...]. Porto Alegre: Sociedade Brasileira de Computação, 2025. p. 241-249. DOI: 10.5753/sbsi.2025.246450."
arquivo_local: "TCC/papers/faria-2025-precos-de-referencia.pdf"
verificado: true
---

# Intelligent Methodologies for Preparing Reference Prices in Brazilian Public Biddings

> **`verificado: true`** — conferido em 06/10/2026. Autores, evento, cidade e
> datas, no PDF. Edição (21ª), páginas 241-249, local e editora, na referência
> que a própria biblioteca digital da SBC fornece na página do artigo. A
> primeira rodada do levantamento registrava "veículo não identificado": é o
> SBSI 2025. O título é em inglês, mas **o texto é em português**.

## Síntese

Os autores, da Universidade Federal de Sergipe, desenvolvem um software que
calcula o preço de referência de uma licitação a partir das cotações
coletadas, criticando os três critérios usuais — média, mediana e menor preço.
A primeira versão escolhe entre tratamentos estatísticos alternativos por
regra; a segunda acrescenta um modelo de aprendizado de máquina para sinalizar
sobrepreço e subpreço. O critério de sucesso é a proximidade entre o preço de
referência calculado e o preço efetivamente homologado.

## Contribuições

- Seletor de algoritmos estatísticos para o preço de referência: coeficiente de
  variação, primeiro quartil, média harmônica, mediana e Lei de Benford.
- Segunda camada de verificação por aprendizado de máquina.
- Comparação quantitativa com a estimativa feita pelos próprios órgãos.

## Método

Pesquisa enquadrada como Design Science. Serviço web que recebe as cotações em
formato estruturado e devolve o preço de referência. Dados: cerca de 500 mil
preços, obtidos de portal federal de contratos — a requisição devolveu mais de
523 mil itens de compra — e do portal federal de compras.

A medida é o desvio absoluto médio entre o valor estimado e o valor contratado.
Compara-se o desvio da estimativa do órgão com o desvio da estimativa do
software, para as mesmas licitações.

A segunda versão treina regressão linear supervisionada e mede a "assertividade"
na detecção de preço irregular.

## Resultados-chave

- Desvio médio de 2,53% do software contra 15,58% dos métodos tradicionais.
- Numa amostra de dez licitações exibida no texto: 9,03 contra 1,62.
- Segunda versão com 70% de assertividade, que os próprios autores consideram
  aquém do desejável.

## Limitações

Declaradas pelos autores: a versão com aprendizado de máquina precisa de mais
treinamento, depende de grande volume de dados e sofre com a variabilidade entre
categorias de produto.

Observadas na leitura, e relevantes para usar o trabalho com cautela:

- **O método de avaliação favorece estimativa baixa.** O valor homologado é o
  preço depois da disputa, e os tratamentos propostos são, por construção,
  sempre menores que os tradicionais (o próprio quadro do artigo diz: média
  harmônica sempre abaixo da aritmética, primeiro quartil sempre abaixo da
  mediana). Estimar mais baixo aproxima do homologado sem que isso prove
  estimativa melhor.
- A seleção das licitações analisadas é pouco descrita: fala-se em "80% das
  licitações", em "universo de mais de 250 registros" e em amostra de dez.
- "Assertividade" não é definida como métrica.
- O texto traz resíduo do modelo de formatação no rodapé final (datas de
  recebimento de 2007 a 2009), sinal de revisão editorial frouxa.

## Relevância para este TCC

É o correlato brasileiro mais direto do cálculo do valor estimado, e foi
publicado em evento da SBC de sistemas de informação — o que também o torna
evidência de que o tema cabe nesse evento.

**Resolve um problema diferente do que foi medido em campo.** O software parte
do conjunto de cotações já montado e pergunta qual estatística aplicar. O
levantamento deste TCC mostrou que o gargalo é anterior: decidir, item por
item, se um preço candidato é comparável. O artigo pressupõe que os preços de
entrada são do mesmo item.

**O critério de sucesso contraria a prática observada.** A servidora
entrevistada seleciona três preços e para, justamente para não puxar a média
para baixo e preservar margem de negociação, já que o valor estimado é teto.
Um método que mira o valor homologado otimiza outra coisa. Isso sustenta a
decisão de deixar o critério de cálculo à escolha do operador (RF25) em vez de
impor um.

Não trata descrição de item, não gera documento e não registra trilha.

## Citáveis

> "os métodos tradicionalmente empregados, baseados em critérios estatísticos
> simples, como a média aritmética, mediana ou o menor preço, podem levar a
> distorções significativas, resultando em sobrepreço ou subpreço" (Faria; Silva;
> Soares, 2025, p. 241)

> "a etapa de formação do preço de referência antecede a fase externa do
> certame" (Faria; Silva; Soares, 2025, p. 242)

## Backlinks

- [[../decisões/2026-09-07-cobertura-de-fontes-e-memoria-de-calculo]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
