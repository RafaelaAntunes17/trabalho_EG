"""Testes da análise semântica (gramatica_ag.lark)."""

from pathlib import Path

import pytest

from caravela.semantica import analisar, verificar_semantica

PASTA = Path(__file__).parent.parent / "exemplos"
EXEMPLOS = sorted(PASTA.glob("*.cav"))
TEMPLO = (PASTA / "3_templo.cav").read_text(encoding="utf-8")

# os erros referidos no exemplo 3: (texto original, texto com erro), mensagem
ERROS_TEMPLO = [
  (("pilar(3, azul)", "pilar(3, azl)"), 'Erro semântico: Nome não declarado'),
  (("pilar(3, azul)", "pilar(azul, 3)"), 'Erro semântico: Argumentos do template com tipo errado'),
  (("draw   templo, chao;", "draw   templo, chao;  if ang > 0 { }"), 'Erro semântico: Nome não declarado'),
  (("draw   templo, chao;", "draw   templo, cam;"), 'Erro semântico: Tipo errado'),
  (("lighting per_vertex; }", "lighting per_vertex { shininess 3; } }"), 'Erro semântico: shininess só existe em lighting phong'),
]

# um caso para cada propriedade semântica
CASOS = [
  ('let a = b; let b = 2; camera c { near a; }', True),
  ('let a = b + 1; let b = a;', 'Erro semântico: Dependência circular entre let'),
  ('scene s = grid length 1 divisions 1; camera s { }', 'Erro semântico: Nome declarado mais de uma vez'),
  ('let red = 1;', 'Erro semântico: As cores pré-definidas não podem ser declaradas de novo'),
  ('template t(h: num) { u(h); } template u(h: num) { t(h); }', 'Erro semântico: Template recursivo'),
  ('scene s { let x = 1; box b { translate (x, 0, 0); } }', True),
  ('scene s { box b { translate (x, 0, 0); } let x = 1; }', 'Erro semântico: Nome não declarado'),
  ('scene s { let x = 1; let x = 2; }', 'Erro semântico: Nome declarado mais de uma vez'),
  ('scene s { if 1 < 2 { let x = 1; } box b { scale (x, x, x); } }', 'Erro semântico: Nome não declarado'),
  ('template p(a: num, a: num) { }', 'Erro semântico: Nome declarado mais de uma vez'),
  ('let v = (1, 2, 3); let c = red; scene s { box b : m { translate v; } } material m { diffuse c; }', True),
  ('let v = 1; scene s { box b { translate v; } }', 'Erro semântico: Tipo errado'),
  ('camera t { } material m { layer day t; }', 'Erro semântico: Tipo errado'),
  ('template p(m: num) { box b : m; }', 'Erro semântico: Tipo errado'),
  ('material m { lighting phong; lighting toon; }', 'Erro semântico: Um material só pode ter um lighting'),
  ('texture t = "a.jpg"; material m { layer day t; layer day t; }', 'Erro semântico: Camada repetida no material'),
  ('texture t = "a.jpg"; material m { layer day t; layer specular t; }', 'Erro semântico: A camada specular exige lighting phong'),
  ('texture t = "a.jpg"; material m { lighting none; layer day t; layer night t; }', 'Erro semântico: A camada night exige um modo com luz'),
  ('texture t = "a.jpg"; material m { lighting phong; layer specular t; }', 'Erro semântico: As camadas specular, night e clouds exigem uma camada day'),
  ('pass p { lighting phong { levels 3; } for all; }', 'Erro semântico: levels só existe em lighting toon'),
]


@pytest.mark.parametrize("ficheiro", EXEMPLOS, ids=lambda f: f.name)
def test_exemplos_semanticamente_corretos(ficheiro):
  assert verificar_semantica(ficheiro.read_text(encoding="utf-8")) is True


@pytest.mark.parametrize("troca, esperado", ERROS_TEMPLO)
def test_erros_do_templo(troca, esperado):
  assert verificar_semantica(TEMPLO.replace(*troca)) == esperado


@pytest.mark.parametrize("codigo, esperado", CASOS)
def test_semantica(codigo, esperado):
  assert verificar_semantica(codigo) == esperado


def test_unidades_de_textura():
  # day, specular e night recebem as unidades 0, 1 e 2; clouds usa ruído e não recebe nenhuma
  raiz = analisar((PASTA / "4_terra.cav").read_text(encoding="utf-8"))
  assert raiz.materiais == {"textured": {"day": 0, "specular": 1, "night": 2}}
