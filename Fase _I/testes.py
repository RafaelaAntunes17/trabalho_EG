"""Testes da Caravela, com doctests como nas fichas das aulas.

Correr com: python testes.py
"""

import doctest
from pathlib import Path

from lark.exceptions import UnexpectedInput

from caravela.semantica import ag_parser, analisar, verificar_semantica
from caravela.sintaxe import parser, tokens, verificar_sintaxe

EXEMPLOS = sorted(Path(__file__).parent.glob("exemplos/*.cav"))


def ler(nome):
  return (Path(__file__).parent / "exemplos" / nome).read_text(encoding="utf-8")


def run_lexer(data):
  """
  Analisador léxico com doctests.

  Palavras reservadas, identificadores e cores (as cores são ID):

  >>> run_lexer('material materialx drawcam red')
  [('MATERIAL', 'material'), ('ID', 'materialx'), ('ID', 'drawcam'), ('ID', 'red')]

  Os comentários e os espaços são ignorados:

  >>> run_lexer('let /* bloco */ a = 1; // fim')
  [('LET', 'let'), ('ID', 'a'), ('EQUAL', '='), ('NUMBER', '1'), ('SEMICOLON', ';')]

  O `-` é um operador e não faz parte do número; `..` é o intervalo do for:

  >>> run_lexer('for i in 0..n-1')
  [('FOR', 'for'), ('ID', 'i'), ('IN', 'in'), ('NUMBER', '0'), ('_RANGE', '..'), ('ID', 'n'), ('SUB', '-'), ('NUMBER', '1')]
  """
  return [(t.type, t.value) for t in tokens(data)]


def run_parser(data):
  """
  Parser LALR com doctests.

  >>> run_parser('camera c { position (1, 2, 3); near 0.1; }')
  True
  >>> run_parser('material m { if modo == 2 { lighting phong { shininess 100; } } else { lighting none; } }')
  'Erro de sintaxe: linha 1, coluna 14'
  >>> run_parser('camera c { position (1, 2, 3) }')
  'Erro de sintaxe: linha 1, coluna 31'
  >>> run_parser('material m { draw x; }')
  'Erro de sintaxe: linha 1, coluna 14'
  >>> run_parser('camera c { position (1, 2); }')
  'Erro de sintaxe: linha 1, coluna 26'
  >>> run_parser('scene texture = model "a.obj";')
  'Erro de sintaxe: linha 1, coluna 7'
  >>> run_parser('camera c { position 5; }')
  'Erro de sintaxe: linha 1, coluna 21'
  >>> run_parser('material m { diffuse 3; }')
  'Erro de sintaxe: linha 1, coluna 22'
  >>> run_parser('pass p { drawcam; }')
  'Erro de sintaxe: linha 1, coluna 10'
  >>> run_parser('camera c { near 0.1; far 100; fov 60; }  light l directional { direction (1, -1, 0); color grey; }')
  True
  >>> run_parser('template t(pos: vec3, c: color) { sphere s { translate pos; } }  scene sc { t((1, 0, 2), red); square chao; axis eixos { scale (5, 5, 5); } }')
  True
  >>> run_parser('material m { diffuse c; let k = 1; }')
  'Erro de sintaxe: linha 1, coluna 25'
  >>> run_parser('camera cam { position (1, 2, 3); }  pass p { draw cam; camera cam; }')
  True

  Os quatro exemplos são aceites:

  >>> [run_parser(f.read_text(encoding="utf-8")) for f in EXEMPLOS]
  [True, True, True, True]
  """
  return verificar_sintaxe(data)


def run_semantica(data):
  """
  Análise semântica (gramática de atributos) com doctests.

  Os quatro exemplos estão corretos:

  >>> [run_semantica(f.read_text(encoding="utf-8")) for f in EXEMPLOS]
  [True, True, True, True]

  As unidades de textura do exemplo da Terra (clouds usa ruído, não tem unidade):

  >>> analisar(ler("4_terra.cav")).materiais
  {'textured': {'day': 0, 'specular': 1, 'night': 2}}

  Os erros referidos no exemplo do templo:

  >>> templo = ler("3_templo.cav")
  >>> run_semantica(templo.replace("pilar(3, azul)", "pilar(3, azl)"))
  'Erro semântico: Nome não declarado'
  >>> run_semantica(templo.replace("pilar(3, azul)", "pilar(azul, 3)"))
  'Erro semântico: Argumentos do template com tipo errado'
  >>> run_semantica(templo.replace("draw   templo, chao;", "draw   templo, chao;  if ang > 0 { }"))
  'Erro semântico: Nome não declarado'
  >>> run_semantica(templo.replace("draw   templo, chao;", "draw   templo, cam;"))
  'Erro semântico: Tipo errado'
  >>> run_semantica(templo.replace("lighting per_vertex; }", "lighting per_vertex { shininess 3; } }"))
  'Erro semântico: shininess só existe em lighting phong'

  Regras de âmbito: um nome de dentro esconde o de fora, e um template não vê os locais de quem o chama:

  >>> run_semantica('let a = 1; scene s { let a = (1, 2, 3); box b { translate a; } }')
  True
  >>> run_semantica('scene s { let x = 1; if 1 < 2 { let x = (1, 2, 3); box b { translate x; } } }')
  True
  >>> run_semantica('template t() { box b { scale (k, k, k); } } scene s { let k = 1; t(); }')
  'Erro semântico: Nome não declarado'
  >>> run_semantica('scene s { for i in 0..3 { } box b { scale (i, i, i); } }')
  'Erro semântico: Nome não declarado'

  Um caso para cada propriedade:

  >>> run_semantica('let a = b; let b = 2; camera c { near a; }')
  True
  >>> run_semantica('let a = b + 1; let b = a;')
  'Erro semântico: Dependência circular entre let'
  >>> run_semantica('scene s = grid length 1 divisions 1; camera s { }')
  'Erro semântico: Nome declarado mais de uma vez'
  >>> run_semantica('let red = 1;')
  'Erro semântico: As cores pré-definidas não podem ser declaradas de novo'
  >>> run_semantica('template t(h: num) { u(h); } template u(h: num) { t(h); }')
  'Erro semântico: Template recursivo'
  >>> run_semantica('scene s { let x = 1; box b { translate (x, 0, 0); } }')
  True
  >>> run_semantica('scene s { box b { translate (x, 0, 0); } let x = 1; }')
  'Erro semântico: Nome não declarado'
  >>> run_semantica('scene s { let x = 1; let x = 2; }')
  'Erro semântico: Nome declarado mais de uma vez'
  >>> run_semantica('scene s { if 1 < 2 { let x = 1; } box b { scale (x, x, x); } }')
  'Erro semântico: Nome não declarado'
  >>> run_semantica('template p(a: num, a: num) { }')
  'Erro semântico: Nome declarado mais de uma vez'
  >>> run_semantica('let v = (1, 2, 3); let c = red; scene s { box b : m { translate v; } } material m { diffuse c; }')
  True
  >>> run_semantica('let v = 1; scene s { box b { translate v; } }')
  'Erro semântico: Tipo errado'
  >>> run_semantica('camera t { } material m { layer day t; }')
  'Erro semântico: Tipo errado'
  >>> run_semantica('template p(m: num) { box b : m; }')
  'Erro semântico: Tipo errado'
  >>> run_semantica('material m { lighting phong; lighting toon; }')
  'Erro semântico: Um material só pode ter um lighting'
  >>> run_semantica('texture t = "a.jpg"; material m { layer day t; layer day t; }')
  'Erro semântico: Camada repetida no material'
  >>> run_semantica('texture t = "a.jpg"; material m { layer day t; layer specular t; }')
  'Erro semântico: A camada specular exige lighting phong'
  >>> run_semantica('texture t = "a.jpg"; material m { lighting none; layer day t; layer night t; }')
  'Erro semântico: A camada night exige um modo com luz'
  >>> run_semantica('texture t = "a.jpg"; material m { lighting phong; layer specular t; }')
  'Erro semântico: As camadas specular, night e clouds exigem uma camada day'
  >>> run_semantica('pass p { lighting phong { levels 3; } for all; }')
  'Erro semântico: levels só existe em lighting toon'
  """
  return verificar_semantica(data)


def aceita(p, data):
  try:
    p.parse(data)
    return True
  except UnexpectedInput:
    return False


def mesma_linguagem():
  """
  A gramática que o LarkAG gera aceita os mesmos programas que a gramática do Lark
  (as alterações da gramática para o LarkAG não mudam a linguagem).

  >>> programas = [f.read_text(encoding="utf-8") for f in EXEMPLOS] + [
  ...   'camera c { position (1, 2); }',
  ...   'material m { draw x; }',
  ...   'pass p { drawcam; }',
  ...   'scene s { if 1 < 2 { let x = 1; } else if 2 < 3 { } }',
  ... ]
  >>> [aceita(parser, p) == aceita(ag_parser, p) for p in programas]
  [True, True, True, True, True, True, True, True]
  """


if __name__ == "__main__":
  falhas, total = doctest.testmod()
  print(f"{total} testes, {falhas} falhas")
