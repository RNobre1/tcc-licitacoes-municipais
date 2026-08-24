# Procedência dos arquivos deste diretório

**Insumo externo. Não editar nenhum arquivo daqui.**

Estes são os artefatos de formatação publicados pela Sociedade Brasileira de
Computação para artigos de conferência. Eles são a **fonte única** do formato
SBC neste repositório: as medidas não são recopiadas para
`scripts/normas_ufopa.py` nem para `texto/comum/sbc-tcc.sty`, e
`tests/leitura_sbc.py` as lê daqui.

Consequência prática: para acompanhar uma revisão publicada pela SBC, basta
substituir o arquivo. Os testes passam a medir contra a geometria nova sem que
uma linha de Python ou de LaTeX mude. Para o oposto — mudar uma medida sem
mudar o `.sty` — não existe caminho, e é de propósito.

## Arquivos

| Arquivo | O que é |
|---|---|
| `sbc-template.sty` | Geometria, tipografia, `\address`, `\inst`, `\email`, ambientes `resumo` e `abstract`, e a redefinição de `thebibliography` |
| `sbc.bst` | Estilo de bibliografia do BibTeX clássico. Produz chamada autor-data entre colchetes, como `[Brasil 2021]` |

## Obtenção

| | |
|---|---|
| **Obtido em** | 24/08/2026 |
| **Origem imediata** | `github.com/cezarlamann/sbc-latex-template`, diretório `template/` |
| **Origem declarada** | Sociedade Brasileira de Computação. O repositório acima se identifica como réplica dos arquivos do sítio oficial da SBC |
| **Autoria do `.sty`** | Jomi Hübner e Rafael Bordini, junho de 2001, atualizado em março de 2005 (declarado no cabeçalho do arquivo) |
| **Versão declarada** | `\ProvidesPackage{sbc-template}[2001/06/09]` |

```
sbc-template.sty  sha256  9538ae30a01c94fa8602567eb4103da010823e0307fe921398577f325361a868
sbc.bst           sha256  d884c6793e4ea54d13f5c751b3d6f4ea529a62d0906cd9774f2ec350b394691f
```

⚠️ **Não conferido contra o sítio oficial da SBC.** A obtenção foi por réplica em
repositório de terceiro, e a cadeia até o original não foi verificada. Antes de
submeter a um congresso, baixar os arquivos do sítio da SBC e comparar as somas
acima. Enquanto isso não for feito, o que está aqui serve ao trabalho acadêmico
e **não** dispensa a conferência para submissão.

## O que foi verificado, e como

Em 24/08/2026, nesta máquina (TinyTeX, TeX Live 2026, macOS):

| Verificação | Resultado |
|---|---|
| Compila com `pdflatex`, UTF-8 e `fontenc` T1 | sim, sem erro |
| Geometria que o `.sty` declara | A4; margens 3,5 cm superior, 2,5 cm inferior, 3,0 cm laterais |
| Corpo e entrelinha | 12 pt sobre 14 pt |
| Recuo de parágrafo e espaço entre parágrafos | 1,27 cm e 6 pt |
| Rótulo pendurado na bibliografia | confirmado: `\itemindent -\leftmargin` puxa o rótulo para fora da mancha, à esquerda, de propósito |
| `caption2`, de que o `.sty` depende | presente no TinyTeX, dentro do pacote `caption` como camada de compatibilidade |

Duas coisas que o `.sty` de exemplo da SBC faz e que **não** foram herdadas,
com o motivo:

- **`inputenc` em `latin1`.** As seções deste repositório são UTF-8. Deixar o
  insumo externo ditar a codificação do que é nosso seria inverter a
  dependência. `texto/comum/sbc-tcc.sty` carrega `utf8`.
- **`enumitem` e `placeins`.** Usados apenas pelo `.tex` de exemplo, não pelo
  `.sty`. Nenhum dos dois está instalado nesta máquina, e o alvo compila sem
  eles.

## Limitação conhecida do `sbc.bst`

É de 2001 e ignora os campos que o `biblatex` introduziu depois. Em
`texto/comum/refs.bib` isso atinge `subtitle` e `urldate`, presentes nas entradas
de legislação: o dado continua no arquivo e sai impresso no alvo do SIBI, mas
**não** aparece no alvo SBC. Conferir a saída quando essas entradas passarem a
ser citadas de fato.

Armadilha relacionada, já corrigida e registrada no cabeçalho do `refs.bib`: o
BibTeX clássico **descarta a entrada inteira** ao encontrar um comentário `%`
entre os campos, com aviso apenas no `.blg` e um `[?]` no PDF como único
sintoma. O `biblatex` aceita as duas formas, e por isso o defeito ficou dormente
até este alvo existir.
