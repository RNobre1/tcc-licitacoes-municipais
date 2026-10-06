# Arquitetura do sistema

### Esboço macro, em dois níveis de zoom

| | |
|---|---|
| Versão | 0.1, esboço |
| Data | 22 de setembro de 2026 |
| Autor | Rafael Nobre de Souza |
| Situação | Primeira versão, para discussão com a orientação |

---

> **Os diagramas estão no arquivo `arquitetura.drawio`**, na mesma pasta. Abra em
> diagrams.net, no aplicativo de desktop ou na extensão do editor. São três
> páginas: contexto, contêineres e o caminho de um processo. As caixas estão
> posicionadas à mão e podem ser arrastadas durante a conversa.

## 1. O que este desenho cobre

Antes dos níveis, o recorte, porque ele muda a leitura de tudo o que vem depois.

O sistema trata contratações cujo **valor estimado se monta por pesquisa de
preços**: material de consumo, material permanente e serviço comum. Obras e
serviços de engenharia ficam de fora, porque o orçamento delas se constrói por
planilha de custos sobre tabela de referência, que é outro mecanismo e exigiria
um segundo sistema.

**Um único usuário.** O sistema é operado apenas pelo servidor do setor de
licitações. As secretarias demandantes não acessam nada: elas mandam o documento
de demanda pelos meios que já usam, e quem o importa é o operador. A razão é que
o gargalo medido está inteiramente nesse setor, e exigir que cinco secretarias
adotem um sistema novo acrescentaria dependência de adesão, treinamento e decisão
administrativa sem tocar no que custa caro. A própria usuária pediu isso: que o
sistema importasse os documentos que ela já recebe.

Ainda assim **há autenticação**, e não por formalidade. A trilha de auditoria
precisa nomear quem decidiu cada coisa, e trilha anônima vale pouco perante o
controle externo. Além disso, o modelo de dados e o controle de acesso admitem
mais de um usuário e mais de um órgão desde já, ainda que só um perfil seja
implementado: prever isso agora custa pouco, e descobrir depois que o desenho não
comporta custa caro.

Dentro desse recorte, nem todo processo percorre o mesmo caminho. Uma demanda de
uma única secretaria não passa pela consolidação. Uma adesão a ata não passa pela
pesquisa de preços, porque o preço já existe no instrumento aderido. Por isso o
fluxo da terceira página traz **etapas condicionais**, e não uma sequência única.

E há uma coisa que convém dizer antes que alguém pergunte: o caminho completo não
é o processo mais frequente do setor. Por contagem, dispensas, inexigibilidades e
adesões a ata provavelmente somam mais. Ele é o que **concentra o tempo** — uma
cotação consolidada de cento e cinquenta itens levou vinte e oito dias corridos,
enquanto uma adesão a ata não tem cotação nenhuma. A proporção exata entre os
tipos ainda não foi medida, e está na lista do que perguntar.

---

## 2. Como ler este documento

A arquitetura está desenhada em níveis de zoom, do mais distante para o mais
próximo, seguindo o modelo C4. Cada nível só é aberto quando o de cima estiver
estável, e este documento cobre os dois primeiros.

| Nível | O que mostra | Estado |
|---|---|---|
| 1, contexto | O sistema como uma caixa única e quem conversa com ele | esboçado aqui |
| 2, contêiner | O que existe dentro dessa caixa, e o papel de cada parte | esboçado aqui |
| 3, componente | O que existe dentro de cada contêiner | ainda não |
| 4, código | Classes e funções | provavelmente fora do escopo do trabalho |

A escolha de parar no nível 2 é deliberada. Descer antes de ter certeza do que
cada contêiner faz produz desenho que será jogado fora, e a orientação já
observou que camada nova costuma aparecer quando a medição revela o limite, e
não antes.

---

## 3. Nível 1: contexto

Quem usa o sistema, e com que mundo externo ele conversa.

**O que este nível já decide.** O sistema é autônomo: não se comunica com sistema
algum da prefeitura, e sua única dependência externa é uma base pública. Isso não
é limitação, é escolha, e ela existe porque a maior parte das prefeituras de
pequeno porte não dispõe de serviço pago de pesquisa de preços.

**Um ator, não dois.** A versão anterior deste desenho trazia também o servidor
da secretaria demandante como usuário. Ele saiu: quem opera o sistema é apenas o
setor de licitações, e o documento de demanda entra por importação.

**O que ele deixa em aberto.** Nada sobre tecnologia. Um diagrama de contexto que
já cita linguagem ou banco está descrevendo outra coisa.

---

## 4. Nível 2: contêineres

O que existe dentro da caixa do nível anterior. Cinco partes, e cada uma tem uma
razão de existir separada das demais.

### Por que cada parte existe

**Aplicação web.** Concentra a interface, as regras de negócio, a triagem dos
candidatos a preço e a montagem dos documentos. Não foi dividida em mais partes
porque ainda não há motivo medido para dividir: separar cedo demais cria
fronteira que depois atrapalha.

**Serviço de ingestão, separado da aplicação.** Esta é a única separação que o
esboço já assume, e o motivo é concreto. Percorrer e indexar a base pública é
trabalho de minutos ou horas, e não cabe dentro do tempo de uma requisição de
página. Se estivesse junto, a primeira carga derrubaria a aplicação, e a
aplicação não poderia ser reiniciada sem interromper a carga.

**Banco relacional.** Guarda o que tem estrutura e precisa de integridade: o
processo, as demandas de cada secretaria, os documentos em suas duas versões, os
preços selecionados e a trilha de auditoria. A trilha é o que permite reconstituir
uma pesquisa como ela era na data em que foi feita, e isso exige um armazenamento
que não perca nem reescreva o passado.

**Índice semântico.** Guarda a representação das descrições dos itens
contratados, para que a busca encontre item comparável por proximidade de
significado, e não por coincidência de palavra. É o coração do trabalho: o
problema medido no levantamento é exatamente este.

### Por que dois bancos, e não um

A pergunta é legítima e vai ser feita. A resposta tem medição própria por trás.

Em experimento realizado no âmbito da iniciação científica, comparando a extensão
vetorial do banco relacional com dois bancos vetoriais dedicados, os resultados
divergem conforme o tipo de consulta:

| Cenário | Extensão do relacional | Banco dedicado |
|---|---|---|
| Busca por similaridade, sem filtro | melhor desempenho | equivalente |
| Busca por similaridade com filtro restritivo | recupera menos de 6% do esperado | recupera acima de 99% |

O caso deste sistema é sempre o segundo. Buscar preço de referência nunca é
buscar em toda a base: é buscar dentro de uma categoria, num recorte geográfico e
numa janela de doze meses. O filtro restritivo é a operação normal, não a
exceção.

Daí a divisão: o relacional faz o que faz bem, que é integridade e histórico; o
índice dedicado faz o que o outro não faz, que é recuperação sob filtro.

### O que este nível deliberadamente não tem

**Não há fila de mensagens.** Ela seria a resposta natural para desacoplar a
ingestão da aplicação, e provavelmente vai aparecer. Mas ainda não há medição que
mostre a necessidade, e acrescentar agora é complexidade sem evidência. O ponto
onde ela entraria está identificado: entre o serviço de ingestão e a aplicação.

**Não há memória intermediária de resultados.** Mesma razão. O ponto onde entraria
é a busca de candidatos, que é a operação mais cara e mais repetida.

**Não há separação entre geração de documento e aplicação.** A geração é a parte
mais provável de crescer até virar contêiner próprio, mas hoje não há motivo.

Os três estão listados aqui de propósito. Arquitetura que não declara o que
escolheu não fazer parece apenas incompleta.

---

## 5. O caminho de um processo pelo sistema

Uma leitura do nível 2 no sentido do uso, e não da estrutura.

Três observações sobre este fluxo.

O ciclo de ajuste entre a proposta de descrição e a resposta das secretarias
existe porque é assim que o trabalho acontece hoje: quando duas secretarias
pedem o mesmo item com descrições divergentes, chega-se a uma descrição de
consenso e pede-se que as demais se alinhem a ela. Manter as duas duplicaria o
item no processo.

A minuta aparece antes da pesquisa de preços, e não é um detalhe: é o ciclo de
vida real do documento no setor estudado, com a seção de estimativa de valor
redigida no futuro e reescrita depois.

A triagem aparece como etapa própria porque é onde está o custo do processo
atual, medido entre nove e vinte e oito dias corridos conforme o tamanho da
contratação.

O **preço esperado** aparece como entrada do operador, e não como etapa, porque é
isso que ele é. Foi observado na demonstração de tela que a servidora descarta
candidatos antes mesmo de ler a descrição, apenas por implausibilidade de valor.
A origem desse número varia: conhecimento de consumo cotidiano, cotação pedida a
um fornecedor local, ou consulta a mecanismo de busca comum quando ela não domina
o item.

A consequência para o desenho é que o ranqueamento tem duas dimensões, e não uma:
semelhança do item e proximidade ao preço esperado. Elas são exibidas separadas,
e não fundidas em um escore único, porque o operador precisa saber qual das duas
puxou cada candidato para cima. E a avaliação do sistema roda nas duas condições,
com e sem a âncora, para separar quanto do acerto vem de entender o item e quanto
vem de já conhecer o preço.

---

## 6. Decisões ainda abertas

Registradas como abertas, e não resolvidas por omissão.

| # | Decisão | Por que não está fechada |
|---|---|---|
| A1 | Linguagem e arcabouço da aplicação | Não afeta os níveis 1 e 2, e fechar cedo prende sem necessidade |
| A2 | Modelo de representação das descrições | Depende de teste com as descrições reais da base pública, que são curtas e ruidosas |
| A3 | Estratégia de atualização da ingestão | Depende de conhecer o volume e a taxa de publicação da base |
| A4 | Onde mora a geração dos documentos | Depende de quanto ela cresce; hoje cabe na aplicação |
| A5 | Mecanismo de autenticação | Há um só perfil, mas o acesso é autenticado e o modelo admite mais usuários e mais de um órgão. O mecanismo concreto não foi escolhido |
| A6 | Quanto do trabalho do setor o recorte de fato cobre | Depende de medir a proporção entre os tipos de processo, que é pergunta para a fonte de domínio |

---

## 7. O que vem a seguir

1. Fechar A2, porque é a decisão que mais afeta o resultado do trabalho.
2. Medir o volume da base pública, que fecha A3 e dimensiona o índice.
3. Abrir o nível 3 apenas para a aplicação web, que é onde está a lógica.
