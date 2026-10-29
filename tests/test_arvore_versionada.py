"""Guardas sobre o que entra no versionamento.

O repositório é vitrine acadêmica e público por destino, e duas classes de
arquivo não podem entrar nele: produto de compilação e o que a política de dados
mantém fora. Nenhuma das duas dispara erro de compilação — o sintoma aparece
depois do `push`, quando já não volta atrás.

Estes testes são rápidos e não dependem de LaTeX, então rodam em
``pytest -m "not lento"`` junto com o resto.

Duas razões de existirem, e as duas são erros já cometidos neste projeto:

1. O alvo SBC criou um PDF cujo nome não casava com a regra do ``.gitignore``
   daquele momento, e o arquivo entraria no repositório em silêncio. A regra foi
   trocada por uma baseada em posição.
2. A primeira versão **deste arquivo** enumerava, em código versionado, os
   caminhos que a política mantém fora — e assim publicava exatamente a lista que
   a regra existe para não publicar. É o mesmo erro registrado no log de 18/08,
   cometido de novo no arquivo escrito para impedi-lo.

O conserto do segundo é o que define o desenho daqui: a lista de exclusões vive
em ``.git/info/exclude``, que **não** é versionado, e este arquivo a **lê** em vez
de repetir. Assim a guarda é regra e não lista — cobre o caminho que a política
acrescentar amanhã, sem que nada precise ser escrito aqui.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

import pytest

from tests.execucao import executar

RAIZ = Path(__file__).resolve().parent.parent
EXCLUSOES_LOCAIS = RAIZ / ".git" / "info" / "exclude"


def _rastreados() -> list[str]:
    """Caminhos que o git tem no índice, um por linha."""
    resultado = executar(["git", "ls-files"], cwd=RAIZ, exigir_sucesso=True)
    return [linha for linha in resultado.stdout.splitlines() if linha]


def _ignorado(caminho: Path) -> bool:
    """Se o git ignoraria este caminho. Vale para arquivo que ainda não existe."""
    relativo = caminho.relative_to(RAIZ).as_posix()
    resultado = executar(["git", "check-ignore", "-q", relativo], cwd=RAIZ)
    return resultado.returncode == 0


def _padroes_de_exclusao_local() -> list[str]:
    """Padrões declarados em ``.git/info/exclude``, sem comentário nem vazio.

    Lê do arquivo de propósito: ele não é versionado, e é isso que permite a esta
    suíte conferir a política sem publicá-la.
    """
    if not EXCLUSOES_LOCAIS.is_file():
        return []
    linhas = EXCLUSOES_LOCAIS.read_text(encoding="utf-8").splitlines()
    return [
        linha.strip() for linha in linhas if linha.strip() and not linha.lstrip().startswith("#")
    ]


def _casa(caminho: str, padrao: str) -> bool:
    """Se ``caminho`` é coberto por ``padrao`` no sentido do gitignore.

    Cobre as formas que a política usa: diretório com barra final (prefixo
    recursivo) e caminho ou nome de arquivo, com ou sem curinga. Não pretende
    implementar a gramática completa do gitignore — pretende não deixar passar o
    que está escrito no arquivo de exclusões deste projeto.
    """
    padrao = padrao.removeprefix("/")
    if padrao.endswith("/"):
        return caminho.startswith(padrao) or f"/{padrao}" in f"/{caminho}"
    return (
        caminho == padrao
        or fnmatch.fnmatch(caminho, padrao)
        or fnmatch.fnmatch(caminho, f"{padrao}/*")
        or fnmatch.fnmatch(Path(caminho).name, padrao)
    )


# --- Produto de compilação ----------------------------------------------------


def test_nenhum_pdf_de_saida_esta_versionado():
    """PDF na raiz de um documento é produto de compilação, nunca fonte."""
    culpados = [
        caminho
        for caminho in _rastreados()
        if caminho.startswith("texto/") and caminho.endswith(".pdf") and caminho.count("/") == 2
    ]
    assert culpados == [], (
        f"PDF de saída no índice do git: {culpados}. "
        "Remover com `git rm --cached` e conferir a regra no .gitignore."
    )


@pytest.mark.parametrize(
    "documento", ["tcc1", "tcc2", "nota-inicial", "documento-que-ainda-nao-existe"]
)
@pytest.mark.parametrize("alvo", ["main.pdf", "main-sbc.pdf", "main-qualquer-alvo.pdf"])
def test_pdf_de_qualquer_alvo_futuro_ja_esta_ignorado(documento: str, alvo: str):
    """A regra vale para o alvo que nascer amanhã, não só para os de hoje.

    Inclui de propósito um documento e um alvo que não existem: é isso que
    diferencia uma regra de uma lista. Se este teste passar a falhar, alguém
    trocou a regra de posição por uma que enumera nomes.
    """
    assert _ignorado(RAIZ / "texto" / documento / alvo), (
        f"texto/{documento}/{alvo} NÃO está ignorado — a regra do .gitignore "
        "voltou a enumerar nomes em vez de cobrir a posição."
    )


def test_insumo_em_subpasta_de_documento_nao_e_ignorado():
    """Contraprova da regra acima: ela não pode engolir insumo.

    A ficha catalográfica é fornecida pela biblioteca e precisa ser versionada.
    Uma regra ampla demais — ``texto/**/*.pdf`` — a excluiria junto com as saídas,
    e o defeito só apareceria no dia da entrega.
    """
    insumo = RAIZ / "texto" / "tcc2" / "figuras" / "ficha-catalografica.pdf"
    assert not _ignorado(insumo), (
        f"{insumo.relative_to(RAIZ)} está sendo ignorado. A regra do .gitignore "
        "ficou ampla demais e passou a excluir insumo, não só produto."
    )


# --- Entregável gerado sob docs/ ----------------------------------------------


@pytest.mark.parametrize("pasta", ["requisitos", "arquitetura", "pasta-que-ainda-nao-existe"])
@pytest.mark.parametrize("gerado", ["requisitos.docx", "arquitetura.pdf", "outro-nome.docx"])
def test_entregavel_gerado_sob_docs_ja_esta_ignorado(pasta: str, gerado: str):
    """``gerar_requisitos.py`` emite ``.docx`` e ``.pdf`` ao lado do markdown fonte.

    São binários que mudam de bytes a cada geração mesmo sem mudança de conteúdo,
    e por isso ficam fora do versionamento. A regra tem de valer para a pasta que
    nascer amanhã: a primeira versão dela nomeava ``docs/requisitos/``, e quando
    ``docs/arquitetura/`` nasceu em 22/09/2026 os dois binários dela passaram a
    entrar no índice em silêncio — o mesmo erro que o comentário daquela regra
    dizia estar evitando.

    O desenho que corrige isso inverte o padrão: sob ``docs/``, binário de
    escritório é ignorado por omissão, e insumo é liberado por exceção explícita.
    Errar para esse lado é barato — o arquivo novo nasce fora e alguém precisa
    decidir incluí-lo. Errar para o outro publica sem ninguém perceber.
    """
    assert _ignorado(RAIZ / "docs" / pasta / gerado), (
        f"docs/{pasta}/{gerado} NÃO está ignorado — a regra do .gitignore voltou "
        "a enumerar pastas em vez de cobrir a posição."
    )


def test_markdown_fonte_sob_docs_continua_versionado():
    """Contraprova: a regra cobre o gerado, não a fonte que o gera."""
    fonte = RAIZ / "docs" / "requisitos" / "README.md"
    assert not _ignorado(fonte), (
        f"{fonte.relative_to(RAIZ)} está sendo ignorado. A regra passou a excluir "
        "a fonte única junto com o que ela gera."
    )


def test_insumo_normativo_sob_docs_continua_versionado():
    """Segunda contraprova: nem todo PDF sob ``docs/`` é saída.

    O guia do SIBI é insumo baixado do portal da instituição e precisa viajar com
    o repositório, porque o manifesto de normas é derivado dele. Uma regra que
    varresse ``docs/**/*.pdf`` sem exceção o levaria junto.
    """
    insumo = RAIZ / "docs" / "normas" / "guia-ufopa-producao-academica-3ed-2025.pdf"
    assert not _ignorado(insumo), (
        f"{insumo.relative_to(RAIZ)} está sendo ignorado. A regra ficou ampla "
        "demais e passou a excluir insumo normativo, não só produto gerado."
    )


# --- Política de exclusão local -----------------------------------------------


def test_o_arquivo_de_exclusoes_locais_existe():
    """Clone novo não herda ``.git/info/exclude``, e nada avisa.

    É a consequência de manter a política ali em vez de no ``.gitignore``: a lista
    não é publicada, mas também não viaja. Ao clonar em outra máquina, o arquivo
    tem de ser recriado antes do primeiro commit — ou a política simplesmente não
    está em vigor.

    Na integração contínua o clone é sempre novo, e a lista não pode chegar até
    ela sem ser publicada. Lá o aviso não tem a quem servir, e a política é
    conferida na máquina de quem faz o ``push``.
    """
    if os.environ.get("CI"):
        pytest.skip("clone da CI não carrega as exclusões locais; a guarda vale na máquina local")
    assert EXCLUSOES_LOCAIS.is_file(), (
        f"{EXCLUSOES_LOCAIS.relative_to(RAIZ)} não existe. Em clone novo isso é "
        "esperado, e significa que a política de exclusão NÃO está ativa: "
        "recriar o arquivo antes de qualquer `git add`."
    )
    assert _padroes_de_exclusao_local(), (
        "o arquivo de exclusões locais existe mas não declara nenhum padrão."
    )


def test_nada_que_a_politica_exclui_esta_no_indice():
    """Nenhum caminho rastreado casa com um padrão das exclusões locais.

    A guarda é regra, não lista: os padrões são lidos de ``.git/info/exclude``, que
    não é versionado. Um caminho acrescentado à política amanhã passa a ser
    coberto sem que uma linha deste arquivo mude — e sem que a política apareça em
    blob nenhum.

    A mensagem de falha nomeia o caminho encontrado, e isso é aceitável: ela só
    aparece em execução local, quando o arquivo em questão já está no índice e o
    problema é justamente removê-lo antes do push.
    """
    padroes = _padroes_de_exclusao_local()
    if not padroes:
        pytest.skip("sem exclusões locais declaradas — ver o teste anterior")
    rastreados = _rastreados()
    achados = sorted(
        {caminho for caminho in rastreados for padrao in padroes if _casa(caminho, padrao)}
    )
    assert achados == [], (
        f"{len(achados)} caminho(s) no índice do git casam com a política de "
        f"exclusão local: {achados}. Remover com `git rm --cached` antes do push."
    )


def test_nenhuma_excecao_do_gitignore_desfaz_a_politica_local():
    """O ``.gitignore`` tem precedência sobre ``.git/info/exclude``.

    Consequência: uma linha de exceção — ``!algum/padrão`` — pode ressuscitar um
    caminho que a política local mantinha fora, e nada avisa. O arquivo volta a
    aparecer como não rastreado, e entra no primeiro ``git add -A`` distraído.

    Aconteceu: a exceção que liberava o guia normativo sob ``docs/normas/`` foi
    escrita como curinga e arrastou junto um PDF de bastidor que mora na mesma
    pasta. O teste do índice não pegou, porque o arquivo ainda não estava nele.

    Esta guarda fecha a janela entre as duas coisas: confere que todo caminho em
    disco coberto pela política continua de fato ignorado. Lê os padrões do
    arquivo não versionado, como o resto desta suíte, e por isso continua sendo
    regra e não lista.
    """
    padroes = _padroes_de_exclusao_local()
    if not padroes:
        pytest.skip("sem exclusões locais declaradas — ver o teste anterior")
    vazados = sorted(
        caminho.relative_to(RAIZ).as_posix()
        for caminho in RAIZ.rglob("*")
        if caminho.is_file()
        and ".git/" not in caminho.relative_to(RAIZ).as_posix()
        and any(_casa(caminho.relative_to(RAIZ).as_posix(), p) for p in padroes)
        and not _ignorado(caminho)
    )
    assert vazados == [], (
        f"{len(vazados)} caminho(s) que a política local exclui deixaram de ser "
        f"ignorados: {vazados}. Alguma exceção do .gitignore passou por cima do "
        ".git/info/exclude — estreitar a exceção para o arquivo nomeado."
    )


def test_a_guarda_de_exclusao_reconhece_os_padroes_que_usa():
    """Contraprova do casador: teste que passa dos dois lados não testa nada.

    Sem isto, ``_casa`` poderia devolver ``False`` para tudo e o teste acima
    passaria para sempre, dando a impressão de proteção. Os pares abaixo exercitam
    as formas de padrão que o gitignore admite, sem nomear nada da política real.
    """
    assert _casa("algum/arquivo.md", "algum/arquivo.md")
    assert _casa("pasta/coisa.txt", "pasta/")
    assert _casa("nivel/pasta/coisa.txt", "pasta/")
    assert _casa("qualquer/lugar/ARQUIVO.md", "ARQUIVO.md")
    assert _casa("dir/sub/x.tmp", "*.tmp")
    assert not _casa("outro/caminho.md", "algum/arquivo.md")
    assert not _casa("pastaria/coisa.txt", "pasta/")
    assert not _casa("dir/x.txt", "*.tmp")
