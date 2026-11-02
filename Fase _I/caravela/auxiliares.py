# Tipos e funções auxiliares usados nas regras da gramática de atributos.
# Um "uso" é um tuplo (nome, tipo esperado, tipos dos argumentos ou None).

K_NUM, K_VEC3, K_COLOR, K_MATERIAL = "num", "vec3", "color", "material"
K_SCENE, K_CAMERA, K_LIGHT, K_TEXTURE = "scene", "camera", "light", "texture"
K_TEMPLATE, K_PASS, K_ANY, REF = "template", "pass", "any", "ref"
K_NONE, K_PHONG, K_TOON = "none", "phong", "toon"
K_DAY, K_SPECULAR, K_NIGHT = "day", "specular", "night"
K_SHININESS, K_LEVELS = "shininess", "levels"

# ambiente inicial: as cores pré-definidas
PRE = {c: K_COLOR for c in ["white", "black", "red", "green", "blue", "yellow", "grey"]}

# tipos que um valor (let, argumento de template) pode ter
VALORES = {K_NUM, K_VEC3, K_COLOR, K_MATERIAL}

def ref(t):
  """O tipo é uma referência a outro nome, ainda por resolver (let x = y;)."""
  return isinstance(t, tuple) and t[0] == REF

def compativel(t, esperado):
  if esperado == K_ANY:
    return t in VALORES
  if esperado == K_TEMPLATE:
    return isinstance(t, tuple) and t[0] == K_TEMPLATE
  return t == esperado

def _resolver(usos, env):
  """Resolve os usos com os nomes locais de env. Devolve (usos que sobem, nomes com tipo errado)."""
  resto, erros = [], []
  for nome, esperado, args in usos:
    if args is not None:
      args = tuple(env.get(t[1], t) if ref(t) else t for t in args)
    if nome not in env:
      resto.append((nome, esperado, args))
    elif ref(env[nome]):
      resto.append((env[nome][1], esperado, args))
    elif not compativel(env[nome], esperado):
      erros.append(nome)
  return resto, erros

def resto(usos, env):
  return _resolver(usos, env)[0]

def tipos_ok(usos, env):
  return not _resolver(usos, env)[1]

def tipo_local(t, env):
  return env.get(t[1], t) if ref(t) else t

def tipos_globais(nomes):
  """Tabela de símbolos global: nome -> tipo, com as referências entre let resolvidas."""
  brutos = dict(PRE)
  brutos.update({n: t for n, t, deps in nomes})
  def tipo(n, vistos):
    t = brutos.get(n)
    if ref(t):
      return None if t[1] in vistos else tipo(t[1], vistos | {t[1]})
    return t
  return {n: tipo(n, {n}) for n in brutos}

def sem_repetidos(lista):
  return len(lista) == len(set(lista))

def tem_ciclo(grafo):
  estado = {}
  def visita(n):
    if estado.get(n) == 1:
      return True
    if estado.get(n) == 2:
      return False
    estado[n] = 1
    if any(visita(m) for m in grafo[n] if m in grafo):
      return True
    estado[n] = 2
    return False
  return any(visita(n) for n in grafo)

def argumentos_ok(usos, tabela):
  for nome, esperado, args in usos:
    if esperado == K_TEMPLATE and compativel(tabela.get(nome), K_TEMPLATE):
      reais = tuple(tabela.get(t[1]) if ref(t) else t for t in args)
      if None not in reais and reais != tabela[nome][1]:
        return False
  return True
