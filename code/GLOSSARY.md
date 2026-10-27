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

## Names to avoid

Some translations look right and collide with something else.

| Avoid | Because | Use instead |
| --- | --- | --- |
| `collection` for gathering data | In Qdrant, a *collection* is where vectors live. The same word for two things would make the code ambiguous | `fetch`, `ingestion` |
| `sample` for invented data | `sample` already means a slice of **real** public data. Mixing the two hides which numbers are measured and which are made up | `demo_data` |
| `fixtures` for invented data | In Django, *fixtures* are files loaded into the database, which is a different mechanism | `demo_data` |
| `process` for a procurement case | It reads as an operating-system process | `Procurement` |
