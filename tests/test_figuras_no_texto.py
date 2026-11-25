"""Guarda das figuras no texto: rótulo, citação cruzada e comentário.

POR QUE ESTA GUARDA EXISTE

Na reunião de orientação acadêmica de 10/11/2026, a orientadora firmou uma regra
geral para a escrita do trabalho:

    "Comentar toda figura, sem terminar seção com imagem: vale pra todos."

Em texto acadêmico e na norma de escrita técnica, uma figura não pode aparecer
desconectada do discurso:
1. Todo ambiente ``figure`` ou ``figure*`` precisa ter um rótulo (``\\label``) identificador;
2. Todo ambiente precisa ser citado no texto corrido por ``\\ref`` (ou equivalente,
   como ``\\autoref``, ``\\pageref`` ou ``\\cref``) **fora** do próprio ambiente, preparando
   a leitura ou conectando a imagem ao argumento;
3. Nenhuma figura pode ser o último elemento da sua seção: entre o ``\\end{figure}`` e o
   próximo cabeçalho (``\\chapter``, ``\\section``, ``\\subsection``, ``\\subsubsection``) ou o
   fim do arquivo, deve haver texto corrido substantivo que discuta a figura, e não apenas
   outra figura, tabela ou comentário.

A guarda é uma regra universal e não uma lista pré-definida: ela varre todos os
arquivos ``.tex`` de ``texto/*/secoes/`` e ``texto/*/capitulos/`` fiscalizando cada
ambiente ``figure`` presente.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVOS = sorted(
    [*(RAIZ / "texto").glob("*/secoes/*.tex"), *(RAIZ / "texto").glob("*/capitulos/*.tex")]
)

PADRAO_FIGURA = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.DOTALL)
PADRAO_LABEL = re.compile(r"\\label\{([^}]+)\}")
PADRAO_SECAO = re.compile(
    r"\\(?:chapter|section|subsection|subsubsection)\*?(?:\[[^\]]*\])?\{([^}]+)\}"
)


def _limpar_comentarios(conteudo: str) -> str:
    """Remove comentários LaTeX de cada linha mantendo quebras e números de linha."""
    linhas = [re.sub(r"(?<!\\)%.*$", "", linha) for linha in conteudo.splitlines()]
    return "\n".join(linhas)


def _tem_texto_corrido(trecho: str) -> bool:
    """Há prosa depois da figura? Figuras, tabelas e macros de layout não contam."""
    sem = re.sub(
        r"\\begin\{(figure\*?|table\*?|tabular[x*]?|longtable)\}.*?\\end\{\1\}",
        "",
        trecho,
        flags=re.DOTALL,
    )
    sem = re.sub(
        r"\\(?:label|ref|autoref|pageref|cref|vspace|hspace|input|include|includegraphics)\*?"
        r"(?:\[[^\]]*\])?\{[^}]*\}",
        "",
        sem,
    )
    sem = re.sub(r"\\[a-zA-Z]+\*?", "", sem)
    return len(re.findall(r"[^\W\d_]{2,}", sem)) >= 8


def verificar_figuras(
    arquivos: list[Path], textos_predefinidos: dict[Path, str] | None = None
) -> list[str]:
    """Varre os arquivos informados e devolve a lista de violações encontradas."""
    textos: dict[Path, str] = {}
    for arq in arquivos:
        if textos_predefinidos and arq in textos_predefinidos:
            textos[arq] = _limpar_comentarios(textos_predefinidos[arq])
        else:
            textos[arq] = _limpar_comentarios(arq.read_text(encoding="utf-8"))

    violacoes: list[str] = []

    for arq, texto in textos.items():
        outros_textos = [t for a, t in textos.items() if a != arq]
        caminho_rel = arq.relative_to(RAIZ) if arq.is_relative_to(RAIZ) else arq.name

        for match in PADRAO_FIGURA.finditer(texto):
            linha = texto[: match.start()].count("\n") + 1
            conteudo_figura = match.group(1)

            # Regra 1: tem \label
            m_label = PADRAO_LABEL.search(conteudo_figura)
            if not m_label:
                violacoes.append(f"{caminho_rel}:{linha}: figura sem \\label")
                label = None
            else:
                label = m_label.group(1).strip()
                # Regra 2: é citada por \ref ou equivalente fora do próprio ambiente
                padrao_citacao = re.compile(r"\\(?:[a-zA-Z]*ref\*?)\{" + re.escape(label) + r"\}")
                texto_fora = (
                    texto[: match.start()] + texto[match.end() :] + "\n".join(outros_textos)
                )
                if not padrao_citacao.search(texto_fora):
                    violacoes.append(
                        f"{caminho_rel}:{linha}: figura '{label}' não é citada por \\ref "
                        "ou equivalente fora do próprio ambiente"
                    )

            # Regra 3: não é o último elemento da sua seção
            pos_fim = match.end()
            m_prox_secao = PADRAO_SECAO.search(texto[pos_fim:])
            if m_prox_secao:
                fim_trecho = pos_fim + m_prox_secao.start()
                alvo = m_prox_secao.group(0).strip()
            else:
                fim_trecho = len(texto)
                alvo = "fim do arquivo"

            trecho_apos = texto[pos_fim:fim_trecho]
            if not _tem_texto_corrido(trecho_apos):
                nome_fig = f" '{label}'" if label else ""
                violacoes.append(
                    f"{caminho_rel}:{linha}: figura{nome_fig} é o último elemento da sua seção "
                    f"antes de '{alvo}' (não há texto corrido subsequente)"
                )

    return violacoes


def test_ha_arquivos_de_secoes():
    """Contraprova: se a varredura estiver vazia, o teste passaria no vácuo."""
    assert ARQUIVOS, "nenhum arquivo .tex encontrado em secoes ou capitulos — a varredura é vazia"
    assert any(a.parent.name == "secoes" for a in ARQUIVOS), "a varredura não alcança secoes/"
    assert any(a.parent.name == "capitulos" for a in ARQUIVOS), "a varredura não alcança capitulos/"


def test_guarda_acusa_cada_violacao_em_tex_sintetico(tmp_path: Path):
    """Prova que a guarda captura cada tipo de violação em um arquivo .tex sintético."""
    conteudo_sintetico = r"""
\section{Primeira Seção}
Texto introdutório citando a figura conforme~\ref{fig:conforme}.

\begin{figure}[H]
  \centering
  \caption{Figura conforme}
  \label{fig:conforme}
\end{figure}

Aqui há texto corrido comentando a figura conforme e fechando a seção com análise
substantiva e clara.

\section{Segunda Seção - Violações}
\ref{fig:sem-texto-secao} e \ref{fig:seguida-por-figura-1} e \ref{fig:seguida-por-figura-2}

\begin{figure}[H]
  \centering
  \caption{Figura sem rótulo}
\end{figure}
Texto corrido e substantivo com análise entre figuras consecutivas nesta subseção.

\begin{figure}[H]
  \centering
  \caption{Figura com rótulo mas sem ref}
  \label{fig:sem-ref}
\end{figure}
Texto corrido comentando a figura para fechar com explicação substantiva e adequada.

\begin{figure}[H]
  \centering
  \caption{Figura que termina a seção}
  \label{fig:sem-texto-secao}
\end{figure}

\subsection{Subseção com figuras em sequência sem texto}

\begin{figure}[H]
  \centering
  \caption{Primeira de um par sem texto}
  \label{fig:seguida-por-figura-1}
\end{figure}

\begin{figure}[H]
  \centering
  \caption{Segunda de um par sem texto}
  \label{fig:seguida-por-figura-2}
\end{figure}

\subsubsection{Subsubseção com tabela ou comentário}
\ref{fig:com-comentario} e \ref{fig:com-tabela} e \ref{fig:no-fim-do-arquivo}
e \ref{fig:so-macros} e \ref{fig:antes-de-subsubsecao}

\begin{figure}[H]
  \centering
  \caption{Figura seguida apenas por comentário}
  \label{fig:com-comentario}
\end{figure}
% Comentário com palavras de sobra para passar do limiar de oito, mas que não é prosa.

\begin{figure}[H]
  \centering
  \caption{Figura seguida apenas por tabela}
  \label{fig:com-tabela}
\end{figure}

\begin{table}[H]
  \caption{Tabela logo após a figura, com legenda de muitas palavras para passar do limiar de prosa}
\end{table}

\begin{figure}[H]
  \centering
  \caption{Figura seguida só de macros de layout}
  \label{fig:so-macros}
\end{figure}
\noindent\hfill\clearpage\newpage\par\medskip\smallskip\bigskip\raggedright\centering\vspace{1em}\input{secoes/parte-um-da-segunda-etapa-do-capitulo}

\begin{figure}[H]
  \centering
  \caption{Figura antes de uma subsubseção}
  \label{fig:antes-de-subsubsecao}
\end{figure}

\subsubsection{Subsubseção seguinte}
Texto corrido logo depois do cabeçalho, com palavras de sobra para passar do limiar,
mas que já pertence a outra subsubseção e não comenta a figura anterior.

\section{Última Seção}

\begin{figure}[H]
  \centering
  \caption{Figura no fim do arquivo}
  \label{fig:no-fim-do-arquivo}
\end{figure}
"""
    arquivo_teste = tmp_path / "sintetico.tex"
    arquivo_teste.write_text(conteudo_sintetico, encoding="utf-8")

    violacoes = verificar_figuras([arquivo_teste])

    # Verifica que a figura conforme NÃO foi acusada
    assert not any("fig:conforme" in v for v in violacoes)

    # 1. Figura sem rótulo
    assert any("figura sem \\label" in v for v in violacoes)

    # 2. Figura sem citação fora
    assert any(
        "figura 'fig:sem-ref' não é citada por \\ref ou equivalente fora do próprio ambiente" in v
        for v in violacoes
    )

    # 3. Figura que termina seção
    assert any(
        "figura 'fig:sem-texto-secao' é o último elemento da sua seção antes de "
        "'\\subsection{Subseção com figuras em sequência sem texto}'" in v
        for v in violacoes
    )

    # 4. Figuras em sequência sem texto corrido entre ou após
    assert any("fig:seguida-por-figura-1" in v for v in violacoes)
    assert any("fig:seguida-por-figura-2" in v for v in violacoes)

    # 5. Figura seguida apenas por comentário
    assert any("fig:com-comentario" in v for v in violacoes)

    # 6. Figura seguida apenas por tabela
    assert any("fig:com-tabela" in v for v in violacoes)

    # 6b. Figura seguida só de macros de layout, cujos nomes e argumentos não são prosa
    assert any("fig:so-macros" in v for v in violacoes)

    # 6c. Figura antes de uma subsubseção: a prosa depois do cabeçalho não conta
    assert any(
        "figura 'fig:antes-de-subsubsecao' é o último elemento da sua seção antes de "
        "'\\subsubsection{Subsubseção seguinte}'" in v
        for v in violacoes
    )

    # 7. Figura no fim do arquivo
    assert any(
        "figura 'fig:no-fim-do-arquivo' é o último elemento da sua seção antes de 'fim do arquivo'"
        in v
        for v in violacoes
    )


def test_guarda_pega_citacao_so_na_propria_legenda_e_aceita_citacao_de_outro_arquivo(
    tmp_path: Path,
):
    """Cada cláusula da regra 2 tem a sua prova sintética."""
    a = tmp_path / "a.tex"
    b = tmp_path / "b.tex"
    a.write_text(
        r"""
\section{A}
Veja~\autoref{fig:por-autoref}, ~\ref{fig:citada-no-outro-arquivo} e~\ref{fig:dupla}.

\begin{figure}[H]
  \caption{Citada por autoref}
  \label{fig:por-autoref}
\end{figure}

Texto depois da figura, comentando o que ela mostra ao leitor aqui com frase substantiva.

\begin{figure}[H]
  \caption{Só se cita na própria legenda, ver~\ref{fig:so-na-legenda}}
  \label{fig:so-na-legenda}
\end{figure}

Texto depois da figura, comentando o que ela mostra ao leitor aqui com frase substantiva.

\begin{figure*}[H]
  \caption{Largura dupla, sem texto depois}
  \label{fig:dupla}
\end{figure*}
\section{B}
""",
        encoding="utf-8",
    )
    b.write_text(
        r"""
\section{C}
\begin{figure}[H]
  \caption{Citada só no outro arquivo}
  \label{fig:citada-no-outro-arquivo}
\end{figure}

Texto depois da figura, comentando o que ela mostra ao leitor aqui com frase substantiva.
""",
        encoding="utf-8",
    )
    violacoes = verificar_figuras([a, b])
    assert not any("fig:por-autoref" in v for v in violacoes), violacoes
    assert not any("fig:citada-no-outro-arquivo" in v for v in violacoes), violacoes
    assert any("fig:so-na-legenda" in v and "não é citada" in v for v in violacoes), violacoes
    assert any("fig:dupla" in v and "último elemento" in v for v in violacoes), violacoes


def test_figuras_do_texto_cumprem_as_tres_regras():
    """Toda figura em secoes/ e capitulos/ deve ter label, ser citada por ref e ter prosa."""
    violacoes = verificar_figuras(ARQUIVOS)
    assert violacoes == [], (
        "figura(s) em texto/*/(secoes|capitulos)/ com pendências de norma e apresentação:\n  "
        + "\n  ".join(violacoes)
        + "\nRegra da orientação de 10/11: toda figura deve ter \\label, ser citada por \\ref "
        "e ser comentada por texto corrido subsequente (sem terminar seção com figura)."
    )
