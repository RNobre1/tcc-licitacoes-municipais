# Sistemas inteligentes aplicados à gestão pública

> Trabalho de Conclusão de Curso · Bacharelado em Ciência da Computação
> Universidade Federal do Oeste do Pará — Instituto de Engenharia e Geociências

**Automação da fase preparatória e pesquisa de preços em licitações municipais.**

---

## Problema

A Lei nº 14.133/2021 exige, antes de publicar qualquer edital, que o município
elabore o Estudo Técnico Preliminar e o Termo de Referência da contratação e
fundamente o valor estimado por meio de pesquisa de preços. Em prefeituras de
pequeno porte, essa fase preparatória é o maior gargalo do processo: as
secretarias demandantes não dispõem de modelos padronizados para redigir os
documentos, e a cotação depende de fornecedores locais que respondem devagar ou
simplesmente não respondem.

## Proposta

Uma aplicação web de apoio ao servidor, deliberadamente **não invasiva**: não
substitui sistema em uso, não exige integração com sistema legado e entrega
documentos nos formatos que o processo administrativo já aceita.

- **Geração assistida de minutas** — formulário guiado que produz rascunho de
  ETP e Termo de Referência com os elementos exigidos pela legislação.
- **Composição de pesquisa de preços** — consulta à API pública do Portal
  Nacional de Contratações Públicas, tratamento estatístico dos valores obtidos
  e geração do mapa de cotação.

## Recorte de pesquisa

O trabalho se concentra nas questões de dados que a aplicação levanta:

- persistência e busca por similaridade sobre a legislação e os modelos, para
  sustentar a geração das minutas;
- modelagem e indexação dos dados semiestruturados obtidos da API pública;
- trilha de auditoria que permita reproduzir uma pesquisa de preços exatamente
  como ela era na data em que foi realizada — requisito de quem presta contas a
  órgão de controle.

## Estrutura

```
docs/     documentação do projeto e normas de formatação
texto/    LaTeX — nota de projeto, projeto (TCC I) e monografia (TCC II)
code/     o sistema
scripts/  manifesto de normas e geradores
tests/    conformidade do texto com as normas da instituição
```

## Formatação verificada por teste

O texto segue o *Guia para a elaboração e apresentação da produção acadêmica da
Ufopa* (3. ed., 2025). As medidas normativas — margens, fonte, espaçamento,
recuo, extensão do resumo — são declaradas **uma única vez** em
`scripts/normas_ufopa.py`, de onde o preâmbulo LaTeX e a documentação são
gerados.

Um teste compila o PDF e verifica o que ele realmente entrega: tamanho da
página, fontes embutidas, margens, extensão do resumo, número de palavras-chave
e a caixa das citações no texto — que a norma vigente exige em caixa e baixa, e
não em caixa alta como nos modelos anteriores a 2023.

```bash
pytest                    # conformidade completa, compilando o PDF
pytest -m "not lento"     # só as guardas do manifesto
```

## Compilação

```bash
cd texto/tcc1 && make pdf     # ou make watch
```

Requer TeX Live com `biblatex`, `biblatex-abnt` e `biber`.

### Preparar a máquina

```bash
uv sync --all-groups          # ambiente Python e ferramentas de teste
```

Fora do Python, o texto depende de duas coisas: uma distribuição TeX e o
`poppler`, que fornece o `pdfinfo`, o `pdftotext` e o `pdffonts` usados pelos
testes para medir o PDF.

**Linux (Fedora):**

```bash
sudo dnf install texlive-scheme-medium texlive-biblatex-abnt biber poppler-utils
```

**macOS (Apple Silicon):** o MacTeX pesa cerca de 6 GB e o instalador pede
senha de administrador. O TinyTeX resolve o mesmo problema em uma fração disso
e deixa o `tlmgr` funcionando sem `sudo`:

```bash
curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"   # ponha no ~/.zshrc

tlmgr install biber biblatex biblatex-abnt babel-portuges psnfss cm-super \
  geometry titlesec fancyhdr setspace microtype booktabs float longtable \
  tabularx xcolor hyperref indentfirst csquotes xpatch l3packages rsfs \
  palatino mathpazo pgf

brew install poppler libthai
```

`palatino` e `mathpazo` servem ao alvo de layout do curso, que usa essa fonte.
`pgf` traz o TikZ, com que o modelo de processo é desenhado: a figura não é
imagem importada, é desenho feito pelo próprio compositor, e sem o pacote
nenhum dos três alvos compila.
Se o `tlmgr` recusar a instalação pedindo que ele próprio seja atualizado, rode
`tlmgr update --self` antes — a instalação mínima do TinyTeX envelhece, e a
mensagem aparece anos depois de instalado.

Três armadilhas específicas do macOS, todas encontradas na prática:

- **`libthai`** não é opcional. O `biber` do TeX Live para macOS é um binário
  empacotado que carrega `Unicode::LineBreak`, compilado contra a `libthai` do
  Homebrew. Sem ela o `biber` sequer inicia — falha com `Library not loaded:
  /opt/homebrew/opt/libthai/lib/libthai.0.dylib`, e a bibliografia some do PDF
  sem que o LaTeX reclame.
- **`cm-super`** também não. Sem ele, os trechos em itálico do encoding T1
  saem como fontes Type 3, isto é, bitmaps rasterizados em 600 dpi: o PDF
  compila, as fontes ficam embutidas e o texto serrilha na tela e na impressão.
  Há um teste que pega isso.
- **O Palatino do TeX vem em duas metades.** `palatino` traz as métricas do
  texto; `mathpazo`, as da matemática. O alvo do curso troca só a fonte de
  texto e não usa fórmula alguma, mas o LaTeX carrega o conjunto matemático de
  qualquer maneira ao fechar a página — e falha com `fplmr not loadable` se a
  segunda metade faltar. Instalar as duas.

## Contexto

O trabalho parte de um caso real: a rotina do setor de licitações da Prefeitura
de Prainha-PA, no oeste do Pará. Nenhum documento real de processo licitatório é
publicado neste repositório — os exemplos, testes e ilustrações usam versões
sintéticas, com a mesma estrutura e nenhum dado verdadeiro.

## Autoria

**Rafael Nobre de Souza** — Bacharelado em Ciência da Computação, UFOPA/IEG
**Orientadora:** Socorro Vânia Lourenço Alves

Santarém — Pará · 2026–2027
