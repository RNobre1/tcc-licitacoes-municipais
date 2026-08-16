---
tipo: decisão
data: 2026-08-16
status: aceita
tags: [repositório, github, autoria]
---

# Repositório público, sem ferramental de assistente

## Contexto

O repositório serve a três públicos ao mesmo tempo: a banca, que avalia o
trabalho; quem no futuro quiser reaproveitar a solução; e o mercado, que lê o
perfil do autor. Isso favorece deixá-lo público desde o começo. Em paralelo, o
projeto lida com dado sensível e usa ferramental de assistente de código no
desenvolvimento.

## Decisão

**Repositório público desde o primeiro commit**, com duas exclusões:

1. Dado real de processo licitatório, conforme [[2026-08-16-politica-de-dados-de-dominio]].
2. Qualquer vestígio de ferramental de assistente — arquivos de configuração,
   diretórios de agente, e menção em mensagem de commit ou em conteúdo
   versionado.

Para não perder histórico do que importa, o conteúdo do projeto — identidade,
decisões, cronograma, política de dados, estrutura — fica em `docs/projeto.md`,
versionado e escrito como documentação de projeto. As instruções de trabalho com
o assistente ficam num arquivo à parte, fora do versionamento, que importa
aquele.

## Justificativa

O repositório é peça de avaliação e de portfólio. A autoria do trabalho é do
aluno, e o histórico deve refletir isso sem ambiguidade.

A separação em duas camadas evita o custo colateral óbvio da exclusão: se todo o
documento saísse do versionamento, o arquivo mais importante do projeto ficaria
sem histórico, sem diff e sem backup.

## Consequência

- Antes de qualquer commit, conferir que nenhum arquivo de ferramental entrou no
  índice.
- Mensagens de commit sem trailer de coautoria.
- `docs/projeto.md` precisa ser mantido legível para quem chega de fora, não
  apenas para quem já conhece o projeto.

## Critério de revisão

Reabrir se a orientadora ou o colegiado exigir repositório fechado até a defesa.

## Backlinks
- [[2026-08-16-politica-de-dados-de-dominio]]
