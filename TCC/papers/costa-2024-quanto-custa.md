---
tipo: paper
autores: ["Lucas G. L. Costa", "Marco Túlio Dutra", "Gabriel P. Oliveira", "Mariana O. Silva", "Daniela Cruz Soares", "Luciana de Cássia Silva Faria", "Wagner Meira Jr.", "Gisele L. Pappa"]
ano: 2024
titulo: "Quanto Custa: Banco de Preços de Compras Públicas do Estado de Minas Gerais"
venue: "Anais Estendidos do XXXIX Simpósio Brasileiro de Banco de Dados (SBBD 2024) — oficina de ciência de dados contra a corrupção no setor público"
tags: [trabalhos-relacionados, sistema-existente, pesquisa-de-precos, busca-por-palavra, brasil]
citacao_abnt: "COSTA, Lucas G. L. et al. Quanto Custa: banco de preços de compras públicas do estado de Minas Gerais. In: WORKSHOP ON DATA SCIENCE AGAINST CORRUPTION IN THE PUBLIC SECTOR (DS-COPS); SIMPÓSIO BRASILEIRO DE BANCO DE DADOS (SBBD), 39., 2024, Florianópolis. Anais [...]. Porto Alegre: Sociedade Brasileira de Computação, 2024. p. 239-245. DOI: 10.5753/sbbd_estendido.2024.243804."
arquivo_local: "TCC/papers/costa-2024-quanto-custa.pdf"
verificado: true
---

# Quanto Custa: Banco de Preços de Compras Públicas do Estado de Minas Gerais

> **`verificado: true`** — conferido em 06/10/2026. Autores, evento, cidade e
> paginação (239 a 245), no cabeçalho e no rodapé do PDF; nome da oficina,
> edição, local e editora, na referência fornecida pela biblioteca digital da
> SBC na página do artigo. O sobrenome de uma autora aparece sem acento no PDF
> ("Cassia") e com acento no registro da biblioteca ("Cássia").

## Síntese

Artigo de demonstração de sete páginas. Apresenta a ferramenta web que resulta
da linha de pesquisa de [[brandao-2024-plus]],
[[silva-2024-sobrepreco-itens-licitacao]] e
[[brum-2024-agrupamento-itens-similares]]: um banco de preços com mais de 30
milhões de itens de licitações, contratos e notas fiscais de Minas Gerais, com
busca, estatística de preço e alerta de sobrepreço. Foi desenvolvida pelo
Ministério Público do estado com a UFMG.

**É, ao mesmo tempo, artigo e sistema existente** — o único dos correlatos
brasileiros de preço em que a ferramenta em uso é descrita.

## Contribuições

- Integração de itens de compras municipais e estaduais com três fontes
  externas de preço de referência: medicamentos, combustíveis e hortifrúti.
- Padronização e desambiguação de descrições de item, reaproveitando os
  trabalhos anteriores do grupo.
- Duas formas de busca e três telas de análise.
- Dois estudos de caso de uso.

## Método

Não há experimento. O artigo descreve dados, arquitetura em quatro camadas —
interface, serviço, armazenamento num motor de busca textual e processamento
distribuído — e funcionalidades, e ilustra com dois casos.

## Resultados-chave

**Como a ferramenta busca.** Duas formas:

- **busca "inteligente"**: correspondência de texto com no mínimo 70% de
  precisão — isto é, casamento aproximado de palavras;
- **busca "assistida"**: o usuário escolhe restrições entre os termos — todas as
  palavras, ao menos uma, não contendo, frase exata — e pode usar operadores
  lógicos e caractere curinga.

Filtros de ano, mês, preço unitário, tipo de licitação, região e unidade de
medida.

**O que entrega.** Total de itens e de unidades, preço mínimo, médio e máximo,
histórico no tempo, e marcação de itens acima do limite de sobrepreço.

**Primeiro estudo de caso: obter preço de referência para abrir uma licitação.**
Para achar preços de um palco de seis por quatro metros, o usuário monta uma
consulta que exige a palavra "palco", exige o padrão "6", curinga, "x", curinga,
"4" — para cobrir "6mx4m", "6 x 4" e "6x4" — e exclui a palavra "equipamento",
para tirar da lista os itens de iluminação. Filtra por ano e lê o preço médio.

## Limitações

Não declaradas. Da leitura:

- **A ferramenta só está disponível para usuários internos do Ministério
  Público.** Prefeitura não tem acesso.
- Cobre só Minas Gerais.
- Nenhuma avaliação de qualidade da busca.
- Não registra o que o usuário escolheu nem permite refazer uma consulta
  passada.

## Relevância para este TCC

Corrige uma afirmação e fornece o melhor exemplo publicado do problema.

### A correção

A segunda rodada do levantamento dizia que nenhum correlato brasileiro de preço
apoia quem monta a cotação. **Este apoia, em parte:** consultar preço de
referência para abrir licitação é um dos dois usos descritos. A afirmação
correta é mais estreita — ele apoia **por busca de palavra**, entrega
estatística sobre tudo o que a consulta devolveu, e deixa com o usuário o
trabalho inteiro de decidir o que é comparável.

### O exemplo

O estudo de caso do palco é a descrição, feita pelos próprios autores de um
banco de preços acadêmico, do custo que este trabalho mediu em campo. Para
obter um preço de referência, o usuário precisa:

- prever de antemão as formas como a medida pode ter sido escrita, e codificá-las
  em curinga;
- prever que palavra indesejada vai contaminar o resultado, e excluí-la;
- repetir isso para cada item.

É o mesmo fenômeno dos exemplos relatados pela servidora — a busca por alface
que traz sanduíche, a de trator que traz locação —, agora num sistema
construído por um grupo de pesquisa e apresentado como caso de sucesso. **A
comparabilidade é programada à mão, consulta por consulta.**

### As diferenças para o quadro

| | Quanto Custa | Este trabalho |
|---|---|---|
| Busca | Por palavra, aproximada ou com operadores | Por proximidade de significado |
| Comparabilidade | O usuário a codifica na consulta | Filtro estruturado de unidade, quantidade, natureza, região e período |
| Finalidade principal | Fiscalização e alerta de sobrepreço | Composição da pesquisa de preços |
| Quem usa | Servidores do Ministério Público | Servidor da prefeitura |
| Abrangência | Um estado | Base nacional |
| Registro de decisão | Não | Sim, por requisito |
| Avaliação da busca | Não há | Contra cotações reais |

A existência do sistema reforça, além disso, o argumento de acesso: a melhor
ferramenta pública brasileira do gênero não está ao alcance de quem faz a
cotação no município.

## Citáveis

> "A busca inteligente realiza a correspondência de texto com no mínimo 70% de
> precisão, enquanto a busca assistida permite escolher vários tipos de
> restrições entre os termos buscados" (Costa et al., 2024, p. 242)

> "Como a descrição do item de uma compra pública é um campo de texto livre,
> cada município preenche os dados de forma específica, sem um padrão."
> (Costa et al., 2024, p. 241)

> "A ferramenta está disponível apenas para os usuários internos do MPMG"
> (Costa et al., 2024, p. 240)

## Backlinks

- [[brandao-2024-plus]]
- [[silva-2024-sobrepreco-itens-licitacao]]
- [[brum-2024-agrupamento-itens-similares]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
