# Casos de uso

Visão geral do que o sistema faz para quem o usa. Esta lista é a **fonte**. O
diagrama, na página "Casos de uso" de `docs/arquitetura/arquitetura.drawio`,
desenha esta lista, e o texto do TCC a cita. `tests/test_casos_de_uso.py`
falha se os dois divergirem, ou se um requisito essencial ficar sem caso de
uso que o atenda.

Cada caso de uso ganha documento próprio, com fluxo principal, fluxos
alternativos e regras de negócio, **quando for implementado**, e não antes. A
coluna *Detalhamento* aponta para esse documento quando ele existir.

## Atores

| Ator | Tipo | Quem é |
|---|---|---|
| **Operador do setor de licitações** | Principal | Servidor que conduz a fase preparatória. É o único perfil de usuário do sistema, como decidido em 22/09/2026 |
| **Base pública de contratações (PNCP)** | Secundário, sistema externo | Interface pública do Portal Nacional de Contratações Públicas, de onde vêm os itens contratados que servem de preço de referência |

### Quem não é ator, e por quê

A **secretaria demandante** aparece como raia no modelo de processo, mas não é
ator aqui. Ela formaliza a demanda e participa do alinhamento da descrição,
mas faz isso **fora do sistema**: entrega o documento ao setor e conversa com
o servidor. Quem opera o sistema é o setor de licitações. O modelo de processo
responde a *quem faz cada etapa*; o diagrama de casos de uso responde a *quem
usa o sistema para quê*. São perguntas diferentes.

## Casos de uso

| Código | Caso de uso | Atores | Requisitos | Objetivo | Detalhamento |
|---|---|---|---|---|---|
| UC01 | Importar demanda | Operador | RF01, RF15, RF39 | Trazer para o sistema os itens dos documentos de formalização de demanda ou de uma planilha, e corrigir o que a extração errou | a escrever na implementação |
| UC02 | Validar itens da demanda | Operador | RF02, RF10 | Conferir unidade, item composto, descrição insuficiente para cotação e a coerência entre unidade requisitante, dotação e objeto | a escrever na implementação |
| UC03 | Consolidar demandas entre secretarias | Operador | RF03, RF35, RF36, RF38 | Unir o mesmo item pedido por secretarias distintas, com descrição de consenso decidida pelo operador e a restrição de entrega mais estrita preservada | a escrever na implementação |
| UC04 | Triar candidatos a preço de referência | Operador | RF16, RF17, RF18, RF20, RF21, RF23, RF32 | Recuperar candidatos por significado, sob os filtros da norma, e decidir um a um se são comparáveis, com a decisão registrada na trilha | a escrever na implementação |
| UC05 | Calcular valor estimado e gerar mapa de cotação | Operador | RF25, RF26 | Chegar ao valor estimado pelo critério escolhido e emitir o mapa com a procedência de cada preço | a escrever na implementação |
| UC06 | Gerar minuta do estudo técnico preliminar | Operador | RF04, RF09, RF11, RF14, RF37 | Emitir a minuta anterior à pesquisa de preços, com a estimativa de valor redigida como providência futura | a escrever na implementação |
| UC07 | Gerar termo de referência | Operador | RF05, RF06 | Derivar o termo de referência dos mesmos dados do estudo técnico, com a consistência entre os dois verificada | a escrever na implementação |
| UC08 | Emitir estudo técnico final | Operador | RF11, RF37 | Reescrever a estimativa de valor com o resultado da pesquisa, mantendo as demais seções da minuta | a escrever na implementação |
| UC09 | Revisar e exportar documentos | Operador | RF07, RF33 | Editar qualquer conteúdo gerado e exportar em formato editável | a escrever na implementação |
| UC10 | Reconstituir pesquisa anterior | Operador | RF30, RF32 | Ver uma pesquisa de preços como ela era na data em que foi feita, com as decisões e os candidatos de então | a escrever na implementação |
| UC11 | Manter índice de contratações públicas | Base pública de contratações | RF31 | Coletar da base pública os itens contratados e indexá-los para a busca por significado | a escrever na implementação |

## Relações entre casos de uso

| Relação | De | Para | Condição |
|---|---|---|---|
| `«extend»` | UC03 | UC02 | Só acontece quando o mesmo item é pedido por mais de uma secretaria. É a primeira decisão exclusiva do modelo de processo |

A segunda decisão exclusiva do modelo de processo — pular a pesquisa de preços
quando o preço vem de ata de registro ou de contrato vigente — **não** vira
relação aqui: ela não acrescenta comportamento a um caso de uso, só dispensa
que UC04 e UC05 aconteçam.

## Correspondência com o modelo de processo

| Etapa do modelo de processo | Caso de uso |
|---|---|
| Importar documentos de demanda · Extrair itens, quantidades e unidades | UC01 |
| Decisão "item pedido por mais de uma secretaria?" · Propor descrição de consenso | UC03 |
| Emitir minuta do estudo técnico | UC06 |
| Recuperar candidatos por significado · Triar candidatos e decidir | UC04 |
| Calcular valor e gerar mapa de cotação | UC05 |
| Gerar estudo final e termo de referência | UC07, UC08 |
| Revisar e assinar as peças | UC09; a assinatura acontece fora do sistema |

Formalizar a demanda e alinhar a descrição com as secretarias também acontecem
fora do sistema, e por isso não aparecem como caso de uso.

## O que fica de fora desta lista

Os requisitos **importantes** e **desejáveis** da especificação entram no caso
de uso a que pertencem quando forem implementados. A guarda cobra cobertura só
dos essenciais, porque são eles que definem o escopo mínimo.
