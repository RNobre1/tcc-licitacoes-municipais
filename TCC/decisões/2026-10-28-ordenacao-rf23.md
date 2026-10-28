---
tipo: decisão
data: 2026-10-28
status: aceita
tags: [rf23, ordenação, proximidade, avaliação, protocolo, decisão-relevante]
---

# Candidatos ordenados por faixa de comparabilidade, e a proximidade de valor medida pelo logaritmo da razão

## Contexto

O RF23 manda aceitar uma estimativa de preço esperado e ordenar os candidatos
pelas duas dimensões, comparabilidade e proximidade de valor, **exibidas
separadamente**. O texto da arquitetura proíbe fundi-las num escore único.
Ninguém tinha definido como ordenar por duas dimensões sem fundi-las, nem como
medir a proximidade.

A decisão é relevante pelo protocolo do projeto. O R1 mede se o candidato certo
aparece "entre os primeiros resultados", e é a ordenação que define o que é
"primeiro". O R2 compara as condições com e sem estimativa de preço.

A investigação está em `docs/pesquisas/ordenacao-por-duas-dimensoes.md`.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| **A. Lexicográfica sobre faixas de comparabilidade** | Determinística. A estimativa só reordena dentro da faixa e nunca promove um candidato de faixa inferior. Sem estimativa, a ordem é a da comparabilidade | O limite das faixas é um parâmetro a calibrar |
| B. Coluna de ordenação escolhida pelo operador | Não pressupõe nada | Entrega a escolha a quem pode estar ancorado no preço, e o R1 passa a depender do operador |
| C. Fronteira de Pareto em camadas | Formalmente justificada, sem pesos | A camada pode ser grande, e "os primeiros" deixa de ser um número fixo de posições |
| D. Grade de faixas nas duas dimensões | Lembra o gesto da servidora | Dois conjuntos de limites a calibrar |
| E. Escore ponderado | Simples | Proibida pela arquitetura |

## Decisão

**Escolhida: a opção A.** Ela foi tomada pelo autor em 28/10/2026, com base na
pesquisa.

### Ordenação

Os candidatos são ordenados por:

1. faixa de comparabilidade, da mais alta para a mais baixa;
2. dentro da faixa, proximidade de valor crescente, quando há preço esperado;
3. semelhança decrescente;
4. identificador, para que a ordem seja estável.

**Limites de faixa provisórios, só para o protótipo:**

| Faixa | Semelhança |
|---|---|
| Alta | 0,80 ou mais |
| Média | de 0,60 até menos de 0,80 |
| Baixa | menos de 0,60 |

Esses valores **não são resultado de calibração**. Servem para o protótipo
funcionar e para a orientação ver a tela. Os valores definitivos são fixados no
C11, sobre um subconjunto de ajuste, **antes** de qualquer medição. Usar os
provisórios numa medição seria escolher o limiar olhando o resultado.

### Proximidade de valor

Para o preço unitário *p* > 0 e o preço esperado *e* > 0, na mesma unidade:
*d* = |ln(*p*/*e*)|. A tela exibe a proximidade como fator, por exemplo
"1,35× acima" ou "1,35× abaixo".

| Situação | O que acontece |
|---|---|
| Sem preço esperado | A coluna de proximidade mostra "—", e a ordem é faixa e semelhança. Nada é imputado no lugar da estimativa, nem a mediana dos candidatos |
| Unidade que não converte, ou *p* ≤ 0 | A proximidade é indefinida e sinalizada, e o candidato vai para o fim da sua faixa. Ela nunca vale 0 nem infinito |

**Por que o logaritmo.** A diferença absoluta depende da escala do preço, e a
diferença relativa é assimétrica: pagar o dobro do esperado conta 100%, pagar a
metade conta 50%. O logaritmo da razão é simétrico e adimensional. As fontes
que sustentam isso são de previsão, não de preço. Que a dispersão de preço
cresça com o nível do preço é uma hipótese a verificar nos dados públicos.

### Emendas ao protocolo de avaliação

A pesquisa mostrou que o gabarito foi montado por quem descarta pelo preço
antes de ler a descrição. Isso ficou registrado em campo. Os candidatos
próximos do preço que ela tinha em mente estão, portanto, super-representados
no gabarito. A condição "com estimativa" favorece justamente esses candidatos,
e o contraste entre as duas condições mistura o efeito do sistema com esse
viés. **É uma inferência**, que nenhuma fonte mede, e é testável.

O autor adota as três emendas propostas:

| # | Emenda | Onde entra |
|---|---|---|
| P1 | Reportar o R2 como curva. Sem estimativa, e com estimativa igual ao preço do gabarito mais ruído log-normal em vários níveis. O nível sem ruído é rotulado como limite superior, porque derivar a estimativa do próprio gabarito a transforma em oráculo | R2, no texto, e a bateria de C3 |
| P2 | Na sessão C5, pedir o preço esperado **antes** de mostrar os candidatos, e registrar de onde ele veio | Roteiro da C5 (C6) |
| P3 | No julgamento às cegas, sortear para cada item se o preço fica visível ou oculto. O conjunto sem preço é um gabarito livre do viés de seleção, e a diferença entre os dois estima a ancoragem | Protocolo da C5 |

O R1 passa a declarar a chave de ordenação que mede.

## Justificativa

A opção A é a única que preserva as duas colunas separadas e, ao mesmo tempo,
dá ao R2 uma propriedade interpretável. A condição com estimativa é a condição
sem estimativa reordenada dentro das faixas, então o ganho atribuível ao preço
fica limitado. O R1 continua sendo recall nos *k* primeiros. A reordenação
manual da opção B ficaria fora do que o R1 e o R2 medem.

**Limite que precisa ser dito.** Nenhuma fonte lida mede qual formato o
operador entende melhor. A escolha se apoia em propriedades formais e no
encaixe com a avaliação, e não em evidência de uso. Por ser só exibição, ela é
reversível.

## Consequência

- A T05.3 do protótipo implementa a ordenação e a proximidade desta nota, com os limites provisórios.
- O C11 ganha uma tarefa explícita: fixar os limites de faixa antes de medir.
- O backlog registra P1, P2 e P3 e corrige a afirmação de que a avaliação em duas condições "não é afetada".
- **A orientação é informada desta decisão na reunião de 07/11.** O autor optou por decidir e informar, em vez de pedir aval antes, nesta decisão.

## Critério de revisão

Reabrir se:

1. o escore de semelhança se mostrar pouco calibrado, com faixas instáveis entre conjuntos. Nesse caso, considerar a opção C;
2. a sessão C5 mostrar que o candidato aceito costuma estar numa faixa inferior, mas perto do preço. Nesse caso, considerar C ou D;
3. a emenda P3 mostrar que exibir a proximidade desloca o julgamento de comparabilidade. Nesse caso, ocultar a coluna até o operador marcar a comparabilidade;
4. a orientação discordar das emendas ao protocolo na reunião de 07/11.

## Backlinks

- [[../sessões/2026-10-28]]
- [[2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
