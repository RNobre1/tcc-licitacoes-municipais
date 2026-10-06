# Especificação de Requisitos de Software

### Sistema de apoio à fase preparatória de contratações públicas municipais

| | |
|---|---|
| Versão | 1.0 |
| Data | 06 de setembro de 2026 |
| Autor | Rafael Nobre de Souza |
| Curso | Bacharelado em Ciência da Computação, Universidade Federal do Oeste do Pará |
| Estudo de caso | Setor de licitações da Prefeitura Municipal de Prainha, Pará |
| Situação | Primeira versão |

---

## 1. Introdução

### 1.1 Objetivo deste documento

Este documento especifica o que o sistema desenvolvido no trabalho de conclusão
de curso deve fazer, quais restrições ele precisa respeitar e sob quais
critérios será considerado aceitável. Ele registra também as regras do domínio
que o sistema não escolhe nem negocia, apenas obedece, porque decorrem da
legislação de contratações públicas e da prática do setor estudado.

O público deste texto são a orientação do trabalho, a banca examinadora e o
próprio autor, na fase de implementação. Ele não pressupõe conhecimento prévio
de licitações: a seção 2 apresenta o domínio antes de qualquer requisito, e o
glossário da seção 1.3 define os termos usados ao longo do texto.

Trata-se de um documento vivo. À medida que a implementação avançar e novas
sessões de validação forem realizadas com a fonte de domínio, requisitos serão
acrescentados, alterados ou retirados, e a versão indicada no cabeçalho será
atualizada.

### 1.2 Escopo do produto

O sistema é uma aplicação web de apoio à fase preparatória de contratações
públicas em prefeituras de pequeno porte. Ele atua em dois momentos do processo:
na redação dos documentos que instruem a contratação e na composição da pesquisa
de preços que fundamenta o valor estimado.

O sistema não substitui nenhum sistema em uso pela prefeitura, não se integra a
sistema legado e não participa da condução do certame. Ele entrega documentos
nos formatos que o processo administrativo já aceita, e a decisão sobre o que
fazer com eles continua sendo inteiramente humana.

Está fora do escopo tudo o que ocorre depois da publicação do edital: sessão
pública, julgamento de propostas, habilitação, recursos, contratação e execução
contratual.

**O recorte por tipo de objeto.** O sistema cobre aquisição de material de
consumo, material permanente e serviço comum, ou seja, contratações cujo valor
estimado se monta por pesquisa de preços. **Obras e serviços de engenharia ficam
de fora**, porque o orçamento deles não vem de pesquisa em base de preços
praticados: vem de planilha de custos construída sobre tabela de referência. É
outro mecanismo, com outra fonte de dados e outro documento de entrada, e tratá-lo
exigiria um segundo sistema.

**O recorte por modalidade.** O setor estudado conduz, além do pregão por registro
de preços, dispensas, inexigibilidades e adesões a ata de registro de preços. As
peças que instruem o processo são as mesmas em todos, mas a pesquisa de preços
entra de forma diferente, e na adesão a ata não entra: o preço já existe no
instrumento aderido. O sistema trata a consolidação entre secretarias e a pesquisa
de preços como **etapas condicionais**, que ocorrem ou não conforme o caso.

**Uma declaração sobre frequência que precisa ser honesta.** O caminho completo —
várias secretarias, consolidação, pesquisa de preços sobre centenas de itens — não
é o processo mais frequente do setor. Por contagem, dispensas, inexigibilidades e
adesões provavelmente somam mais. Ele é, porém, o que concentra o tempo: uma
cotação consolidada de cento e cinquenta itens levou vinte e oito dias corridos, e
uma adesão a ata não tem cotação alguma. O sistema mira onde está o custo, não
onde está a contagem. **A proporção entre os tipos de processo ainda não foi
medida**, e essa lacuna está declarada em 3.4.

### 1.3 Definições, siglas e abreviaturas

| Termo | Significado |
|---|---|
| Fase preparatória | Conjunto de etapas anteriores à publicação do edital, em que a contratação é planejada, justificada e orçada |
| DFD | Documento de Formalização de Demanda. Peça que abre o processo, na qual a secretaria interessada declara o que precisa, em que quantidade e por quê |
| ETP | Estudo Técnico Preliminar. Documento que analisa a necessidade, avalia alternativas, estima quantidades e valor, e conclui pela viabilidade da contratação |
| TR | Termo de Referência. Documento derivado do ETP que estabelece as regras da contratação e integra o edital como anexo |
| Pesquisa de preços | Levantamento de preços praticados em contratações semelhantes, usado para calcular o valor estimado |
| Valor estimado | Valor de referência da contratação, que funciona como teto: proposta acima dele é desclassificada |
| Mapa de cotação | Documento que reúne os preços coletados, sua procedência e o cálculo que produziu o valor estimado |
| Memória de cálculo | Demonstração de como se chegou a um número, seja a quantidade demandada, seja o valor estimado |
| Registro de preços | Sistemática em que se licita uma quantidade máxima e as aquisições ocorrem de forma parcelada, durante a vigência da ata |
| Secretaria demandante | Órgão da administração municipal que originou a demanda |
| Portal nacional | Portal Nacional de Contratações Públicas, base pública que reúne contratações realizadas por órgãos de todo o país |
| Banco de preços comercial | Serviço pago que agrega bases públicas e privadas de preços e oferece ferramentas de composição de cotação |
| Recuperação semântica | Busca que localiza registros por proximidade de significado, e não por coincidência de palavras |
| RN, RF, RNF | Regra de negócio, requisito funcional e requisito não funcional |

### 1.4 Organização do documento

A seção 2 descreve o domínio e o problema. A seção 3 explica como os requisitos
foram levantados e apresenta as evidências que os sustentam. A seção 4 lista as
regras de negócio. As seções 5 e 6 trazem os requisitos funcionais e não
funcionais. A seção 7 registra os critérios de aceitação declarados pela usuária
do sistema, e a seção 8 descreve como cada tipo de requisito será verificado. A
seção 9 apresenta a rastreabilidade entre requisitos, regras e evidências.

---

## 2. Descrição geral

### 2.1 O problema

A Lei nº 14.133, de 2021, exige que toda contratação pública seja precedida de
um planejamento formal. A secretaria interessada precisa formalizar sua demanda,
a administração precisa elaborar um estudo técnico preliminar que justifique a
compra, e é necessário realizar uma pesquisa de preços que fundamente o valor
estimado. Só depois disso o edital pode ser publicado.

Em prefeituras de pequeno porte, essa fase concentra a maior parte do tempo do
processo. As secretarias que pedem os materiais não têm modelo padronizado nem
apoio técnico para redigir os documentos, e a pesquisa de preços é feita item por
item, manualmente, por uma equipe reduzida que acumula outras atribuições.

O caso estudado é o setor de licitações de uma prefeitura no oeste do Pará, com
dois servidores responsáveis por essa fase e cerca de dez contratações iniciadas
por semana, considerando todas as modalidades.

### 2.2 O processo de contratação hoje

O processo começa quando uma secretaria identifica uma necessidade e a formaliza
em um DFD, informando o objeto, a quantidade pretendida, o período que ela deve
atender e a justificativa da compra. Como o município opera por registro de
preços, uma demanda por item de uso comum leva o setor a consultar as demais
secretarias. As listas são somadas e o resultado vira um processo único, para
evitar a multiplicação de procedimentos pequenos, que encarece a administração.
Em um dos processos analisados, cinco secretarias apresentaram demandas
individuais e o processo consolidado chegou a cento e cinquenta itens.

Formalizada a demanda, a lei prevê a elaboração do ETP, que analisa a
necessidade, avalia a solução, dimensiona quantidades e estima o valor. Do ETP
deriva o TR, que estabelece as regras da contratação e é anexado ao edital.
Entre os dois entra a pesquisa de preços.

Duas coisas se afastam do desenho normativo na prática observada, e ambas
importam para este trabalho.

A primeira diz respeito a quem executa. O ETP é atribuição do setor de
planejamento, mas quem o redige é o setor de licitações, cabendo ao planejamento
apenas assinar. A servidora entrevistada identificou o problema pelo nome,
segregação de funções, e afirmou que a situação se repete na maioria dos
municípios pequenos.

Convém dizer desde já que **corrigir isso não é objetivo deste trabalho**. A
correção exigiria habilitar cada secretaria demandante a produzir documento
utilizável por conta própria, o que depende de adesão, treinamento e decisão
administrativa fora do alcance de quem desenvolve o sistema. Além disso, não
tocaria no gargalo medido, que está inteiramente no setor de licitações. O
desvio é descrito aqui porque explica a carga de trabalho desse setor, e fica
registrado como desdobramento possível, não como resultado prometido.

A segunda diz respeito ao número de pesquisas. A legislação prevê uma pesquisa de
preços prévia, destinada a instruir o ETP, e uma cotação definitiva posterior, que
fundamenta o valor estimado. Na prática realiza-se uma cotação só, cujo resultado
alimenta os dois documentos. O motivo é custo: em um processo com mais de mil
itens, pesquisar preço duas vezes manualmente é inviável.

Para conciliar isso com a exigência formal, o ETP tem **ciclo de vida em duas
fases**. Primeiro é redigida e assinada uma minuta com todas as seções
preenchidas, exceto a estimativa de valor, que aparece redigida no futuro,
declarando que o valor será aferido pela pesquisa de preços a ser realizada. Em
seguida acontece a cotação. Por fim, a minuta é retomada e a seção de estimativa
de valor é reescrita no passado, com o valor apurado e as fontes consultadas.

A comparação entre a minuta e a versão final de um mesmo processo confirma o
mecanismo: onze das doze seções numeradas são idênticas, e apenas a estimativa de
valor difere. É um dado de projeto, e não apenas de diagnóstico, porque descreve
exatamente a transformação que o sistema precisa reproduzir.

Ao final, o conjunto é submetido ao setor jurídico. No caso estudado o jurídico
trabalha na mesma sala e é consultado ao longo de toda a redação, de modo que a
devolução formal é rara e o parecer sai no mesmo dia.

### 2.3 Onde o trabalho se concentra

O município já utiliza um banco de preços comercial, o Banco de Preços, que
agrega bases públicas e privadas. Esse serviço resolve a coleta dos preços, calcula a média, gera memória
de cálculo, monta o mapa comparativo, registra a procedência de cada preço e
emite relatório com certificado de autenticidade. A coleta, portanto, é um
problema resolvido.

O que esse serviço não faz é interpretar o item. A busca é por palavra: o
operador digita um termo e o sistema devolve todo registro cuja descrição o
contenha. Cabe à pessoa ler candidato por candidato e decidir se aquilo que
apareceu corresponde ao que foi pedido. Os exemplos relatados na entrevista
ilustram bem o tipo de erro que isso produz, por exemplo: uma busca por alface
trouxe preços de sanduíche natural, porque a descrição do sanduíche menciona
alface; uma busca por urna funerária trouxe também serviços funerários de
translado; uma busca por trator de esteira trouxe locações de trator cobradas
por hora, que são serviço e não equipamento.

O sistema especificado neste documento ataca esse ponto. Ele recupera candidatos
a preço de referência por proximidade de significado, aplica os filtros que hoje
a pessoa aplica de cabeça, apresenta a evidência que sustenta cada candidato e
gera os documentos da fase preparatória a partir desses mesmos dados.

### 2.4 Perspectiva do produto

O sistema recebe os documentos de demanda tais como já circulam no setor,
consulta uma base pública de contratações e devolve documentos e planilhas. Não se comunica
com nenhum sistema da prefeitura, não exige instalação em servidor municipal e
não depende do banco de preços comercial para funcionar.

Essa independência é deliberada. O município estudado paga pelo serviço
comercial, mas a maior parte das prefeituras de pequeno porte não tem esse
recurso, e é justamente onde o apoio faz mais falta. Ao não depender dele, o
sistema atende também quem parte de uma situação pior que a descrita aqui.

### 2.5 Perfil dos usuários

**O sistema tem um único perfil de usuário:** o servidor do setor de licitações,
que conduz a fase preparatória e responde pela cotação. Ele domina o processo
administrativo e não tem formação em tecnologia.

As demais pessoas envolvidas no processo aparecem no domínio, mas não operam o
sistema:

| Quem | Papel no processo | Relação com o sistema |
|---|---|---|
| Servidor da secretaria demandante | Origina a demanda e a envia como documento | Nenhuma. O documento chega por meio já em uso, e é o operador quem o importa |
| Assessoria jurídica | Analisa a legalidade das peças | Nenhuma. Lê os documentos exportados |
| Ordenador de despesa e setor de planejamento | Assinam as peças | Nenhuma |

**Por que um perfil só.** O gargalo medido está inteiramente no setor de
licitações: a triagem dos candidatos a preço, a redação das peças e a revisão.
As secretarias não participam dele. Exigir que elas usem o sistema acrescentaria
dependência de adesão, treinamento e decisão administrativa que estão fora do
alcance deste trabalho, sem tocar no que custa caro. A própria usuária pediu o
contrário: que o sistema importasse os documentos de demanda que ela já recebe,
em vez de pedir que as secretarias os preenchessem ali.

Nenhum perfil inclui equipe de tecnologia da informação. O setor estudado tem
dois servidores, e nenhum deles é da área.

### 2.6 Restrições

O sistema opera dentro de limites que não são negociáveis.

Os documentos precisam sair em formato editável, porque circulam entre setores e
são ajustados manualmente antes da assinatura. A servidora entrevistada foi
categórica ao afirmar que sempre solicita os documentos em formato editável, e
nunca em formato fechado.

A unidade de medida não é escolha de quem redige. O sistema de prestação de
contas do tribunal de contas competente aceita um conjunto fechado de unidades, e
o que não pertence a ele é recusado. Embalagem e forma farmacêutica, como bisnaga
ou comprimido, não são unidade de medida: pertencem à descrição do item. Essa é a
origem da regra, e é o que a torna inegociável.

A estrutura dos documentos não pode ser inventada. O ETP obedece a um conjunto de
seções vinculadas aos incisos da lei, e cada seção declara explicitamente qual
dispositivo atende. A ordem das seções adotada pelo município não coincide com a
ordem dos incisos, e as duas convenções precisam ser respeitadas ao mesmo tempo.

Por fim, a qualidade da correspondência entre itens é limitada pela qualidade
das descrições disponíveis na base pública, que o sistema não controla. Em um dos
processos analisados, o item demandado especificava dezoito atributos técnicos, e
nenhum dos preços candidatos trazia descrição que permitisse verificar um único
deles.

### 2.7 Suposições e dependências

Supõe-se que a base pública de contratações continue disponível, com interface
de programação estável, e que os dados nela publicados mantenham o nível atual de
detalhe. Uma degradação nessa base afetaria diretamente a qualidade da
recuperação.

Supõe-se também que a prefeitura mantenha a prática de consolidar demandas de
várias secretarias em um processo único, já que boa parte da complexidade
tratada aqui decorre dessa consolidação.

Por fim, a avaliação do sistema depende da colaboração continuada da fonte de
domínio, tanto para a validação com usuário quanto para a cessão de processos
encerrados que sirvam de referência.

---

## 3. Levantamento: método e evidências

### 3.1 Entrevista

Foi realizada uma entrevista estruturada com a servidora responsável pela fase
preparatória no setor de licitações do município estudado. O roteiro foi
elaborado previamente, com quarenta e três perguntas distribuídas em sete
blocos divididos assim: o processo hoje, os pontos de travamento, os documentos, a pesquisa de
preços, a linha de base de tempo, os critérios de aceitação e a verificação
externa. Quarenta e uma perguntas foram respondidas.

O roteiro escrito antes da sessão foi uma decisão de método. A conversa era
presencial e única, e sem preparo prévio o tempo teria sido gasto descobrindo o
que perguntar em vez de perguntando.

A parte mais produtiva da sessão, porém, não estava no roteiro. A entrevistada
abriu o sistema de cotação que utiliza e demonstrou o fluxo completo na tela, do
cadastro da cotação até a emissão do relatório. Boa parte do que se sabe hoje
sobre como a seleção de preços realmente acontece vem dessa demonstração.

### 3.2 Análise documental

A fonte de domínio cedeu quinze documentos referentes a três processos
administrativos já encerrados, escolhidos de modo a cobrir naturezas distintas de
objeto.

| Processo | Objeto | Itens | DFDs | ETP | TR | Cotação |
|---|---|---|---|---|---|---|
| A | Veículo utilitário | 1 | não cedido | 1 | 1 | 1 |
| B | Material de higiene e limpeza | 120 | 1 | 1 | 1 | 1 |
| C | Material de expediente | 150 | 5 | 1 | 1 | 1 |

A escolha de objetos diferentes foi proposital. Um bem de capital indivisível,
um lote de consumo homogêneo e um lote de consumo heterogêneo permitem separar o
que é característica do processo do que é característica do objeto. Foi essa
separação que revelou, por exemplo, que conclusões tiradas do processo A não se
sustentavam nos demais.

### 3.3 Evidências quantitativas

As afirmações desta especificação que envolvem números foram calculadas sobre os
documentos, e não estimadas. O que segue é o resultado.

**Tempo de composição da pesquisa de preços.** Os relatórios registram a data de
início e a de encerramento de cada cotação.

| Processo | Itens | Duração | Páginas do relatório |
|---|---|---|---|
| A | 1 | 11 dias corridos | 4 |
| B | 120 | 9 dias corridos | 223 |
| C | 150 | 28 dias corridos | 248 |

Em entrevista, a estimativa declarada havia sido de cerca de dois dias para cem
itens e uma semana para cento e cinquenta. As duas medidas são compatíveis: a
declarada corresponde a trabalho concentrado, e a medida corresponde ao tempo que
o processo de fato consome, com as interrupções da rotina. A razão entre elas
fica entre quatro e quatro e meio, o que dá contorno numérico à percepção
relatada de que há mais espera do que trabalho.

O processo de um único item é o dado mais informativo do conjunto. Onze dias
corridos para cotar um item mostram que existe um custo fixo considerável antes
de qualquer ganho de escala, e que o benefício de um sistema não será
proporcional ao número de itens.

**Origem dos preços.** Cada preço no relatório declara a fonte de onde foi
extraído. A tabela abaixo considera todos os preços de cada processo.

| Origem | Processo B | Processo C |
|---|---|---|
| Portal nacional de contratações | 47,5% | 62,3% |
| Plataformas privadas de pregão | 35,0% | 23,3% |
| Base federal de compras | 5,8% | 7,6% |
| Tribunais de contas | 8,3% | 4,1% |
| Fontes distintas listadas no relatório | 15 | 18 |

O portal nacional é, isoladamente, a maior fonte, mas está longe de responder
pelo conjunto: entre 38% e 52% dos preços vêm de outros lugares, com destaque
para as plataformas privadas de pregão eletrônico. Essa distribuição é o que
dimensiona a perda de cobertura discutida na seção 2.4, e o número precisa ser
lido com essa gravidade.

**Conformidade das regras observadas.**

| Regra verificada | Resultado |
|---|---|
| Mínimo de três preços por item | Cumprida com exatidão: 3,00 e 2,99 preços por item |
| Preço coletado há menos de doze meses | Cumprida integralmente, em 811 preços datados |
| Método de cálculo declarado no documento | Média aritmética, nos três processos |
| Procedência declarada | Presente em 100% dos preços |
| Procedência com endereço direto do registro | 55,8% no processo B e 66,7% no processo C |

Três observações sobre esta tabela.

A primeira é que a média de preços por item é praticamente três exatos, e não
três como piso a partir do qual se acrescenta. Isso confirma o que a
entrevistada declarou: ela seleciona três e para, porque um quarto preço puxaria
a média para baixo e ela quer preservar margem de negociação.

A segunda é que a validade temporal é contada a partir do início da pesquisa, e
não do encerramento. O preço é selecionado no dia em que é buscado, e é essa a
data que a regra observa. Aplicando o critério assim, nenhum dos 811 preços está
vencido, e a folga é pequena: o mais antigo estava a nove dias do limite. A
janela útil de dados é curta, o que tem consequência direta sobre o
dimensionamento da base do sistema.

A terceira diz respeito à procedência, e a distinção importa. Todo preço tem
fonte declarada, com o órgão contratante, a data, a modalidade e a identificação
da contratação de origem. O que varia é se essa fonte vem com o endereço do
registro específico ou apenas com o nome da plataforma. Em 44,2% dos preços do
processo B e 33,3% dos do processo C há o nome da plataforma, mas não o
endereço: para conferir aquele preço, é preciso ir até a plataforma e buscar
manualmente pela identificação da contratação. A procedência existe, mas custa
caro verificar, e é esse custo que o requisito RF26 ataca.

**Invariância dos documentos.** Comparando os três ETPs seção por seção, mediu-se
a similaridade do texto entre processos de objetos diferentes.

O método é determinístico e reproduzível, e convém declará-lo. Cada seção é
extraída pelo seu cabeçalho numerado. O cabeçalho e a citação legal ao lado dele
são descartados, porque são fixos pelo modelo e compará-los mediria o formulário
em vez do texto redigido. O que resta é normalizado, com caixa baixa, remoção de
acentuação e descarte de pontuação, e então quebrado em palavras. A comparação
entre dois conjuntos de palavras usa o algoritmo de casamento de padrões de
Ratcliff e Obershelp, na implementação da biblioteca padrão da linguagem
utilizada, que devolve duas vezes a quantidade de elementos coincidentes
dividida pelo total de elementos das duas sequências. O resultado fica entre
zero, quando não há nada em comum, e um, quando os textos são idênticos.

A unidade de comparação é a palavra, e não o caractere. Comparando caracteres,
palavras diferentes que compartilham letras apareceriam como semelhantes, o que
não responde à pergunta de interesse. A pergunta é quanto do texto de um
documento reaparece em outro.

A coluna abaixo traz, para cada seção, a **menor** similaridade entre os três
pares possíveis de documentos, que é o valor conservador.

| Seção do ETP | Menor similaridade entre os três |
|---|---|
| Descrição da necessidade | 0,07 |
| Requisitos da contratação | 0,16 |
| Estimativa de quantidades | 0,03 |
| Levantamento de mercado | 0,25 |
| Estimativa de valor | 0,11 |
| Descrição da solução | 0,40 |
| Justificativa para parcelamento | 0,14 |
| Resultados pretendidos | 0,14 |
| Providências prévias | 0,23 |
| Contratações correlatas | 0,97 |
| Impactos ambientais | 0,16 |
| Posicionamento conclusivo | 0,18 |

A mediana das menores similaridades é 0,16.

O resultado é claro e teve consequência sobre o desenho do sistema. A estrutura é
totalmente invariante: as mesmas quinze seções, com os mesmos títulos, na mesma
ordem e com o mesmo vínculo aos incisos da lei, nos três processos. O texto, ao
contrário, não é reaproveitável. Apenas uma seção se repete de fato entre
processos, e é a mais curta de todas.

Isso confirma o que a entrevistada havia declarado, ao dizer que segue os mesmos
tópicos mas adapta um texto novo a cada situação. E indica que a geração dos
documentos não pode ser tratada como preenchimento de um modelo com lacunas: o
esqueleto é reaproveitável, o conteúdo precisa ser produzido caso a caso, a
partir dos dados do processo.

Há ainda uma evidência de que a cópia entre processos produz erro. Entre os
processos B e C, redigidos no mesmo período, a seção de levantamento de mercado
apresenta similaridade de 1,00: texto idêntico, palavra por palavra, para
objetos completamente diferentes.

Os ETPs analisados afirmam que os quantitativos foram definidos considerando o
histórico de consumo de contratações anteriores e a demanda executada em
exercícios precedentes. Nenhum dos seis DFDs que esses estudos citam como fonte
apresenta memória de cálculo. A justificativa deles consiste em texto corrido
sobre as dificuldades logísticas do município, e a quantidade aparece apenas como
número em uma tabela.

Do lado do preço ocorre o mesmo. Um dos estudos afirma que a estimativa de valor
considerou as particularidades logísticas do município, e o relatório de cotação
anexado ao próprio processo apresenta preços originados de licitações realizadas
em outros estados.

Não há indício de má-fé nesses casos. Trata-se de texto padrão que sobreviveu de
um processo para outro e passou por redação, revisão jurídica e assinatura sem
que a discrepância fosse notada. É exatamente esse tipo de falha que um documento
gerado a partir da evidência real deixa de produzir, porque a afirmação passa a
ser construída sobre o que de fato foi feito.

### 3.4 Limitações do levantamento

O levantamento cobre um único município e uma única informante principal. É um
estudo de caso, não uma amostra, e os resultados devem ser lidos nesse registro.

A entrevistada trabalhou anteriormente em outra prefeitura, onde o ETP era
praticamente um gabarito, mudando apenas o objeto, a justificativa e o quadro de
valores. No município estudado cada processo tem estudo próprio. O ganho medido
aqui, portanto, não se transfere automaticamente para um município que já opera
por gabarito.

Existe efeito de observação, uma vez que quem sabe estar sendo medido trabalha de
maneira diferente.

Nem tudo o que foi declarado se confirmou na análise. A entrevistada descreveu
uma prioridade geográfica na busca de preços, começando pelo estado, passando
pela região e só depois recorrendo ao âmbito nacional. Essa prioridade se
verifica em um dos processos e não em outro, provavelmente porque para material
comum há preço regional disponível e para bem de capital específico não há.
Heurística declarada por informante é indício de prática, não prova de aplicação
uniforme.

Há uma limitação relevante para a avaliação do sistema. O relatório de cotação
registra os preços escolhidos, mas não os candidatos que foram examinados e
descartados. Existe, portanto, um conjunto de julgamentos positivos e
incompletos: é possível medir se o sistema recupera o que a servidora escolheu,
mas não é possível concluir que aquilo que ele traz a mais está errado.

Por fim, e esta é a lacuna de maior consequência, **a proporção entre os tipos de
processo não foi medida**. Sabe-se que o setor conduz cerca de dez contratações
por semana somando todas as modalidades, e que o caminho descrito aqui é apenas
um deles. Não se sabe que fatia do volume, nem do tempo de trabalho, corresponde
a ele. Enquanto esse número não existir, a afirmação de ganho vale para o tipo de
processo estudado, e não para a rotina do setor como um todo. Medir isso depende
de uma pergunta simples à fonte de domínio, e está na lista do que perguntar.

---

## 4. Regras de negócio

As regras a seguir decorrem da legislação e da prática do setor. Elas valem
independentemente da existência do sistema, e o sistema não pode contrariá-las.

| Código | Regra |
|---|---|
| RN01 | Toda contratação nasce de um Documento de Formalização de Demanda emitido pela secretaria requisitante, contendo objeto, justificativa, quantidade e período de atendimento |
| RN02 | A quantidade solicitada exige memória de cálculo, com base em consumo anterior, atas ou contratos, e o período a que se destina |
| RN03 | Demandas de mesmo objeto vindas de secretarias distintas são consolidadas em um processo único de registro de preços, preservando-se a quantidade de cada uma |
| RN04 | O Termo de Referência é derivado do Estudo Técnico Preliminar. Divergência entre os dois em campo pareado é motivo de questionamento e pode levar ao cancelamento do processo |
| RN05 | O valor estimado funciona como teto. Proposta acima dele é desclassificada |
| RN06 | A pesquisa de preços exige no mínimo três preços por item. Com menos de três, é obrigatório justificar |
| RN07 | Um preço só é válido como parâmetro se tiver sido coletado dentro dos últimos doze meses |
| RN08 | Todo preço utilizado deve ter procedência comprovável anexada ao processo. Anexa-se o relatório íntegro da pesquisa, e não um resumo redigido à parte |
| RN09 | O valor estimado admite média, mediana, menor preço ou média saneada. A prática observada no setor é a média aritmética |
| RN10 | Preço discrepante deve ser descartado. Se o descarte deixar menos de três preços, é preciso justificar o conjunto remanescente |
| RN11 | Preços originados do mesmo evento de contratação não constituem observações independentes |
| RN12 | Item divisível é julgado por item, para ampliar a disputa. Item indivisível é tratado como lote único. A decisão é registrada no ETP |
| RN13 | A unidade de medida do preço de referência deve ser compatível com a unidade do item demandado |
| RN14 | A ordem de grandeza da quantidade do preço de referência deve se aproximar da quantidade demandada |
| RN15 | Item composto por peças de preços distintos é decomposto em itens elementares antes de ser cotado |
| RN16 | A unidade de medida provém de vocabulário fechado. Embalagem não é unidade de medida |
| RN17 | A busca de preço observa prioridade geográfica: estado, depois região, depois âmbito nacional |
| RN18 | O ETP é assinado pelo setor de planejamento e o TR pelo ordenador de despesa. A segregação entre quem redige e quem assina é exigência normativa |
| RN19 | A elaboração do ETP deveria ser precedida de pesquisa prévia de preços, hoje suprimida por razões de custo |
| RN20 | O documento de pesquisa de preços registra o método matemático aplicado, e cada preço declara o dispositivo legal que o autoriza como parâmetro |
| RN21 | O relatório de pesquisa anexado ao processo traz mecanismo de verificação de autenticidade |
| RN22 | Preço coletado de base pública é, em regra, derivado de propostas finais de contratações já homologadas, tratando-se portanto de preço já negociado |

Duas observações sobre este conjunto.

A regra RN02 merece precisão, porque a primeira leitura desta especificação a
descreveu de forma equivocada. O levantamento de quantidade **existe**: as
secretarias o fazem, tomando por base o consumo do exercício anterior, ou dos
dois anteriores, e justificam quando pedem aumento. O que não existe é o
**registro** desse levantamento. Nenhum dos seis documentos de demanda analisados
traz a conta que levou até a quantidade, e o setor de licitações não a confere ao
receber. Os estudos técnicos derivados afirmam que houve levantamento, e houve,
mas não há prova anexada ao processo. É uma lacuna de documentação, não de
método, e a seção 5.2 detalha como o sistema a trata.

A regra RN16 tem evidência direta nos documentos. Entre os seis DFDs analisados,
a mesma unidade de medida aparece escrita de quatro formas diferentes, o que
inviabiliza qualquer filtro automático por unidade e confirma que o problema é
real, e não hipotético.

---

## 5. Requisitos funcionais

### 5.1 Convenções

Cada requisito recebe um identificador único e permanente. Requisito retirado
não tem seu código reaproveitado, para que referências antigas continuem
inteligíveis.

A prioridade segue três níveis:

| Nível | Significado |
|---|---|
| Essencial | Sem ele o sistema não cumpre seu propósito. Precisa estar na primeira versão funcional |
| Importante | O sistema funciona sem ele, mas com perda significativa de utilidade |
| Desejável | Agrega valor e pode ser adiado sem prejuízo ao restante |

O verbo "deve" indica obrigação. O verbo "pode" indica possibilidade oferecida ao
usuário, e não obrigação do sistema.

### 5.2 Módulo de documentos da fase preparatória

| Código | Requisito | Prioridade |
|---|---|---|
| RF01 | O sistema deve importar os documentos de formalização de demanda em formato editável, tais como chegam ao setor, e deles extrair objeto, justificativa, itens, quantidades, unidades de medida e secretaria de origem | Essencial |
| RF39 | O sistema deve permitir que o operador corrija e complemente o que foi extraído do documento importado, antes de a demanda entrar no processo | Essencial |
| RF02 | O sistema deve validar a descrição de cada item, verificando a unidade de medida contra vocabulário fechado, detectando item composto e sinalizando descrição insuficiente para cotação | Essencial |
| RF03 | O sistema deve consolidar demandas de mesmo objeto vindas de secretarias distintas, somando os quantitativos e preservando a quantidade atribuída a cada uma | Essencial |
| RF38 | O sistema deve preservar, no documento consolidado, a restrição de entrega mais estrita declarada entre as secretarias participantes, ou sinalizar explicitamente quando ela for descartada | Essencial |
| RF04 | O sistema deve gerar minuta de Estudo Técnico Preliminar com as quinze seções previstas, na ordem adotada pelo município, indicando ao lado de cada uma o dispositivo legal que atende | Essencial |
| RF05 | O sistema deve gerar minuta de Termo de Referência derivada do mesmo conjunto de dados que originou o Estudo Técnico Preliminar | Essencial |
| RF06 | O sistema deve verificar a consistência entre Estudo Técnico Preliminar e Termo de Referência nos campos que aparecem nos dois documentos, e apontar divergência antes da exportação | Essencial |
| RF07 | O sistema deve exportar os documentos em formato editável | Essencial |
| RF08 | O sistema deve recuperar, no acervo de documentos anteriores do próprio município, a redação empregada em processos de objeto semelhante, oferecendo-a como repertório de consulta | Importante |
| RF09 | O sistema deve destacar visualmente todo trecho gerado que exija conferência humana, em especial base legal citada, prazo e valor numérico | Essencial |
| RF10 | O sistema deve verificar a coerência entre a unidade requisitante declarada, o órgão indicado na dotação orçamentária e o objeto da contratação, apontando divergência | Essencial |
| RF11 | O sistema deve redigir as seções que descrevem método a partir do resultado efetivo do processo, e não de texto padrão. Isso vale para as fontes consultadas, o critério de cálculo aplicado, o recorte utilizado e a origem declarada da quantidade | Essencial |
| RF12 | O sistema deve verificar, seção por seção, se o conteúdo responde ao que o dispositivo citado exige, sinalizando seção preenchida com conteúdo pertencente a outra | Importante |
| RF13 | O sistema deve detectar defeitos de forma recorrentes, entre eles divergência entre numeral e valor por extenso, cláusula condicional inaplicável ao caso, tempo verbal incompatível com a cronologia do processo, formatação numérica ambígua em campo de quantidade e numeração de subitem fora de sequência | Importante |
| RF14 | Quando a memória de cálculo não for informada, o sistema deve gerar o documento assim mesmo, sem afirmar que houve levantamento de histórico de consumo, e deve registrar a lacuna de forma que ela permaneça visível no arquivo exportado | Essencial |
| RF34 | O sistema deve **produzir a memória de cálculo** a partir do consumo dos exercícios anteriores, quando esses dados forem informados, de modo que a justificativa da quantidade deixe de depender de o demandante redigi-la | Importante |
| RF35 | O sistema deve consolidar as justificativas dos vários documentos de demanda em uma justificativa única para o processo, preservando o que é próprio de cada secretaria | Essencial |
| RF36 | O sistema deve identificar itens equivalentes pedidos por secretarias distintas com descrições ou unidades divergentes, propor uma descrição de consenso e submetê-la ao operador, que decide. O alinhamento com as secretarias continua acontecendo fora do sistema, pelos meios já em uso | Essencial |
| RF37 | O sistema deve emitir o Estudo Técnico Preliminar em duas versões a partir do mesmo estado: a minuta, anterior à pesquisa de preços, com a estimativa de valor redigida como providência futura, e a versão final, com o valor apurado e as fontes consultadas | Essencial |

Sobre RF14, cabe explicar a decisão. Bloquear o processo até que a memória de
cálculo seja preenchida seria a solução mais correta do ponto de vista da norma,
mas um sistema que trava numa exigência que hoje ninguém cumpre seria abandonado
no primeiro uso, e o defeito continuaria acontecendo sem ele. Optou-se por gerar
o documento e marcar a lacuna. O custo dessa escolha é conhecido: a marcação pode
ser ignorada. Por isso a exigência de que ela sobreviva à exportação, e não fique
apenas na tela. Um documento que chega ao processo com a lacuna visível obriga
quem for removê-la a fazer isso conscientemente.

### 5.3 Módulo de pesquisa de preços

| Código | Requisito | Prioridade |
|---|---|---|
| RF15 | O sistema deve importar a lista de itens por planilha, contendo descrição resumida, descrição completa, quantidade e unidade de medida | Essencial |
| RF16 | O sistema deve recuperar candidatos a preço de referência por proximidade de significado da descrição, e não por coincidência de palavras | Essencial |
| RF17 | O sistema deve filtrar e ordenar os candidatos por compatibilidade de unidade de medida, ordem de grandeza da quantidade, recorte geográfico e janela temporal | Essencial |
| RF18 | O sistema deve distinguir produto de serviço e excluir candidatos cuja natureza não corresponda à do item demandado | Essencial |
| RF19 | O sistema deve agrupar candidatos originados do mesmo evento de contratação, de modo que não sejam contados como observações independentes | Importante |
| RF20 | O sistema deve exibir, para cada candidato, a evidência que sustenta a decisão: descrição integral, unidade, quantidade, órgão contratante, data, fonte e valor | Essencial |
| RF21 | O sistema deve sinalizar, para cada candidato, quais especificações exigidas pelo item demandado não podem ser verificadas na descrição disponível | Essencial |
| RF22 | O sistema deve apresentar o contexto da contratação de origem de cada candidato, incluindo objeto, modalidade e se houve adesão a ata, de modo que a comparabilidade seja julgada e não presumida | Importante |
| RF23 | O sistema deve aceitar uma estimativa de preço esperado e ordenar os candidatos considerando tanto a comparabilidade do item quanto a proximidade a essa estimativa, exibindo as duas dimensões separadamente | Essencial |
| RF24 | O sistema deve sinalizar preço discrepante indicando o critério aplicado, e não apenas o valor | Importante |
| RF25 | O sistema deve calcular o valor estimado pelo critério escolhido pelo usuário, produzindo memória de cálculo exportável | Essencial |
| RF26 | O sistema deve gerar o mapa de cotação com a procedência de cada preço resolvida até o registro de origem, e recusar preço cuja procedência não possa ser resolvida | Essencial |
| RF27 | O sistema deve emitir o mapa de cotação com mecanismo de verificação de autenticidade | Importante |
| RF28 | O sistema deve registrar o início e o encerramento da composição de cada pesquisa | Desejável |
| RF29 | O usuário pode duplicar uma pesquisa anterior e reexecutá-la, e o sistema deve indicar quais preços perderam validade | Importante |
| RF30 | O sistema deve permitir reconstituir uma pesquisa anterior tal como ela se encontrava na data em que foi realizada, sobre os dados vigentes naquela data | Essencial |
| RF31 | O sistema deve coletar e indexar itens contratados a partir da interface pública do portal nacional de contratações | Essencial |

Sobre RF23, convém registrar de onde veio. Durante a demonstração de tela,
observou-se que a servidora descartou um candidato antes mesmo de ler a
descrição, apenas por considerar o valor implausível, e explicou em voz alta o
raciocínio, dizendo que precisava chegar perto do que julgava ser o preço certo.
Em outro momento da entrevista ela descreveu o mesmo procedimento de forma
explícita: solicita uma cotação a um fornecedor local e, a partir dela, busca na
base preços que se aproximem daquele patamar, por corresponderem à realidade do
município.

A seleção humana, portanto, considera duas dimensões simultâneas: a semelhança do
item e a plausibilidade do preço. Um mecanismo que ordenasse apenas por
semelhança não reproduziria esse comportamento, e seria injusto avaliá-lo como se
devesse reproduzir.

Sobre RF26, a exigência é mais rigorosa do que a prática atual, e isso é
proposital. Mediu-se que entre um terço e quase metade dos preços de
processos reais trazem a fonte apenas nomeada, sem o endereço do registro que a
sustenta. A procedência existe, mas conferi-la exige busca manual na plataforma
de origem. Como a regra RN08 exige procedência comprovável, e comprovação que
custa caro tende a não ser feita, o sistema deve resolver a fonte até o registro
específico.

### 5.4 Requisitos transversais

| Código | Requisito | Prioridade |
|---|---|---|
| RF32 | O sistema deve registrar trilha de auditoria de cada decisão, indicando quem decidiu, quando, quais candidatos estavam disponíveis, quais foram escolhidos e sob qual critério | Essencial |
| RF33 | O usuário pode editar qualquer conteúdo gerado antes da exportação | Essencial |

---

## 6. Requisitos não funcionais

| Código | Requisito | Categoria | Prioridade |
|---|---|---|---|
| RNF01 | O sistema não deve exigir substituição de sistema em uso pela prefeitura nem integração com sistema legado | Restrição de projeto | Essencial |
| RNF02 | Os documentos devem ser entregues em formato editável e as planilhas em formato de uso corrente, compatíveis com o que o processo administrativo já aceita | Interoperabilidade | Essencial |
| RNF03 | A revisão manual de um Estudo Técnico Preliminar gerado pelo sistema não deve ultrapassar duas horas de trabalho | Usabilidade | Essencial |
| RNF04 | Toda afirmação presente em documento gerado deve ser rastreável até sua origem, e nenhuma base legal pode ser citada sem referência conferível | Confiabilidade | Essencial |
| RNF05 | O sistema deve ser operável por uma única pessoa, sem apoio de equipe de tecnologia da informação | Usabilidade | Essencial |
| RNF06 | O sistema deve processar contratação de até mil e quinhentos itens sem degradação que inviabilize o uso | Desempenho | Essencial |
| RNF07 | A recuperação de candidatos deve ser rápida o suficiente para permitir triagem interativa item a item | Desempenho | Essencial |
| RNF08 | A trilha de auditoria deve ser imutável e consultável, permitindo reproduzir o estado de uma pesquisa passada | Confiabilidade | Essencial |
| RNF09 | A interface e o vocabulário devem estar em português, empregando os termos correntes do domínio | Usabilidade | Importante |
| RNF10 | O acesso ao sistema deve exigir autenticação individual, e toda ação registrada na trilha de auditoria deve nomear quem a praticou | Segurança | Essencial |
| RNF11 | O modelo de dados e o controle de acesso devem admitir mais de um usuário e mais de um órgão, ainda que apenas um perfil seja implementado nesta versão | Manutenibilidade | Importante |

Sobre RNF10 e RNF11, cabe registrar o motivo, já que o sistema tem um único
perfil de usuário e alguém poderia concluir que autenticação sobra.

Ela não sobra, por duas razões independentes. A primeira é a trilha de auditoria:
o requisito RF32 exige registrar quem tomou cada decisão, e isso só faz sentido
se houver quem. Um sistema sem autenticação produz trilha anônima, que perante um
órgão de controle vale pouco. A segunda é que o sistema lida com processo
administrativo em curso, cujo valor estimado ainda não é público, e deixar isso
aberto seria decisão difícil de defender.

O RNF11 é de outra natureza: é uma decisão de projeto, não uma exigência do
domínio. Um perfil é o que este trabalho implementa, mas nada no modelo de dados
deve impedir que outros venham depois, seja outro servidor do mesmo setor, seja
outro município. O custo de prever isso agora é baixo; o de descobrir depois que
o desenho não comporta é alto.

---

## 7. Critérios de aceitação

Os critérios a seguir não foram formulados pelo autor. São o que a servidora
responsável pelo processo declarou, em entrevista, que precisaria acontecer para
que o sistema fosse considerado útil.

**Sobre a confiança no documento gerado.** O que destruiria a confiança são as
fontes, e em especial base legal citada de forma imprecisa. A entrevistada já
utiliza ferramentas de geração de texto e descreveu o problema com precisão:
disse que a resposta costuma vir bem escrita, mas que tudo precisa ser adaptado à
realidade local, porque às vezes o texto enfeita demais e inclui coisas que não
correspondem ao caso, e que é sempre necessário conferir as leis citadas para
saber se são realmente aquelas.

**Sobre a realidade local.** Texto genérico não serve. O documento precisa
refletir as condições concretas do município, inclusive a dificuldade logística
de os produtos chegarem, que é elemento recorrente das justificativas.

**Sobre a edição.** O documento gerado precisa ser editável, sem exceção.

**Sobre o esforço residual.** Até duas horas de revisão manual em um Estudo
Técnico Preliminar tornam o apoio compensador, comparado ao mais de um dia que a
redação exige hoje. O limite foi declarado como uma hora na primeira sessão e
revisto para duas na validação, com a justificativa de que o ajuste atual às
vezes passa de um dia inteiro.

**Sobre a verificação da pesquisa de preços.** A conferência é feita
visualmente, campo por campo: fonte, data, descrição e unidade de medida. O
sistema precisa tornar essa conferência barata, e não substituí-la.

**Sobre o momento do apoio.** O apoio é mais útil durante a composição e também
na conferência, e não em apenas um dos dois momentos.

---

## 8. Verificação

Cada categoria de requisito será verificada por um método definido, e a escolha
do método é parte da especificação.

| Categoria | Método de verificação |
|---|---|
| Geração de documento | Inspeção do documento gerado contra a estrutura exigida, com verificação automatizada da presença de todas as seções e do vínculo declarado a cada dispositivo legal |
| Consistência entre documentos | Teste automatizado sobre casos construídos com divergência deliberada em cada campo pareado |
| Detecção de defeitos | Teste sobre um conjunto de documentos com defeitos conhecidos, derivado das classes identificadas na análise documental |
| Recuperação de preços | Medição de recuperação contra pesquisas de preço já realizadas, verificando se os preços escolhidos pela servidora aparecem entre os primeiros resultados |
| Valor estimado | Comparação entre o valor produzido pelo sistema e o valor produzido manualmente para o mesmo conjunto de itens |
| Desempenho | Teste de carga com processo de mil e quinhentos itens |
| Esforço residual | Medição cronometrada de revisão com a usuária, comparada à linha de base declarada |
| Trilha de auditoria | Demonstração de reconstituição de uma pesquisa passada |

Sobre a verificação da recuperação de preços, é preciso registrar duas ressalvas
que decorrem da limitação apontada na seção 3.4.

A primeira é que se mede recuperação, e não precisão. Como o relatório não
registra os candidatos descartados, um preço que o sistema traga e que a
servidora não tenha escolhido pode ser igualmente aceitável, e nada no registro
permite distinguir. Uma sessão curta de validação, apresentando a ela os
primeiros resultados de alguns itens e perguntando quais aceitaria, resolveria
essa lacuna e está prevista.

A segunda é que a avaliação será executada em duas condições, com e sem a
estimativa de preço esperado prevista em RF23. A diferença entre as duas isola
quanto do acerto decorre de compreender o item e quanto decorre de já conhecer o
preço. Esse resultado deve ser reportado, e não omitido: se o desempenho só se
sustentar na condição favorável, isso significa que o sistema depende de o
operador já saber a resposta, e a contribuição precisa ser reformulada.

---

## 9. Rastreabilidade

Todo requisito desta especificação tem origem declarada em uma das três fontes
descritas na seção 3: a entrevista estruturada, a análise dos documentos ou a
medição realizada sobre eles. Não há requisito derivado de suposição do autor sem
que isso esteja indicado no próprio texto do requisito ou no comentário que o
acompanha.

A tabela a seguir relaciona os principais requisitos às regras de negócio e às
evidências que os justificam.

| Requisito | Regras relacionadas | Evidência |
|---|---|---|
| RF02, RF15 | RN13, RN15, RN16 | Unidade de medida escrita de quatro formas distintas entre documentos de demanda irmãos |
| RF01, RF39 | RN01 | Documentos de demanda recebidos em formato editável, pelos meios já em uso no setor |
| RF03, RF36 | RN03, RN13, RN16 | Cinco demandas de secretarias diferentes consolidadas em um processo de cento e cinquenta itens, com descrição e unidade normalizadas antes da cotação |
| RF37 | RN19 | Minuta e versão final de um mesmo estudo: onze das doze seções idênticas, só a estimativa de valor difere |
| RF38 | RN03 | Horário de entrega mais restrito de uma secretaria ausente do documento consolidado |
| RF34, RF35 | RN02 | Levantamento de quantidade realizado pelas secretarias, sem registro no documento de demanda; justificativas recebidas descritas pela usuária como genéricas |
| RF04, RF05 | RN01, RN04, RN18 | Estrutura de quinze seções idêntica nos três processos analisados |
| RF06 | RN04 | Divergência de local de entrega entre estudo e termo, em processo real |
| RF08 | RN04 | Similaridade de texto entre 0,03 e 0,40 nas seções que variam; mediana 0,16 |
| RF11, RF14 | RN02, RN08, RN20 | Estudos afirmando levantamento de histórico de consumo que os documentos de demanda não contêm |
| RF16, RF17, RF18 | RN13, RN14, RN17 | Busca por palavra devolvendo sanduíche para alface e serviço para equipamento |
| RF19 | RN11 | Candidatos com mesmo valor e mesma data identificados manualmente pela operadora |
| RF21 | Restrição de seção 2.6 | Item com dezoito atributos técnicos exigidos e nenhum candidato com descrição que permita verificar qualquer um |
| RF23 | RN17, RN22 | Descarte de candidato por implausibilidade de valor, antes da leitura da descrição |
| RF26 | RN08 | Entre 33% e 44% dos preços com fonte nomeada mas sem endereço do registro |
| RF30, RF32 | RN08, RN21 | Registro atual preservado como documento estático de duzentas e vinte e três páginas, não consultável |
| RNF03 | Seção 7 | Limite de duas horas declarado pela usuária na sessão de validação |
| RNF10 | RF32 | Trilha de auditoria precisa nomear o autor de cada decisão |
| RNF06 | Seção 3.3 | Maior processo medido com cento e cinquenta itens; a usuária confirmou em validação uma cotação de medicamentos com cerca de mil e quinhentos |

---
