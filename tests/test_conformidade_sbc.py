"""Conformidade do alvo SBC com o ``.sty`` canônico da Sociedade Brasileira de
Computação e com o limite de páginas fixado pela orientação.

O padrão SBC é o formato do texto principal do trabalho, decidido em 24/08/2026
(``TCC/decisões/2026-08-24-formato-do-texto-artigo-do-curso.md``). O alvo do guia
do SIBI continua existindo, medido por ``test_conformidade_pdf.py``, porque a
biblioteca exige o formato tradicional no depósito.

As medidas esperadas **não** estão escritas aqui: são lidas de
``texto/comum/sbc/sbc-template.sty`` por ``tests/leitura_sbc.py``. Trocar o
``.sty`` por uma revisão da SBC muda o que estes testes exigem, sem editar
Python — que é o ponto.

São lentos (compilam o documento). Rode só eles com:

    pytest -m lento

E o resto com:

    pytest -m "not lento"
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests import leitura_pdf, leitura_sbc
from tests.execucao import executar
from tests.leitura_pdffonts import fontes_bitmap, fontes_nao_embutidas

RAIZ = Path(__file__).resolve().parent.parent
FONTE_SBC = "main-sbc.tex"
DOCUMENTOS = ["tcc1", "tcc2"]

# TCC I organiza o texto em `secoes/`, TCC II em `capitulos/`. A expressão aceita
# os dois para que a guarda de conteúdo único valha nos dois documentos.
ENTRADAS_DE_TEXTO = re.compile(r"\\input\{((?:secoes|capitulos)/[^}]+)\}")

# Limite de páginas fixado pela orientação na reunião de 19/08/2026, com o
# precedente declarado por ela: banca do semestre anterior cobrou um trabalho de
# mais de 60 páginas porque artigo com esse tamanho não existe. O piso de 20 não
# é testado — documento em estágio de projeto tem menos, por construção, e um
# teste que exigisse o piso agora falharia por motivo legítimo.
#
# Mora aqui, e não em `scripts/normas_ufopa.py`, porque aquele módulo declara a
# sua procedência como o guia do SIBI e esta exigência não vem dele. Se um
# terceiro lugar do repositório passar a precisar deste número, aí ele vira
# manifesto — hoje o único consumidor é este teste.
PAGINAS_MAX = 25

# Ver a justificativa da mesma folga em `test_conformidade_pdf.py`: o microtype
# projeta pontuação para fora da mancha de propósito, e isso é tipografia
# correta. O que estes testes precisam pegar é invasão estrutural.
FOLGA_PROTRUSAO_PT = 3.0

pytestmark = pytest.mark.lento


@pytest.fixture(scope="session", params=DOCUMENTOS)
def pdf_sbc(request) -> Path:
    """Compila o alvo SBC do documento e devolve o caminho do PDF."""
    return leitura_pdf.compilar(RAIZ / "texto" / request.param, FONTE_SBC)


# --- Procedência do .sty ------------------------------------------------------


def test_sty_da_sbc_esta_presente_e_intacto():
    """O ``.sty`` canônico é insumo externo: some ou é editado sem ninguém ver.

    Não roda o TeX — é a guarda mais barata da suíte e a única que continua
    valendo se o LaTeX não estiver instalado.
    """
    assert leitura_sbc.STY_SBC.is_file(), f"{leitura_sbc.STY_SBC} ausente"
    assert leitura_sbc.papel() == "a4paper"
    assert leitura_sbc.corpo_e_entrelinha_pt() == (12, 14)
    margens = leitura_sbc.margens_cm()
    assert set(margens) >= {"top", "bottom", "left", "right"}


# --- Página -------------------------------------------------------------------


def test_pagina_e_a4(pdf_sbc: Path):
    """O ``.sty`` pede ``a4paper``; este teste prova que o PDF entregou A4."""
    assert leitura_sbc.papel() == "a4paper", "o .sty da SBC deixou de pedir A4"
    tamanho = leitura_pdf.info(pdf_sbc)["Page size"]
    largura, altura = (float(n) for n in re.findall(r"[\d.]+", tamanho)[:2])
    assert largura == pytest.approx(595.28, abs=1.0), f"largura fora do A4: {tamanho}"
    assert altura == pytest.approx(841.89, abs=1.0), f"altura fora do A4: {tamanho}"


def test_nao_passa_do_limite_de_paginas(pdf_sbc: Path):
    """Limite de entrega, não de estilo: orçamento de página é restrição real.

    Mede a versão **apresentável**, em ``entregas/``, e não a de trabalho: o
    limite vale para o que chega às mãos de quem avalia, e os marcadores de
    pendência são bilhete interno que não estará lá.

    A ressalva, e ela importa: marcador vira prosa, e prosa ocupa mais espaço
    que o marcador que a anunciava. Estar dentro do limite hoje não garante
    estar depois de escrever o que falta — por isso a folga é reportada na
    mensagem, e não só o veredito.
    """
    entrega = RAIZ / "entregas" / "tcc1-formato-sbc.pdf"
    alvo = entrega if entrega.is_file() else pdf_sbc
    total = leitura_pdf.paginas(alvo)
    folga = PAGINAS_MAX - total
    assert total <= PAGINAS_MAX, (
        f"documento com {total} páginas; a orientação fixou o máximo em "
        f"{PAGINAS_MAX}. Cortar conteúdo, não aumentar o limite."
    )
    if folga <= 1:
        print(
            f"\n  atenção: {total} de {PAGINAS_MAX} páginas, folga de {folga}. "
            "Escrever as pendências restantes deve estourar o limite."
        )


# --- Tipografia ---------------------------------------------------------------


def test_fonte_do_corpo_e_times(pdf_sbc: Path):
    """O ``.sty`` da SBC carrega ``times``; o PDF tem de mostrar isso."""
    leitura_pdf.exige("pdffonts")
    fontes = executar(["pdffonts", str(pdf_sbc)], exigir_sucesso=True).stdout
    assert re.search(r"Times|NimbusRom", fontes, re.IGNORECASE), (
        f"nenhuma fonte Times/Nimbus Roman embutida:\n{fontes}"
    )


def test_todas_as_fontes_estao_embutidas(pdf_sbc: Path):
    """PDF de submissão com fonte não embutida troca de tipografia no revisor."""
    leitura_pdf.exige("pdffonts")
    saida = executar(["pdffonts", str(pdf_sbc)], exigir_sucesso=True).stdout
    nao_embutidas = fontes_nao_embutidas(saida)
    assert nao_embutidas == [], f"fontes não embutidas: {nao_embutidas}\n{saida}"


def test_nenhuma_fonte_e_bitmap(pdf_sbc: Path):
    """Type 3 é fonte rasterizada: serrilha na tela e na impressão.

    Mesma armadilha do alvo do SIBI, registrada na sessão de 18/08: sem
    ``cm-super``, o itálico do encoding T1 sai como bitmap PK. O PDF continua
    válido e as fontes continuam embutidas, então o teste acima não pega.
    """
    leitura_pdf.exige("pdffonts")
    saida = executar(["pdffonts", str(pdf_sbc)], exigir_sucesso=True).stdout
    bitmap = fontes_bitmap(saida)
    assert bitmap == [], f"fontes rasterizadas: {bitmap} — falta cm-super?\n{saida}"


# --- Margens ------------------------------------------------------------------


def _caixas_do_corpo(pdf: Path) -> list[tuple[float, float, float, float]]:
    """Caixas de palavra de todas as páginas do corpo, fora da bibliografia.

    Aqui esteve uma dispensa para páginas giradas, de quando a figura do
    processo ficava em paisagem. Ela saiu junto com a página girada: enquanto
    existiu, media-se a margem de uma parte do documento e supunha-se a da
    outra. Com o documento inteiro em retrato, toda página do corpo é medida —
    e `tests/test_processo_cabe_na_mancha.py` é o que garante que continue
    assim.
    """
    caixas: list[tuple[float, float, float, float]] = []
    for pagina in leitura_pdf.paginas_antes_das_referencias(pdf):
        caixas.extend(leitura_pdf.caixas_de_palavra(pdf, pagina))
    return caixas


def test_margem_esquerda_segue_o_sty_da_sbc(pdf_sbc: Path):
    """Nenhuma palavra do corpo invade a margem esquerda declarada no ``.sty``.

    A lista de referências fica de fora, e não por conveniência: o
    ``sbc-template.sty`` redefine ``thebibliography`` com ``\\itemindent
    -\\leftmargin``, que pendura o rótulo à esquerda da mancha de propósito.
    Medir a bibliografia aqui reprovaria o formato oficial da SBC pelo próprio
    estilo dele — ver ``test_rotulo_da_bibliografia_fica_pendurado``.
    """
    esperado = leitura_sbc.em_pontos(leitura_sbc.margens_cm()["left"])
    caixas = _caixas_do_corpo(pdf_sbc)
    if not caixas:
        pytest.skip("corpo sem texto extraível")
    menor_x = min(x0 for x0, _, _, _ in caixas)
    assert menor_x >= esperado - FOLGA_PROTRUSAO_PT, (
        f"texto invade a margem esquerda: {menor_x:.1f}pt < {esperado:.1f}pt"
    )


def test_margem_direita_segue_o_sty_da_sbc(pdf_sbc: Path):
    esperado = leitura_sbc.em_pontos(leitura_sbc.margens_cm()["right"])
    limite = leitura_pdf.largura_pt(pdf_sbc) - esperado
    caixas = _caixas_do_corpo(pdf_sbc)
    if not caixas:
        pytest.skip("corpo sem texto extraível")
    maior_x = max(x1 for _, _, x1, _ in caixas)
    assert maior_x <= limite + FOLGA_PROTRUSAO_PT, (
        f"texto invade a margem direita: {maior_x:.1f}pt > {limite:.1f}pt"
    )


def test_rotulo_da_bibliografia_fica_pendurado(pdf_sbc: Path):
    """O rótulo sai da margem à esquerda, e é isso que o formato SBC quer.

    Guarda em duas direções, e é por isso que o teste existe em vez de a
    bibliografia ser simplesmente ignorada:

    - se o rótulo **não** estiver pendurado, o ``.sty`` foi trocado por um que
      não é o da SBC, ou algum pacote sobrescreveu ``thebibliography``;
    - se estiver pendurado além de uma linha de recuo, alguma referência tem
      rótulo longo demais e vai sangrar para fora do papel.
    """
    margem = leitura_sbc.em_pontos(leitura_sbc.margens_cm()["left"])
    total = leitura_pdf.paginas(pdf_sbc)
    corpo = set(leitura_pdf.paginas_antes_das_referencias(pdf_sbc))
    paginas_bib = [n for n in range(1, total + 1) if n not in corpo]
    caixas: list[tuple[float, float, float, float]] = []
    for pagina in paginas_bib:
        caixas.extend(leitura_pdf.caixas_de_palavra(pdf_sbc, pagina))
    if not caixas:
        pytest.skip("documento ainda não tem lista de referências")
    menor_x = min(x0 for x0, _, _, _ in caixas)
    assert menor_x < margem, (
        f"rótulo da bibliografia não está pendurado ({menor_x:.1f}pt >= "
        f"{margem:.1f}pt): o thebibliography do sbc-template foi sobrescrito?"
    )
    assert menor_x > 0, f"bibliografia sangra para fora do papel: {menor_x:.1f}pt"


# --- Conteúdo compartilhado ---------------------------------------------------


def test_usa_as_mesmas_secoes_do_alvo_do_sibi():
    """Prova que o conteúdo é único, e não uma segunda cópia da prosa.

    É a guarda da regra de fonte única aplicada ao texto: dois alvos de layout
    são legítimos, duas cópias das seções não. Um `\\input` de arquivo próprio
    passaria pelos testes de geometria sem que ninguém notasse a bifurcação.
    """
    for documento in DOCUMENTOS:
        projeto = RAIZ / "texto" / documento
        alvo_sbc = (projeto / FONTE_SBC).read_text(encoding="utf-8")
        alvo_sibi = (projeto / "main.tex").read_text(encoding="utf-8")
        secoes_sbc = ENTRADAS_DE_TEXTO.findall(alvo_sbc)
        secoes_sibi = ENTRADAS_DE_TEXTO.findall(alvo_sibi)
        assert secoes_sbc, f"{documento}/{FONTE_SBC} não inclui nenhuma seção"
        assert secoes_sbc == secoes_sibi, (
            f"{documento}: os dois alvos divergem nas seções incluídas.\n"
            f"  SBC : {secoes_sbc}\n  SIBI: {secoes_sibi}"
        )
