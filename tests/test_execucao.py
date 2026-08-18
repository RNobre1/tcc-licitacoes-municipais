"""Execução de processo externo cuja saída não é necessariamente UTF-8.

Estes testes existem por causa de uma falha real: o fixture que compila o PDF
chamava `subprocess.run(..., text=True)` sem dizer o encoding, e o Python
decodificava a saída como UTF-8 estrito. Quando o TeX emite aviso de caixa em
uma linha acentuada, ele ecoa o texto no encoding **T1 da fonte** ---

    Underfull \\hbox (badness 1888) in paragraph at lines 35--35
    \\T1/ptm/m/n/12 (+20) como req-ui-sito para obten\\xe7\\xe3o do grau de

--- onde `ç` é o byte 0xE7 solto. A compilação terminava com sucesso e o teste
morria ao ler a saída dela.

A falha é intermitente por natureza: só ocorre quando aquele aviso aparece, o
que depende de o documento ser compilado do zero. Passou despercebida em duas
máquinas antes de estourar numa terceira.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests.execucao import executar


def _emitindo(literal_de_bytes: str) -> list[str]:
    """Comando que escreve bytes crus, sem passar por encoding do shell.

    A primeira versão destes testes usava `printf "\\xe7"`, e o `printf` do
    sistema devolveu o literal `xe7` em vez do byte — o teste passava contra o
    código quebrado e contra o consertado, que é o mesmo que não existir. Daí
    escrever direto no buffer binário.
    """
    return [sys.executable, "-c", f"import sys; sys.stdout.buffer.write({literal_de_bytes})"]


def test_saida_em_utf8_chega_intacta(tmp_path):
    resultado = executar(_emitindo("'acentuação'.encode()"), cwd=tmp_path)
    assert resultado.stdout == "acentuação"


def test_byte_solto_de_encoding_de_fonte_nao_derruba(tmp_path):
    """O caso real: 0xE7 e 0xE3 sem sequência UTF-8 válida em volta.

    É a linha que o TeX ecoa no aviso de caixa: `obten\\xe7\\xe3o`.
    """
    resultado = executar(_emitindo(r"b'obten\xe7\xe3o do grau'"), cwd=tmp_path)
    assert resultado.returncode == 0
    assert resultado.stdout.startswith("obten")
    assert resultado.stdout.endswith("o do grau")
    assert "�" in resultado.stdout, "o byte inválido devia virar U+FFFD, não sumir"


def test_codigo_de_erro_e_preservado(tmp_path):
    """Por padrão quem chama decide o que fazer com a falha."""
    resultado = executar(["sh", "-c", "exit 3"], cwd=tmp_path)
    assert resultado.returncode == 3


def test_exigir_sucesso_levanta_com_a_saida_de_erro(tmp_path):
    """Ferramenta de leitura que falha precisa estourar, e não devolver vazio.

    Sem isto, um `pdfinfo` quebrado devolveria stdout vazio e o teste de
    conformidade acusaria "página fora do A4" — diagnóstico errado para um
    problema de ambiente.
    """
    with pytest.raises(subprocess.CalledProcessError) as erro:
        executar(["sh", "-c", "echo 'quebrou' >&2; exit 1"], cwd=tmp_path, exigir_sucesso=True)
    assert "quebrou" in erro.value.stderr


def test_exigir_sucesso_deixa_passar_quando_da_certo(tmp_path):
    assert executar(_emitindo("b'ok'"), cwd=tmp_path, exigir_sucesso=True).stdout == "ok"


def test_binario_ausente_levanta(tmp_path):
    with pytest.raises(FileNotFoundError):
        executar(["nao-existe-este-binario-xyz"], cwd=tmp_path)
