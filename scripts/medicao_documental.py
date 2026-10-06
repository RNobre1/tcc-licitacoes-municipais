"""Medição sobre os documentos do estudo de caso.

Os números que a especificação de requisitos afirma saem daqui, e não de
leitura a olho. O ponto é ser **reproduzível**: qualquer pessoa com os mesmos
arquivos roda este módulo e obtém os mesmos valores, porque não há nada
estatístico nem probabilístico envolvido.

## O método, em uma frase

A similaridade entre dois textos é calculada por `difflib.SequenceMatcher`, da
biblioteca padrão do Python, que implementa uma variante do algoritmo de
casamento de padrões de Ratcliff e Obershelp. Ele devolve ``2M / T``, onde ``M``
é a quantidade de elementos casados entre as duas sequências e ``T`` é o total
de elementos das duas somadas. O resultado fica entre 0 e 1.

## Duas decisões de método que precisam ser declaradas

**A unidade de comparação é a palavra, não o caractere.** Comparar caractere a
caractere faria "cotação" e "coação" parecerem quase iguais, o que não diz nada
sobre reaproveitamento de texto. Comparando palavras, a medida responde à
pergunta que interessa: quanto do texto de um documento reaparece no outro.

**Antes de comparar, o texto é normalizado**: caixa baixa, acento removido e
pontuação descartada. Sem isso, "Análise Técnica" e "analise tecnica" apareceriam
como textos diferentes, e a diferença seria de digitação, não de conteúdo.

## O que este módulo não faz

Não usa modelo de linguagem, não usa aprendizado de máquina e não estima nada.
É contagem e comparação determinística. Rodando duas vezes, dá o mesmo número.

## Uso

    python scripts/medicao_documental.py --etp a.txt b.txt c.txt
    python scripts/medicao_documental.py --cotacao relatorio.txt

Os arquivos de entrada são a extração em texto dos documentos. Eles vivem fora
do versionamento, conforme a política de dados do projeto, e por isso os testes
deste módulo usam fixtures sintéticas.
"""

from __future__ import annotations

import argparse
import difflib
import re
import statistics
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from itertools import combinations
from pathlib import Path

VALIDADE_DIAS = 365

# Cabeçalho de seção numerada, como aparece nos Estudos Técnicos Preliminares:
# "03-DESCRIÇÃO DA NECESSIDADE", "13 - CONTRATAÇÕES CORRELATAS".
PADRAO_SECAO = r"^\s*(\d{1,2})\s*[-–.]\s*[A-ZÀ-Ú][^\n]{4,90}$"


# --- Similaridade ------------------------------------------------------------


def palavras(texto: str) -> list[str]:
    """Normaliza e quebra em palavras: caixa baixa, sem acento, sem pontuação."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento).split()


def similaridade(a: str, b: str) -> float:
    """Similaridade entre dois textos, de 0 a 1, comparando palavra a palavra.

    Determinística: mesmos textos, mesmo número, sempre.
    """
    pa, pb = palavras(a), palavras(b)
    if not pa and not pb:
        return 1.0
    if not pa or not pb:
        return 0.0
    return difflib.SequenceMatcher(None, pa, pb, autojunk=False).ratio()


def secoes(texto: str) -> dict[str, str]:
    """Fatia um documento pelas seções numeradas, devolvendo {número: texto}."""
    marcas = [(m.start(), m.group(1).zfill(2)) for m in re.finditer(PADRAO_SECAO, texto, re.M)]
    fora: dict[str, str] = {}
    for i, (inicio, chave) in enumerate(marcas):
        fim = marcas[i + 1][0] if i + 1 < len(marcas) else len(texto)
        fora[chave] = texto[inicio:fim]
    return fora


def corpo_da_secao(secao: str) -> str:
    """Descarta o cabeçalho e a citação legal, deixando só o texto redigido.

    O título da seção e o inciso citado ao lado dele são fixos pelo modelo: são
    idênticos em todos os documentos por construção. Compará-los infla a
    similaridade e responde à pergunta errada — a pergunta é quanto do texto
    **redigido** se repete, não quanto do formulário se repete.

    O efeito é maior nas seções curtas, onde o cabeçalho chega a ser uma fração
    grande do total.
    """
    linhas = secao.splitlines()[1:]  # fora o cabeçalho
    uteis = [
        ln
        for ln in linhas
        if not re.fullmatch(r"\s*\(?\s*Art\.?\s*\d+.*?\)?\s*", ln, re.I)
        and not re.fullmatch(r"\s*\(.*?Lei\s+(Federal\s+)?n[º°]?.*?\)\s*", ln, re.I)
    ]
    return "\n".join(uteis)


def comparar_secoes(documentos: dict[str, str]) -> dict[str, dict]:
    """Compara, seção a seção, todos os pares de documentos.

    Devolve, por seção comum a todos, a menor e a maior similaridade entre os
    pares. A **menor** é o número que interessa: ela responde "no pior caso,
    quanto do texto se repete", e é ela que sustenta a afirmação sobre
    reaproveitamento.
    """
    if len(documentos) < 2:
        raise ValueError("é preciso pelo menos dois documentos para comparar")

    fatiados = {nome: secoes(texto) for nome, texto in documentos.items()}
    comuns = set.intersection(*(set(f) for f in fatiados.values()))

    fora: dict[str, dict] = {}
    for chave in sorted(comuns):
        pares = {
            f"{x}x{y}": similaridade(
                corpo_da_secao(fatiados[x][chave]), corpo_da_secao(fatiados[y][chave])
            )
            for x, y in combinations(sorted(documentos), 2)
        }
        fora[chave] = {
            "menor": round(min(pares.values()), 2),
            "maior": round(max(pares.values()), 2),
            "pares": {k: round(v, 2) for k, v in pares.items()},
        }
    return fora


# --- Cotação -----------------------------------------------------------------


@dataclass
class Cotacao:
    itens: int = 0
    precos: int = 0
    inicio: date | None = None
    fim: date | None = None
    com_link: int = 0
    so_dominio: int = 0
    sem_fonte: int = 0
    fontes: Counter = field(default_factory=Counter)
    idades: list[int] = field(default_factory=list)

    @property
    def precos_por_item(self) -> float:
        return round(self.precos / self.itens, 2) if self.itens else 0.0

    @property
    def duracao_dias(self) -> int:
        return (self.fim - self.inicio).days if self.inicio and self.fim else 0

    @property
    def idade_maxima_dias(self) -> int:
        return max(self.idades) if self.idades else 0

    @property
    def fora_da_validade(self) -> int:
        return sum(1 for i in self.idades if i > VALIDADE_DIAS)

    @property
    def procedencia_com_link_pct(self) -> float:
        return round(100 * self.com_link / self.precos, 1) if self.precos else 0.0


def _dominio(endereco: str) -> str:
    limpo = re.sub(r"^https?://", "", endereco).split("/")[0].split(":")[0]
    return re.sub(r"^www\.", "", limpo)


def ler_cotacao(texto: str) -> Cotacao:
    """Extrai as métricas de um relatório de cotação.

    A idade de cada preço é contada a partir do **início** da pesquisa, e não do
    fim. Foi assim que se verificou o comportamento nos relatórios reais: o
    preço é selecionado no dia em que é buscado, então é essa a data que a regra
    de validade observa. Medir a partir do fim faz preço válido parecer vencido.
    """
    c = Cotacao()
    c.itens = len({int(x) for x in re.findall(r"^\s*Item (\d+):", texto, re.M)})

    janela = re.search(
        r"Pesquisa realizada entre (\d{2}/\d{2}/\d{4})[^\n]*?e (\d{2}/\d{2}/\d{4})", texto
    )
    if janela:
        c.inicio = datetime.strptime(janela.group(1), "%d/%m/%Y").date()
        c.fim = datetime.strptime(janela.group(2), "%d/%m/%Y").date()

    blocos = re.split(r"(?=Preço \([^)\n]{3,40}\)\s*\d+\s*:)", texto)[1:]
    c.precos = len(blocos)

    for bloco in blocos:
        fonte = re.search(r"Fonte:\s*(\S+)", bloco)
        if not fonte:
            c.sem_fonte += 1
        else:
            endereco = fonte.group(1)
            if endereco.startswith(("http://", "https://")):
                c.com_link += 1
            else:
                c.so_dominio += 1
            c.fontes[_dominio(endereco)] += 1

        data = re.search(r"\bData:\s*(\d{2}/\d{2}/\d{4})", bloco)
        if data and c.inicio:
            coletado = datetime.strptime(data.group(1), "%d/%m/%Y").date()
            c.idades.append((c.inicio - coletado).days)

    return c


# --- Linha de comando --------------------------------------------------------


def _relatar_etp(caminhos: list[Path]) -> None:
    documentos = {p.stem[:22]: p.read_text(encoding="utf-8", errors="replace") for p in caminhos}
    resultado = comparar_secoes(documentos)
    print(f"\nSimilaridade entre {len(documentos)} documentos, por seção")
    print("Método: difflib.SequenceMatcher sobre palavras normalizadas\n")
    print(f"{'seção':>6}  {'menor':>6}  {'maior':>6}   pares")
    for chave, v in resultado.items():
        pares = "  ".join(f"{k}={x:.2f}" for k, x in v["pares"].items())
        print(f"{chave:>6}  {v['menor']:6.2f}  {v['maior']:6.2f}   {pares}")
    menores = [v["menor"] for v in resultado.values()]
    invariantes = [k for k, v in resultado.items() if v["menor"] > 0.85]
    print(f"\nseções comparadas: {len(resultado)}")
    print(f"menor similaridade mediana: {statistics.median(menores):.2f}")
    print(f"seções de fato invariantes (acima de 0,85): {invariantes or 'nenhuma'}")


def _relatar_cotacao(caminhos: list[Path]) -> None:
    for p in caminhos:
        c = ler_cotacao(p.read_text(encoding="utf-8", errors="replace"))
        print(f"\n=== {p.name} ===")
        print(f"  itens                     {c.itens}")
        print(f"  preços                    {c.precos}")
        print(f"  preços por item           {c.precos_por_item}")
        print(f"  janela da pesquisa        {c.inicio} a {c.fim} ({c.duracao_dias} dias)")
        print(f"  procedência com link      {c.com_link} ({c.procedencia_com_link_pct}%)")
        print(f"  procedência só nomeada    {c.so_dominio}")
        print(f"  sem procedência           {c.sem_fonte}")
        print(f"  idade máxima do preço     {c.idade_maxima_dias} dias")
        print(f"  fora da validade          {c.fora_da_validade}")
        if c.fontes:
            total = sum(c.fontes.values())
            print("  fontes:")
            for dom, n in c.fontes.most_common(8):
                print(f"    {dom:44s} {n:5d}  {100 * n / total:5.1f}%")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--etp", nargs="+", type=Path, help="documentos a comparar seção a seção")
    p.add_argument("--cotacao", nargs="+", type=Path, help="relatórios de cotação a medir")
    args = p.parse_args(argv)

    if not args.etp and not args.cotacao:
        p.error("informe --etp ou --cotacao")
    for caminho in (args.etp or []) + (args.cotacao or []):
        if not caminho.is_file():
            print(f"não encontrei: {caminho}", file=sys.stderr)
            return 1

    if args.etp:
        _relatar_etp(args.etp)
    if args.cotacao:
        _relatar_cotacao(args.cotacao)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
