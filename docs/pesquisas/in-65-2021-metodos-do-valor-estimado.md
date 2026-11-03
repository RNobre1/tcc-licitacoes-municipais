# Métodos do valor estimado na IN SEGES/ME nº 65/2021

Leitura na fonte primária, feita em 03/11/2026, para sustentar os testes do
cálculo do valor estimado (RF25). Fecha a pendência do backlog "texto da
instrução normativa que ampara a pesquisa de preços".

**Fonte:** Instrução Normativa SEGES/ME nº 65, de 7 de julho de 2021, publicada
no *Diário Oficial da União*:
<https://www.in.gov.br/en/web/dou/-/instrucao-normativa-seges-/me-n-65-de-7-de-julho-de-2021-330673635>.

## O artigo 6º, na íntegra

> **Metodologia para obtenção do preço estimado**
>
> Art. 6º Serão utilizados, como métodos para obtenção do preço estimado, a
> média, a mediana ou o menor dos valores obtidos na pesquisa de preços, desde
> que o cálculo incida sobre um conjunto de três ou mais preços, oriundos de um
> ou mais dos parâmetros de que trata o art. 5º, desconsiderados os valores
> inexequíveis, inconsistentes e os excessivamente elevados.
>
> § 1º Poderão ser utilizados outros critérios ou métodos, desde que
> devidamente justificados nos autos pelo gestor responsável e aprovados pela
> autoridade competente.
>
> § 2º Com base no tratamento de que trata o caput, o preço estimado da
> contratação poderá ser obtido, ainda, acrescentando ou subtraindo determinado
> percentual, de forma a aliar a atratividade do mercado e mitigar o risco de
> sobrepreço.
>
> § 3º Para desconsideração dos valores inexequíveis, inconsistentes ou
> excessivamente elevados, deverão ser adotados critérios fundamentados e
> descritos no processo administrativo.
>
> § 4º Os preços coletados devem ser analisados de forma crítica, em especial,
> quando houver grande variação entre os valores apresentados.
>
> § 5º Excepcionalmente, será admitida a determinação de preço estimado com
> base em menos de três preços, desde que devidamente justificada nos autos
> pelo gestor responsável e aprovada pela autoridade competente.
>
> § 6º Quando o preço estimado for obtido com base única no inciso I do art.
> 5º, o valor não poderá ser superior à mediana do item nos sistemas
> consultados.

## O que isso fixa no sistema

| Ponto | Origem | Consequência |
|---|---|---|
| Três métodos: média, mediana e menor valor | caput | São as três funções do dia 06 |
| Três ou mais preços | caput e § 5º | Com menos de três, o valor pode ser calculado, mas exige justificativa. É a RN06. O sistema sinaliza, e não recusa |
| Nenhum preço | consequência do caput | Não há valor estimado. Nunca vale zero, porque o valor estimado é teto (RN05), e zero desclassificaria toda proposta |
| Descarte de inexequíveis, inconsistentes e excessivos | caput e § 3º | Exige critério fundamentado e descrito no processo. É o RF24 e a RN10. As funções do dia 06 recebem a lista já tratada |
| Outros métodos, como a média saneada da RN09 | § 1º | Só com justificativa. A média saneada depende do critério de descarte, que ainda não foi decidido |
| Acréscimo ou desconto percentual | § 2º | Fora do protótipo |
| Teto pela mediana dos sistemas oficiais | § 6º | Vale só quando a única fonte é o inciso I do art. 5º. Fora do protótipo |

## O que a norma não diz

- **Arredondamento.** A norma não fixa casas decimais nem regra de
  arredondamento. Como o valor estimado é teto (RN05), arredondar para cima ou
  para baixo muda quais propostas ficam abaixo dele. As funções devolvem o valor
  exato, em `Decimal`, e o arredondamento fica para a memória de cálculo do
  RF25, como decisão aberta no backlog.
- **Critério de discrepância.** O § 3º exige critério fundamentado, mas não diz
  qual. A escolha é do RF24, também aberta no backlog.
