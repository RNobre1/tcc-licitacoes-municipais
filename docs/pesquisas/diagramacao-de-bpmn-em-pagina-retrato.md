---
tipo: pesquisa
titulo: "Como artigos publicados cabem um processo em BPMN numa página em retrato"
status: um experimento e três exemplos de compras públicas lidos por inteiro; diretrizes de modelagem lidas no preprint; frequência das soluções não mensurável com a amostra
criado: 2026-10-18
autor: Rafael Nobre de Souza
relacionado:
  - docs/pesquisas/metodologia-dsr-e-modelagem-de-processo.md
tags: [pesquisa, bpmn, processo, diagramacao, legibilidade]
---

# Diagramação de BPMN em página retrato

## 1. O problema

O processo da fase preparatória tem 14 etapas em 3 raias. Desenhado com raias
horizontais e fluxo da esquerda para a direita, a figura fica com proporção de
cerca de 2:1. Reduzida à largura da coluna, o texto das caixas cai abaixo de
5 pt. Página em paisagem foi descartada.

## 2. Resposta curta

1. **A especificação permite raias verticais.** Piscina e raia se estendem pelo
   diagrama "either horizontally or vertically", e a geometria guarda isso num
   atributo próprio [1, §10.8; §12]. Não é improviso.
2. **Não há, na literatura encontrada, levantamento de quantas vezes cada
   solução aparece em artigos.** Os quatro diagramas de compras públicas
   examinados usam quatro soluções diferentes — seção 4. Com quatro casos, não
   se fala em "predominante".
3. **A evidência medida mais próxima do nosso caso contraria a decomposição em
   subprocessos.** Num experimento com 200 participantes e dois modelos BPMN
   reais, o modelo achatado — sem subprocessos — foi tão bem ou melhor
   compreendido que o modelo com subprocessos em vistas separadas, e o papel
   superou a tela. Os autores registram que **a folha A4 foi inadequada** para
   ler os modelos, de 122 a 133 nós, e usaram A3 [2].
4. **A diretriz de tamanho mais citada manda decompor acima de 50 elementos**
   [3, G7]. O processo de 14 etapas, com eventos e desvios, fica abaixo disso;
   a diretriz não obriga a decompor.
5. **Recomendação: raias verticais em página retrato inteira, modelo achatado.**
   Seção 6.

## 3. O que a literatura diz sobre tamanho e compreensão

| Fonte | Tipo de evidência | O que sustenta | Leitura |
|---|---|---|---|
| Türetken et al., *Business & Information Systems Engineering*, 2020 [2] | **Experimento**: 60 profissionais e 140 alunos de pós-graduação; dois modelos BPMN reais de colaboração, 122 e 133 nós, 5 piscinas cada; três formas — achatado, achatado com grupos, subprocessos recolhidos em vistas separadas | Subprocessos em vistas separadas **não** melhoraram a compreensão; em perguntas locais, a pioraram (efeito de atenção dividida). O achatado foi percebido como mais fácil. O papel deu mais acertos que a tela. A4 foi inadequada; usaram A3 | **Lido por inteiro** |
| Mendling, Reijers e van der Aalst, *Information and Software Technology*, 2010 [3] | **Síntese** de estudos empíricos anteriores, mais consulta a especialistas | Sete diretrizes. G1: usar o menor número de elementos. G7: decompor acima de 50 elementos, porque acima disso a probabilidade de erro de modelagem tende a passar de 50% | **Lido no preprint** de julho de 2009, nas seções de fundamentação e das diretrizes. A versão publicada não foi aberta. **Ressalva:** o limiar de 50 vem de probabilidade de **erro de modelagem** em modelos de outra notação, não de compreensão de leitor |

Encontrados na base de literatura acadêmica e **não lidos** — não citar:

| Fonte | Por que importaria | Por que não |
|---|---|---|
| Mendling et al., 2012, *Journal of Systems and Software* | Limiares derivados de 2.000 modelos para medidas de tamanho e complexidade | Cópia aberta indicada não respondeu |
| Avila et al., 2020, *Business Process Management Journal* | Revisão sistemática de 45 diretrizes de modelagem e da evidência empírica de cada uma | Acesso fechado |
| Dikici et al., 2017, *Information and Software Technology* | Revisão sistemática dos fatores de compreensibilidade | Cópia aberta não obtida |
| Reijers et al., 2011, *Information Systems* | Experimento em que subprocessos ajudaram pela ocultação de informação | Acesso fechado |
| Schreiber et al., 2024, *Information Systems* | Rastreamento ocular: fragmentação prejudica tarefas que cruzam módulos | Baixado e não lido por inteiro |

O conjunto não lido é a contraprova de [2]: há resultado a favor de
subprocessos [Reijers 2011, não lido]. A conclusão honesta é que a evidência
sobre decomposição é mista, e a mais próxima do nosso formato — BPMN de
colaboração, no papel — é a de [2].

## 4. Exemplos de compras públicas, e como cada um foi diagramado

| Fonte | Processo | Diagramação | Raias | Elementos | Partido? | Leitura |
|---|---|---|---|---|---|---|
| Trilha, Alves e Nunes, *Navus*, 2018 [4] | Compra por dispensa de licitação numa universidade federal | **Raias verticais, fluxo de cima para baixo**, página retrato inteira | 4 (requerente, coordenadoria, direção de compras, contabilidade) | 25 atividades numeradas, um desvio, início e fim | **Sim: continua na página seguinte**, com o cabeçalho das raias repetido | **Lido por inteiro**. O artigo chama a figura de fluxograma, com formas de BPMN |
| Araújo, Rodrigues Filho e Gonçalves, *Brazilian Journal of Operations & Production Management*, 2016 [5] | Licitação num instituto federal | Figura **girada 90°** ocupando página inteira — paisagem dentro de página retrato | 8 setores | Cerca de 30, contados na figura | Não | **Lido por inteiro**. A outra figura do artigo, com 3 raias e poucos elementos, cabe na largura da coluna sem girar |
| Semerdjieva e Krastev, *Serdica Journal of Computing*, 2012 [6] | Compra pública na Bulgária | **Decomposição**: uma visão geral de colaboração com subprocessos, e uma figura filha por fase | Visão geral com 3 piscinas, contadas na figura | Visão geral pequena; filhas com cerca de 6 a 10 elementos, contados na figura | **Sim, por subprocessos** | **Lido por inteiro** |
| Türetken et al., 2020 [2] | Dois processos de qualidade de uma empresa grande | No experimento, impressos em **A3**; no artigo, reduzidos e **sem rótulos**, só para mostrar tamanho | 5 piscinas | 122 e 133 nós | Testado com e sem subprocessos | Lido por inteiro |

**Achado com Lei 14.133/2021 não lido:** Dal'Bosco Re et al., 2026, *Smart and
Sustainable Built Environment*, modela em BPMN um macroprocesso federal com
municípios alinhado à nova lei. Acesso não confirmado; não citar.

**Sobre a pergunta (e) — reduzir raias.** Nenhum dos exemplos lidos descreve ter
colapsado participantes para caber a figura. Não há evidência para essa opção.

## 5. O que a especificação diz sobre orientação

Lida na especificação BPMN 2.0.2 (OMG, formal/13-12-09):

- "a Lane is a sub-partition within a Process [...] and will extend the entire
  length of the Process level, either vertically [...] or horizontally";
- a piscina "extends the entire length of the Diagram, either horizontally or
  vertically";
- na geometria, um atributo "determines if it should be depicted horizontally
  (true) or vertically (false)".

Raia vertical é BPMN válido, e o formato de arquivo registra a escolha.

## 6. Recomendação

**Raias verticais, três colunas, fluxo de cima para baixo, numa página retrato
inteira, com o modelo achatado.** Três colunas na largura útil de uma página A4
deixam cada raia com cerca de 5 cm, e 14 etapas empilhadas usam a altura que a
página tem e a largura que falta. A especificação permite [1]; um artigo
brasileiro de compras públicas fez exatamente isso [4]; e o experimento mais
próximo não dá vantagem a subprocessos no papel [2]. Se não couber numa
página, partir em duas continuando as mesmas colunas, como em [4], em vez de
recolher subprocessos.

**Custo:** o verificador de geometria precisa aceitar raias verticais; o
gerador da figura precisa dispor o fluxo de cima para baixo.

## 7. Referências

| # | Referência | Identificador | Arquivo local |
|---|---|---|---|
| [1] | OBJECT MANAGEMENT GROUP. *Business Process Model and Notation (BPMN)*, version 2.0.2. Documento formal/13-12-09. 2013 | `https://www.omg.org/spec/BPMN/2.0.2/` | `TCC/papers/omg-2013-bpmn-2-0-2.pdf` |
| [2] | TURETKEN, O.; DIKICI, A.; VANDERFEESTEN, I.; ROMPEN, T.; DEMIRORS, O. The influence of using collapsed sub-processes and groups on the understandability of business process models. *Business & Information Systems Engineering*, v. 62, n. 2, p. 121-141, 2020. Publicado on-line em 2019 | doi:10.1007/s12599-019-00577-4 | Lido no navegador, acesso aberto; não salvo |
| [3] | MENDLING, J.; REIJERS, H. A.; VAN DER AALST, W. M. P. Seven process modeling guidelines (7PMG). *Information and Software Technology*, v. 52, n. 2, p. 127-136, 2010 | doi:10.1016/j.infsof.2009.08.004 | `TCC/papers/mendling-2010-7pmg-preprint.pdf` (preprint) |
| [4] | TRILHA, C. C. S.; ALVES, G. K.; NUNES, R. S. Avaliação dos processos de compras com dispensa de licitação: estudo em uma universidade federal. *Navus*, v. 8, n. 2, p. 73-86, 2018 | doi:10.22279/navus.2018.v8n2.p73-86.617 | `TCC/papers/trilha-2018-compras-dispensa-bpmn.pdf` |
| [5] | ARAÚJO, M. B.; RODRIGUES FILHO, B. A.; GONÇALVES, R. F. Business process management notation for a costing model conception. *Brazilian Journal of Operations & Production Management*, v. 13, n. 3, p. 244-251, 2016 | doi:10.14488/BJOPM.2016.v13.n3.a2 | `TCC/papers/araujo-2016-bpmn-licitacao-ifsp.pdf` |
| [6] | SEMERDJIEVA, M.; KRASTEV, E. BPMN analysis of public procurement. *Serdica Journal of Computing*, v. 6, n. 2, p. 195-206, 2012 | doi:10.55630/sjc.2012.6.195-206 | `TCC/papers/semerdjieva-2012-bpmn-compras-publicas.pdf` |

Metadados de [2] a [6] conferidos no PDF e no registro do DOI em 18/10/2026. O
número do fascículo de [6] vem só do registro do DOI.

Busca na base de literatura acadêmica em 18/10/2026, sem filtro:
*process model size understandability empirical experiment number of elements
error probability*; *modularization of process models subprocess decomposition
understandability experiment*; *BPMN modelagem processo licitação compras
públicas administração pública*.
