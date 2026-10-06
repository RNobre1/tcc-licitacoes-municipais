---
tipo: paper
autores: ["Igor Sampaio", "Flávia Bernardini", "José Viterbo", "Daniel Oliveira", "Sérgio Fontes"]
ano: 2026
titulo: "Public procurement risk indicators from open government data and provenance model"
venue: "EGOV-CeDEM-ePart International Conference 2026 — Proceedings of Ongoing Research, Practitioners, Posters, Workshops, and Projects"
tags: [trabalhos-relacionados, proveniencia, trilha-de-auditoria, dados-abertos, controle-externo, brasil]
citacao_abnt: "SAMPAIO, Igor et al. Public procurement risk indicators from open government data and provenance model. In: EGOV-CEDEM-EPART INTERNATIONAL CONFERENCE, 2026, [s. l.]. Proceedings of ongoing research, practitioners, posters, workshops, and projects [...]. [S. l.]: TU Delft OPEN Publishing, 2026. DOI: 10.59490/6a91adc10fd2bd55cd254870."
arquivo_local: "TCC/papers/sampaio-2026-indicadores-risco-proveniencia.pdf"
verificado: true
---

# Public procurement risk indicators from open government data and provenance model

> **`verificado: true`** — conferido em 06/10/2026 contra o cabeçalho e o rodapé
> do PDF: evento, trilha dos anais, datas (30 de agosto a 3 de setembro de
> 2026), instituições-sede, editora, DOI e 13 páginas. **Os nomes dos autores
> foram tirados do PDF**: o registro do DOI os traz corrompidos, com a letra do
> índice de afiliação colada ao sobrenome ("Bernardinia", "Viterboa",
> "Oliveiraa", "Fontesb"). **A cidade do evento não consta no PDF** e ficou como
> `[s. l.]` — conferir antes de citar. Os anais não trazem paginação contínua.

## Síntese

Trabalho da Universidade Federal Fluminense com a UERJ. Propõe um método para
construir indicadores de risco em compras públicas a partir de dados abertos do
governo brasileiro, documentando por um modelo de proveniência como cada
indicador é derivado. O problema que motiva o trabalho é que indicadores desse
tipo costumam ser calculados sem que se consiga refazer o caminho do dado bruto
até o resultado. Instanciado com onze bases federais, produz 26 indicadores e é
avaliado por 28 auditores.

## Contribuições

- Método que une integração de dados abertos e modelagem de proveniência.
- 26 indicadores de risco, cada um com fonte na literatura ou em entrevista,
  bases necessárias, cálculo e limitação declarada.
- Ambiente integrado de dados de compras públicas, com código publicado.
- Avaliação com auditores da relevância das bases e dos indicadores.

## Método

Design Science. Três entrevistas semiestruturadas com profissionais de órgãos
federais de defesa da concorrência e de controle interno, somando cerca de oito
horas, com análise temática. Revisão rápida da literatura em três bases.

Onze bases federais integradas: transparência, programas sociais, justiça
eleitoral, catálogo de materiais e serviços, contratos, cadastro de pessoas
jurídicas, sancionadas, notas fiscais. O dado bruto é preservado em formato
original numa zona de entrada e transformado para uma zona refinada.

O modelo de proveniência se inspira no padrão do W3C e liga entidades,
atividades e agentes. O fluxo de derivação de cada indicador é modelado de
antemão.

Avaliação por questionário com 28 auditores, com resposta de sim, não ou não
sei para cada base e cada indicador, mais comentário aberto.

## Resultados-chave

- Concordância forte dos auditores quanto à utilidade das bases e dos
  indicadores, sobretudo quando usados de forma integrada. **Os percentuais
  estão só em figuras; o texto não traz os números.**
- A proveniência foi percebida como mecanismo de transparência e confiança.
- Limitações apontadas pelos auditores: dado desatualizado, bases não pensadas
  para fiscalização, barreira técnica de acesso.

## Limitações

- Avaliação qualitativa, com poucos auditores e só no contexto brasileiro.
- Indicador não é prova de fraude, e os autores insistem nisso.
- Trabalho publicado na trilha de pesquisa em andamento; o texto traz um
  parágrafo duplicado e uma seção de instrução do modelo não preenchida.
- A proveniência documenta a derivação prevista do indicador; não há
  demonstração de reconstituição de um resultado numa data passada.

## Relevância para este TCC

**Este trabalho obriga a reescrever a lacuna de proveniência.** A primeira
rodada do levantamento afirmava que nenhum trabalho de proveniência toca
compras públicas. Este toca, é brasileiro e é de 2026. A afirmação, como
estava, não pode ir para o texto.

O que continua não atendido, e é mais estreito:

| | Sampaio et al. | Este TCC |
|---|---|---|
| Etapa | Controle e fiscalização, depois da contratação | Fase preparatória, antes do edital |
| O que se rastreia | Como um indicador foi derivado das bases | Que candidatos estavam disponíveis, quais foram escolhidos, por quem e sob qual critério |
| Usuário | Auditor | Servidor que monta a cotação |
| Dimensão temporal | Dado bruto preservado; derivação modelada de antemão | Reconstituir a pesquisa como estava na data |
| Objeto | Fornecedores e contratos | Preço por item |

O trabalho é, na verdade, apoio ao argumento: mostra auditores brasileiros
dizendo que resultado analítico sem rastro de derivação é difícil de usar como
evidência. É o mesmo raciocínio que sustenta a exigência de procedência
resolvida até o registro de origem.

Os próprios autores indicam como trabalho futuro o uso de proveniência em
sistemas de apoio à decisão do serviço público — que é onde este TCC está.

## Citáveis

> "the analytical pipeline linking raw government data to risk or anomalies
> detection, among other tasks frequently remains insufficiently documented and
> difficult to audit" (Sampaio et al., 2026, p. 2)

> "provenance enables stakeholders to reconstruct the full derivation path from
> raw data to risk indicators" (Sampaio et al., 2026, p. 2)

> "Further studies may also explore the broader use of provenance modeling for
> documenting analytical processes and decision support systems in the digital
> public service delivery when traceability and other data qualities are
> required." (Sampaio et al., 2026, p. 11)

## Backlinks

- [[brandao-2024-plus]]
- [[staudinger-2024-recuperacao-reprodutivel]]
- [[../decisões/2026-09-07-cobertura-de-fontes-e-memoria-de-calculo]]
