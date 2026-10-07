---
tipo: decisão
data: 2026-10-07
status: aceita
tags: [latex, formato, modelo-do-curso, sbc, sibi, fonte-única]
---

# Três alvos de layout: curso, SBC e SIBI

## Contexto

A decisão de 24/08 — [[2026-08-24-formato-do-texto-artigo-sbc]] — adotou o padrão
da SBC como alvo principal porque **o modelo do curso estava inacessível**: o
sítio respondia 301 em laço, sem servir um byte, e o *Guia de Trabalhos
Técnico-Científicos do Programa de Computação* não foi localizado em cópia
arquivada nenhuma. A escolha foi tomada com essa limitação declarada.

Em 07/10/2026 a orientadora cedeu o trabalho de um orientando anterior nos dois
formatos que exige: artigo e tradicional. O modelo deixou de ser inacessível.

## O que o modelo revelou

O artigo cedido **não segue o padrão da SBC**. Tem formato próprio: título,
autores com afiliação numerada e e-mail institucional, a orientadora como
coautora, rodapé com o curso, o endereço da instituição e "página de total".

A estrutura de seções também difere: objetivos e justificativa são subseções da
introdução, não há seção de fundamentação ou trabalhos relacionados, e requisitos
e projeto são os blocos de *Desenvolvimento*.

Não há arquivo de estilo publicado — só o PDF.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Trocar a SBC pelo modelo do curso | É o que a banca do curso conhece | Perde o alvo pronto para submissão a congresso, que foi a razão declarada em 24/08 |
| Manter só a SBC | Zero trabalho | O texto que ela lê não se parece com o modelo que ela mandou |
| **Três alvos irmãos: curso, SBC, SIBI** ✅ | Entrega no formato do curso, submete a congresso sem converter, deposita na biblioteca | Mais um pacote de estilo a manter e a cobrir por teste |

## Decisão

**Escolhida: três alvos.** Escolha do Pilot.

A infraestrutura já suportava: o conteúdo vive uma vez só, em `secoes/`, e cada
alvo é um arquivo fino que escolhe estilo e ordem. O custo marginal do terceiro
foi o pacote de estilo e o teste.

| Alvo | Para quê |
|---|---|
| `main-curso.tex` | O que o curso recebe |
| `main-sbc.tex` | O que um congresso aceita sem retrabalho |
| `main.tex` | O que a biblioteca exige no depósito |

## A diferença de natureza entre os testes

Esta é a parte que precisa sobreviver a esta sessão.

O alvo da SBC é conferido contra o `.sty` **publicado** pela SBC: existe
especificação normativa, e o teste compara a nossa geometria com a dela.

O modelo do curso chegou apenas como **PDF**. Não existe especificação para
comparar — existe um documento impresso, do qual se mede. `scripts/medir_geometria_pdf.py`
extrai as caixas de texto e infere margens, entrelinha e corpo de letra.

Por isso `tests/test_conformidade_curso.py` verifica **semelhança ao modelo
dentro de uma tolerância**, e não conformidade a uma norma. Uma falha ali
significa que o alvo se afastou do modelo — pode ser defeito nosso, ou pode ser
que o modelo tenha sido substituído por outro. As duas hipóteses merecem olhar
antes de mexer no `.sty`.

A tolerância é de meio centímetro nas margens, porque a caixa de uma palavra não
coincide com a margem tipográfica: depende da letra que abre e fecha cada linha.

## Medido

| Medida | Modelo | Nosso | Diferença |
|---|---|---|---|
| Margem esquerda | 2,70 cm | 2,70 cm | 0,00 cm |
| Margem direita | 2,73 cm | 2,71 cm | 0,03 cm |
| Margem superior | 2,74 cm | 2,82 cm | 0,08 cm |
| Margem inferior | 2,01 cm | 2,22 cm | 0,21 cm |
| Entrelinha | 16,2 pt | 16,2 pt | 0,0 pt |
| Altura de letra | 12,2 pt | 12,0 pt | 0,2 pt |

A diferença de três centésimos entre as margens laterais do modelo é ruído de
medição, não assimetria de projeto: nenhum editor produz margens diferentes por
0,3 mm de propósito. Adotou-se 2,70 cm nos dois lados.

## Consequência

**Muda:**

- A estrutura de seções do texto passa a seguir o modelo, com uma divergência
  declarada — ver abaixo.
- `texto/comum/curso-tcc.sty` nasce, com a origem de cada medida documentada.
- O `make pdf` passa a compilar três alvos, e pula o do curso em silêncio nos
  documentos que ainda não o têm.

**Divergência mantida de propósito:**

A seção de fundamentos e trabalhos relacionados, que o modelo não tem. Ela existe
por obrigação expressa da orientação na primeira reunião, que fixou o escopo da
fundamentação em administração pública, prefeituras e licitação. Suprimi-la para
imitar o modelo descumpriria o pedido anterior da mesma pessoa.

**Entra como dependência:**

- `palatino` e `mathpazo` no TeX Live. O modelo usa Palatino, e o TeX o entrega
  em duas metades: texto e matemática. O alvo não tem fórmula nenhuma, mas o
  LaTeX carrega o conjunto matemático ao fechar a página, e falha sem ele.

## Critério de revisão

- Se a orientação publicar o guia de trabalhos técnico-científicos, ou enviar um
  modelo diferente deste, o `.sty` passa a ser conferido contra aquele documento
  e esta decisão é revista.
- Se o alvo da SBC deixar de servir a algum congresso visado, ele pode ser
  aposentado sem tocar nos outros dois.

## Backlinks
- [[2026-08-24-formato-do-texto-artigo-sbc]]
- [[2026-08-16-template-latex-e-normas]]
