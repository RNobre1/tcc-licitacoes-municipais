# Primeira reunião com a orientadora — 18/08/2026

Dois dias de preparo. O objetivo da reunião **não** é entregar texto pronto: é
ela aceitar orientar e ajudar a fechar o recorte. Escrever muito antes disso é
escrever antes de saber o que ela vai querer mudar.

## O que levar

Um documento de 2 a 3 páginas, com esta estrutura:

| Seção | Extensão | O que precisa ter |
|---|---|---|
| Problema | 2 parágrafos | O que a lei exige na fase preparatória e onde isso trava num município pequeno. Com citação dos artigos. |
| Proposta | 1 parágrafo + lista | Os dois módulos, e a característica de não ser invasivo |
| Recorte de dados | 1 parágrafo | Por que isto é um problema de banco de dados — o gancho com a área dela |
| Viabilidade | meia página | O que já foi verificado: a lei aponta o PNCP, a API é pública, os dados existem |
| O que já está feito | 3 linhas | Estrutura do projeto, normas da UFOPA instrumentadas |
| Perguntas em aberto | lista | O que preciso decidir com ela |

Não leve cronograma detalhado nem arquitetura. Nesta reunião os dois viram
conversa, não compromisso.

## Perguntas para ela

Administrativas, que travam o documento:

1. Titulação, para a folha de rosto.
2. Texto exato da natureza do trabalho para TCC I, conforme o colegiado.
3. Datas do calendário de 2026.2 e o que o colegiado exige na entrega do TCC I.
4. O produto do TCC pode ser artigo publicado? Isso muda o planejamento inteiro
   do segundo semestre.

De conteúdo, que definem o trabalho:

5. O recorte cabe em dois semestres, ou os dois módulos são trabalho demais?
6. Ela vê o eixo de banco de dados como suficiente, ou quer puxar mais para um
   lado específico — busca por similaridade, modelagem temporal, auditabilidade?
7. Como ela avalia a questão da contribuição: um sistema funcionando basta, ou
   o trabalho precisa de uma pergunta de pesquisa com resposta medida?
8. O desenho de avaliação proposto — tempo por etapa como medida de esforço e
   verificação automática de completude como medida de conformidade — serve,
   ou ela prefere outro?

## Roteiro de leitura — camada 0, antes da reunião

Fontes primárias. São as que sustentam o problema e as que ela pode cobrar.

| # | O quê | Onde | Tempo | Por quê |
|---|---|---|---|---|
| 1 | Lei nº 14.133/2021 — Art. 6º (inciso XX: ETP; inciso do TR), Art. 18 (fase preparatória) e Art. 23 (valor estimado) | planalto.gov.br | 1h | Só esses artigos, não a lei inteira. O Art. 23, §1º, I nomeia o PNCP como parâmetro — é o alicerce do módulo de cotação |
| 2 | Instrução Normativa SEGES/ME nº 65/2021 | gov.br/compras | 40 min | Metodologia oficial da pesquisa de preços: parâmetros admitidos, cesta de preços, tratamento de valores discrepantes. É o requisito funcional do seu módulo, escrito por quem regula |
| 3 | ~~Manual das APIs de Consulta do PNCP + Swagger~~ | pncp.gov.br/api/consulta/swagger-ui | 1h, mexendo | ✅ **FEITO em 17/08.** Resultado em [`docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md`](../pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md) |

### O que a verificação da API respondeu

Resumo do que levar para a reunião — detalhamento e evidência na nota de pesquisa:

- **O módulo é viável.** Preço unitário por item, com fornecedor e data, é
  acessível publicamente e sem credencial.
- **Mas não pela API que a documentação de consulta anuncia.** É preciso
  combinar duas interfaces, uma delas não documentada.
- **A busca do portal não alcança a descrição do item** — só o objeto da
  contratação. Isto é o achado que sustenta o recorte de banco de dados: sem
  índice próprio sobre as descrições, não há pesquisa de preço por item.
- **A API de Consulta oficial estava fora do ar** durante toda a janela de
  teste. Indisponibilidade da fonte é risco medido, não hipotético.
- **A paginação falha em silêncio:** o padrão devolve 10 itens de uma
  contratação que tem 223, com HTTP 200 e sem aviso.

## Roteiro de leitura — camada 1, depois da reunião

Literatura acadêmica. Encontrada em busca preliminar; **os metadados ainda não
foram conferidos** e nenhuma destas pode ser citada antes disso.

| Eixo | Referência | Onde |
|---|---|---|
| PLN em compras públicas no Brasil | "Uso de processamento de linguagem natural e aprendizagem de máquina…" — TCC de CC, UFCG | dspace.sti.ufcg.edu.br |
| PLN em compras públicas no Brasil | "Técnicas de Processamento de Linguagem Natural em…" — SEMISH/SBC | sol.sbc.org.br |
| Classificação de documentos de licitação | Dissertação sobre classificação e modelagem de tópicos, UFMG | repositorio.ufmg.br |
| IA no controle de compras públicas | Trabalho de pós-graduação do TCU | sites.tcu.gov.br |
| Recuperação sobre texto jurídico | "Towards Reliable Retrieval in RAG Systems for Large Legal Datasets" | arXiv:2510.06999 |
| Geração de documento jurídico | "Enhancing legal document building with Retrieval-Augmented Generation" | ScienceDirect |
| Panorama de IA em compras públicas | Open Contracting Partnership, 2026 | open-contracting.org |

Para ampliar a lista, use `docs/pesquisas/prompt-levantamento-literatura.md`.

## Ordem sugerida dos dois dias

**Dia 1** — ✅ a leitura 3 está feita: a API entrega o que o projeto precisa, com
três ressalvas registradas na nota de pesquisa. Restam as leituras 1 e 2,
anotando os artigos que sustentam cada afirmação do problema. Na leitura 2, uma
pergunta específica ficou pendente da verificação técnica: **a IN 65 admite
preço homologado de contratação pública como parâmetro, e em que ordem de
preferência?** É o que decide se o dado que a API entrega serve como
fundamentação legal do valor estimado.

**Dia 2** — discutir as conclusões das leituras e escrever o documento de 2 a
3 páginas, com as fontes já em mãos.

O levantamento de literatura fica para **depois** da reunião: ela pode eliminar
metade dos eixos de busca, e leitura apressada de artigo é pior que leitura
nenhuma.

## Risco a encarar antes de escrever

O maior risco deste projeto não é técnico: é o trabalho virar desenvolvimento
de sistema sem pergunta de pesquisa. "Construí um sistema que faz X" não é
contribuição científica por si só, e a banca avalia contribuição explicitamente.

Duas saídas possíveis, a discutir com ela:

- **Pergunta comparativa:** o sistema é o instrumento, e a contribuição é a
  medição — por exemplo, comparar estratégias de recuperação sobre texto
  normativo quanto à fidelidade do documento gerado.
- **Pergunta de aplicação:** a contribuição é caracterizar o problema num
  contexto pouco estudado — município pequeno da Amazônia — e demonstrar
  viabilidade com avaliação junto a usuários reais.

Levar as duas para a reunião, com preferência declarada, vale mais que levar a
pergunta pronta.
