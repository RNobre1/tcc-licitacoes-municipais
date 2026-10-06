---
tipo: pesquisa
titulo: "Que sistemas em uso já atendem a fase preparatória e a pesquisa de preços, e como cada um busca?"
status: quatorze sistemas levantados em documentação pública; três serviços observados em uso; dezessete fontes conferidas em segunda leitura
criado: 2026-10-06
autor: Rafael Nobre de Souza
relacionado:
  - docs/pesquisas/levantamento-literatura-segunda-rodada.md
  - docs/pesquisas/ampliacao-de-bases-e-escolha-do-modelo-de-representacao.md
  - docs/requisitos/README.md
  - docs/tasks/backlog.md
  - TCC/papers/costa-2024-quanto-custa.md
tags: [pesquisa, sistemas-existentes, trabalhos-relacionados, pesquisa-de-precos, etp, tr, busca]
---

# Sistemas existentes para a fase preparatória e a pesquisa de preços

> ## Como ler esta nota
>
> O quadro comparativo dos trabalhos correlatos só tinha artigos. Esta nota
> levanta o que **não é literatura**: os sistemas que um servidor encontra hoje
> quando vai redigir o estudo técnico e o termo de referência, ou cotar preço.
>
> Cada célula do quadro tem um nível de evidência, e os níveis não se misturam:
>
> | Marca | Significa |
> |---|---|
> | **(O)** | **Observado**: a interface ou o serviço público foi usado em 06/10/2026, sem login |
> | **(D)** | **Documentado** pelo mantenedor: norma, manual, tutorial ou página oficial |
> | **(A)** | **Afirmado** pelo fornecedor na página de produto. É alegação comercial, não verificada |
> | **(T)** | Descrito em **documento de terceiro**. Ver a ressalva da seção 8 |
> | n.i. | Não informado na documentação pública consultada |
> | n.v. | **Não verificável sem acesso autenticado** |
>
> Nenhum login foi tentado, e nenhuma credencial foi usada. O que estava atrás de
> autenticação está nomeado na seção 7.

## 1. Contexto

A orientação pediu que o quadro comparativo incluísse os sistemas que já
existiam, e não só os trabalhos acadêmicos. Além disso, o levantamento de
requisitos mostrou que o município já usa um banco de preços comercial, de modo
que o diferencial do trabalho precisa ser afirmado contra produtos reais.

O eixo do diferencial é a busca: se o sistema encontra o item por palavra ou por
proximidade de significado. Por isso o quadro ganha uma coluna só para isso.

## 2. Pergunta

Que sistemas, do governo e do mercado, atendem hoje a redação das peças da fase
preparatória e a pesquisa de preços sob a Lei nº 14.133/2021 — e, em cada um,
como o usuário chega ao item, o que o sistema faz com o preço, e o que fica
registrado?

## 3. Resposta curta

1. **Nenhum sistema documenta busca por significado sobre descrição de item.**
   Onde o mecanismo está descrito ou pôde ser observado, ele é palavra, código
   de catálogo ou código de barras. Isso vale para o portal nacional, para a
   pesquisa de preços federal, para o painel de um tribunal de contas estadual e
   para o banco de preços acadêmico de Minas Gerais.

2. **O defeito relatado pela fonte de domínio foi reproduzido na ferramenta
   federal gratuita.** Digitar "alface" no catálogo da pesquisa de preços
   federal devolve, antes da classe de verduras, um fármaco e um agrotóxico
   cujos nomes começam com as mesmas letras. Erro de grafia e expressão sinônima
   devolvem zero — seção 6.4.

3. **Gerar ETP e TR com modelo de linguagem já é produto de prateleira.** Há
   pelo menos oito produtos comerciais com página pública que afirmam fazê-lo.
   Nenhum publica método, modelo, base de recuperação ou avaliação. O trabalho
   não pode apresentar a geração em si como novidade — seção 9.

4. **O governo federal já tem recuperação com geração em produção, mas sobre
   normas.** Um assistente lançado em março de 2026 responde dúvidas de
   planejamento a partir de uma base curada de leis e normativos. Não redige a
   peça, não busca item, não busca preço.

5. **Filtro estruturado de item já existe.** A busca avançada do portal nacional
   filtra por unidade de medida, quantidade, valor unitário e data de
   homologação; a pesquisa de preços federal filtra por localização e intervalo
   de quantidade. O diferencial do trabalho não é o filtro: é combiná-lo com a
   busca por significado e registrar a decisão.

6. **Nenhum sistema documenta guardar o candidato descartado com o motivo, nem
   refazer uma pesquisa como ela era numa data.** A norma federal de pesquisa de
   preços exige a justificativa da desconsideração de valores; nenhuma
   ferramenta consultada descreve onde isso fica.

7. **Parte do que ficou atrás de login pode ser temporária.** Um tutorial
   oficial declara que conteúdo foi retirado do ar pelo período eleitoral, de
   4 de julho a 25 de outubro de 2026. Vale repetir a consulta depois dessa data.

## 4. Método

Consulta feita em 06/10/2026.

- **Normas**, lidas no portal oficial: a Lei nº 14.133/2021 e as três instruções
  normativas federais que regem estudo técnico, termo de referência e pesquisa
  de preços.
- **Documentação do mantenedor**: manuais, tutoriais, perguntas frequentes,
  comunicados e páginas de apresentação.
- **Páginas de produto** dos fornecedores comerciais.
- **Observação direta** de três serviços públicos que não pedem login: a busca
  do portal nacional, a página de uma contratação nele, e o catálogo da pesquisa
  de preços federal. As consultas de teste estão nas seções 6.4 e 6.5.
- **Um artigo**, para o banco de preços de Minas Gerais, lido por inteiro.

**Segunda leitura.** O levantamento foi feito numa passada e conferido em outra:
os trechos que sustentam as linhas do quadro foram procurados em cópia baixada
de novo de dezessete fontes, e encontrados — em três delas, só depois de abrir a
página no navegador, porque o texto é montado na tela. O que **não** passou por
segunda leitura está listado na seção 8.

**Limite.** O que se descreve é o que a documentação pública diz. Ausência de
uma funcionalidade na página pública não prova ausência no produto.

## 5. Quadro

Colunas do quadro dos trabalhos correlatos, mais a de busca e a de acesso.

### 5.1 Governo federal

| Sistema e mantenedor | Objeto documental | Etapa atendida | País e norma | Tratamento de preço | Trilha reproduzível | Busca: palavra ou significado | Quem usa e custo |
|---|---|---|---|---|---|---|---|
| **ETP Digital** — órgão central de compras federal | Estudo técnico preliminar | Redação em formulário de seções; cópia de estudo existente | Brasil; Lei 14.133, art. 18; IN 58/2022 | A estimativa é um elemento a registrar; nenhum cálculo descrito (D) | Histórico de alterações do documento; saída em PDF (D) | **Palavra**: termo, com aspas para restringir (D) | Obrigatório na administração federal; cessão a estados e municípios por termo de acesso; gratuito; exige perfil e login (D) |
| **TR Digital** — idem | Termo de referência | Redação a partir de modelos oficiais | Brasil; IN 81/2022 | Remete à norma de pesquisa de preços (D) | n.v. | n.v. | Como o anterior (D) |
| **MentorIA** — ministério da gestão e empresa federal de processamento de dados [F25] | Respostas de orientação; **não gera a peça** | Dúvidas no planejamento da contratação | Brasil; base curada de leis e normativos | Nenhum | Conversa exportável com usuário, data e hora; mostra a referência usada (D) | Recuperação sobre **normas**, com geração; mecanismo de recuperação n.i. Não busca item nem preço (D) | Usuário de governo com login (D) |
| **Pesquisa de Preços** — idem; módulo com login e versão pública | Relatório resumido e detalhado; planilha | Estimativa do valor | Brasil; Lei 14.133, art. 23; IN 65/2021 | Só compras homologadas no sistema federal; 12 meses; filtros de localização, valor e quantidade; média, mediana, desvio padrão, coeficiente de variação; o usuário desativa cotações (D) | Sem login não salva; com login salva, desde 02/10/2026; motivo do descarte n.i. (D) | **Palavra → catálogo**: o texto devolve classes do catálogo por casamento de caracteres; o preço sai pelo código (O) | Versão pública: qualquer pessoa, gratuita. Módulo completo: usuário de governo (D) |
| **Portal nacional de contratações**, interface pública | Editais, atas, contratos, planos anuais | Divulgação; serve de fonte de preço | Brasil; Lei 14.133, art. 174 | Mostra valor estimado e homologado por item; **não calcula nada**; exporta a lista (O) | Histórico por contratação; nada sobre a consulta do usuário (O) | **Palavra**; alcança a descrição do item, mas devolve a **contratação**, não o item (O) | Público, gratuito, sem login (O) |

### 5.2 Tribunais de contas, ministério público e estados

| Sistema e mantenedor | Objeto documental | Etapa atendida | País e norma | Tratamento de preço | Trilha reproduzível | Busca: palavra ou significado | Quem usa e custo |
|---|---|---|---|---|---|---|---|
| **Preço de Referência** — tribunal de contas, governo e universidade federal da Paraíba | Certificado eletrônico de cotação | Pesquisa de preços | Brasil, um estado; manual de 2020 | Notas fiscais eletrônicas do estado; 12 meses; filtro por região e município; mínimo, máximo e média; descarta atípicos por intervalo interquartil; só mostra produto com mais de trinta notas (D) | Certificado com chave para consulta posterior (D) | **Palavra** — lista o que contém ao menos uma das palavras — ou código de barras (D) | Aberto e gratuito (D) |
| **Quanto Custa** — ministério público e universidade federal de Minas Gerais | Consulta e painéis | Fiscalização; consulta de preço de referência | Brasil, um estado | Mais de 30 milhões de itens; mínimo, média e máximo; alerta de sobrepreço | Não descrita | **Palavra**: casamento aproximado, ou operadores e curinga escritos pelo usuário | **Só usuários internos** do órgão |
| **Banco de Preços do TCE-MG** — tribunal de contas de Minas Gerais | Consulta de preços pagos | Pesquisa de preços | Brasil, um estado | Notas fiscais eletrônicas | n.i. | O tribunal afirmou, em 2018, agrupar produtos por característica com técnica de aprendizado; a busca não é descrita (D) | **Desativado**, por comunicado de 15/04/2026 (D) |

A linha do Quanto Custa vem de artigo lido por inteiro, e não de documentação do
mantenedor. O estado de São Paulo não tem módulo próprio de estudo técnico: adota
o sistema federal por decreto de 2023 [F24] (D).

### 5.3 Bancos de preços comerciais

| Sistema e mantenedor | Objeto documental | Etapa atendida | País e norma | Tratamento de preço | Trilha reproduzível | Busca: palavra ou significado | Quem usa e custo |
|---|---|---|---|---|---|---|---|
| **Banco de Preços** — Negócios Públicos | Relatório de cotação; especificação de objeto; termo de referência | Pesquisa de preços e mais sete módulos da fase interna | Brasil; declara as Leis 8.666, 14.133 e 13.303 e as IN 73/2020 e 65/2021 | Licitações, tabelas de referência, sítios de domínio amplo, notas fiscais e cotação direta; duas variantes de média saneada; pesquisa **item por item** (A) | Justificativa por item quando há menos de três preços (A); pesquisas salvas e relatório datado com código de verificação (T) | Mecanismo **não descrito** na página pública. Por palavra, com filtros (T) | Assinatura, com login; teste gratuito; três versões (A) |
| **Fonte de Preços** — Promáxima | Cotações e relatórios; modelos de documentos da fase interna | Pesquisa de preços | Brasil; declara atender a IN 65/2021 | "Mais de 420 milhões de preços homologados" (A) | n.i. | n.i. Afirma "tecnologia de IA", sem descrever (A) | Assinatura; teste gratuito; preço n.i. (A) |
| **Cotação Zênite** — Zênite | Relatório de cotação | Pesquisa de preços | Brasil; norma n.i. | Duas fontes federais; resultado ordenado por data, declaradamente sem sugestão (D, termos de 2022) | n.i. | n.i. | Cortesia, pelos termos de 2022; situação atual n.i. |

### 5.4 Produtos comerciais que afirmam gerar as peças com modelo de linguagem

Tudo nesta tabela é **(A)**: alegação de página de produto.

| Sistema e mantenedor | Objeto documental | Etapa atendida | País e norma | Tratamento de preço | Trilha reproduzível | Busca: palavra ou significado | Quem usa e custo |
|---|---|---|---|---|---|---|---|
| **GovPlan ETP** — Negócios Públicos | Plano anual, formalização da demanda, estudo técnico | Planejamento | Brasil; Lei 14.133 | Integração com o banco de preços do mesmo grupo | "Registros automáticos e justificativas documentadas" | n.i.; geração "com perguntas guiadas" e dados históricos do próprio órgão | Órgãos públicos; preço n.i. |
| **CRIADOC** | Estudo técnico, formalização da demanda, termo de referência, mapa de risco; pesquisa de preços | Documentos e pesquisa de preços | Brasil; Lei 14.133 | Portal nacional e base de um tribunal de contas; filtros de período, valor, órgão e região; média, mediana, mínimo, máximo | "Histórico salvo para auditoria"; "rastreabilidade das sugestões" | Afirma pesquisa **"em linguagem natural"**; mecanismo n.i. | Demonstração; preço n.i. |
| **Licita IA** | Plano anual, formalização da demanda, estudo técnico, termo de referência, matriz de riscos, pesquisa de preços | Fase preparatória inteira | Brasil; Lei 14.133 | Consolidação de preços praticados e mapa comparativo | Afirma trilha de quem alterou cada trecho, resumo criptográfico e registro em cadeia de blocos | n.i. | Só órgãos públicos; preço n.i. |

Outros cinco produtos com a mesma alegação foram localizados e não
aprofundados: SollAI, SophiaIA, GDL, PreparaGov e Sistema de TR.

## 6. Evidência por sistema

### 6.1 ETP Digital

A norma federal manda elaborar o estudo no sistema, lista os elementos a
registrar — a estimativa do valor entre eles — e manda pesquisar nele os
estudos de outras unidades para identificar soluções semelhantes [F2, arts. 4º,
9º e 12]. O manual descreve uma página com as seções a preencher, a criação de
estudo a partir de outro por cópia, o histórico de alterações e a saída em PDF
[F6]. A busca é por termo: palavra, expressão ou número da unidade, com aspas
para restringir [F6]. As perguntas frequentes, de 2020, falam em "busca por
metadados" sem dizer quais [F5].

**O manual é de junho de 2021 e cita a norma anterior**, revogada pela de 2022.
Não foi localizado manual mais novo. Não há, nele, sugestão nem geração de texto.

O uso pode ser cedido a estados e municípios por termo de acesso [F2, art. 5º].

### 6.2 TR Digital

Só a norma pôde ser lida: o termo deve ser elaborado no sistema, que traz os
modelos instituídos pelo órgão central com apoio do assessoramento jurídico; a
estimativa de valor remete à norma de pesquisa de preços; e, enquanto o sistema
não estiver completo, o órgão pode usar outra ferramenta [F3, arts. 4º, 9º e
15]. **O manual está atrás de login.**

### 6.3 MentorIA

Lançado em 2 de março de 2026 [F25]. O tutorial, versão 1.0, apresenta um
assistente conversacional para a fase de planejamento e declara que ele usa recuperação com geração sobre
"uma base de documentos oficiais, leis e normativos previamente curada" [F7].
A resposta traz a referência encontrada; a conversa pode ser exportada com
identificação do usuário, data e hora [F7].

Três limites, todos do próprio tutorial: ele orienta, não redige — o usuário
copia a resposta para colar no estudo ou no termo; a base é de normas, não de
itens nem de preços; e o tutorial não descreve como a recuperação é feita.

### 6.4 Pesquisa de Preços federal

Há três formas de uso: módulo com login, versão pública e dados abertos [F8]. A
versão pública declara reunir as contratações feitas pelo sistema federal de
compras, com doze meses de histórico, filtros por localização, valor homologado
e intervalo de quantidade, e cálculo de média, mediana, desvio padrão e
coeficiente de variação [F9]. O tutorial, versão 1.0 de junho de 2026, mostra
que o usuário descreve o item num campo de texto, recebe opções do catálogo, e
pode desativar cotações para tirá-las do cálculo [F10]. Sem login nada é salvo
[F10]; desde 02/10/2026, com login, as pesquisas ficam vinculadas à conta [F11].

**O que a base cobre.** Só o que foi comprado pelo sistema federal. Compra de
município que usa outra plataforma não está ali.

**Como o item é encontrado — observado.** O campo de texto consulta um serviço
de sugestão do catálogo, cujo parâmetro se chama, literalmente, "palavra". Onze
consultas de teste:

| Texto digitado | Sugestões | As primeiras |
|---|---|---|
| alface | 10 | Alfacalcidol; Alfacipermetrina; Verdura in natura; Semente |
| alfase | 0 | — |
| hortaliça folhosa | 0 | — |
| hortaliça | 10 | Sopa infantil; Mistura suplementação alimentar; Sopa; Substrato agrícola |
| papel sulfite a4 | 10 | Papel abrasivo; Papel alfa cheque; Papel almaço; Papel alumínio |
| sulfite | 10 | Sulfito de sódio; Papel correspondência; Papel monolúcido |
| sulfit | 10 | Sulfito de sódio; Revelador radiológico; Papel correspondência |
| resma papel oficio | 0 | — |
| caneta esferográfica azul | 10 | Caneta esferográfica; Caneta - indicador; Caneta alta rotação |
| caneta azul esferográfica | 10 | As mesmas, na mesma ordem |
| sequência sem sentido | 0 | — |

Leitura: o casamento é de caracteres. Quem procura alface recebe primeiro um
fármaco e um agrotóxico; quem erra uma letra ou usa outra expressão para a mesma
coisa não recebe nada; e a lista para em dez. As sugestões são **classes** do
catálogo, não itens: a escolha fina é feita depois, por características.

Na interface de dados abertos, o módulo de preços exige o código do catálogo;
texto livre só existe na consulta ao próprio catálogo [F12].

### 6.5 Portal nacional de contratações

A lei cria o portal para divulgação centralizada e manda que ele ofereça, entre
outras coisas, painel para consulta de preços [F1, art. 174]. Um parágrafo
acrescentado em 2025 diz que essas funcionalidades serão os sistemas do
Executivo federal [F1, art. 174, § 3º-A] — isto é, o painel de preços do portal
é a pesquisa de preços da seção anterior.

**Observado na tela pública** [F13]:

- um campo de palavra-chave, três abas — editais, atas, contratos — e 18
  filtros de contratação: órgão, unidade, estado, município, esfera, modalidade,
  ano e outros;
- uma busca avançada com mais filtros de contratação e dois grupos de filtro de
  **item**: situação, tipo, unidade de medida, quantidade e valor unitário
  estimados; e, para o resultado, data de homologação, quantidade e valor
  unitário homologados, porte e município do fornecedor;
- exportação da lista em planilha;
- a tela informou 9.990 resultados em todas as consultas feitas, mesmo quando o
  serviço de busca informava total maior — o que indica um teto de exibição.

**Como a busca se comporta — observado.** Totais de editais para doze consultas:

| Consulta | Total |
|---|---|
| papel | 237.727 |
| sulfite | 23.893 |
| sulfit | 23.890 |
| a4 | 64.290 |
| resma | 14.856 |
| papel sulfite | 23.101 |
| papel sulfite a4 | 17.971 |
| "papel sulfite a4", entre aspas | 7.105 |
| alface | 27.808 |
| alfase | 10 |
| hortaliça folhosa | 117 |
| sequência sem sentido | 0 |

Acrescentar palavra reduz o total; aspas reduzem mais; a forma truncada casa com
a inteira; erro de grafia e sinônimo quase não devolvem. É busca por palavra.

**O que ela alcança e o que devolve — observado.** Em três contratações
testadas, uma palavra que só existia na descrição de um item trouxe a
contratação de volta. A amostra é pequena, mas indica que o texto dos itens é
indexado. O que volta, porém, é a **contratação**: para ver o preço, abre-se cada
uma e lê-se a tabela de itens, que traz número, descrição, quantidade e valores
estimados. Não há busca dentro da página, nem cálculo, nem estatística.

A interface de consulta documentada não tem parâmetro de texto: filtra por data,
modalidade, órgão e local [F14].

### 6.6 Preço de Referência, da Paraíba

Manual de abril de 2020 [F15]. A base são notas fiscais eletrônicas do estado. A
busca devolve os produtos que contêm ao menos uma das palavras digitadas, ou
aceita código de barras. O próprio manual reconhece o limite: um mesmo item
recebe descrições diferentes, com abreviaturas e palavras em outra ordem. A
cotação pode ser guardada como certificado com chave de acesso para consulta
futura.

### 6.7 Quanto Custa, de Minas Gerais

Descrito em artigo lido por inteiro, com fichamento em
`TCC/papers/costa-2024-quanto-custa.md`. É o melhor exemplo publicado do
problema: para obter um preço de referência, o usuário escreve à mão uma
consulta com operadores e curinga, prevendo como a medida do objeto pode ter
sido grafada e que palavra vai contaminar o resultado. A ferramenta só está
disponível a usuários internos do órgão.

### 6.8 Banco de Preços do TCE-MG

O tribunal de contas de Minas Gerais anunciou em 2018 um sistema que agruparia produtos comuns pelas
características informadas pelo fornecedor [F16]. Um comunicado de 15/04/2026
informa que ele permanece desativado, à espera de nova solução [F17]. É o caso
mais próximo de casamento por significado num sistema público, e não está no ar.

### 6.9 Banco de Preços

Da página pública do fornecedor, lida no navegador [F18]:

- oito módulos da fase interna, entre eles pesquisa de preços, especificação de
  objetos e termo de referência;
- na especificação, o usuário informa o nome do objeto e recebe as
  características técnicas já usadas em outras licitações;
- no termo de referência, o fornecedor afirma auxiliar "na confecção de 80%" do
  documento a partir de modelo oficial ou do modelo do órgão;
- as fontes de preço: licitações, tabelas de referência, sítios de domínio
  amplo, notas fiscais eletrônicas e cotação direta com fornecedor;
- o fluxo: cadastra-se a cotação, incluem-se os itens, e "só então" se pesquisa
  o preço "de item por item";
- quando um item fica com menos de três preços, o sistema marca a pendência e
  pede justificativa, com modelos prontos;
- duas variantes de média saneada, com a regra de cada uma.

**A página não descreve como a busca funciona.** As palavras "palavra-chave",
"inteligência artificial" e "semântica" não aparecem nela.

### 6.10 Fonte de Preços e Cotação Zênite

A página do primeiro afirma mais de 420 milhões de preços homologados, modelos
prontos de documentos da fase interna, atendimento integral à norma federal de
pesquisa de preços e "tecnologia de IA" — sem dizer o que ela faz [F19]. Filtros,
fontes e relatório não estão na página.

Do segundo, só os termos de uso, de 2022: duas fontes federais, resultado
ordenado por data, com a declaração expressa de que a ordem não é sugestão
[F20]. A situação atual do serviço não foi apurada.

### 6.11 Produtos que afirmam gerar as peças

As três páginas foram lidas [F21, F22, F23]. Todas afirmam gerar estudo técnico
e termo de referência com apoio de modelo de linguagem; duas afirmam também
pesquisa de preços. **Nenhuma informa o modelo usado, a base de recuperação, o
método, ou qualquer avaliação.** Nenhuma publica preço.

Duas alegações tocam diretamente este trabalho, e as duas pedem cautela:

- **Pesquisa de preço "em linguagem natural"** sobre o portal nacional. Aceitar
  uma frase na entrada não prova recuperação por significado: pode ser extração
  de palavras seguida de busca textual.
- **Trilha com resumo criptográfico e cadeia de blocos.** O que se descreve é
  autoria e integridade do documento, não a reconstituição de uma pesquisa de
  preços.

Uma das páginas declara que o sistema não toma decisão autônoma e que todo
conteúdo gerado passa por validação humana — a mesma posição adotada neste
trabalho.

## 7. O que ficou atrás de login

Todas as páginas abaixo, do portal federal de compras, responderam "Conteúdo
Restrito — É necessário autenticar". Nenhuma foi contornada.

| Página | O que provavelmente esclareceria |
|---|---|
| Iniciativas de inteligência artificial em compras públicas | Se há geração de peça no sistema federal |
| Apresentação dos sistemas, inclusive do ETP Digital | Estado atual do módulo |
| Manual do TR Digital | Busca, histórico e exportação do termo |
| Manual do módulo de pesquisa de preços com login, e o tutorial de dados abertos | Fontes, filtros e relatório do módulo completo |
| Modelos de relatório da pesquisa de preços | O que o relatório registra |
| Caderno de logística de pesquisa de preços | Orientação metodológica oficial |
| Passo a passo da adesão de estados e municípios | Custo real de acesso para um município |
| Apresentação de lançamento do assistente | Arquitetura e escopo |
| Comunicados de 2025 | Situação do antigo painel de preços |

Os dois bancos de preços comerciais só abrem com assinatura, e o de Minas Gerais
só para usuários internos. **Para um município pequeno, o que resta aberto sem
custo e sem cadastro é a pesquisa de preços federal pública e a busca do portal
nacional** — as duas observadas nas seções 6.4 e 6.5.

**Sobre o bloqueio.** O tutorial da versão pública da pesquisa de preços informa
que conteúdo foi removido temporariamente em atendimento à lei eleitoral, e que
em 2026 o período vai de 4 de julho a 25 de outubro [F10]. É hipótese, não
provada página a página, que o bloqueio acima tenha essa causa. O teste é
simples: repetir a consulta depois de 25/10/2026.

## 8. O que não foi conferido

- **Ressalva sobre documentos de terceiros.** Parte do que se sabe do Banco de
  Preços — busca por palavra, filtros por código de catálogo e região, pesquisas
  salvas, relatório datado com código de verificação, e preço — vem de propostas
  comerciais e termos de referência publicados por órgãos que o contrataram.
  São documentos públicos, mas são documentos reais de contratação, e a política
  de dados do projeto precisa dizer se podem ser citados. Por isso aparecem aqui
  só em paráfrase, marcados com (T), sem endereço, sem valor e sem nome de
  órgão. **A decisão está em aberto.**
- **Não passaram por segunda leitura:** os outros cinco geradores de documentos;
  o tutorial do módulo de pesquisa de preços com login; as orientações técnicas
  e os termos de uso do painel da Paraíba; o redirecionamento do item "painel
  para consulta de preços" do portal nacional.
- **Filtros de item do portal nacional:** os dois grupos foram vistos; não foi
  testado se restringem itens ou só contratações que tenham algum item
  compatível.
- **Alcance da busca do portal sobre itens:** três testes.
- **Portaria que rege o termo de acesso** de estados e municípios: não lida.
- **Antigo painel de preços federal:** o endereço não respondeu; a
  descontinuação não tem fonte primária lida.
- **Uma base de preços de tribunal de contas** citada por um fornecedor como
  fonte não foi levantada.
- **O mecanismo real** de qualquer produto comercial. Nenhum foi usado.

## 9. O que isso muda

### 9.1 Para o módulo de redação das peças

A existência de geração por modelo de linguagem está estabelecida no mercado.
O que não está é a **evidência**: nenhum produto diz de onde vem o texto, contra
o quê foi avaliado, nem como o servidor confere a origem de cada trecho. O
espaço do trabalho é esse — recuperação sobre a legislação e os modelos
aprovados pelo próprio município, com a origem de cada trecho à vista, avaliada
com a fonte de domínio — e não a geração em si.

Há ainda a referência pública mais próxima, que é o assistente federal: ele
mostra que recuperação com geração sobre normas já foi adotada pelo órgão
central, e também onde para — orienta, não redige.

### 9.2 Para o módulo de pesquisa de preços

A afirmação que o levantamento sustenta é esta, e não outra mais forte:

> Nos sistemas cuja busca está documentada ou pôde ser observada, o item é
> encontrado por palavra, por código de catálogo ou por código de barras. Há
> alegações comerciais de busca "inteligente" ou "em linguagem natural", sem
> descrição de mecanismo.

O dado novo mais útil é a observação da seção 6.4: o defeito que a fonte de
domínio relatou num produto pago aparece também na ferramenta gratuita do
governo, e pode ser reproduzido por qualquer leitor.

### 9.3 Para o filtro estruturado e a trilha

- Filtro por unidade, quantidade, valor e período **já existe** em dois sistemas
  públicos. O que não existe documentado é o filtro como condição de uma busca
  por significado.
- Trilha, nos sistemas vistos, é uma de três coisas: certificado com chave,
  relatório datado com código de verificação, ou pesquisa salva na conta.
  Nenhuma descreve o registro do candidato descartado, e nenhuma descreve
  refazer a pesquisa como era na data.
- A norma federal dá o gancho: o documento da pesquisa deve conter as
  justificativas da metodologia, "em especial para a desconsideração de valores
  inconsistentes, inexequíveis ou excessivamente elevados" [F4, art. 3º, VI].

### 9.4 Para o argumento de acesso

| Sistema | Aberto a um município pequeno? |
|---|---|
| Pesquisa de preços federal, versão pública | Sim; mas só cobre compras do sistema federal |
| Busca do portal nacional | Sim; mas devolve contratação, não item, e não calcula |
| Bancos de preços comerciais | Por assinatura |
| Banco de preços acadêmico de Minas Gerais | Não: uso interno |
| Banco de preços do tribunal de contas de Minas Gerais, com agrupamento por característica | Não: desativado |
| Módulos federais de estudo técnico e termo de referência | Por termo de acesso |

O ponto descoberto é a base nacional com busca no nível do **item**.

## 10. Fontes

Todas acessadas em 06/10/2026.

| # | Fonte | Endereço |
|---|---|---|
| F1 | Lei nº 14.133, de 1º de abril de 2021 | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm |
| F2 | Instrução Normativa Seges nº 58, de 8 de agosto de 2022 | https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-seges-no-58-de-8-de-agosto-de-2022 |
| F3 | Instrução Normativa Seges/ME nº 81, de 25 de novembro de 2022 | https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-seges-me-no-81-de-25-de-novembro-de-2022 |
| F4 | Instrução Normativa Seges/ME nº 65, de 7 de julho de 2021 | https://www.in.gov.br/en/web/dou/-/instrucao-normativa-seges-/me-n-65-de-7-de-julho-de-2021-330673635 |
| F5 | Perguntas frequentes do ETP Digital, publicadas em 20/08/2020 | https://www.gov.br/compras/pt-br/acesso-a-informacao/perguntas-frequentes/etp-digital |
| F6 | Manual do ETP Digital, versão 2.1, arquivo de 23/06/2021 | https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/copy_of_manuais/manual-fase-interna/manual-etp-digital-pdf/temporario-manual-etp-versao-2-1.pdf |
| F7 | Tutorial do MentorIA, versão 1.0, março de 2026 | https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/copy_of_manuais/manual-fase-interna/manual-mentoria/V2TemporrioTutorial_MentorIAMaro26.pdf |
| F8 | Página de apresentação da Pesquisa de Preços | https://www.gov.br/compras/pt-br/sistemas/conheca-o-compras/pesquisa-de-precos |
| F9 | Pesquisa de Preços, versão pública | https://pesquisaprecos.compras.gov.br/pesquisa-precos-frontend-semlogin/ |
| F10 | Tutorial da versão pública da Pesquisa de Preços, versão 1.0, junho de 2026 | https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/copy_of_manuais/manual-fase-interna/manual-pesquisa-de-precos/v2-temporario-tutorial-pesquisa-de-precos-lite.pdf |
| F11 | Comunicado nº 43/26, de 02/10/2026 | https://www.gov.br/compras/pt-br/acesso-a-informacao/comunicados/comunicados_2026/no-43-26-2013-pesquisa-de-precos-lite-acesso-com-login-gov-br-para-salvar-as-pesquisas |
| F12 | Especificação da interface de dados abertos de compras | https://dadosabertos.compras.gov.br/v3/api-docs |
| F13 | Portal nacional de contratações, busca pública | https://pncp.gov.br/app/editais |
| F14 | Portal nacional de contratações, especificação da interface de consulta | https://pncp.gov.br/api/consulta/v3/api-docs |
| F15 | Preço de Referência, instruções de uso, abril de 2020 | https://precodereferencia.tce.pb.gov.br/ajuda/instrucoes-de-uso |
| F16 | Notícia do tribunal de contas de Minas Gerais sobre o banco de preços, 06/11/2018 | https://tce.mg.gov.br/noticia/Detalhe/1111623348 |
| F17 | Comunicado de indisponibilidade do banco de preços, 15/04/2026 | https://tce.mg.gov.br/noticia/Detalhe/1111628764 |
| F18 | Banco de Preços, página do produto | https://www.bancodeprecos.com.br/ |
| F19 | Fonte de Preços, página do produto | https://fontedeprecos.com.br/ |
| F20 | Cotação Zênite, termos de uso atualizados em 04/01/2022 | https://zenite.com.br/arquivos/termos/cotacao.pdf |
| F21 | GovPlan, página do produto | https://govplan.com.br/ |
| F22 | CRIADOC, página do produto | https://criadoc.com.br/ |
| F23 | Licita IA, página do produto | https://licitaia.com.br/ |
| F24 | Decreto estadual nº 68.017, de 11 de outubro de 2023, de São Paulo | https://www.al.sp.gov.br/repositorio/legislacao/decreto/2023/decreto-68017-11.10.2023.html |
| F25 | Notícia do lançamento do assistente federal, 04/03/2026 | https://tiinside.com.br/04/03/2026/serpro-e-mgi-lancam-primeira-ferramenta-de-ia-voltada-para-compras-publicas/ |

O banco de preços de Minas Gerais é citado pelo artigo: COSTA, Lucas G. L. et
al. Quanto Custa: banco de preços de compras públicas do estado de Minas Gerais.
Anais Estendidos do XXXIX Simpósio Brasileiro de Banco de Dados, 2024, p.
239-245. DOI: 10.5753/sbbd_estendido.2024.243804.
