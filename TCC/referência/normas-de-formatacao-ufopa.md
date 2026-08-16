---
tipo: referência
conceito: "normas de formatação da produção acadêmica da UFOPA"
tags: [abnt, normalização, latex]
---

# Normas de formatação da UFOPA

## Definição

Conjunto de regras de apresentação que a instituição exige dos trabalhos
acadêmicos, consolidando normas da ABNT e decisões próprias do Sistema
Integrado de Bibliotecas.

## Detalhamento

Os valores operacionais não são repetidos aqui de propósito: eles vivem em
`scripts/normas_ufopa.py` e são publicados em `docs/normas/README.md` por
geração. Duplicá-los nesta nota criaria uma terceira cópia para envelhecer.

O que importa registrar como conhecimento:

- O Regimento de Graduação vincula a entrega da versão definitiva do TCC às
  diretrizes do SIBI, o que torna o guia norma institucional e não sugestão.
- A ficha catalográfica é elaborada por bibliotecário da instituição, mediante
  solicitação via SIGAA — é dependência externa com prazo próprio, e precisa
  ser pedida antes da entrega final.
- A folha de aprovação pode ser substituída pela ata de defesa assinada.

## Variantes

A divergência que mais custa caro: o guia adota o padrão pós-2023 de citação em
caixa e baixa no texto — `(Brasil, 2005b)` — mantendo caixa alta apenas na lista
de referências. Modelos LaTeX brasileiros mais antigos produzem caixa alta nos
dois lugares.

## Onde aparece neste trabalho

Em todo o `texto/`. A conformidade é verificada por teste sobre o PDF compilado,
não por leitura.

## Fontes

UNIVERSIDADE FEDERAL DO OESTE DO PARÁ. Sistema Integrado de Bibliotecas. *Guia
para a elaboração e apresentação da produção acadêmica da Ufopa*. 3. ed. rev. e
atual. Santarém: Ufopa, 2025. Cópia em `docs/normas/`.

## Pegadinhas

- O recuo de parágrafo recomendado pelo guia é de 2 cm, diferente do valor mais
  comum em modelos ABNT (1,5 cm).
- Pré-textuais são contados na paginação, mas o número só aparece a partir da
  parte textual. A capa não é contada.
- O destaque dos títulos no sumário deve ser idêntico ao usado no texto.

## Backlinks
- [[../decisões/2026-08-16-template-latex-e-normas]]
