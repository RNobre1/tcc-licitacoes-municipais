---
tipo: decisão
data: 2026-08-24
status: aceita
tags: [latex, formato, artigo, sbc, normas, fonte-única, orientação]
---

# Texto principal no formato de artigo da SBC; layout do SIBI passa a ser o alvo de depósito

## Contexto

A decisão de 16/08 — [[2026-08-16-template-latex-e-normas]] — escolheu o guia do
SIBI como norma de formatação, por ser o único documento normativo da instituição
disponível. Ela continua correta para o problema que resolvia. O que mudou é o
problema.

Na primeira reunião de orientação, em 19/08, a orientadora fixou que o texto
principal é **artigo de 20 a 25 páginas**, e não o formato tradicional. Também
informou que a **biblioteca não aceita o modelo do curso no depósito** e exige o
formato tradicional, com capa, folha de rosto e agradecimento. O mesmo conteúdo
passou a ter dois destinos com layouts incompatíveis.

Perguntada se o modelo do curso segue o padrão da Sociedade Brasileira de
Computação, respondeu que o curso afirma seguir, mas que o material está
desatualizado. Essa dúvida motivou a investigação documental abaixo.

## O que a investigação encontrou

O sítio do curso está **inacessível**: os endereços com e sem o prefixo `www2`
respondem 301 um para o outro, em laço infinito, sem servir um byte. A
investigação usou cópias arquivadas, e por isso **todo achado aqui é datado e
não confirmado como vigente**.

| Fonte | Data da cópia | O que estabelece |
|---|---|---|
| Resolução do Colegiado do curso nº 01/2014, de 10/11/2014 | 2019-12 | Produtos possíveis do TCC: monografia **ou** artigo científico completo. Quanto à forma, remete ao *Guia de Trabalhos Técnico-Científicos do Programa de Computação*. Art. 18: o produto de TCC I é a **Proposta de Trabalho**, definida naquele guia. Art. 19, § único: a Proposta vai a **comissão de docentes**, não só ao orientador |
| Página de TCC do curso | 2020-01 | Estrutura comum aos dois formatos: Resumo, Abstract, Introdução, Trabalhos Relacionados, Desenvolvimento, Análise dos Resultados, Conclusão, Referências |
| Modelo de TCC publicado pelo curso | 2019-12 | Arquivo **Word**. Modelo próprio, e **não** o padrão da SBC: margens 2,50/1,90/2,70 cm, títulos em Arial, citação **numérica** |
| *Guia de Trabalhos Técnico-Científicos do Programa de Computação* | — | **Não localizado.** Sem cópia arquivada em nenhum endereço da instituição |

Ou seja: o modelo que o curso publica e o padrão da SBC são artefatos distintos,
e divergem no que tem consequência de configuração — a chamada de citação é
numérica em um e autor-data no outro.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Manter só o layout do SIBI | Já implementado, testado, gerado do manifesto | Contraria a orientação recebida. O texto que a banca lê é o artigo |
| Adotar o modelo próprio do curso | É o que o sítio do curso publica | Cópia de 2019 não confirmada; internamente inconsistente com a própria página do curso; não serve a submissão em congresso |
| **Padrão da SBC como principal, SIBI como depósito** ✅ | É o que a orientadora nomeou, e o único que serve à banca **e** a um congresso sem retrabalho | Nenhuma fonte do curso o confirma por escrito |

## Decisão

**Escolhida:** o **padrão da SBC** passa a ser o alvo principal do texto. O
layout do SIBI **não é descartado** — passa a ser o alvo de depósito na
biblioteca.

Escolha do Pilot, reafirmada depois de eu apresentar o achado de que o modelo
publicado pelo curso não é a SBC. Razão declarada por ele: *"ela vai mandar um
modelo de qualquer forma em algum momento, então podemos seguir o da SBC por
enquanto, até por fins de publicar em congresso"*.

O conteúdo continua **único**, em `secoes/` no TCC I e `capitulos/` no TCC II.
Cada alvo é um documento fino que só escolhe estilo e ordem.

## Justificativa

A orientação é quem avalia, e ela nomeou a SBC. Some-se a isso o que ela mesma
ofereceu na reunião: submeter o artigo a congresso da área, com o precedente de
um orientando cujo trabalho foi aceito e recebeu nota máxima. Nesse caminho, o
padrão da SBC deixa de ser aproximação e passa a ser o formato exigido — adotá-lo
agora é o único que não cobra retrabalho depois.

Manter o layout do SIBI é a decisão mais barata das disponíveis: já está
implementado, gerado do manifesto e coberto por teste, e a biblioteca vai
exigi-lo de qualquer maneira.

**As medidas da SBC não foram copiadas para o manifesto.** O `.sty` publicado
pela SBC é a fonte única do formato, e `tests/leitura_sbc.py` lê a geometria
dele. Aqui a relação com o manifesto de normas se inverte de propósito: para o
guia do SIBI o repositório é dono do fato, porque não existe artefato oficial em
LaTeX; para a SBC o artefato existe e é ele que os congressos aceitam.

## O que foi implementado e verificado nesta data

| Verificação | Resultado |
|---|---|
| `pytest` | 70 passed, 4 skipped (antes: 36 passed, 4 skipped) |
| `ruff check` e `ruff format` | limpos |
| `make pdf` em TCC I | 4 páginas SBC, 13 páginas SIBI |
| `make pdf` em TCC II | 2 páginas SBC, 13 páginas SIBI |
| Overfull hbox no alvo SBC | 0 |
| Contraprova do alvo SIBI | texto extraído **idêntico** ao anterior nos dois documentos, 13 páginas antes e depois |

Três defeitos apareceram no caminho, cada um com o conserto na causa:

1. **`secoes/07-cronograma.tex` chamava `singlespace` diretamente**, ambiente do
   `setspace` que só existe no alvo do SIBI. Carregar `setspace` no alvo SBC
   esconderia o problema e a próxima seção quebraria igual. O conserto foi criar
   o ambiente `ufopaespacosimples` nos dois alvos: a seção compartilhada pede o
   **efeito**, não o mecanismo.
2. **`refs.bib` tinha comentários `%` dentro das entradas.** O BibTeX clássico
   descarta a entrada inteira ao encontrá-los, com aviso só no `.blg` e um `[?]`
   no PDF como único sintoma. O `biblatex` aceita as duas formas, e por isso o
   defeito ficou dormente até este alvo existir. Comentários movidos para antes
   de cada entrada, sem perder uma palavra, e a regra registrada no cabeçalho.
3. **O `.gitignore` excluía `texto/**/main.pdf`** — regra que nomeia o arquivo de
   hoje. `main-sbc.pdf` nasceu fora dela e entraria no repositório. Trocada por
   `texto/*/*.pdf`, que cobre **posição** em vez de nome, com
   `tests/test_arvore_versionada.py` como guarda, inclusive para alvo que ainda
   não existe.

Duas duplicações foram eliminadas no caminho, porque o segundo alvo as revelou:
os utilitários de leitura de PDF, que estavam privados na suíte do SIBI e agora
vivem em `tests/leitura_pdf.py`; e os dois `.latexmkrc` idênticos, agora
reduzidos a um `do` de `texto/comum/latexmkrc-comum`.

## Consequência

- **Orçamento de página é restrição de projeto.** 20 a 25 páginas com
  fundamentação, sistema e avaliação dentro. `tests/test_conformidade_sbc.py`
  falha acima de 25.
- **Resumo passa a ter duas versões, e é a única duplicação de prosa
  legítima.** A SBC pede no máximo 10 linhas; a NBR 6028 pede 150 a 500
  palavras no alvo do SIBI. Não são a mesma coisa cortada.
- **A decisão de 16/08 sobre caixa nas citações fica restrita ao alvo do SIBI.**
  O alvo SBC usa `sbc.bst` com BibTeX clássico, que produz `[Brasil 2021]`. A
  regra de nunca ligar `accite` continua valendo onde se aplica.
- **`sbc.bst` é de 2001 e não imprime `subtitle` nem `urldate`.** O dado
  continua em `refs.bib` e sai no alvo do SIBI. Conferir quando as entradas de
  legislação passarem a ser citadas de fato.
- **`make pdf` agora compila os dois layouts.** `pdf-sbc` e `pdf-sibi` fazem um
  de cada vez.
- **Os arquivos da SBC não foram conferidos contra o sítio oficial.** Vieram de
  réplica em repositório de terceiro, com somas SHA-256 registradas em
  `texto/comum/sbc/PROCEDÊNCIA.md`. Antes de submeter a congresso, baixar do
  sítio da SBC e comparar.
- **O modelo do curso continua pendente**, e a orientadora vai enviá-lo. Quando
  chegar, comparar com o que está registrado aqui.

## Critério de revisão

Reabrir quando a orientadora enviar o modelo do curso, quando o Guia de
Trabalhos Técnico-Científicos for obtido, ou se a orientação dispensar o
depósito no formato tradicional.

## Backlinks
- [[2026-08-16-template-latex-e-normas]]
- [[../sessões/2026-08-19]]
- [[../requisitos/2026-08-19-orientacao-primeira-reuniao]]
