"""Leitura da tabela que o `pdffonts` imprime.

A tabela tem largura de coluna variável no início (nome, tipo e encoding) e
largura fixa no fim:

    name            type       encoding   emb sub uni object ID
    --------------- ---------- ---------- --- --- --- ---------
    ABCDEF+Nimbus   Type 1     Custom     yes yes yes      96  0

Por isso as colunas são lidas **a partir do fim**: os dois últimos campos são o
número e a geração do objeto, e antes deles vêm `uni`, `sub` e `emb`, nessa
ordem. Ler por substring erra — `emb`, `sub` e `uni` têm os mesmos dois valores
possíveis e ficam lado a lado.
"""

from __future__ import annotations

# Contando de trás para frente na linha: [-1] geração, [-2] número do objeto,
# [-3] uni, [-4] sub, [-5] emb.
_COLUNA_EMB = -5
_CAMPOS_MINIMOS = 7  # nome, tipo (2 palavras), encoding, emb, sub, uni, obj, ger


def linhas_de_fonte(saida: str) -> list[str]:
    """Descarta o cabeçalho, o separador de traços e as linhas em branco."""
    return [
        linha
        for linha in saida.splitlines()
        if linha.strip()
        and not linha.lstrip().startswith("-")
        and not linha.lstrip().startswith("name")
        and len(linha.split()) >= _CAMPOS_MINIMOS
    ]


def _nome(linha: str) -> str:
    return linha.split()[0]


def fontes_nao_embutidas(saida: str) -> list[str]:
    """Fontes que o PDF referencia sem carregar — trocam de tipografia no leitor."""
    return [_nome(linha) for linha in linhas_de_fonte(saida) if linha.split()[_COLUNA_EMB] == "no"]


def fontes_bitmap(saida: str) -> list[str]:
    """Fontes Type 3, isto é, rasterizadas: serrilham na tela e na impressão."""
    return [_nome(linha) for linha in linhas_de_fonte(saida) if "Type 3" in linha]


__all__ = ["fontes_bitmap", "fontes_nao_embutidas", "linhas_de_fonte"]
