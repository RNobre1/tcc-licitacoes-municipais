# Synthetic PNCP API Responses

The data in this directory is synthetic demonstration data (`demo_data`) designed
for testing PNCP client pagination and metric calculations without network calls.
All public bodies, CNPJs, descriptions, and quantities are fictitious.

## Endpoints and files

- `publications_page_1.json`: mimics page 1 of `GET /api/consulta/v1/contratacoes/publicacao`
  with pagination envelope (`data`, `totalRegistros`, `totalPaginas: 2`, `numeroPagina: 1`,
  `paginasRestantes: 1`).
- `publications_page_2.json`: mimics page 2 of `GET /api/consulta/v1/contratacoes/publicacao`
  with pagination envelope (`data`, `totalRegistros`, `totalPaginas: 2`, `numeroPagina: 2`,
  `paginasRestantes: 0`).
- `items_page_1.json`: mimics page 1 of `GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens`
  as a bare JSON array.
- `items_page_2.json`: mimics page 2 of `GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens`
  as a bare JSON array.
- `items_quantity.json`: mimics `GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens/quantidade`,
  returning an integer matching the total number of items across all item pages.
