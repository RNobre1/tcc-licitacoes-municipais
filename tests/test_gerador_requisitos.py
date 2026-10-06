"""Testes do gerador de entregáveis da especificação de requisitos.

`docs/requisitos/README.md` é a fonte única. O `.docx` que vai para a orientação
e o `.pdf` são **derivados** — regenerados por `scripts/gerar_requisitos.py`,
nunca editados à mão.

Vale aqui a mesma regra do manifesto de normas: documento gerado sem teste é
pior que documento escrito à mão, porque envelhece igual e carrega um selo de
procedência que faz quem lê confiar mais.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts import gerar_requisitos as gr

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "docs" / "requisitos" / "README.md"


AMOSTRA = """# Título

Parágrafo com **negrito** e `código`.

## Seção

- item um
- item dois

| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |

> Uma citação recuada.

```mermaid
flowchart LR
    A --> B
```

Fim.
"""


# --- Leitura do markdown -----------------------------------------------------


def test_reconhece_os_tipos_de_bloco_que_o_documento_usa():
    tipos = [b.tipo for b in gr.blocos(AMOSTRA)]
    assert tipos == [
        "titulo",
        "paragrafo",
        "titulo",
        "lista",
        "tabela",
        "citacao",
        "diagrama",
        "paragrafo",
    ]


def test_titulo_guarda_o_nivel():
    bs = gr.blocos(AMOSTRA)
    assert (bs[0].nivel, bs[0].texto) == (1, "Título")
    assert (bs[2].nivel, bs[2].texto) == (2, "Seção")


def test_tabela_separa_cabecalho_das_linhas_e_descarta_o_tracejado():
    tabela = next(b for b in gr.blocos(AMOSTRA) if b.tipo == "tabela")
    assert tabela.cabecalho == ["A", "B"]
    assert tabela.linhas == [["1", "2"], ["3", "4"]]


def test_marcacao_inline_vira_trechos_com_estilo():
    p = gr.blocos(AMOSTRA)[1]
    assert gr.trechos(p.texto) == [
        ("Parágrafo com ", set()),
        ("negrito", {"negrito"}),
        (" e ", set()),
        ("código", {"mono"}),
        (".", set()),
    ]


def test_diagrama_nao_vira_texto_solto():
    """Mermaid não é renderizável aqui; tem de virar aviso, não código cru."""
    d = next(b for b in gr.blocos(AMOSTRA) if b.tipo == "diagrama")
    assert "flowchart" not in d.texto
    assert "não reproduzido" in d.texto.lower()


# --- O documento tem de se sustentar sozinho ---------------------------------

# Ele é apresentado a quem não tem acesso ao repositório, com a tela
# compartilhada e nada mais aberto. Referência a caminho de arquivo do projeto
# vira, ali, uma frase que ninguém consegue seguir.
_RASTROS_DO_REPOSITORIO = (
    r"docs/",
    r"scripts/",
    r"tests/",
    r"texto/",
    r"dados-dominio",
    r"TCC/",
    r"\.md\b",
    r"\.py\b",
    r"\.sty\b",
    r"README",
    r"pytest",
    r"git\b",
)


def _rastros(texto: str) -> list[str]:
    import re

    return sorted({p for p in _RASTROS_DO_REPOSITORIO if re.search(p, texto)})


def test_a_guarda_de_autocontencao_reconhece_o_que_procura():
    """Contraprova: a guarda acusa mesmo, não passa tudo."""
    assert _rastros("ver docs/requisitos/README.md") != []
    assert _rastros("O sistema deve exportar em formato editável.") == []


def test_o_documento_nao_aponta_para_arquivo_do_projeto():
    achados = _rastros(FONTE.read_text(encoding="utf-8"))
    assert achados == [], (
        f"o documento cita caminho ou artefato do repositório: {achados}. "
        "Ele é apresentado sozinho, sem o repositório aberto."
    )


def test_nem_o_docx_nem_o_tex_reintroduzem_rastro(tmp_path):
    bs = gr.blocos(FONTE.read_text(encoding="utf-8"))
    assert _rastros(gr.escrever_tex(bs)) == []
    destino = tmp_path / "r.docx"
    gr.escrever_docx(bs, destino)
    with zipfile.ZipFile(destino) as z:
        assert _rastros(z.read("word/document.xml").decode("utf-8")) == []


# --- Saída .docx -------------------------------------------------------------


def test_docx_e_um_pacote_ooxml_valido(tmp_path):
    destino = tmp_path / "s.docx"
    gr.escrever_docx(gr.blocos(AMOSTRA), destino)
    with zipfile.ZipFile(destino) as z:
        assert z.testzip() is None
        nomes = set(z.namelist())
        assert {"[Content_Types].xml", "word/document.xml", "word/styles.xml"} <= nomes


def test_docx_preserva_as_celulas_da_tabela(tmp_path):
    destino = tmp_path / "s.docx"
    gr.escrever_docx(gr.blocos(AMOSTRA), destino)
    with zipfile.ZipFile(destino) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    assert xml.count("<w:tbl>") == 1
    assert xml.count("<w:tr>") == 3  # cabeçalho + duas linhas
    for celula in ("A", "B", "1", "2", "3", "4"):
        assert f"<w:t>{celula}</w:t>" in xml or f'<w:t xml:space="preserve">{celula}</w:t>' in xml


def test_docx_escapa_caractere_que_quebraria_o_xml(tmp_path):
    destino = tmp_path / "s.docx"
    gr.escrever_docx(gr.blocos("Comparação de A & B <teste>.\n"), destino)
    with zipfile.ZipFile(destino) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    assert "A &amp; B &lt;teste&gt;" in xml


def test_docx_usa_a_geometria_do_guia_da_ufopa(tmp_path):
    """Mesmas margens do resto do trabalho: 3 cm em cima e à esquerda, 2 nos outros."""
    destino = tmp_path / "s.docx"
    gr.escrever_docx(gr.blocos(AMOSTRA), destino)
    with zipfile.ZipFile(destino) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    assert 'w:top="1701"' in xml and 'w:left="1701"' in xml
    assert 'w:right="1134"' in xml and 'w:bottom="1134"' in xml


# --- Saída .tex --------------------------------------------------------------


def test_tex_escapa_os_caracteres_reservados():
    tex = gr.escrever_tex(gr.blocos("Custo de 50% & mais_um #teste.\n"))
    assert r"50\%" in tex
    assert r"\&" in tex
    assert r"mais\_um" in tex
    assert r"\#teste" in tex


def test_tex_emite_tabela_com_o_numero_certo_de_colunas():
    tex = gr.escrever_tex(gr.blocos(AMOSTRA))
    assert r"\begin{longtable}" in tex
    # o cabeçalho sai em negrito, então o separador não fica colado no texto
    assert r"\textbf{A} & \textbf{B}" in tex
    assert r"1 & 2" in tex and r"3 & 4" in tex
    assert tex.count(r"p{0.460\textwidth}") == 2  # duas colunas de largura igual


def test_tex_nao_deixa_marcacao_de_markdown_vazar():
    tex = gr.escrever_tex(gr.blocos(AMOSTRA))
    assert "**" not in tex
    assert "|---" not in tex


def test_simbolo_fora_do_latin1_vira_comando_de_tex():
    tex = gr.escrever_tex(gr.blocos("Compara ETP↔TR — com ≥ 3 preços.\n"))
    assert r"$\leftrightarrow$" in tex
    assert "---" in tex
    assert r"$\geq$" in tex


def test_a_guarda_acusa_simbolo_que_ninguem_mapeou():
    """Guarda de varredura: é regra, não lista. Símbolo novo é acusado, não ignorado."""
    assert gr.nao_mapeados(gr.escrever_tex(gr.blocos("puro ascii\n"))) == set()
    assert gr.nao_mapeados("um ⚡ perdido") == {"⚡"}


def test_o_documento_real_nao_tem_simbolo_que_o_pdflatex_nao_componha():
    tex = gr.escrever_tex(gr.blocos(FONTE.read_text(encoding="utf-8")))
    sobraram = gr.nao_mapeados(tex)
    assert sobraram == set(), (
        f"símbolos sem tradução para LaTeX: {sorted(sobraram)}. "
        "Acrescente em scripts/gerar_requisitos.py::_SIMBOLOS."
    )


# --- O documento real --------------------------------------------------------


def test_a_fonte_existe():
    assert FONTE.is_file(), "docs/requisitos/README.md é a fonte única dos entregáveis"


def test_o_documento_real_atravessa_o_gerador_inteiro(tmp_path):
    bs = gr.blocos(FONTE.read_text(encoding="utf-8"))
    assert len(bs) > 50, "o documento real tem muitos blocos; algo se perdeu na leitura"
    assert any(b.tipo == "tabela" for b in bs)
    destino = tmp_path / "requisitos.docx"
    gr.escrever_docx(bs, destino)
    assert destino.stat().st_size > 10_000
    tex = gr.escrever_tex(bs)
    assert r"\begin{document}" in tex and r"\end{document}" in tex


def test_toda_tabela_do_documento_real_tem_linhas_do_tamanho_do_cabecalho():
    """Tabela desalinhada vira célula perdida no .docx sem erro nenhum."""
    ruins = []
    for i, b in enumerate(gr.blocos(FONTE.read_text(encoding="utf-8"))):
        if b.tipo != "tabela":
            continue
        for linha in b.linhas:
            if len(linha) != len(b.cabecalho):
                ruins.append((i, b.cabecalho, linha))
    assert ruins == [], f"tabelas desalinhadas: {ruins[:3]}"


@pytest.mark.lento
def test_o_pdf_compila_e_tem_o_titulo(tmp_path):
    pdf = gr.compilar_pdf(gr.blocos(FONTE.read_text(encoding="utf-8")), tmp_path)
    assert pdf.is_file() and pdf.stat().st_size > 10_000


# --- Linha de comando --------------------------------------------------------

# O gerador nasceu preso a um documento só. Passou a servir a qualquer markdown
# quando foi preciso emitir o roteiro de validação: duplicar o script para um
# segundo documento criaria dois lugares para consertar o mesmo defeito.


def test_gera_qualquer_markdown_informado(tmp_path):
    fonte = tmp_path / "exemplo.md"
    fonte.write_text(AMOSTRA, encoding="utf-8")
    saida = tmp_path / "saida"
    assert gr.main(["--fonte", str(fonte), "--saida", str(saida), "--sem-pdf"]) == 0
    assert (saida / "exemplo.docx").is_file()


def test_sem_argumento_usa_a_especificacao_de_requisitos(tmp_path):
    saida = tmp_path / "s"
    assert gr.main(["--saida", str(saida), "--sem-pdf"]) == 0
    assert (saida / "requisitos.docx").is_file()


def test_erra_alto_quando_a_fonte_nao_existe(tmp_path):
    assert gr.main(["--fonte", str(tmp_path / "nao_existe.md"), "--sem-pdf"]) == 1
