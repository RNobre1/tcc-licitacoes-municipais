---
tipo: validação
data: 2026-11-05
alvo: "Base pública do PNCP: volume e forma das descrições de itens"
participantes: []
tags: [validação, pncp, ingestão, métricas, índice, volume]
---

# Validação: medição exploratória da base pública do PNCP

## Pergunta
Qual o volume e a forma das descrições de itens na base pública, para dimensionar o índice?

## Configuração
- **Versão do sistema:** comandos de ingestão (`fetch_pncp`) e medição (`measure_sample`) desenvolvidos no ciclo até 07/11 (dia 09).
- **Dados usados:** dados reais e públicos coletados via API do PNCP, mantidos estritamente no banco relacional local (tabela de registros brutos `RawRecord`). Em cumprimento à política de dados de domínio do projeto, nenhum dado real é armazenado no repositório Git.
- **Ambiente:** máquina local de desenvolvimento (macOS, Apple M4), banco de dados PostgreSQL local.
- **Tarefa proposta ao participante:** não se aplica (medição automatizada sobre dados públicos, sem participantes humanos).

A coleta foi realizada em 05/11/2026 via:
```bash
python code/manage.py fetch_pncp --start 2026-10-26 --end 2026-10-30 --uf PA --modality 6
```

A medição das métricas foi executada via:
```bash
python code/manage.py measure_sample --start 2026-10-26 --end 2026-10-30 --uf PA --modality 6
```
O comando de medição foi executado duas vezes consecutivas sobre a base local, gerando resultado idêntico em ambas as rodadas.

## Como foi medido
Os registros brutos foram persistidos com paginação atômica e deduplicados na leitura, considerando a captura mais recente (`fetched_at`) para cada par `(endpoint, params)`. Os itens foram associados às publicações da janela pelas chaves `cnpj`, `anoCompra` e `sequencialCompra`.

Critérios operacionais das métricas:
- **Publicações, páginas de itens e itens:** contagens de registros únicos considerados na janela.
- **Volume por dia:** agrupamento de publicações pela data de `dataPublicacaoPncp`.
- **Proporção de campos ausentes (`missing_share`):** fração de itens em que o atributo está ausente, é nulo (`None`) ou string vazia após remoção de espaços em branco (`strip()`).
- **Mediana do tamanho da descrição:** mediana de `len(descricao.strip())` calculada apenas sobre os itens cuja descrição não esteja ausente no sentido acima.
- **Unidades distintas:** contagem de valores únicos de `unidadeMedida` após `strip()` e `casefold()`, desconsiderando valores ausentes.

Comandos que geram cada número:
- Os totais de publicações (105), páginas de itens (108), itens coletados (5.116), falhas (0) e tempo de execução (49,6 s) são reportados diretamente pelo comando `fetch_pncp`:
  ```bash
  python code/manage.py fetch_pncp --start 2026-10-26 --end 2026-10-30 --uf PA --modality 6
  ```
- A distribuição diária de publicações, as frações de campos ausentes, a mediana do comprimento das descrições e o número de unidades distintas são calculados e impressos pelo comando determinístico `measure_sample`:
  ```bash
  python code/manage.py measure_sample --start 2026-10-26 --end 2026-10-30 --uf PA --modality 6
  ```

Não há linha de base comparativa anterior porque esta é a primeira medição empírica realizada sobre a base real do PNCP para dimensionamento do projeto.

## Resultado

| Métrica | Valor |
|---|---|
| Publicações | 105 |
| Páginas de itens | 108 |
| Itens | 5.116 |
| Publicações por dia: 26, 27, 28, 29 e 30/10 | 23, 23, 23, 35 e 1 |
| Campos faltando: `descricao`, `unidadeMedida`, `quantidade`, `valorUnitarioEstimado` | 0% nos quatro (0,0000) |
| Mediana do tamanho da descrição | 77 caracteres |
| Unidades distintas | 94 |

A coleta da janela completa levou 49,6 s, sem nenhuma falha de requisição ou paginação.

## Observações

Separando fato observado de inferência:

- **Volume atípico no dia 30/10:** O dia 30/10/2026 teve apenas 1 publicação registrada na API (contra 23, 23, 23 e 35 nos dias anteriores). A janela de teste inicial de um único dia (30/10), tentada antes de ampliar para a semana, era atípica. **Inferência:** A queda abrupta decorreu muito provavelmente do ponto facultativo alusivo ao Dia do Servidor Público no final de outubro. Isso é inferência: a API externa apenas entrega a data da publicação, sem justificar a oscilação administrativa de volume.
- **Definição de campo ausente:** O resultado de 0% de campos faltando restringe-se **à definição operacional adotada**. A métrica verifica apenas chave inexistente, valor `None` ou string em branco. Valores numericamente zerados, como os casos de orçamento sigiloso previstos no PNCP para `valorUnitarioEstimado`, não contam como ausentes nessa definição.
- **Diversidade de unidades:** A identificação de 94 unidades de medida distintas em 5.116 itens demonstra que a conversão e o tratamento de unidades de fornecimento (questão D11 do backlog) são indispensáveis para a comparação de itens e a proximidade de valor.

## Limitações
- **Modalidade única:** Os dados cobrem exclusivamente pregões eletrônicos (código de modalidade 6).
- **Recorte geográfico restrito:** Coleta limitada ao estado do Pará (UF = PA).
- **Janela temporal curta:** Uma semana de dias úteis (26 a 30/10/2026).
- Esta é uma medição estritamente exploratória para balizar o dimensionamento técnico inicial, e não uma amostra estatisticamente representativa do volume nacional ou de todas as modalidades da Lei nº 14.133/2021.

## O que muda por causa disto

Marcando inferência como inferência:

- **Ordem de grandeza de itens:** O volume medido aponta cerca de 1.000 itens por dia útil no recorte estadual de pregão eletrônico (~5.100 itens em cinco dias). Essa proporção dimensiona o tamanho mínimo da memória e capacidade de busca do índice vetorial e do banco relacional.
- **Viabilidade da ingestão noturna (Decisão A3):** A coleta da semana inteira exigiu apenas 49,6 s de processamento de rede e banco, com zero falhas. **Inferência:** Mantida essa ordem de grandeza de latência e estabilidade da API, uma rotina periódica de ingestão (diária ou noturna) para o estado cabe com folga dentro da janela operacional prevista. Isso responde à pergunta de autoverificação da T09.3 e sustenta a viabilidade da estratégia de ingestão local (Decisão A3).
- **Próximos passos:** Expandir as medições para períodos mais longos (meses completos) e incluir outras modalidades (como dispensas eletrônicas), avaliando se a completude de campos e a vazão da API se sustentam.

## Backlinks
- `docs/pesquisas/api-pncp-viabilidade-pesquisa-de-precos.md`
- `TCC/decisões/2026-08-16-politica-de-dados-de-dominio.md`
- `TCC/decisões/2026-08-16-tema-e-recorte.md`
- `TCC/decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao.md`
- `TCC/decisões/2026-10-18-pilha-tecnologica.md`
- `docs/tasks/backlog.md`
