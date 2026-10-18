---
tipo: decisão
data: 2026-10-18
status: aceita
tags: [arquitetura, implementação, python, django, postgresql, A1]
---

# Linguagem, arcabouço e banco relacional da aplicação

## Contexto

A decisão A1 estava registrada como aberta desde agosto, com a observação de que
não afeta os dois níveis de arquitetura desenhados. Isso continua verdade, e por
isso ela não precisou ser fechada antes. O que mudou é o momento: a
implementação começa em 2027.1, e a decisão precisa estar no texto da
qualificação para que a banca não a cobre como lacuna.

Duas perguntas foram levantadas junto com ela: *a escolha precisa de pesquisa?* e
*precisa de justificativa no texto?*

A resposta separa dois tipos de decisão. A metodologia adotada cobra o registro
das alternativas de projeto descartadas, mas o que merece comparação é a decisão
que **muda o resultado medido**. A escolha do modelo de representação, A2, muda:
é a contribuição do trabalho. A escolha da linguagem não muda — o mesmo
experimento daria o mesmo número em qualquer uma delas. Gastar páginas
comparando arcabouços web, num orçamento de 25, desloca espaço do que é
avaliado.

Logo: escolher com critério declarado, registrar em uma passagem curta, e não
abrir pesquisa comparativa.

## Opções consideradas

### Linguagem

| Opção | Prós | Contras |
|---|---|---|
| **Python** | É a linguagem em que a bateria de avaliação de A2 já roda: modelos de representação, cliente do banco vetorial, leitura dos relatórios de cotação, teste estatístico. O repositório já é Python, com `pytest` e `ruff` configurados | Desempenho bruto inferior ao de linguagem compilada — irrelevante aqui, porque o gargalo é entrada e saída e chamada de modelo |
| TypeScript | Mesma linguagem no servidor e no navegador | Descartada por preferência declarada do autor. Além disso, obrigaria uma segunda pilha para a avaliação, que é Python |
| Java, C# | Maturidade corporativa | Mesma objeção: a avaliação continuaria em Python, e o trabalho passaria a ter duas pilhas e uma ponte entre elas |

### Arcabouço

| Opção | Prós | Contras |
|---|---|---|
| **Django** | Autenticação, migrações, formulários, sessão e painel administrativo vêm prontos. Fecha por tabela a decisão A5, de mecanismo de autenticação | Opinativo; mais pesado que o necessário para uma interface de programação pura |
| FastAPI | Leve, assíncrono, comum em projetos com modelo de linguagem | Autenticação, formulários, migrações e sessão seriam escritos à mão. São semanas que pertencem à avaliação |

### Interface

Modelos de página do próprio Django, com HTMX para as interações de tela. Sem
arcabouço de navegador, sem etapa de construção, sem Node no ambiente. O módulo
1 é formulário guiado; formulário com validação e erro é exatamente o que o
servidor já sabe renderizar.

### Banco relacional

| Opção | Prós | Contras |
|---|---|---|
| **PostgreSQL** | `JSONB` guarda a resposta da base pública como ela veio **e** indexa campo dentro dela; intervalo temporal com restrição de exclusão por sobreposição resolve o versionamento que a trilha de auditoria exige | Mais pesado para operar que um banco embutido |
| MySQL ou MariaDB | Operação simples, muito difundido | Suporte a JSON mais pobre, sem o recurso de intervalo temporal |
| SQLite | Zero operação | Sem concorrência de escrita adequada ao serviço de ingestão, que roda em segundo plano |

## Decisão

**Python, com Django e HTMX, sobre PostgreSQL.**

O banco vetorial permanece o **Qdrant**, decidido à parte e por medição. A
persistência é dupla, e não passa a ser única por conta desta decisão.

## Justificativa

Dois dos quatro itens têm razão técnica verificável, e dois não têm. A
distinção está declarada no texto, porque alegar superioridade onde não há abre
uma pergunta que não se quer responder na banca.

**Com razão técnica:**

- **PostgreSQL por `JSONB`.** O recorte do trabalho inclui indexação de dados
  semiestruturados vindos de interface de programação. A resposta da base
  pública é JSON aninhado e muda de forma entre versões. Guardar o documento
  como veio, e ainda assim indexar campo dentro dele, é requisito e não
  conveniência.
- **PostgreSQL pelo versionamento temporal.** Reproduzir uma pesquisa de preços
  exatamente como ela era numa data é a regra RN08. Tipo de intervalo com
  restrição de exclusão resolve isso no banco, em vez de em código de aplicação
  que ninguém consegue auditar.

**Sem razão técnica, e declarado como tal:**

- **Python** é continuidade com o ferramental da avaliação, não superioridade.
- **Django** é economia de tempo em assunto que não é avaliado.

## Consequência

- A decisão A1 sai da tabela de decisões em aberto do texto, e a A5 passa a ter
  resposta: autenticação é a do próprio arcabouço, com perfil único, como já
  decidido em 22/09.
- Entra uma passagem curta na subseção de projeto, declarando a pilha e
  separando o que tem razão técnica do que não tem.
- Fica **fora de escopo** comparar arcabouços web, bancos relacionais ou
  linguagens. Quem quiser revisitar precisa trazer um requisito novo, não uma
  preferência.
- O ambiente de desenvolvimento não ganha Node nem etapa de construção de
  frontend.

## Critério de revisão

Reabrir se, e somente se:

1. uma medição mostrar que a geração dos documentos ou a ingestão não cabem no
   mesmo processo da aplicação — o que afeta A4, não A1; ou
2. aparecer requisito de concorrência ou de tempo de resposta que o arcabouço
   síncrono não atenda, medido e não suposto.

Preferência por outra linguagem não é critério de revisão.

## Backlinks

- [[2026-09-22-um-unico-perfil-de-usuario]]
- [[../../docs/pesquisas/escolha-do-banco-vetorial]]
- [[2026-10-15-classificacao-da-pesquisa-dsr]]
