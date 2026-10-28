# TCC — Sistemas inteligentes aplicados à gestão pública

Fonte de verdade do projeto. Leia inteiro antes de trabalhar. Toda decisão que
sobreviver a esta sessão é registrada aqui ou numa nota de decisão no vault.

## Identidade

| | |
|---|---|
| **Título** | Sistemas inteligentes aplicados à gestão pública: automação da fase preparatória e pesquisa de preços em licitações municipais |
| **Autor** | Rafael Nobre de Souza |
| **Orientadora** | Socorro Vânia Lourenço Alves — *titulação a confirmar* |
| **Instituição** | Universidade Federal do Oeste do Pará — Instituto de Engenharia e Geociências, Santarém-PA |
| **Curso** | Bacharelado em Ciência da Computação |
| **Etapas** | TCC I em 2026.2 · TCC II com defesa prevista para 2027.1 |

## Problema

A Lei nº 14.133/2021 exige, na fase preparatória de cada contratação, a
elaboração de Estudo Técnico Preliminar (ETP) e Termo de Referência (TR), além
de pesquisa de preços que fundamente o valor estimado. Em prefeituras de
pequeno porte, essa fase concentra o maior atraso do processo: as secretarias
demandantes não têm modelo padronizado para redigir os documentos, e a cotação
depende de fornecedores que respondem devagar ou não respondem.

O caso de referência é a Prefeitura de Prainha-PA, com acesso direto a servidora
do setor de licitações como fonte de domínio.

## Proposta

Aplicação web de apoio — não substitui nenhum sistema em uso pela prefeitura,
não se integra a sistema legado, e entrega documentos nos formatos que o
processo administrativo já aceita. Dois módulos:

1. **Geração assistida de minutas** de ETP e TR, a partir de formulário guiado,
   com recuperação sobre a legislação e os modelos aprovados.
2. **Composição de pesquisa de preços** a partir da API pública do Portal
   Nacional de Contratações Públicas, com tratamento estatístico dos valores
   obtidos e geração do mapa de cotação.

O recorte de banco de dados, que motiva a orientação: persistência vetorial para
a busca semântica, indexação de dados semiestruturados vindos da API, e trilha
de auditoria que permita reproduzir uma pesquisa de preços exatamente como ela
era na data em que foi realizada.

> **O levantamento de requisitos de 06/09/2026 reformulou o módulo 2.** O
> município já usa um banco de preços comercial que resolve coleta, cálculo e
> registro de procedência. O gargalo medido não é obter preço — é decidir, item
> por item, se um preço candidato é comparável ao item demandado, porque a busca
> desses sistemas é por palavra. Isso reforça o recorte de banco de dados em vez
> de enfraquecê-lo: recuperação semântica com filtro estruturado obrigatório é
> exatamente o cenário medido na iniciação científica. O escopo exato do módulo
> segue em aberto — ver `docs/requisitos/README.md`.

## Estrutura do repositório

```
.
├── docs/
│   ├── projeto.md      # este arquivo
│   ├── normas/         # guia da UFOPA + destilado operacional (gerado)
│   ├── requisitos/     # requisitos funcionais, não funcionais e regras de negócio
│   ├── tasks/          # decomposição de trabalho em andamento
│   └── pesquisas/      # investigações que sustentam decisões
├── TCC/                # vault Obsidian — notas, fichamentos, decisões, logs
├── texto/              # LaTeX
│   ├── comum/          # preâmbulo e bibliografia compartilhados
│   ├── tcc1/           # projeto (2026.2)
│   └── tcc2/           # monografia (2027.1)
├── entregas/           # os três layouts sem marcador de pendência (gerado)
├── code/               # o sistema desenvolvido
├── scripts/            # manifesto de normas e geradores
└── tests/              # testes de conformidade do texto
```

Papéis separados, sem mistura:

- **`TCC/`** é o cérebro. Leitura, decisão, requisito, rascunho e log de sessão
  moram aqui em markdown. Backlinks fazem parte do método — é o que permite
  rastrear, na hora de escrever, qual fonte sustenta cada afirmação.
- **`texto/`** é o entregável. O PDF é gerado; o `.tex` é o fonte.
- **`code/`** é o sistema: Python, Django e HTMX sobre PostgreSQL, com Qdrant
  para o índice semântico. Interface só web, e em português. O código é
  escrito em inglês, e `code/GLOSSARY.md` faz a ponte com o vocabulário do
  domínio.
- **`docs/`** é o que o repositório precisa explicar a quem chega.

## Decisões firmes

Não revisitar sem motivo técnico novo. Cada uma tem nota em `TCC/decisões/`.

| Decisão | Escolha |
|---|---|
| Norma de formatação | Guia do SIBI/Ufopa, 3ª ed. (2025), internalizado em `docs/normas/` |
| Fonte das medidas | `scripts/normas_ufopa.py` — manifesto único; `.sty` e documentação são gerados |
| Composição do texto | LaTeX, `article` + preâmbulo próprio aderente ao guia |
| Bibliografia | `biblatex` com estilo `abnt` e backend `biber` |
| Caixa nas citações | Caixa e baixa no texto, caixa alta na lista — nunca ligar a opção `accite` |
| Fonte tipográfica | Times New Roman (via `mathptmx`) |
| Documentos do texto | Dois projetos irmãos com preâmbulo e bibliografia compartilhados |
| Dados de domínio | Documento real nunca versionado; testes e texto usam versão sintética |
| Classificação da pesquisa | *Design Science Research*, com o estudo na prefeitura como contexto de avaliação dentro dela |
| Contribuição declarada | O protocolo que corrige o viés do gabarito — contribuição do tipo "métodos e métricas de avaliação" |
| Persistência vetorial | Qdrant, por medição própria: sob filtro de 1%, a extensão do relacional recupera 6% dos vizinhos contra 99,96% |
| Linguagem e arcabouço | Python com Django e HTMX — continuidade com o ferramental da avaliação, sem alegação de superioridade |
| Banco relacional | PostgreSQL, por `JSONB` para o retorno da API e intervalo temporal para a trilha de auditoria |
| Idioma do código | Inglês em `code/`, com termos do domínio vindos de `code/GLOSSARY.md`; interface e o resto do projeto em português |
| Ordenação dos candidatos (RF23) | Lexicográfica por faixa de comparabilidade; proximidade de valor como \|ln(preço/esperado)\|, sem fusão num escore único |

## Política de dados

Documento real de processo licitatório — edital, ETP, TR, certidão, proposta,
mapa de cotação — entra em `dados-dominio/`, que não é versionado. Dele se
deriva à mão uma versão sintética, com a mesma estrutura e nenhum dado
verdadeiro, e é essa que aparece em teste, exemplo, figura e anexo.

A regra vale também para as notas do vault: não colar trecho literal de
documento real, nem "só para ilustrar". O repositório é público, e nome de
servidor, CNPJ de fornecedor e valor contratado não voltam atrás depois de
publicados.

## Convenções do vault

| Pasta | Conteúdo |
|---|---|
| `papers/` | Um fichamento por trabalho lido, com frontmatter e citação conferida na fonte |
| `referência/` | Notas conceituais reusáveis, linkáveis a partir de fichamentos e rascunhos |
| `decisões/` | Uma nota datada por decisão: contexto, opções, escolha, consequência, critério de revisão |
| `requisitos/` | Sessões com a fonte de domínio: o que foi dito, o que foi inferido, o que ficou em aberto |
| `validações/` | Testes com usuário e medições, com configuração e resultado |
| `drafts/` | Trechos destinados ao texto, com backlink para a fonte de cada afirmação |
| `lições/` | Erros cometidos e a regra que evita repeti-los |
| `sessões/` | Log condensado por sessão: onde paramos, o que foi entregue, próximo passo |

Antes de criar nota nova, verifique se há template em `TCC/_templates/`.

As pastas `requisitos/` e `lições/` existem no vault mas não são versionadas:
a primeira guarda relato de trabalho de terceiros, a segunda registra erros
próprios. As duas são de uso interno.

## Rigor bibliográfico

Regra dura, herdada de erro já cometido: **nunca preencher metadados de citação
a partir de memória.** Venue, ano, volume, páginas, tipo de trabalho e ordem das
iniciais dos autores são conferidos na fonte primária — o PDF do artigo, o
portal oficial da norma. Enquanto não conferida, a entrada em `refs.bib` fica
marcada com `VERIFICAR` e não pode ser citada no texto.

## Como trabalhar

```bash
# texto
cd texto/tcc1 && make pdf          # compila os três layouts; `make watch` ao salvar
cd texto/tcc2 && make pdf

# versão apresentável, sem os marcadores de pendência
python scripts/gerar_entregas.py   # regera entregas/
python scripts/gerar_figuras.py    # regera as figuras dos diagramas
python scripts/gerar_bpmn.py       # regera a figura do processo em BPMN

# normas
python scripts/gerar_normas.py     # regera .sty e docs/normas/README.md

# requisitos
python scripts/gerar_requisitos.py # regera .docx e .pdf a partir do README.md

pytest -m "not lento"              # manifesto e guardas de frescor
pytest                             # inclui conformidade do PDF compilado
```

O `.sty` gerado e a tabela de normas **não** são editados à mão: mude o
manifesto e regere. O teste falha se o disco divergir.

## Cronograma

| Etapa | Período | Entrega |
|---|---|---|
| 1 — Definição do tema e do problema | 2026.2 | Tema aceito pela orientadora |
| 2 — Revisão bibliográfica | 2026.2 | Fichamentos e fundamentação |
| 3 — Levantamento de requisitos | 2026.2 | Registro das sessões com a fonte de domínio |
| 4 — Modelagem de dados e arquitetura | 2026.2 | Modelo e decisões registradas |
| ▶ **TCC I** | fim de 2026.2 | Projeto qualificado |
| 5 — Implementação | 2027.1 | Sistema funcionando |
| 6 — Avaliação | 2027.1 | Resultados medidos |
| ▶ **TCC II** | fim de 2027.1 | Monografia e defesa |

A tabela do documento LaTeX é a versão canônica; esta espelha. Datas reais de
execução ficam em `TCC/sessões/` — cronograma de planejamento e log de execução
são coisas diferentes e não devem ser confundidos.

## Hardware

Máquina de trabalho desde 18/08/2026: MacBook com Apple M4, 10 núcleos, 16 GiB
de memória unificada, SSD de 460 GiB.

Antes: notebook Dell G15 5530 com Fedora Linux — Intel i5-13450HX (10c/16t),
16 GiB DDR5, NVMe 1 TB, NVIDIA RTX 3050 6 GB. Continua disponível, e é a única
das duas com GPU dedicada: se algum experimento exigir treinar ou rodar modelo
localmente, é nela.

A troca importa para o texto: o `README.md` traz o preparo do ambiente nas duas
plataformas, com as duas dependências que só o macOS exige (`libthai` para o
`biber` iniciar, `cm-super` para o PDF não sair com fonte rasterizada).

## Pendências abertas

A lista vive em **`docs/tasks/backlog.md`**, que é a fonte única. Cada item diz
quem resolve — autor, fonte de domínio, orientação, instituição ou terceiro —,
porque é isso que separa o que pode andar agora do que está bloqueado em alguém.

Esta seção não repete a lista de propósito. Pendência copiada em dois lugares
envelhece num deles, e quem lê não descobre qual.

O caminho crítico de hoje, só para orientar a leitura:

1. Medir volume e descrições da base pública, que dimensiona o índice.
2. Montar o conjunto de avaliação a partir dos relatórios de cotação recebidos.
3. Rodar a bateria de modelos de representação contra ele.

As decisões de escopo dos dois módulos e do desenho da avaliação foram fechadas
em 06/09/2026 e estão registradas em `TCC/decisões/`.
