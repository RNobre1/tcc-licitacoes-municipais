---
tipo: paper
autores: ["Lucia Siciliani", "Vincenzo Taccardi", "Pierpaolo Basile", "Marco Di Ciano", "Pasquale Lops"]
ano: 2023
titulo: "AI-based decision support system for public procurement"
venue: "Information Systems, v. 119, artigo 102284"
tags: [trabalhos-relacionados, busca-semantica, apoio-a-decisao, licitacao, italia]
citacao_abnt: "SICILIANI, Lucia et al. AI-based decision support system for public procurement. Information Systems, [s. l.], v. 119, art. 102284, 2023. DOI: 10.1016/j.is.2023.102284."
arquivo_local: ""
verificado: true
---

# AI-based decision support system for public procurement

> **`verificado: true`** — conferido em 06/10/2026 contra o cabeçalho do PDF da
> editora, obtido no repositório institucional da Universidade de Bari:
> periódico, volume 119, ano 2023, número de artigo 102284, DOI, os cinco
> autores na ordem e a licença de acesso aberto. O local de publicação não
> consta no PDF. O arquivo não ficou salvo em disco.

## Síntese

Sistema de apoio à decisão para compras públicas desenvolvido com a região da
Apúlia, na Itália. Reúne numa aplicação web dados estruturados da base nacional
de contratos e documentos de editais da plataforma regional, e oferece busca
semântica sobre a documentação, sumarização, extração de triplas, agregador de
informação sobre empresas e painéis com indicadores de risco de conluio. A
avaliação é de usabilidade, com servidores públicos.

## Contribuições

- Integração de dado estruturado e não estruturado de licitação num ponto único
  de acesso.
- Motor de busca com dois modos combináveis: por palavra e por proximidade de
  significado.
- Sugestão de conceitos relacionados à consulta, para cobrir o vocabulário que
  o usuário não domina.
- Busca sobre triplas extraídas dos anexos.
- Indicadores de risco de conluio calculados sobre dado aberto.

## Método

Coleta de 7.017.055 registros de licitação da base nacional em cerca de quatro
horas, mais os anexos da plataforma regional, obtidos por raspagem autorizada
porque a plataforma não oferece interface de programação. Documentos
digitalizados passam por reconhecimento de caracteres.

A busca por palavra usa BM25. A busca semântica representa consultas e
documentos num espaço vetorial construído por indexação aleatória e ordena por
similaridade de cosseno. Os dois modos podem ser combinados.

Avaliação por questionário com 33 servidores usuários de licitação: escala de
usabilidade de sistema e índice de recomendação. Um segundo estudo, com 11
responsáveis por verificação anticonluio, mede valor percebido, benefício e
custo de adoção em escala de sete pontos.

## Resultados-chave

- Usabilidade média de 77,1, acima do limiar de 68.
- Índice de recomendação de 30,3 (45,5% promotores e 15,2% detratores).
- Busca semântica e painéis dividem a preferência como recurso mais útil.
- 57,6% consideraram o painel de indicadores o recurso menos útil, e ele foi
  retirado.
- No segundo estudo: valor percebido 5,52, benefício 5,50, custo de adoção 3,30.

## Limitações

- **Não há medição de qualidade da recuperação** — nem revocação, nem precisão.
  A avaliação é só de percepção de uso.
- Prova de conceito com recurso de hardware restrito, o que os autores dizem
  ter condicionado escolhas técnicas.
- Uma única resposta à pergunta aberta sobre melhoria.
- Depende de raspagem onde não há interface pública.

## Relevância para este TCC

É o precedente mais citado de busca semântica em compras públicas — 40 citações
segundo a base, em periódico de sistemas de informação — e por isso é o que a
banca mais provavelmente conhece.

Coincide no argumento central: busca por significado encontra o que a busca por
palavra não encontra, e ajuda quem não domina o vocabulário do objeto. Diverge
em quatro pontos, que são o diferencial a destacar no quadro:

1. **O que se busca.** Lá, editais e seus anexos, para consultar casos
   anteriores. Aqui, itens contratados, para decidir se um preço é comparável.
2. **Filtro estruturado.** Lá há filtros de painel; a busca semântica não é
   condicionada a unidade, quantidade, natureza e janela temporal.
3. **Preço.** Não há tratamento de preço além de um indicador de valor relativo
   da licitação.
4. **Avaliação.** Lá, usabilidade. Aqui, recuperação medida contra cotações
   reais, em duas condições.

Não registra decisão do usuário nem permite reconstituir consulta passada.

## Citáveis

> "This approach allows finding documents that do not contain the keyword
> provided in the query." (Siciliani et al., 2023, p. 6)

> "If we consider a case where the RUP has no knowledge of computer components,
> this kind of functionality can help bridge the vocabulary gap." (Siciliani et
> al., 2023, p. 7)

> "none of them is intended to aid public agencies throughout the entire
> tendering process by making holistic use of the bulk of information already in
> existence" (Siciliani et al., 2023, p. 2)

## Backlinks

- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
- [[brum-2024-agrupamento-itens-similares]]
