---
tipo: decisão
data: 2026-09-22
status: aceita
tags: [escopo, arquitetura, usuários, autenticação]
---

# Um único perfil de usuário, com autenticação mantida

## Contexto

A primeira versão da especificação previa dois perfis: o servidor do setor de
licitações e o servidor da secretaria demandante, este último preenchendo um
formulário para originar a demanda. O diagrama de contexto trazia os dois como
atores.

Esse desenho era suposição do autor, e a sessão de validação mostrou que a fonte
de domínio pedia o contrário. Ao ser perguntada sobre o que poderia não funcionar
na prática, ela descreveu espontaneamente o que gostaria: que o sistema
importasse os documentos de demanda que ela já recebe, fizesse a varredura neles
e consolidasse as justificativas. Ela já faz isso hoje por fora, com ferramenta
de geração de texto.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| A — Um perfil, com importação do documento de demanda | Ataca o gargalo inteiro, que está no setor de licitações; é o que a usuária pediu; elimina dependência de adesão de terceiros; cabe no semestre de implementação | Perde o argumento de restabelecer a segregação de funções |
| B — Dois perfis, com formulário para a secretaria | Permitiria habilitar a secretaria a produzir documento utilizável, corrigindo a quebra de segregação de funções | Depende de adesão, treinamento e decisão administrativa fora do alcance de quem desenvolve; não toca no gargalo medido; risco de nunca ser exercitado na avaliação |
| C — Dois perfis, com o segundo apenas consultando | Meio-termo | Consulta sem escrita não resolve nada do problema e continua exigindo acesso e credencial para quem não ganha com isso |

## Decisão

**Escolhida: A.** Um único perfil de usuário, o servidor do setor de licitações.
Os documentos de demanda entram por importação, no formato em que já circulam.

**A autenticação permanece**, por decisão expressa do orientando, com duas
justificativas independentes da quantidade de perfis.

## Justificativa

O gargalo medido está inteiramente no setor de licitações: a triagem dos
candidatos a preço, que custa de nove a vinte e oito dias corridos, a redação das
peças e a revisão. As secretarias não participam dele. Um segundo perfil
acrescentaria superfície sem tocar no que custa caro.

A avaliação planejada também é com uma pessoa só. Perfil que ninguém exercita no
experimento é código que não será avaliado, e o semestre de implementação é um.

Sobre a autenticação, as duas razões são estas. A trilha de auditoria exige
registrar quem tomou cada decisão, e isso só faz sentido se houver quem: trilha
anônima vale pouco perante o órgão de controle externo. E o sistema lida com
processo administrativo em curso, cujo valor estimado ainda não é público.

Além disso, o modelo de dados e o controle de acesso admitem desde já mais de um
usuário e mais de um órgão, ainda que apenas um perfil seja implementado. Isso
mantém aberta a possibilidade de uso por outro município adiante, sem que o
trabalho prometa algo que não vai entregar.

## Consequência

**Muda:**

- O requisito de entrada deixa de ser formulário estruturado e passa a ser
  importação do documento de demanda em formato editável, com correção pelo
  operador antes de a demanda entrar no processo.
- A proposta de descrição de consenso é submetida ao operador, que decide. O
  alinhamento com as secretarias continua acontecendo fora do sistema, pelos
  meios já em uso.
- O nível 1 da arquitetura passa a ter um ator, e não dois.
- No fluxo, a etapa de alinhamento com as secretarias aparece marcada como
  externa ao sistema.

**Entra:**

- Requisito de autenticação individual, com a trilha de auditoria nomeando o
  autor de cada ação.
- Requisito de o modelo admitir mais de um usuário e mais de um órgão.

**Sai do escopo:**

- Restabelecer a segregação de funções entre quem redige e quem assina as peças.
  Segue descrito no diagnóstico, porque explica a carga de trabalho do setor, mas
  como desdobramento possível e não como resultado prometido. A orientação já
  havia autorizado esse tipo de recorte.

## Critério de revisão

- Se a validação com usuário mostrar que a importação do documento não extrai o
  suficiente, e o operador acabar redigitando tudo, a entrada precisa ser
  repensada.
- Se o município manifestar intenção de envolver as secretarias, a opção B volta
  a ser discutível. O modelo de dados já preserva qual secretaria pediu o quê e
  quanto, então a porta continua destrancada.

## Backlinks
- [[2026-09-06-escopo-dos-modulos-e-desenho-da-avaliacao]]
- [[2026-09-07-cobertura-de-fontes-e-memoria-de-calculo]]
- [[../sessões/2026-09-21]]
