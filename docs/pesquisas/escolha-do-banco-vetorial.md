---
tipo: pesquisa
titulo: "Qual camada de persistência vetorial atende a busca filtrada da pesquisa de preços?"
status: recomendação, pendente de aval da orientação
criado: 2026-08-24
autor: Rafael Nobre de Souza
relacionado:
  - docs/projeto.md
  - docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md
tags: [pesquisa, banco-vetorial, pgvector, qdrant, arquitetura, decisão]
---

# Recomendação de camada de persistência vetorial

> **Baseada em medição própria.** A evidência que sustenta esta recomendação é o
> experimento da Iniciação Científica em andamento — *Comparação de desempenho de
> soluções de bancos de dados vetoriais para busca semântica: uma análise entre
> pgvector e bancos de dados especializados* —, cujos resultados parciais foram
> medidos em 23/08/2026. Literatura de terceiros entra como contexto, e a seção 4
> explica por que ela **não** decide neste caso.

## 1. Recomendação

**Qdrant** para o índice de itens de contratação. O motivo é um único resultado, e
ele não é sobre velocidade: é sobre **qualidade de recuperação sob filtro
restritivo**.

## 2. O dado que decide

Cenário B do experimento — busca vetorial combinada com filtro de metadados,
condição equalizada, `ef_search` = 64, K = 10. A seletividade *p* é a fração da
base que satisfaz o predicado.

| Seletividade | pgvector | Qdrant | Weaviate |
|---|---|---|---|
| 1 % | **0,0592** | 0,9996 | 0,5662 |
| 10 % | **0,6312** | 0,9912 | 0,9302 |
| 50 % | 0,9783 | 0,9848 | 0,9833 |
| 100 % | 0,9851 | 0,9974 | 0,9699 |

*recall@10, base de 100 mil vetores. A escala de 500 mil reproduz o padrão:
0,0656 no pgvector contra 0,9987 no Qdrant em p = 1 %.*

Com filtro de 1 %, o pgvector recupera **menos de 6 %** dos vizinhos corretos. A
causa está diagnosticada no relatório e não é de configuração: o pgvector aplica
o predicado como *post-filter* sobre os candidatos que o grafo HNSW devolveu, de
modo que sob seletividade restritiva poucos candidatos sobrevivem ao filtro.
Acrescentar índice B-tree sobre o atributo **não altera o resultado** — foi
testado. O Qdrant integra o predicado à travessia do grafo, e é por isso que
preserva o recall.

## 3. Por que esse é o cenário do trabalho, e não uma exceção

A composição da pesquisa de preços não busca item semelhante em toda a base.
Busca item semelhante **sob restrição composta**: categoria do objeto, recorte
geográfico, janela temporal e situação da contratação. Um exemplo do caso real —
*papel A4 comprado por município de porte comparável, no Pará, nos últimos doze
meses, contratação homologada* — é filtro de seletividade bem abaixo de 1 % sobre
um índice estadual.

Ou seja: a operação que o sistema vai executar em produção é justamente a que
separa os três sistemas. Busca sem filtro, onde o pgvector é competitivo, é o
caso raro aqui.

## 4. Por que a literatura de terceiros não decide isto

Há trabalho publicado favorecendo o pgvector, e ele **não contradiz** o dado
acima — mede outra coisa. [Benchmarking Open Source Vector Databases](https://consensus.app/papers/details/1ad8f058522f5f2daa4919b070c3be86/)
compara sete sistemas, incluindo os três avaliados aqui, e conclui que o pgvector
com HNSW supera os dedicados exceto o Chroma. [Comparative Analysis of Performance
Aspects Between Chroma and Pgvector](https://consensus.app/papers/details/cd5a463b6d6b5f24ade14e8c73ae586b/)
conclui que o pgvector é mais viável em produção, com overhead de armazenamento de
3 a 4 vezes contra 395 do Chroma.

**Os dois medem busca pura, sem filtro de metadados.** Nesse cenário o
experimento próprio concorda com eles: no Cenário A, em 100 mil vetores, o
pgvector registra a menor mediana (0,63 ms) e o maior *throughput* (1.369 QPS) de
toda a comparação.

A divergência de recomendação, portanto, não é conflito de evidência: é diferença
de pergunta. A literatura consultada não avaliou o cenário que governa este caso
de uso, e é por isso que a decisão se apoia na medição própria.

> Metadados dos dois trabalhos citados **não conferidos na fonte primária**. Não
> podem entrar em `refs.bib` nem ser citados no texto antes da conferência.

## 5. O que o volume de dados muda, e o que não

Contagens já medidas na investigação da API do PNCP: 19.549 editais com o termo
"aquisição" no Pará, 39 num município de pequeno porte, e uma contratação
examinada com 223 itens.

| Corpus | Escala estimada | Pesa na decisão? |
|---|---|---|
| Legislação e modelos de ETP e TR | 10³ a 10⁴ fragmentos | **Não.** Nessa escala os três sistemas empatam |
| Itens do município de referência, cinco anos | 10⁴ a 10⁵ vetores | Marginalmente |
| Itens de âmbito estadual | 10⁶ a 10⁷ | Sim, para latência e disco |
| Itens de âmbito nacional | 10⁸ ou mais | Fora do escopo do trabalho |

**O volume não é o eixo da decisão.** O déficit de recall do pgvector sob filtro
já aparece em 100 mil vetores e não melhora ao subir para 500 mil — 0,0592 e
0,0656. Se o critério fosse latência, medir o volume-alvo seria pré-requisito;
como o critério é recuperação sob filtro, ele já está resolvido na escala menor.

O volume importa para outra decisão, e essa fica em aberto: **o que indexar**.
Índice municipal, estadual ou nacional é escolha de escopo do produto, não de
tecnologia, e depende do que a fonte de domínio disser sobre a origem dos preços
que ela de fato usa.

## 6. Ressalvas que acompanham a recomendação

Declaradas no relatório parcial e não omitidas aqui:

- **O experimento não fechou.** A escala de 1 milhão de vetores e o cenário de
  carga mista — inserção concorrente com busca — estão previstos para a segunda
  fase, com relatório final em dezembro de 2026.
- **Medição única por configuração.** A reexecução mostrou que percentis altos
  isolados não se reproduzem: o mesmo ponto variou até 3,3 vezes em QPS entre
  execuções, com recall idêntico. A comparação que se sustenta é de mediana e de
  *throughput*, não de percentil extremo. **O recall, que é o que decide aqui,
  reproduziu** — desvio máximo de 0,0028.
- **Hardware único**, notebook com 16 GiB, e três das seis execuções da sessão
  registraram atividade de *swap* no hospedeiro, na escala de 500 mil.
- **O tempo de indexação do pgvector está subestimado como limite.** Os 8 a 12
  vezes a mais que os especializados refletem `maintenance_work_mem` no valor
  default de 64 MB, não capacidade máxima da implementação. Lê-se como default
  contra default.

Nenhuma dessas ressalvas atinge o resultado que sustenta a recomendação: o
diagnóstico de *post-filter* é arquitetural, foi verificado com índice dedicado
sobre o atributo, e o recall reproduziu entre execuções e entre escalas.

## 7. Consequência se a recomendação for aceita

- Persistência dividida: **PostgreSQL** para o relacional, o semiestruturado e a
  trilha de auditoria; **Qdrant** para o índice de similaridade.
- Custo assumido: dois sistemas em vez de um, com a sincronização entre eles
  passando a ser problema de projeto — e é exatamente o problema que a trilha de
  auditoria reproduzível tem de resolver de qualquer maneira.
- A alternativa de um só sistema continua aberta **para o corpus de legislação e
  modelos**, que é pequeno e não sofre do problema de filtro. Usar `pgvector` ali
  e Qdrant no índice de itens é desenho defensável, e reduz a superfície do
  segundo sistema.

## 8. O que decide isto

A recomendação vai à orientação com o dado parcial e a ressalva de que o
experimento não fechou. A pergunta a fazer é concreta: **ela aceita fechar a
arquitetura com resultado parcial, ou prefere esperar o relatório final de
dezembro?** Esperar atrasa a arquitetura, que atrasa a implementação. Decidir
agora assume o risco de a segunda fase mudar o quadro — risco baixo, porque o
resultado que decide é o recall sob filtro, e ele é o que mais reproduziu.
