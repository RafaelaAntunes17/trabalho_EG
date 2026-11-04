"""Métricas de qualidade da gramática e da gramática de atributos (como na NB07).

Correr com: python -m caravela.metricas
"""

import re
from collections import Counter
from pathlib import Path

from .semantica import GRAMATICA_AG, ag
from .sintaxe import GRAMATICA, parser


def metricas_tamanho(parser):
  """Métricas de tamanho da gramática, sobre as regras BNF que o Lark gera."""
  rules = parser.rules
  productions_per_symbol = Counter(rule.origin.name for rule in rules)
  rhs_lengths = [len(rule.expansion) for rule in rules]
  n_unitary = sum(len(rule.expansion) == 1 and not rule.expansion[0].is_term for rule in rules)
  return {
    "terminais": len(parser.terminals),
    "não-terminais": len(productions_per_symbol),
    "  (auxiliares do Lark, de * e ?)": sum(1 for n in productions_per_symbol if n.startswith("__")),
    "produções": len(rules),
    "produções unitárias": n_unitary,
    "lado direito (média)": round(sum(rhs_lengths) / len(rhs_lengths), 2),
    "lado direito (máximo)": max(rhs_lengths),
    "produções por não-terminal (média)": round(len(rules) / len(productions_per_symbol), 2),
    "produções por não-terminal (máximo)": max(productions_per_symbol.values()),
    "subgramáticas importadas": 0,
  }


def grafo_dependencias(parser):
  """Arestas A -> B: o não-terminal A usa o não-terminal B numa produção."""
  return {
    (rule.origin.name, symbol.name)
    for rule in parser.rules
    for symbol in rule.expansion
    if not symbol.is_term
  }


def metricas_dependencias(parser):
  edges = grafo_dependencias(parser)
  nonterminals = {rule.origin.name for rule in parser.rules}
  in_degree = Counter(b for a, b in edges)
  out_degree = Counter(a for a, b in edges)
  return {
    "arestas": len(edges),
    "grau de entrada (média)": round(sum(in_degree[n] for n in nonterminals) / len(nonterminals), 2),
    "grau de saída (média)": round(sum(out_degree[n] for n in nonterminals) / len(nonterminals), 2),
  }


def metricas_parser(parser):
  """Tamanho da tabela LALR (usa partes internas do Lark, como na NB07)."""
  states = parser.parser.parser._parse_table.states
  return {
    "estados LALR": len(states),
    "entradas das tabelas ACTION/GOTO": sum(len(actions) for actions in states.values()),
  }


def recursivos_indiretos(parser):
  """Não-terminais que chegam a si próprios passando por outro não-terminal."""
  vizinhos = {}
  for a, b in grafo_dependencias(parser):
    if a != b:
      vizinhos.setdefault(a, set()).add(b)
  res = set()
  for inicio in vizinhos:
    vistos, pilha = set(), list(vizinhos[inicio])
    while pilha:
      n = pilha.pop()
      if n == inicio:
        res.add(inicio)
        break
      if n not in vistos:
        vistos.add(n)
        pilha.extend(vizinhos.get(n, ()))
  return res


def metricas_forma(parser, texto):
  rules = [r for r in parser.rules if not r.origin.name.startswith("__")]
  esquerda = {str(r.origin.name) for r in rules
              if r.expansion and not r.expansion[0].is_term and r.expansion[0].name == r.origin.name}
  direita = {str(r.origin.name) for r in rules
             if r.expansion and not r.expansion[-1].is_term and r.expansion[-1].name == r.origin.name}
  indiretos = {str(n) for n in recursivos_indiretos(parser) if not n.startswith("__")}

  # notação: vê-se no texto da gramática, porque o Lark converte tudo para BNF
  definicoes = re.findall(r"^([a-z_0-9]+)\s*:(.*?)(?=^[a-zA-Z_0-9]+\s*:|\Z)", texto, re.M | re.S)
  ebnf = sorted(n for n, corpo in definicoes if re.search(r'[*?+]|\(', re.sub(r'"[^"]*"', "", corpo)))
  return {
    "recursividade direta à esquerda": sorted(esquerda),
    "recursividade direta à direita": sorted(direita),
    "recursividade indireta": sorted(indiretos),
    "regras escritas": len(definicoes),
    "regras com EBNF (* ? ( ))": len(ebnf),
    "regras só com BNF": len(definicoes) - len(ebnf),
  }


def metricas_lexicograficas(parser):
  terminais = parser.terminals
  palavras = [t.pattern.value for t in terminais
              if t.pattern.type == "str" and re.fullmatch(r"[a-z_0-9]+", t.pattern.value)]
  flexiveis = [t.name for t in terminais if t.pattern.type == "re"]
  comentario = next(t for t in terminais if t.name == "COMMENT").pattern.value
  return {
    "palavras reservadas": len(palavras),
    "terminais flexíveis (expressão regular)": flexiveis,
    "terminais fixos": len(terminais) - len(flexiveis),
    "comentários de linha": "//" in comentario.replace("\\/", "/"),
    "comentários de bloco": "/*" in comentario.replace("\\/", "/").replace("\\*", "*"),
  }


def metricas_ga(ag, texto):
  """Métricas da gramática de atributos (código da NB07 mais as de forma)."""
  attributes = [
    attribute
    for symbol_attributes in ag.generator.__attributes__.values()
    for attribute in symbol_attributes.values()
  ]
  semantic_rules = [
    rule
    for alternatives in ag.generator.__semantics__.values()
    for alternative in alternatives
    for rule in alternative["semantics"]
  ]
  regras = [r["code"] for r in semantic_rules if r["type"] == "er"]
  copias = [r for r in regras if re.fullmatch(r"\w+(\[\d\])?\.\w+ = \w+(\[\d\])?\.\w+", r.strip())]
  return {
    "atributos": len(attributes),
    "herdados": sum(a["inheritance"] == "IA" for a in attributes),
    "sintetizados": sum(a["inheritance"] == "SA" for a in attributes),
    "atributos de tipo atómico (str, bool)": sum(a["type"] in ("str", "bool", "int") for a in attributes),
    "atributos de tipo estruturado (list, dict, tuple)": sum(a["type"] in ("list", "dict", "tuple") for a in attributes),
    "atributos de tipo any": sum(a["type"] == "any" for a in attributes),
    "regras de avaliação": len(regras),
    "  das quais só copiam um atributo": len(copias),
    "condições de contexto": sum(r["type"] == "cc" for r in semantic_rules),
    "funções auxiliares": len(re.findall(r"^def ", Path(__file__).with_name("auxiliares.py").read_text(), re.M)),
  }


def mostrar(titulo, metricas):
  print(titulo)
  for k, v in metricas.items():
    print(f"  {k:<50} {v}")


if __name__ == "__main__":
  mostrar("Gramática: tamanho", metricas_tamanho(parser))
  mostrar("Gramática: dependências", metricas_dependencias(parser))
  mostrar("Gramática: parser", metricas_parser(parser))
  mostrar("Gramática: forma", metricas_forma(parser, GRAMATICA))
  mostrar("Gramática: lexicográficas", metricas_lexicograficas(parser))
  mostrar("Gramática de atributos", metricas_ga(ag, GRAMATICA_AG))
