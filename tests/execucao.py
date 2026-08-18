"""Chamada de processo externo para os testes de conformidade.

Existe por um motivo só: **nunca decodificar saída de ferramenta externa como
UTF-8 estrito.** O TeX ecoa trechos do documento no encoding da fonte (T1),
onde `ç` é o byte 0xE7 solto; o `pdffonts` e o `pdfinfo` repassam nomes de
fonte e metadados de PDFs de terceiros, que podem vir em qualquer coisa.

A saída aqui é diagnóstico: serve para dizer ao humano o que deu errado. Um
caractere trocado por U+FFFD numa mensagem de erro é irrelevante; uma exceção
de decodificação escondendo a mensagem inteira, não. Daí `errors="replace"`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def executar(
    args: list[str],
    cwd: Path | str | None = None,
    *,
    exigir_sucesso: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Roda o comando e devolve o resultado.

    Por padrão não levanta em código de saída diferente de zero: quem compila o
    documento quer inspecionar o log antes de decidir o que dizer.

    Com `exigir_sucesso=True`, levanta `CalledProcessError`. É o modo das
    ferramentas de leitura do PDF — `pdfinfo` que falha e devolve stdout vazio
    faria o teste acusar violação de norma quando o problema é de ambiente.

    Levanta `FileNotFoundError` se o binário não existir, nos dois modos: isso é
    erro de ambiente, não resultado do processo, e quem chama precisa saber.
    """
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=exigir_sucesso,
    )
