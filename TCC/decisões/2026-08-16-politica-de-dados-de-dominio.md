---
tipo: decisão
data: 2026-08-16
status: aceita
tags: [dados, lgpd, ética, repositório]
---

# Documento real de licitação nunca é versionado

## Contexto

A fonte de domínio tem acesso a documentos reais de processos licitatórios do
município: editais, ETPs, Termos de Referência, certidões, propostas e mapas de
cotação. Esses documentos são o melhor material possível para entender o
domínio e para testar o sistema — e carregam nome de servidor, CNPJ de
fornecedor, valores e endereços. O repositório do trabalho é público.

## Opções consideradas

| Opção | Fidelidade ao real | Risco |
|---|---|---|
| Versionar documentos reais | Máxima | Inaceitável: exposição de dado pessoal em repositório público, irreversível |
| Versionar documentos anonimizados | Alta | Anonimização de PDF é difícil de garantir; um resíduo esquecido é publicação definitiva |
| **Documento real fora do versionamento, fixture sintética versionada** ✅ | Suficiente | Fixture pode não refletir a bagunça do real — mitigável ampliando os casos |

## Decisão

**Escolhida:** documento real vai para `dados-dominio/`, ignorada pelo git, e
serve apenas para leitura e entendimento. Dele se deriva **à mão** uma versão
sintética — mesma estrutura, nenhum dado verdadeiro — e é essa que aparece em
teste, exemplo, figura e anexo do texto.

## Justificativa

Vazamento em repositório público não volta atrás: o histórico do git preserva
o arquivo mesmo depois de removido, e um clone feito nesse intervalo é
permanente. A fixture sintética entrega o que o desenvolvimento precisa — a
estrutura do documento — sem carregar o que cria risco.

Como efeito secundário, a política dispensa autorização formal da prefeitura
para publicar o repositório.

## Consequência

- Nenhuma nota do vault pode conter trecho literal de documento real, nem "só
  para ilustrar".
- A limitação precisa ser declarada na metodologia do texto: a avaliação usa
  dados sintéticos, e isso restringe o que se pode afirmar sobre o
  comportamento do sistema diante da variedade real de documentos.

## Critério de revisão

Reabrir se a prefeitura autorizar formalmente, por escrito, a publicação de
documentos específicos — o que muda o cálculo de risco, mas não a preferência
pela fixture nos testes.

## Backlinks
- [[2026-08-16-repositorio-publico]]
