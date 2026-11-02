"""Linha de comandos: python -m caravela programa.cav [--tokens] [--arvore]"""

import argparse
import sys

from lark.exceptions import UnexpectedInput
from lark_ag import ContextConditionError

from .auxiliares import PRE
from .semantica import analisar
from .sintaxe import parser, tokens


def main():
  ap = argparse.ArgumentParser(prog="caravela", description="Verifica um programa em Caravela.")
  ap.add_argument("ficheiro", help="programa em Caravela (.cav)")
  ap.add_argument("--tokens", action="store_true", help="mostra os tokens do analisador léxico")
  ap.add_argument("--arvore", action="store_true", help="mostra a árvore sintática")
  args = ap.parse_args()

  with open(args.ficheiro, encoding="utf-8") as f:
    codigo = f.read()

  try:
    if args.tokens:
      for t in tokens(codigo):
        print(f"{t.type:<18} {t.value!r}")
    if args.arvore:
      print(parser.parse(codigo).pretty())
    raiz = analisar(codigo)
  except UnexpectedInput as e:
    print(f"{args.ficheiro}: erro de sintaxe na linha {e.line}, coluna {e.column}")
    sys.exit(1)
  except ContextConditionError as e:
    print(f"{args.ficheiro}: erro semântico: {e}")
    sys.exit(1)

  print(f"{args.ficheiro}: programa correto")
  print("  tabela de símbolos:", {n: t for n, t in raiz.tabela.items() if n not in PRE})
  print("  unidades de textura:", raiz.materiais)


if __name__ == "__main__":
  main()
