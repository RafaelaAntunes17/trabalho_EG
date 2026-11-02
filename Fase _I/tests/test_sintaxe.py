"""Testes da análise léxica e sintática (gramatica.lark)."""

import re
from pathlib import Path

import pytest

from caravela.semantica import ag_parser
from caravela.sintaxe import parser, tokens, verificar_sintaxe

EXEMPLOS = sorted(Path(__file__).parent.parent.glob("exemplos/*.cav"))

CASOS = [
  ('camera c { position (1, 2, 3); near 0.1; }', True),
  ('material m { if modo == 2 { lighting phong { shininess 100; } } else { lighting none; } }', 'Erro de sintaxe: linha 1, coluna 14'),
  ('camera c { position (1, 2, 3) }', 'Erro de sintaxe: linha 1, coluna 31'),
  ('material m { draw x; }', 'Erro de sintaxe: linha 1, coluna 14'),
  ('camera c { position (1, 2); }', 'Erro de sintaxe: linha 1, coluna 26'),
  ('scene texture = model "a.obj";', 'Erro de sintaxe: linha 1, coluna 7'),
  ('camera c { position 5; }', 'Erro de sintaxe: linha 1, coluna 21'),
  ('material m { diffuse 3; }', 'Erro de sintaxe: linha 1, coluna 22'),
  ('pass p { drawcam; }', 'Erro de sintaxe: linha 1, coluna 10'),
  ('camera c { near 0.1; far 100; fov 60; }  light l directional { direction (1, -1, 0); color grey; }', True),
  ('template t(pos: vec3, c: color) { sphere s { translate pos; } }  scene sc { t((1, 0, 2), red); square chao; axis eixos { scale (5, 5, 5); } }', True),
  ('material m { diffuse c; let k = 1; }', 'Erro de sintaxe: linha 1, coluna 25'),
  ('camera cam { position (1, 2, 3); }  pass p { draw cam; camera cam; }', True),
]


@pytest.mark.parametrize("codigo, esperado", CASOS)
def test_sintaxe(codigo, esperado):
  assert verificar_sintaxe(codigo) == esperado


@pytest.mark.parametrize("ficheiro", EXEMPLOS, ids=lambda f: f.name)
def test_exemplos_sintaticamente_corretos(ficheiro):
  assert verificar_sintaxe(ficheiro.read_text(encoding="utf-8")) is True


def test_palavras_reservadas_e_identificadores():
  tipos = [(t.type, t.value) for t in tokens("material materialx drawcam red")]
  assert tipos == [("MATERIAL", "material"), ("ID", "materialx"), ("ID", "drawcam"), ("ID", "red")]


def test_comentarios_ignorados():
  assert [t.value for t in tokens("let /* bloco */ a = 1; // fim")] == ["let", "a", "=", "1", ";"]


def aceita(p, codigo):
  try:
    p.parse(codigo)
    return True
  except Exception:
    return False


@pytest.mark.parametrize("codigo", [c for c, _ in CASOS] + [f.read_text(encoding="utf-8") for f in EXEMPLOS])
def test_gramatica_do_larkag_aceita_a_mesma_linguagem(codigo):
  # as transformações da gramática para o LarkAG não mudam a linguagem aceite
  assert aceita(parser, codigo) == aceita(ag_parser, codigo)
