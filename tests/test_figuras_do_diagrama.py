"""Guarda de frescor das figuras exportadas do diagrama.

As figuras da arquitetura são **geradas** de ``docs/arquitetura/arquitetura.drawio``
e versionadas em ``texto/tcc1/figuras/``. Versioná-las é decisão deliberada: o
texto precisa compilar em qualquer máquina, inclusive a de quem avalia, sem
depender de um aplicativo gráfico instalado.

O preço dessa decisão é o risco que esta guarda cobre: alguém move uma caixa no
diagrama, não reexporta, e o PDF sai com a figura antiga. Nada reclama — o
documento compila, a figura aparece, e só está errada.

A guarda **não** usa data de modificação: ela não sobrevive a um clone, e um
clone novo passaria a acusar tudo como velho. Compara-se a impressão digital do
diagrama registrada no momento da exportação com a do diagrama em disco.

Regerar com ``python scripts/gerar_figuras.py``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIAGRAMA = RAIZ / "docs" / "arquitetura" / "arquitetura.drawio"
FIGURAS = RAIZ / "texto" / "tcc1" / "figuras"
PROCEDENCIA = FIGURAS / "procedencia.txt"

# As três páginas do diagrama, na ordem em que aparecem no arquivo.
ESPERADAS = (
    "arquitetura-nivel1-contexto.pdf",
    "arquitetura-nivel2-conteineres.pdf",
    "arquitetura-fluxo-processo.pdf",
)


def _impressao(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_o_diagrama_existe():
    """Contraprova: sem o diagrama, toda a guarda abaixo é vácuo."""
    assert DIAGRAMA.is_file(), f"{DIAGRAMA.relative_to(RAIZ)} não existe"


def test_todas_as_figuras_foram_exportadas():
    faltando = [nome for nome in ESPERADAS if not (FIGURAS / nome).is_file()]
    assert faltando == [], (
        f"figura(s) ausente(s) em {FIGURAS.relative_to(RAIZ)}: {faltando}. "
        "Regerar com `python scripts/gerar_figuras.py`."
    )


def test_as_figuras_nao_estao_vazias():
    """Exportação que falha no meio deixa arquivo de zero byte, e o LaTeX aceita."""
    vazias = [nome for nome in ESPERADAS if (FIGURAS / nome).stat().st_size == 0]
    assert vazias == [], f"figura(s) de tamanho zero: {vazias}. A exportação falhou."


def test_as_figuras_correspondem_ao_diagrama_em_disco():
    """O coração da guarda: diagrama mexido sem reexportar é acusado aqui.

    Se este teste falhar, a figura que está no PDF não é a que está no diagrama.
    Regerar, conferir que o resultado é o esperado, e versionar os dois juntos.
    """
    assert PROCEDENCIA.is_file(), (
        f"{PROCEDENCIA.relative_to(RAIZ)} não existe. Sem ele não há como saber "
        "de que versão do diagrama as figuras saíram — regerar."
    )
    registrada = PROCEDENCIA.read_text(encoding="utf-8").strip()
    atual = _impressao(DIAGRAMA)
    assert registrada == atual, (
        "o diagrama mudou depois que as figuras foram exportadas. O PDF está "
        "mostrando a versão antiga, e nada mais acusa isso. "
        "Regerar com `python scripts/gerar_figuras.py`."
    )


def test_a_figura_do_processo_corresponde_ao_modelo_bpmn():
    """Mesma guarda da anterior, para o modelo de processo.

    O ``.bpmn`` é a fonte e abre em qualquer ferramenta da notação — inclusive na
    que a orientação indicou, para conferência. A figura é derivada dele, e
    envelhece em silêncio se alguém editar o modelo sem reexportar.

    Regerar com ``python scripts/gerar_bpmn.py``.
    """
    from scripts.gerar_bpmn import PROCEDENCIA, figuras, impressao, modelos

    ausentes = [m.name for m in modelos() if not m.is_file()]
    assert ausentes == [], f"modelo(s) de processo ausente(s): {ausentes}"
    nao_geradas = [f.name for f in figuras() if not f.is_file() or f.stat().st_size == 0]
    assert nao_geradas == [], (
        f"figura(s) do processo ausente(s) ou vazia(s): {nao_geradas}. "
        "Rodar `python scripts/gerar_bpmn.py`."
    )
    assert PROCEDENCIA.is_file(), (
        f"{PROCEDENCIA.relative_to(RAIZ)} não existe. Sem ele não há como saber "
        "de que versão do modelo a figura saiu — regerar."
    )
    assert PROCEDENCIA.read_text(encoding="utf-8").strip() == impressao(), (
        "o modelo de processo mudou depois que a figura foi exportada. O PDF "
        "mostra a versão antiga. Regerar com `python scripts/gerar_bpmn.py`."
    )


def test_o_texto_referencia_todas_as_figuras_exportadas():
    """Figura exportada e não usada é peso morto; figura usada e não exportada quebra.

    Verifica o lado que o LaTeX não verifica: o compilador acusa a figura que
    falta, nunca a que sobra.
    """
    secoes = (RAIZ / "texto" / "tcc1" / "secoes").glob("*.tex")
    texto = "\n".join(arquivo.read_text(encoding="utf-8") for arquivo in secoes)
    orfas = [nome for nome in ESPERADAS if nome not in texto]
    assert orfas == [], (
        f"figura(s) exportada(s) e não referenciada(s) no texto: {orfas}. "
        "Ou inserir no texto, ou parar de exportar."
    )


def test_os_modelos_de_processo_nao_tem_linha_cruzada():
    """O defeito que motivou refazer o desenho, agora verificado por teste.

    A primeira versão do modelo tinha ligações se cruzando e uma passando por
    dentro de uma caixa. Dá para ver a olho numa figura pequena, mas não dá para
    ver relendo XML — e é o XML que se edita.
    """
    from scripts.gerar_bpmn import modelos
    from scripts.verificar_bpmn import verificar

    for modelo in modelos():
        r = verificar(modelo.read_text(encoding="utf-8"))
        detalhe = {
            "sobrepostas": r.sobrepostas,
            "diagonais": r.diagonais,
            "cruzamentos": r.cruzamentos,
            "atravessam": r.atravessam,
        }
        assert r.problemas == 0, f"{modelo.name} tem problemas de leitura: {detalhe}"
