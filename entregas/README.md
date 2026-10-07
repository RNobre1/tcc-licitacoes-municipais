# Entregas

Versões **apresentáveis** do texto: os três layouts compilados sem os marcadores
de pendência.

Os marcadores são bilhete de trabalho — anotam o que falta escrever, com que
fonte, e por quê. Servem a quem escreve e não a quem lê. Nesta pasta eles não
aparecem.

| Arquivo | Para quê |
|---|---|
| `tcc1-modelo-do-curso.pdf` | O formato que o curso usa, conforme o modelo cedido pela orientação |
| `tcc1-formato-sbc.pdf` | Padrão da Sociedade Brasileira de Computação, para submissão a evento |
| `tcc1-formato-sibi.pdf` | Formato tradicional do guia do SIBI, exigido no depósito da biblioteca |

## Como regerar

```bash
python scripts/gerar_entregas.py              # recompila os três
python scripts/gerar_entregas.py --conferir   # só diz se estão atualizados
```

O conteúdo é o mesmo dos três: o texto vive uma vez só, em `texto/tcc1/secoes/`,
e cada layout é um arquivo fino que escolhe estilo. A diferença de número de
páginas entre eles vem da margem, do corpo de letra e da entrelinha de cada
formato.

## Sobre estes arquivos serem versionados

Arquivo gerado normalmente não entra no repositório, e este projeto segue essa
regra em todo o resto. A exceção aqui é deliberada: o PDF precisa estar
disponível para quem não vai compilar nada.

O preço da exceção é o risco de envelhecerem em silêncio enquanto o texto avança.
`tests/test_entregas_apresentaveis.py` cobre isso: o script grava, em
`procedencia.txt`, a impressão digital de tudo que entra na compilação — seções,
estilos, figuras e bibliografia —, e o teste falha quando o texto em disco não
corresponde mais ao que está publicado aqui.
