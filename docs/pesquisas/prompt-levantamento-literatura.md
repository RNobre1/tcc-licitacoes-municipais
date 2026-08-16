# Prompt para levantamento de literatura

Prompt autocontido para enviar a assistentes com acesso à web. Traga os
resultados de volta para filtrarmos juntos o que entra na fila de leitura.

Use um assistente por vez e compare as listas: a sobreposição entre respostas
independentes é o sinal mais barato de que uma referência é de fato central.

---

## O prompt

```text
Preciso levantar literatura para o meu Trabalho de Conclusão de Curso em
Ciência da Computação (Universidade Federal do Oeste do Pará, Brasil).

CONTEXTO DO TRABALHO

Tema: aplicação web de apoio à fase preparatória de contratações públicas
municipais no Brasil, sob a Lei nº 14.133/2021.

O sistema tem dois módulos:
1. Geração assistida de minutas de Estudo Técnico Preliminar (ETP) e Termo de
   Referência (TR), a partir de formulário guiado, com recuperação de
   informação sobre a legislação e sobre modelos de documento já aprovados.
2. Composição de pesquisa de preços a partir da API pública do Portal Nacional
   de Contratações Públicas (PNCP), com tratamento estatístico dos valores
   obtidos para compor o valor estimado da contratação.

A orientação é de uma professora da área de BANCO DE DADOS. O recorte que
interessa academicamente, portanto, é o de dados: persistência e busca por
similaridade sobre texto normativo, modelagem e indexação de dados
semiestruturados vindos de API pública, e trilha de auditoria que permita
reproduzir uma consulta exatamente como ela era na data em que foi feita.

O contexto é de município pequeno do interior da Amazônia, com equipe reduzida
e sem sistema próprio para essa etapa.

O QUE EU PRECISO

Uma lista de leituras priorizada, organizada nos cinco eixos abaixo. Para cada
referência, traga:

- autores, título, veículo (periódico, conferência ou instituição), ano;
- DOI ou URL estável;
- 2 a 3 frases sobre o que o trabalho faz e por que ele é relevante para o meu;
- qual dos meus eixos ele atende;
- se é fonte primária, revisão de literatura ou relato de experiência.

EIXOS

A. Recuperação de informação e geração assistida sobre texto jurídico ou
   normativo — incluindo avaliação de qualidade e de fidelidade à fonte, que é
   o que mais me preocupa em um domínio onde erro tem consequência legal.

B. Aplicação de processamento de linguagem natural e aprendizado de máquina a
   compras públicas, licitações e contratos administrativos. Priorize trabalhos
   sobre o contexto BRASILEIRO — teses, dissertações, artigos da SBC, produção
   de tribunais de contas e da Enap são bem-vindos.

C. Estimativa de preços e detecção de valores discrepantes em compras públicas:
   metodologias estatísticas, uso de bases de preços governamentais, análise de
   sobrepreço.

D. Modelagem e persistência de dados para os problemas acima: busca vetorial e
   busca híbrida, indexação de dados semiestruturados, dados temporais,
   versionamento e trilha de auditoria em sistemas que prestam contas a órgãos
   de controle.

E. Trabalhos que já façam algo parecido com o que proponho — sistemas de apoio
   à elaboração de documentos de licitação, ou de automação de pesquisa de
   preços. Quero saber o que já existe, inclusive produto comercial e sistema
   de governo, para posicionar minha contribuição e não reinventar.

REGRAS IMPORTANTES

1. Não invente referências. Se não tiver certeza dos metadados, diga
   explicitamente que precisam ser conferidos na fonte. Prefiro uma lista curta
   e verificável a uma lista longa e duvidosa.
2. Marque claramente o que é artigo revisado por pares e o que é literatura
   cinzenta (relatório técnico, post institucional, documentação).
3. Priorize dentro de cada eixo: comece pelo que eu deveria ler primeiro e
   diga por quê.
4. Se um eixo tiver pouca literatura, diga isso em vez de preencher com
   trabalho tangencial — a escassez em si é informação útil, porque indica
   onde pode estar minha contribuição.
5. Para o eixo B, se houver pouca coisa em português, diga e sugira o termo de
   busca em inglês que mais se aproxima do contexto brasileiro.
6. Ao final, aponte: qual é a lacuna que esse conjunto de trabalhos deixa em
   aberto, e que pergunta de pesquisa ela sugere.
```

---

## O que fazer com as respostas

1. Junte as listas num só lugar e marque as referências que apareceram em mais
   de uma resposta — são as candidatas mais prováveis a serem centrais.
2. Descarte sem dó o que for tangencial. Vinte referências mal lidas valem
   menos que cinco fichadas de verdade.
3. Cada uma que sobrar vira um fichamento em `TCC/papers/`, seguindo o template
   — e o campo `verificado` só vira `true` depois de conferir os metadados no
   próprio documento.
