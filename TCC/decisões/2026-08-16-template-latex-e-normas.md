---
tipo: decisão
data: 2026-08-16
status: aceita
tags: [latex, abnt, normas, fonte-única]
---

# Template LaTeX próprio, com as normas da UFOPA como manifesto único

## Contexto

Não existe modelo LaTeX oficial da UFOPA disponível. O que existe é o *Guia para
a elaboração e apresentação da produção acadêmica da Ufopa* (3. ed., 2025), do
SIBI, e exemplos de TCC aprovados no curso.

Ao conferir o guia contra os modelos ABNT usuais, apareceu uma divergência que
invalida o reaproveitamento direto de template antigo: o guia adota o padrão
**pós-2023** para citação no texto — `(Barbosa, C., 1958)`, `(Brasil, 2005b)`,
em caixa e baixa — mantendo o sobrenome em caixa alta apenas na lista de
referências.

## Opções consideradas

| Opção | Citação no texto | Veredito |
|---|---|---|
| `abntex2cite` com estilo `alf` | CAIXA ALTA | Reprovada: diverge da norma da própria instituição |
| Classe `abntex2` completa | Depende do pacote de citação | Traz muito elemento que este trabalho não usa |
| **`article` + preâmbulo próprio + `biblatex` estilo `abnt`** ✅ | Caixa e baixa | Aderente ao guia; comprovado por compilação |

## Decisão

**Escolhida:** `article` com preâmbulo próprio em `texto/comum/ufopa-tcc.sty`,
bibliografia com `biblatex` estilo `abnt` e backend `biber`.

As medidas normativas não ficam no `.sty`: vivem em `scripts/normas_ufopa.py`,
manifesto único de onde o `.sty` e a documentação `docs/normas/README.md` são
**gerados**. Um teste falha se o disco divergir do manifesto, e outro compila o
PDF e verifica o que ele realmente entrega.

## Justificativa

A verificação empírica confirmou que `biblatex-abnt` produz exatamente o par
exigido — `(Canto, 2014)` no texto, `CANTO, Sidney Augusto.` na lista — porque
seu comportamento padrão usa caixa e baixa na citação. A opção `accite`, que
força caixa alta, **não deve ser ligada**.

O manifesto único resolve o problema que apareceria de qualquer jeito: as
mesmas medidas precisariam concordar entre o preâmbulo, a documentação e a
conferência antes da entrega. Três lugares, e o compilador não alcança nenhum
dos dois últimos.

## Consequência

- Mudar uma margem significa editar o manifesto e rodar o gerador. Editar o
  `.sty` gerado à mão faz o teste falhar, por construção.
- TCC I e TCC II compartilham preâmbulo e bibliografia. Copiar configuração de
  um para o outro é proibido.
- Depende de `biblatex-abnt`, que não vem no TeX Live padrão do Fedora — está
  instalado em `~/texmf/tex/latex/biblatex-abnt`.

## Critério de revisão

Reabrir se a UFOPA publicar modelo LaTeX oficial, se sair a 4ª edição do guia,
ou se o colegiado exigir elemento que o `article` não comporte bem.

## Backlinks
- [[../referência/normas-de-formatacao-ufopa]]
- [[../lições/2026-08-16-armadilhas-do-template-latex]]
