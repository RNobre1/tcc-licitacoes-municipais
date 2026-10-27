---
tipo: decisão
data: 2026-10-27
status: aceita
tags: [código, idioma, convenção, implementação]
---

# O código é escrito em inglês; o resto do projeto, em português

## Contexto

Até aqui a regra do projeto era português em tudo, inclusive no código, com
identificadores em inglês só quando fossem o padrão da linguagem. A regra foi
pensada para o texto e o vault, numa época em que ainda não havia código.

O desenvolvimento começa agora, e com ele aparece uma pergunta que a regra
antiga não respondia direito: em que língua se nomeiam pastas, classes,
funções, variáveis e comentários.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Português em tudo, como até aqui | Uma regra só, e o vocabulário do código bate com o da lei sem tradução | Destoa do padrão da área e mistura com as palavras-chave da linguagem e do arcabouço, que são em inglês |
| **Inglês no código, português no resto** | É o padrão da área; o código fica legível para qualquer pessoa que programe; e o autor pratica inglês técnico | Os termos do domínio não têm tradução exata. Sem uma referência única, cada módulo traduz de um jeito |
| Inglês em tudo, inclusive no texto e no vault | Uma regra só | O texto vai para uma banca brasileira e para revistas brasileiras. O vault sustenta esse texto |

## Decisão

**Escolhida:** a regra passa a depender do território.

| Território | Língua |
|---|---|
| `code/`: nomes, comentários, docstrings, testes, documentação do código | Inglês |
| Texto que o usuário vê na tela | Português |
| Texto do TCC, vault, `docs/`, backlog, casos de uso, `scripts/` e `tests/` do texto | Português |
| Mensagens de commit | A do que o commit altera. Commit que mexe nos dois territórios se divide em dois |

Os termos do domínio saem de **`code/GLOSSARY.md`**, que é a fonte única. Um
termo novo entra primeiro no glossário e só depois vira identificador.

A regra vale para **todo o desenvolvimento daqui em diante**, e não só para o
ciclo atual.

## Justificativa

- Inglês é o padrão de código na área, e isso basta como razão técnica.
- Há também uma **preferência declarada do autor**, que é praticar inglês técnico. O modelo de nota de decisão admite preferência pessoal como razão, desde que declarada como tal.
- A interface fica em português por causa de quem a usa. Quem opera o sistema é a servidora do setor de licitações. Montar uma camada de tradução para uma língua que nenhum usuário vai escolher seria trabalho sem uso.
- O glossário existe por causa do risco que a opção escolhida traz. *Ata de registro de preços*, *termo de referência* e *mapa de cotação* não têm equivalente exato em inglês. Sem uma fonte única, o código para de bater com a lei, com os requisitos e com o texto do TCC — e ninguém nota, porque cada tradução parece razoável isoladamente.

## Consequência

- O histórico do repositório passa a ter commits nas duas línguas, conforme o território alterado.
- O texto do TCC, ao citar um componente do sistema, usa o identificador em inglês, que é o nome real dele, e o glossário faz a ponte com o termo do domínio.
- Os `scripts/` e `tests/` do texto, que já existem em português, **não** são renomeados. São ferramentas do texto, e renomear tudo daria muito trabalho sem ganho.

## Critério de revisão

Reabrir se a banca ou um veículo de publicação exigir código em português, ou
se o glossário passar a crescer mais rápido do que o código que o usa. Esse
segundo sinal indicaria que o domínio está sendo traduzido além do necessário.

## Backlinks

- [[2026-10-18-pilha-tecnologica]]
- [[../sessões/2026-10-24]]
