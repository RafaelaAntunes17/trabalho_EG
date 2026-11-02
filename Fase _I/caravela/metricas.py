"""Medidas de qualidade da gramática e da gramática de atributos (secção 4 do relatório).

Correr com: python -m caravela.metricas
"""

import math
import re

from lark import Lark, Tree
from lark.load_grammar import GrammarBuilder


def medidas_gramatica(texto):
  g = Lark(texto, parser="lalr", lexer="basic")
  nao_terminais = {r.origin.name for r in g.rules if not r.origin.name.startswith("_")}
  reservadas = [t for t in g.terminals if t.pattern.type == "str" and re.fullmatch(r"[a-z_0-9]+", t.pattern.value)]
  return {"não-terminais": len(nao_terminais), "terminais": len(g.terminals), "palavras reservadas": len(reservadas),
          "linhas": len(texto.strip().splitlines())}

def profundidade(t):
  return 1 + max([profundidade(c) for c in t.children if isinstance(c, Tree)] + [0])


def regras_ebnf(texto):
  """As regras tal como estão escritas (EBNF): nome -> árvore do lado direito."""
  gb = GrammarBuilder()
  gb.load_grammar(texto)
  return {str(n): d.tree for n, d in gb._definitions.items() if not d.is_term}

def simbolos(arvore):
  """Os símbolos (operandos) e os metassímbolos (operadores) de um lado direito."""
  operandos, operadores = [], []
  for t in arvore.iter_subtrees_topdown():
    if t.data == "expansions" and len(t.children) > 1:
      operadores += ["|"] * (len(t.children) - 1)
    elif t.data == "expansions" and t is not arvore:
      operadores.append("( )")
    elif t.data == "expr":
      operadores.append(str(t.children[1]))
    elif t.data == "value":
      s = t.children[0]
      operandos.append(str(s.name) if hasattr(s, "name") else str(s.children[0]))
  return operandos, operadores

def alcancaveis(grafo, a):
  vistos, pilha = set(), [a]
  while pilha:
    for b in grafo[pilha.pop()]:
      if b not in vistos:
        vistos.add(b)
        pilha.append(b)
  return vistos

def metricas_gramatica(texto, inicial="start"):
  """Métricas de tamanho e de estrutura de Power e Malloy (2004)."""
  regras = regras_ebnf(texto)
  g = Lark(texto, parser="lalr", lexer="basic")

  # tamanho
  operandos, operadores = [], []
  for nome, arvore in regras.items():
    o, m = simbolos(arvore)
    operandos += o
    operadores += [":"] + m
  decisoes = sum(1 for m in operadores if m in ("|", "?", "*", "+"))
  n1, n2 = len(set(operadores)), len(set(operandos))
  N1, N2 = len(operadores), len(operandos)
  volume = (N1 + N2) * math.log2(n1 + n2)
  dificuldade = n1 / 2 * N2 / n2

  # estrutura: grafo "A usa B", e os níveis (componentes fortemente ligadas)
  grafo = {a: {s for s in simbolos(t)[0] if s in regras} for a, t in regras.items()}
  alc = {a: alcancaveis(grafo, a) for a in regras}
  nivel = {a: frozenset({a} | {b for b in alc[a] if a in alc[b]}) for a in regras}
  niveis = set(nivel.values())
  arestas = {frozenset((a, b)) for a in grafo for b in grafo[a] if a != b}
  n, e = len(regras), len(arestas)

  def altura(lv, memo={}):
    if lv not in memo:
      seguintes = {nivel[b] for a in lv for b in grafo[a]} - {lv}
      memo[lv] = 1 + max([altura(s) for s in seguintes] + [0])
    return memo[lv]

  return {
    "TERM": len(g.terminals),
    "VAR": n,
    "MCC": decisoes,
    "AVS": round(N2 / n, 2),
    "HAL": round(dificuldade * volume / 1000, 1),
    "TIMP": round(200 * (e - n + 1) / ((n - 1) * (n - 2)), 1),
    "CLEV": round(100 * len(niveis) / n, 1),
    "NSLEV": sum(1 for lv in niveis if len(lv) > 1),
    "DEP": max(len(lv) for lv in niveis),
    "HEI": altura(nivel[inicial], {}),
    "produções BNF": len(g.rules),
    "estados LALR": len(g.parser.parser.parser.parse_table.states),
    "maior nível": sorted(max(niveis, key=len)),
  }

def metricas_atributos(texto):
  """Equações da gramática de atributos, separadas pelo que fazem."""
  lados = re.findall(r"\b[a-z]+(?:\[\d\])?\.[a-z]+ = ([^;]*);", texto)
  copia = [r for r in lados if re.fullmatch(r"[a-z]+(?:\[\d\])?\.[a-z]+", r.strip())]
  constante = [r for r in lados if re.fullmatch(r"\[\]|\{\}|None|True|False|K_[A-Z]+", r.strip())]
  sa = re.findall(r"^SA\(\w+\)\s*\{([^}]*)\}", texto, re.M)
  ia = re.findall(r"^IA\(\w+\)\s*\{([^}]*)\}", texto, re.M)
  return {
    "atributos sintetizados": sum(s.count(":") for s in sa),
    "atributos herdados": sum(s.count(":") for s in ia),
    "equações": len(lados),
    "cópias": len(copia),
    "constantes": len(constante),
    "calculadas": len(lados) - len(copia) - len(constante),
    "condições de contexto": len(re.findall(r'-> "', texto)),
  }


if __name__ == "__main__":
  from pathlib import Path

  from .semantica import GRAMATICA_AG, ag
  from .sintaxe import GRAMATICA, parser

  for titulo, texto in [("Gramática (gramatica.lark)", GRAMATICA), ("Gramática gerada pelo LarkAG", ag.getCFG())]:
    print(titulo)
    for k, v in medidas_gramatica(texto).items():
      print(f"  {k:<23} {v}")
    for k, v in metricas_gramatica(texto).items():
      print(f"  {k:<23} {v}")
  print("Gramática de atributos (gramatica_ag.lark)")
  for k, v in metricas_atributos(GRAMATICA_AG).items():
    print(f"  {k:<23} {v}")
  print("Exemplos")
  for f in sorted(Path("exemplos").glob("*.cav")):
    programa = f.read_text(encoding="utf-8")
    arvore = parser.parse(programa)
    print(f"  {f.name}: {len(programa.splitlines())} linhas, árvore com "
          f"{len(list(arvore.iter_subtrees()))} nós e profundidade {profundidade(arvore)}")
