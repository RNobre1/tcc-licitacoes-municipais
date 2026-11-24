# Domain glossary

The code is written in English. The domain is not. Brazilian public procurement
law, the people who use this system and the thesis that describes it all speak
Portuguese, and many of their terms have no exact English equivalent.

This file is the **single source** for how each domain term becomes an
identifier. Without it, every module translates on its own, and the code slowly
stops matching the law, the requirements and the thesis text.

**The rule:** a new domain term is added here **first**, and only then used in
code. If you are about to name something after a domain concept and it is not
in this table, stop and add it.

What the user sees on screen stays in Portuguese. This table is about names in
the code, not about interface text.

## Naming conventions

- Classes and Django models: `PascalCase`, singular — `RequestedItem`, not `RequestedItems`.
- Functions, variables, modules and packages: `snake_case`.
- Acronyms from the domain (ETP, TR, PNCP) are spelled out in class names and kept lowercase only when they are proper nouns — `pncp` is the name of a portal, so it stays.

## Terms

### The procurement and who takes part in it

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| processo de contratação | `Procurement` | One procurement case, from the first demand to the signed documents |
| secretaria demandante | `RequestingDepartment` | The municipal department that asks for the purchase |
| setor de licitações | `ProcurementOffice` | The office that runs the procurement. Its staff are the users of this system |
| documento de formalização de demanda | `DemandRequest` | The document in which a department formalizes a need |
| item demandado | `RequestedItem` | Something a department asks for: description, quantity and unit |
| unidade de fornecimento | `unit` | The unit in which an item is supplied — box, kilogram, hour |
| órgão | `agency` | A public body that published a contract or a price |

### Consolidating demands

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| consolidação de demandas | `consolidation` | Merging the same item requested by more than one department |
| descrição de consenso | `consensus_description` | The single description agreed for a consolidated item |

### Documents

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| estudo técnico preliminar (ETP) | `PreliminaryTechnicalStudy` | The study that analyses the need and sizes the solution |
| termo de referência (TR) | `TermsOfReference` | The document that sets the rules of the contract |
| minuta | `draft` | The first, unsigned version of a document |

### Price survey

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| pesquisa de preços | `PriceSurvey` | The search for reference prices that grounds the estimated value |
| preço candidato | `PriceCandidate` | A price found in public records that may be comparable to the requested item |
| triagem | `screening` | The operator deciding, candidate by candidate, whether it is comparable |
| semelhança do item | `similarity` | First ranking dimension: how close the candidate's description is to the requested item |
| proximidade de valor | `price_proximity` | Second ranking dimension: how close the candidate's price is to the expected price |
| preço esperado | `expected_price` | The operator's own estimate, optional |
| ordenação | `ranking` | Ordering candidates by the two dimensions above, **never merged into one score** |
| valor estimado | `estimated_value` | The value the price survey produces |
| critério de cálculo | `estimation_method` | The statistical criterion used to reach the estimated value, among those the regulation allows |
| média | `mean` | The arithmetic mean of the prices. One of the three methods of art. 6 of IN 65/2021 |
| mediana | `median` | The middle price; with an even count, the mean of the two middle prices. One of the three methods of art. 6 |
| menor valor | `min` | The lowest of the prices. One of the three methods of art. 6 |
| justificativa | `justification` | The written reason the process needs when the estimated value rests on fewer than three prices (RN06, IN 65/2021, art. 6, § 5) |
| memória de cálculo | `calculation_memo` | The record of how the estimated value was reached |
| mapa de cotação | `QuotationMap` | The comparison sheet listing each accepted price and where it came from |
| procedência | `provenance` | Where a price comes from, resolved down to the original record |
| ata de registro de preços | `PriceRegistrationRecord` | A standing price agreement. A price taken from one skips the price survey |
| contrato vigente | `active_contract` | A contract still in force. Like a price registration record, it skips the survey |
| trilha de auditoria | `audit_trail` | Who decided what, when, and based on what |

### Public data

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| Portal Nacional de Contratações Públicas | `pncp` | The national public procurement portal, whose API is the data source. A proper noun, so it stays as is |
| registro bruto | `RawRecord` | An API response stored exactly as it was received |
| ingestão | `ingestion` | Bringing public data into the system |
| buscar (na API) | `fetch` | One request, or one run of requests, against the API. **Not** "collect": see below |
| amostra | `sample` | A real, small slice of public data, used for measurement |
| dados de demonstração | `demo_data` | Invented data for the prototype. **Not** "sample": see below |
| índice semântico | `semantic_index` | Where descriptions are stored as vectors, for search by meaning |
| item publicado | `PublicItem` | One item of a public purchase published in the PNCP, normalized from its raw records: description, unit, quantity, prices, date, agency, state and the PNCP key that is its provenance |
| preço unitário estimado | `estimated_unit_price` | The unit price the buying agency estimated before the purchase. Zero when the budget is secret |
| preço unitário homologado | `awarded_unit_price` | The unit price actually awarded. The one IN 65/2021 accepts as a reference price |
| resultado do item | `item_result` | The PNCP record of an item's award (`/itens/{n}/resultados`), which carries the awarded price |
| orçamento sigiloso | `secret_budget` | A purchase whose estimated value is withheld; its items come with an estimated price of zero |
| unidade da federação (UF) | `state` | The Brazilian state where the buying agency is |

### Semantic search and its evaluation

| Portuguese | Identifier | Meaning |
| --- | --- | --- |
| busca semântica | `semantic_search` | Finding candidates by meaning, under the mandatory structured filter |
| busca por palavra | `keyword_search` | Finding candidates by shared words. The mandatory baseline of the evaluation |
| modelo de representação | `embedding_model` | The model that turns a description into a vector |
| vetor | `embedding` | The vector a model produces for one description |
| filtro estruturado | `structured_filter` | Conditions applied outside the vector: unit, state, period. Never learned, always enforced |
| faixa de comparabilidade | `comparability_band` | The band a candidate falls in by similarity, the first key of the RF23 ranking |
| relatório de cotação | `QuotationReport` | The report of a past price survey from the commercial price bank, with the prices the operator chose |
| conjunto de avaliação | `evaluation_set` | The requested items of past price surveys, each with the public records the operator chose |
| gabarito | `ground_truth` | The public records the operator chose for an item, taken as relevant |
| espaço de busca | `corpus` | The public items a search runs over |
| bateria | `benchmark` | Running every candidate search method against the evaluation set |
| subconjunto de ajuste | `tuning_split` | The part of the evaluation set where thresholds and parameters may be chosen |
| subconjunto de medição | `measurement_split` | The part of the evaluation set that is only measured, after every threshold is fixed |
| linha de base | `baseline` | The method every other method is compared with |

## Names to avoid

Some translations look right and collide with something else.

| Avoid | Because | Use instead |
| --- | --- | --- |
| `collection` for gathering data | In Qdrant, a *collection* is where vectors live. The same word for two things would make the code ambiguous | `fetch`, `ingestion` |
| `sample` for invented data | `sample` already means a slice of **real** public data. Mixing the two hides which numbers are measured and which are made up | `demo_data` |
| `fixtures` for invented data | In Django, *fixtures* are files loaded into the database, which is a different mechanism | `demo_data` |
| `process` for a procurement case | It reads as an operating-system process | `Procurement` |
| `homologated` for the awarded price | Not an English word in this sense | `awarded_unit_price` |
| `test_set` or `test_split` for the measured split | In this project `test` already names the code that checks code | `measurement_split` |
