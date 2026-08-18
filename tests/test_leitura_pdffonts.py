"""Leitura da tabela do `pdffonts`.

Estes testes existem porque a primeira versão da leitura procurava a substring
`" no "` na linha inteira. A tabela tem três colunas de sim/não lado a lado
(`emb sub uni`), então uma fonte embutida mas **subconjunta** — `yes no no` —
era acusada de não estar embutida. O falso positivo só apareceu ao trocar de
máquina, quando surgiram fontes Type 3 no PDF.

São testes rápidos, sobre texto fixo: não compilam nada.
"""

from __future__ import annotations

from tests.leitura_pdffonts import fontes_bitmap, fontes_nao_embutidas

CABECALHO = (
    "name                                 type              encoding"
    "         emb sub uni object ID\n"
    "------------------------------------ ----------------- ----------------"
    " --- --- --- ---------\n"
)


def _tabela(*linhas: str) -> str:
    return CABECALHO + "".join(linha + "\n" for linha in linhas)


def _linha(nome: str, tipo: str, emb: str, sub: str, uni: str, obj: int) -> str:
    """Monta uma linha com o mesmo alinhamento de colunas que o `pdffonts` usa."""
    return f"{nome:<37}{tipo:<18}{'Custom':<17}{emb:<4}{sub:<4}{uni:<4}{obj:>7}  0"


# Saída real desta máquina antes do `cm-super`: embutida, subconjunta, Type 3.
TYPE3_EMBUTIDA = _linha("F113", "Type 3", "yes", "no", "no", 143)
TYPE1_EMBUTIDA = _linha("OMHTEV+NimbusRomNo9L-Regu", "Type 1", "yes", "yes", "yes", 96)
NAO_EMBUTIDA = _linha("Helvetica", "Type 1", "no", "no", "no", 12)


def test_fonte_embutida_mas_subconjunta_nao_e_acusada():
    """O caso que quebrou: `sub=no` não significa `emb=no`."""
    assert fontes_nao_embutidas(_tabela(TYPE3_EMBUTIDA)) == []


def test_fonte_nao_embutida_e_encontrada():
    assert fontes_nao_embutidas(_tabela(NAO_EMBUTIDA)) == ["Helvetica"]


def test_distingue_as_duas_na_mesma_tabela():
    tabela = _tabela(TYPE1_EMBUTIDA, TYPE3_EMBUTIDA, NAO_EMBUTIDA)
    assert fontes_nao_embutidas(tabela) == ["Helvetica"]


def test_tabela_vazia_nao_quebra():
    assert fontes_nao_embutidas(CABECALHO) == []
    assert fontes_bitmap(CABECALHO) == []


def test_bitmap_encontra_type_3():
    tabela = _tabela(TYPE1_EMBUTIDA, TYPE3_EMBUTIDA)
    assert fontes_bitmap(tabela) == ["F113"]


def test_bitmap_ignora_type_1():
    assert fontes_bitmap(_tabela(TYPE1_EMBUTIDA, NAO_EMBUTIDA)) == []
