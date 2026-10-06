---
tipo: paper
autores: ["Emanuele Musumeci", "Michele Brienza", "Vincenzo Suriani", "Daniele Nardi", "Domenico Daniele Bloisi"]
ano: 2024
titulo: "LLM Based Multi-Agent Generation of Semi-structured Documents from Semantic Templates in the Public Administration Domain"
venue: "arXiv, preprint arXiv:2402.14871v1 [cs.CL]"
tags: [trabalhos-relacionados, geracao-de-documento, administracao-publica, italia, preprint]
citacao_abnt: "MUSUMECI, Emanuele et al. LLM based multi-agent generation of semi-structured documents from semantic templates in the public administration domain. arXiv, 21 fev. 2024. Preprint arXiv:2402.14871v1. Disponível em: https://arxiv.org/abs/2402.14871. Acesso em: 6 out. 2026."
arquivo_local: "TCC/papers/musumeci-2024-geracao-documentos-semiestruturados.pdf"
verificado: true
---

# LLM Based Multi-Agent Generation of Semi-structured Documents from Semantic Templates in the Public Administration Domain

> **`verificado: true` vale para a versão lida, que é o preprint.** Conferido em
> 06/10/2026 contra o PDF: autores, título, identificador e data (21/02/2024).
> **Existe versão publicada, não lida e não conferida**: o registro do DOI
> 10.1007/978-3-031-60615-1_7 aponta capítulo na série Lecture Notes in Computer
> Science, páginas 98-117, 2024, e outro artigo a cita como trabalho de uma
> conferência internacional de interação humano-computador. Enquanto essa versão
> não for aberta, cita-se o preprint.

## Síntese

Grupo da Sapienza, em Roma. O problema é gerar documento semiestruturado — que
tem um conjunto fixo de dados, mas não um formato fixo — a partir de um
documento-modelo, sem depender de marcação de campos. A solução divide o
trabalho entre três agentes baseados em modelo de linguagem, que percorrem o
modelo seção por seção: um identifica o que a seção pede, outro verifica se a
informação necessária já foi fornecida e, se não, pergunta ao usuário, e o
terceiro redige.

## Contribuições

- Fluxo de interação que troca o refinamento manual de instruções por uma
  descrição de tarefa derivada da própria seção do modelo.
- Divisão em três papéis: identificação de semântica, recuperação de
  informação e geração de conteúdo.
- Acúmulo, numa única fonte, de tudo que o usuário informou, usada apenas como
  dado.
- Registro do processo de refinamento das instruções de cada agente.

## Método

A estrutura do documento-modelo é extraída por um serviço comercial de análise
de PDF. Os agentes usam um modelo de linguagem comercial de uso geral.

A "avaliação" consiste em mostrar, em tabelas, como a resposta de cada agente
melhora à medida que a instrução é refinada — acrescentando ordem explícita,
exemplo de saída e um marcador que o agente devolve quando não falta
informação.

## Resultados-chave

- Acrescentar exemplos do formato esperado à instrução é o que mais melhora a
  resposta dos agentes.
- Sem restrição explícita, o agente inventa conteúdo plausível em vez de
  descrever o que a seção pede.

## Limitações

Nenhuma é declarada pelos autores. Da leitura:

- **Não há avaliação quantitativa**, nem especialista do domínio, nem medida de
  qualidade do documento final.
- **Os exemplos não são documentos de administração pública.** São trechos de
  carta genérica — nome, saudação, parágrafo de apresentação de candidato a
  vaga — endereçada a uma universidade fictícia.
- Não há base de conhecimento externa. A "recuperação de informação" do título
  de um dos agentes é busca dentro do que o usuário já digitou, não recuperação
  sobre legislação ou documentos anteriores.
- Nenhuma norma é citada, e nenhuma verificação de base legal é feita.

## Relevância para este TCC

**A primeira rodada do levantamento superestimou este trabalho.** Ele foi
listado, pelo resumo, como cobrindo geração de documento em administração
pública "com multi-agente e recuperação". Lido inteiro, cobre o mecanismo de
seguir um modelo seção por seção e perguntar o que falta — e só. Não há
documento administrativo real, não há medição e não há fundamentação em fonte.

Serve para duas coisas no texto:

1. Como precedente do desenho de geração por seção, guiada pela estrutura do
   documento. Converge com o achado de campo de que a estrutura do estudo
   técnico é invariante e o texto não é.
2. Como contraste: o que este TCC acrescenta é exatamente o que falta ali —
   conteúdo redigido a partir da evidência do processo, base legal conferível
   e medição do esforço de revisão.

Não derruba sozinho nenhuma lacuna. Quem sustenta que geração assistida em
órgão público já existe é [[vandermeer-2026-legalcheck]].

## Citáveis

> "Semi-structured documents present a fixed set of data without a fixed
> format." (Musumeci et al., 2024, p. 1 do preprint)

> "The most important undesirable behavior to keep under control is the chance
> for hallucination, which in this case can alter the data in the generated
> content" (Musumeci et al., 2024, p. 11 do preprint)

## Backlinks

- [[vandermeer-2026-legalcheck]]
- [[zhao-2024-geracao-documento-licitacao]]
- [[../decisões/2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
