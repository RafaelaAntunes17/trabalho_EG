"""Análise léxica e sintática da Caravela (gramática em gramatica.lark)."""

from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedInput

GRAMATICA = (Path(__file__).parent / "gramatica.lark").read_text(encoding="utf-8")

# strict=True faz o Lark recusar a gramática se houver algum conflito LALR
parser = Lark(GRAMATICA, parser="lalr", lexer="basic", strict=True)


def tokens(codigo):
  """Devolve a lista de tokens produzidos pelo analisador léxico."""
  return list(parser.lex(codigo))


def verificar_sintaxe(codigo):
  """Devolve True se o programa for sintaticamente correto, ou a mensagem de erro."""
  try:
    parser.parse(codigo)
    return True
  except UnexpectedInput as e:
    return f"Erro de sintaxe: linha {e.line}, coluna {e.column}"
