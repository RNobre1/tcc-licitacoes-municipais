# Coleção Postman — API do PNCP

Requisições que sustentam
[`../api-pncp-viabilidade-pesquisa-de-precos.md`](../api-pncp-viabilidade-pesquisa-de-precos.md).

Cada requisição carrega asserções que verificam um achado da nota. **Se uma
asserção falhar, a nota está desatualizada** — a coleção é a guarda de frescor da
pesquisa, no mesmo espírito do teste que compara o `.sty` gerado com o manifesto.

## Importar

1. Postman → **Import** → arraste `pncp.postman_collection.json`.
2. Abra `0. Descobrir contratação` → **Buscar compra encerrada com resultado** →
   **Send**.
3. Pronto. Esse passo grava `cnpj`, `ano` e `seq` nas variáveis da coleção; todas
   as outras requisições passam a funcionar.

Não há arquivo de *environment* e não é preciso preencher nada à mão. Isso é
deliberado: nenhum identificador de contratação real fica gravado em arquivo
versionado, conforme a política de dados do projeto.

Para rodar tudo de uma vez: **Collection Runner**, na ordem das pastas.

## O que tem em cada pasta

| Pasta | Para quê |
|---|---|
| `0. Descobrir contratação` | Busca por termo. Popula as variáveis |
| `0b. Varredura pela API de Consulta` | **Caminho principal.** Varre por período e município, sem termo. Também popula as variáveis |
| `1. O que o projeto precisa` | O caminho até o preço unitário por item |
| `2. Armadilhas` | Cinco comportamentos que produzem resultado errado sem erro |
| `3. Provas negativas` | O que a API **não** faz, a prova de que a leitura é pública e o registro do endpoint que mudou de lugar |
| `4. Especificações` | OpenAPI cru das duas APIs |

Qualquer uma das duas pastas de descoberta (`0` ou `0b`) serve para popular as
variáveis. A diferença importa:

| | `0. Descobrir` (`/api/search/`) | `0b. Varredura` (API de Consulta) |
|---|---|---|
| Documentada | não | **sim** |
| Precisa de termo de busca | **sim**, obrigatório | não |
| Filtro de município | id interno do PNCP | **código IBGE oficial** |
| Total e nº de páginas | `total` | `totalRegistros`, `totalPaginas` |
| `User-Agent` de navegador | **obrigatório** | não |
| Disponibilidade observada | estável | caiu por ~1h40 em 17/08 e devolveu 500 em 18/08 |

Use `0b` como padrão. Use `0` quando precisar procurar por termo — é a única
forma de fazer isso.

## O endpoint que mudou de lugar em 18/08/2026

Se você rodou esta coleção em 17/08, a requisição **Contratação (cabeçalho)**
passava com 200 na API de Integração. Em 18/08 o mesmo endereço passou a
devolver **301**:

```
Este endpoint foi movido para:
https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}
```

A coleção já aponta para o endereço novo. O antigo ficou registrado como prova
negativa, porque o fato importa mais que o conserto: **o contrato da API mudou
em um dia, sem versão e sem changelog.**

A migração é **parcial** — e é isso que salva o projeto. `/itens`,
`/itens/quantidade` e `/itens/{n}/resultados` continuam na API de Integração
respondendo 200; os mesmos caminhos sob `/api/consulta` devolvem 404. O preço
unitário por item, que é o dado que interessa, não mudou de casa.

Para ver o 301 com os próprios olhos, **desligue** *Automatically follow
redirects* nas Settings do Postman — com ele ligado o app segue o redirecionamento
e a evidência some. No terminal:

```bash
curl -i "https://pncp.gov.br/api/pncp/v1/orgaos/01611858000155/compras/2025/141"
```

## Três coisas que vão te surpreender

**A busca exige `User-Agent` de navegador.** Sem ele o servidor encerra a
conexão sem devolver código HTTP. A coleção já manda o cabeçalho; se você
reescrever a requisição do zero, não esqueça. A pasta `2. Armadilhas` tem uma
requisição que reproduz a falha de propósito.

**A paginação falha em silêncio.** `/itens` devolve 10 por padrão, em array JSON
puro, HTTP 200, sem envelope e sem nenhum cabeçalho de total. Numa contratação
com 111 itens você recebe 10 e a resposta parece completa. Sempre consulte
`/itens/quantidade` antes e confira o número.

**Parâmetro errado é ignorado sem erro.** `status=encerrada` (singular) não
filtra nada; `status=encerradas` filtra. O padrão é o plural. As duas
requisições da `ARMADILHA 2` mostram os totais lado a lado.

## Equivalentes em curl

Para conferir no terminal, sem Postman. Substitua `CNPJ`, `ANO` e `SEQ` pelos
valores que a busca devolver.

```bash
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

# 1a. CAMINHO PRINCIPAL — varrer por período e município, sem termo de busca
curl -s 'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20250801&dataFinal=20250831&codigoModalidadeContratacao=6&uf=PA&pagina=1&tamanhoPagina=50' \
  | jq -r '"\(.totalRegistros) contratações em \(.totalPaginas) páginas",
           (.data[] | "\(.orgaoEntidade.cnpj) \(.anoCompra) \(.sequencialCompra)  \(.unidadeOrgao.municipioNome)")' | head -6

# 1b. alternativa: descobrir por termo (única forma de buscar texto)
curl -s -H "User-Agent: $UA" \
  'https://pncp.gov.br/api/search/?q=aquisição&tipos_documento=edital&ufs=PA&anos=2025&status=encerradas&pagina=1&tam_pagina=50' \
  | jq -r '.items[] | select(.tem_resultado==true)
           | "\(.orgao_cnpj) \(.ano) \(.numero_sequencial)  \(.orgao_nome)"' | head -5

# 2. quantos itens a contratação tem (SEMPRE antes de coletar)
curl -s 'https://pncp.gov.br/api/pncp/v1/orgaos/CNPJ/compras/ANO/SEQ/itens/quantidade'

# 3. itens completos — sem tamanhoPagina vêm só 10
curl -s 'https://pncp.gov.br/api/pncp/v1/orgaos/CNPJ/compras/ANO/SEQ/itens?pagina=1&tamanhoPagina=500' \
  | jq -r '.[] | "\(.numeroItem)\t\(.valorUnitarioEstimado)\t\(.unidadeMedida)\t\(.descricao[0:60])"'

# 4. preço unitário HOMOLOGADO do item 1 — o dado que o projeto precisa
curl -s 'https://pncp.gov.br/api/pncp/v1/orgaos/CNPJ/compras/ANO/SEQ/itens/1/resultados' \
  | jq -r '.[] | "unit: \(.valorUnitarioHomologado)  qtd: \(.quantidadeHomologada)  data: \(.dataResultado)"'

# 5. prova de que a leitura é pública: 400 de validação, não 401
curl -s -o /dev/null -w '%{http_code}\n' \
  'https://pncp.gov.br/api/pncp/v1/orgaos/10000000000003/compras/2021/1/itens'

# 6. a busca sem User-Agent de navegador: conexão encerrada
curl -sv 'https://pncp.gov.br/api/search/?q=papel&tam_pagina=1' -H 'User-Agent:' 2>&1 | tail -3
```

## Filtros da busca

Verificados um a um comparando o total retornado.

| Funciona | Ignorado sem erro |
|---|---|
| `q` (obrigatório), `ufs`, `municipios`, `modalidades`, `esferas`, `poderes`, `orgaos`, `anos`, `status`, `tipos_documento`, `ordenacao` | `ano` (singular), `status=encerrada` (singular), `situacao`, `situacoes`, `tem_resultado`, `data_inicial`, `dataFinal`, `data_publicacao_inicial`, `data_publicacao_pncp_inicial` |

Dois detalhes que custam tempo:

- `municipios` usa o **id interno do PNCP**, não o código IBGE. Para descobrir o
  id de um município, busque pelo nome e leia `municipio_id` no retorno.
- Não existe curinga. `q=*` e `q=a` devolvem zero — a busca serve para procurar
  por termo, **não para varredura exaustiva** de um período.

## Estado do serviço de consulta

A API de Consulta (`/api/consulta`) caiu durante a verificação de 17/08/2026,
com degradação progressiva, e voltou:

| Hora | Retorno |
|---|---|
| 09h51 | **200** — `api-docs` entregou o OpenAPI completo |
| 09h52 | 500 — `"Erro na comunicação com o banco de dados."` |
| 09h53–10h05 | 504 após 70 s (timeout de gateway) |
| 10h18 | 502 |
| 11h20 | 503 — `"No server is available to handle this request."` |
| 11h33 | **200** — serviço restabelecido, 0,45 s |

Às 11h20 nem o `api-docs` respondia — o mesmo endpoint que às 09h51 entregou a
especificação inteira. Enquanto isso a API de Integração respondia em 0,2 s.

Duração observada da queda: **~1h40, com recuperação.** Uma observação não
estabelece frequência: se você rodar a coleção em dias diferentes e anotar o
resultado, isso vira dado de disponibilidade utilizável no texto. As requisições
da pasta `0b` e de `3. Provas negativas` servem como monitor — ambas tratam 5xx
como resposta esperada, não como falha da coleção.
