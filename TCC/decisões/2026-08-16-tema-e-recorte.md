---
tipo: decisão
data: 2026-08-16
status: aceita
tags: [tema, escopo, govtech]
---

# Tema do TCC: automação da fase preparatória de licitações municipais

## Contexto

O tema precisava atender a três condições simultâneas: ser um software (não um
estudo puramente teórico), ter acesso real a quem sente a dor, e caber em dois
semestres. O funil partiu de dois domínios com fonte de domínio dentro de casa —
gestão pública (mãe, servidora do setor de licitações da Prefeitura de
Prainha-PA) e agronomia (pai e irmão, técnicos agrônomos).

## Opções consideradas

| Opção | Domínio | Por que foi descartada ou escolhida |
|---|---|---|
| Hub de chamadas públicas PNAE/PAA | Agro + licitações | Híbrido: exige entender dois domínios e dois grupos de usuário |
| Assistente de campo com sincronização offline | Extensão rural | Arquitetura offline-first com resolução de conflito é o problema mais difícil da lista, e o teste real exige ir a campo |
| Analisador de documentos de habilitação | Licitações, fase externa | Depende de OCR sobre PDF digitalizado por terceiro; a qualidade da entrada é o maior risco e não é controlável |
| **Apoio à fase preparatória: minutas + pesquisa de preços** ✅ | Licitações, fase interna | Entrada controlada pelo próprio sistema, dados públicos disponíveis, validação diária com a fonte de domínio, e ataca o gargalo apontado por ela |

## Decisão

**Escolhida:** apoio à fase preparatória, com dois módulos — geração assistida
de minutas de ETP e TR, e composição de pesquisa de preços a partir de dados
públicos de contratações.

O módulo de pesquisa de preços entrou depois do funil inicial, por informação da
fonte de domínio: a cotação é a etapa mais demorada da rotina dela. Como a
pesquisa de preços faz parte da fase preparatória, o módulo cabe no mesmo
recorte em vez de ampliá-lo.

## Justificativa

- A entrada do sistema é controlada por formulário próprio, não por arquivo
  enviado por terceiro — o que remove a maior fonte de falha das alternativas.
- A legislação, os modelos de documento e os dados de contratações são públicos.
- A solução é não invasiva: não substitui sistema em uso pela prefeitura, não
  exige integração com sistema legado, e entrega arquivo nos formatos que o
  processo administrativo já aceita. Isso torna um piloto real viável dentro do
  prazo do TCC.

## Consequência

- Fica **fora de escopo**: fase externa do certame, julgamento de propostas,
  análise de habilitação, integração com portal de pregão e com sistema
  financeiro do município.
- O recorte de banco de dados — busca por similaridade, indexação de dados
  semiestruturados e trilha de auditoria — passa a ser o eixo acadêmico do
  trabalho, por ser a área da orientadora.

## Critério de revisão

Reabrir se a orientadora apontar que o recorte é largo demais para dois
semestres, ou se o levantamento de trabalhos relacionados mostrar que um dos
módulos já está resolvido de forma amplamente disponível.

## Backlinks
- [[../requisitos/2026-08-16-contexto-inicial-do-dominio]]
