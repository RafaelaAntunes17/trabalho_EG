"""Análise semântica da Caravela: gramática de atributos em LarkAG (gramatica_ag.lark).

O LarkAG gera a partir da gramática de atributos uma gramática Lark (getCFG) e um
Interpreter que calcula os atributos e verifica as condições de contexto. O Interpreter
é executado num espaço de nomes com as funções de auxiliares.py, que as regras usam.
"""

from pathlib import Path

from lark import Lark
from lark_ag import Lark_AG, ContextConditionError

from . import auxiliares

GRAMATICA_AG = (Path(__file__).parent / "gramatica_ag.lark").read_text(encoding="utf-8")

ag = Lark_AG(GRAMATICA_AG)

# o mesmo parser da análise sintática (LALR com lexer="basic"), e não o Earley do LarkAG
ag_parser = Lark(ag.getCFG(), parser="lalr", lexer="basic")

_ns = dict(vars(auxiliares))
exec(ag.getInterpreterFile(), _ns)


def analisar(codigo):
  """Analisa um programa e devolve a raiz da árvore, já com os atributos calculados.

  Lança lark.exceptions.UnexpectedInput se houver um erro de sintaxe e
  ContextConditionError se alguma condição de contexto falhar.
  """
  tree = ag_parser.parse(codigo)
  _ns["MyInterpreter"]().visit(tree)
  return tree


def verificar_semantica(codigo):
  """Devolve True se o programa estiver correto, ou a mensagem do primeiro erro semântico."""
  try:
    analisar(codigo)
    return True
  except ContextConditionError as e:
    return f"Erro semântico: {e}"
