# Sistemas inteligentes aplicados à gestão pública

> Trabalho de Conclusão de Curso · Bacharelado em Ciência da Computação
> Universidade Federal do Oeste do Pará — Instituto de Engenharia e Geociências

**Automação da fase preparatória e pesquisa de preços em licitações municipais.**

---

## Problema

A Lei nº 14.133/2021 exige, antes de publicar qualquer edital, que o município
elabore o Estudo Técnico Preliminar e o Termo de Referência da contratação e
fundamente o valor estimado por meio de pesquisa de preços. Em prefeituras de
pequeno porte, essa fase preparatória é o maior gargalo do processo: as
secretarias demandantes não dispõem de modelos padronizados para redigir os
documentos, e a cotação depende de fornecedores locais que respondem devagar ou
simplesmente não respondem.

## Proposta

Uma aplicação web de apoio ao servidor, deliberadamente **não invasiva**: não
substitui sistema em uso, não exige integração com sistema legado e entrega
documentos nos formatos que o processo administrativo já aceita.

- **Geração assistida de minutas** — formulário guiado que produz rascunho de
  ETP e Termo de Referência com os elementos exigidos pela legislação.
- **Composição de pesquisa de preços** — consulta à API pública do Portal
  Nacional de Contratações Públicas, tratamento estatístico dos valores obtidos
  e geração do mapa de cotação.

## Recorte de pesquisa

O trabalho se concentra nas questões de dados que a aplicação levanta:

- persistência e busca por similaridade sobre a legislação e os modelos, para
  sustentar a geração das minutas;
- modelagem e indexação dos dados semiestruturados obtidos da API pública;
- trilha de auditoria que permita reproduzir uma pesquisa de preços exatamente
  como ela era na data em que foi realizada — requisito de quem presta contas a
  órgão de controle.

## Estrutura

```
docs/     documentação do projeto e normas de formatação
texto/    LaTeX — projeto (TCC I) e monografia (TCC II)
code/     o sistema
scripts/  manifesto de normas e geradores
tests/    conformidade do texto com as normas da instituição
```

## Formatação verificada por teste

O texto segue o *Guia para a elaboração e apresentação da produção acadêmica da
Ufopa* (3. ed., 2025). As medidas normativas — margens, fonte, espaçamento,
recuo, extensão do resumo — são declaradas **uma única vez** em
`scripts/normas_ufopa.py`, de onde o preâmbulo LaTeX e a documentação são
gerados.

Um teste compila o PDF e verifica o que ele realmente entrega: tamanho da
página, fontes embutidas, margens, extensão do resumo, número de palavras-chave
e a caixa das citações no texto — que a norma vigente exige em caixa e baixa, e
não em caixa alta como nos modelos anteriores a 2023.

```bash
pytest                    # conformidade completa, compilando o PDF
pytest -m "not lento"     # só as guardas do manifesto
```

## Compilação

```bash
cd texto/tcc1 && make pdf     # ou make watch
```

Requer TeX Live com `biblatex`, `biblatex-abnt` e `biber`.

## Contexto

O trabalho parte de um caso real: a rotina do setor de licitações da Prefeitura
de Prainha-PA, no oeste do Pará. Nenhum documento real de processo licitatório é
publicado neste repositório — os exemplos, testes e ilustrações usam versões
sintéticas, com a mesma estrutura e nenhum dado verdadeiro.

## Autoria

**Rafael Nobre de Souza** — Bacharelado em Ciência da Computação, UFOPA/IEG
**Orientadora:** Socorro Vânia Lourenço Alves

Santarém — Pará · 2026–2027
