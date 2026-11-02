# Caravela

Projeto Parte I de Engenharia Gramatical (MEI, 2026/27).

A **Caravela** é uma linguagem de domínio específico para descrever cenas 3D do
[Nau](https://github.com/Nau3D/nau), o motor gráfico usado em Visualização em Tempo Real.
No Nau, cada projeto é um conjunto de ficheiros de texto (`.xml`, `.mlib`, `.vert`, `.frag`)
ligados entre si por nomes que ninguém verifica: um nome mal escrito faz o objeto aparecer
preto, sem nenhum aviso. Em Caravela escreve-se um só programa, com os mesmos conceitos
(texturas, materiais, cenas, câmaras, luzes, passes), e a análise semântica verifica todas
essas ligações antes de se gerarem os ficheiros do Nau.

O projeto mais simples da aula 2 de VTR tem 175 linhas em 4 ficheiros. Em Caravela são 28
linhas num só ficheiro ([exemplos/1_iluminacao_simples.cav](exemplos/1_iluminacao_simples.cav)).

## Instalação

Requer Python 3.10 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilização

Verificar um programa (análise léxica, sintática e semântica):

```bash
python -m caravela exemplos/3_templo.cav
```

Se o programa estiver correto, mostra a tabela de símbolos global e as unidades de textura
calculadas para cada material. Se não, mostra o erro:

```
$ python -m caravela exemplos/3_templo.cav
exemplos/3_templo.cav: programa correto
  tabela de símbolos: {'n': 'num', 'raio': 'num', 'azul': 'material', 'branco': 'material', 'pilar': ('template', ('num', 'material')), ...}
  unidades de textura: {'azul': {}, 'branco': {}}
```

Opções: `--tokens` mostra os tokens do analisador léxico e `--arvore` mostra a árvore sintática.

Correr os testes:

```bash
pytest -q
```

Calcular as medidas de qualidade da gramática e da gramática de atributos:

```bash
python -m caravela.metricas
```

## Estrutura

```
caravela/
  gramatica.lark      léxico e gramática independente de contexto (Lark, LALR(1))
  gramatica_ag.lark   gramática de atributos (LarkAG)
  auxiliares.py       tipos e funções auxiliares usados pelas regras da gramática de atributos
  sintaxe.py          parser LALR construído a partir de gramatica.lark
  semantica.py        avaliação da gramática de atributos (análise semântica)
  metricas.py         medidas de qualidade da gramática
  __main__.py         linha de comandos
exemplos/             os quatro programas de exemplo
tests/                testes de sintaxe e de semântica (pytest)
```

## A linguagem

| Conceito | Em Caravela |
|---|---|
| Variável | `let raio = 4;` |
| Textura | `texture earth = "earthDay.jpg" mipmap;` |
| Material | `material azul { diffuse rgb(0.0, 0.34, 0.72); lighting phong { shininess 60; } }` |
| Iluminação | `lighting per_vertex;`, `lighting phong { ... }`, `lighting toon { levels 4; }`, `lighting none;` |
| Camada de textura | `layer day earth;`, `layer specular spec;`, `layer night eNight;`, `layer clouds noise speed 0.0001;` |
| Cena | `scene chao = grid length 20 divisions 2;` ou `scene templo { ... }` |
| Objeto | `box caixa : azul { translate (2, 0, 0); }` |
| Template | `template pilar(h: num, mat: material) { ... }` |
| Ciclo e condição | `for i in 0..n { ... }`, `if i % 2 == 0 { ... } else { ... }` |
| Câmara e luz | `camera cam { position (8, 6, 8); look_at (0, 1, 0); }`, `light sol directional { ... }` |
| Passe | `pass render { draw templo, chao; camera cam; lights sol; }` |

O utilizador não escreve shaders: cada material diz só o efeito que quer (`lighting`, `layer`)
e o compilador escolhe o shader e faz as ligações com o `.mlib`.

Exemplo ([exemplos/3_templo.cav](exemplos/3_templo.cav)): oito pilares em círculo, que alternam
entre duas alturas e dois materiais.

```
let n    = 8;
let raio = 4;

material azul   { diffuse rgb(0.0, 0.34, 0.72); lighting phong { shininess 60; } }
material branco { diffuse white;                lighting per_vertex; }

template pilar(h: num, mat: material) {
    box p : mat {
        scale     (0.5, h, 0.5);
        translate (0, h / 2, 0);
    }
}

scene templo {
    for i in 0..n {
        let ang = i * 360 / n;
        if i % 2 == 0 {
            pilar(3, azul)   { rotate ang around (0, 1, 0); translate (raio, 0, 0); }
        } else {
            pilar(2, branco) { rotate ang around (0, 1, 0); translate (raio, 0, 0); }
        }
    }
}
...
```

| Exemplo | Original (aulas de VTR) | Caravela |
|---|---|---|
| [1. Iluminação simples](exemplos/1_iluminacao_simples.cav) (aula 2) | 175 linhas, 4 ficheiros | 28 linhas |
| [2. Iluminação por píxel](exemplos/2_iluminacao_por_pixel.cav) (aula 2) | 191 linhas, 4 ficheiros | 34 linhas, com os três modos |
| [3. Templo com pilares](exemplos/3_templo.cav) (cena nova) | — | 38 linhas |
| [4. Texturas da Terra](exemplos/4_terra.cav) (aula 3) | 232 linhas, 4 ficheiros + `noise.frag` | 33 linhas |

## Léxico e sintaxe

A gramática está em [caravela/gramatica.lark](caravela/gramatica.lark). O parser é LALR(1),
com `lexer="basic"` e `strict=True`, por isso o Lark recusa a gramática se houver algum conflito.

- Identificadores `[a-zA-Z_][a-zA-Z0-9_]*`, números sem sinal (o `-` é um operador), texto entre aspas,
  comentários `//` e `/* */`. Há 58 palavras reservadas.
- As cores (`white`, `red`, ...) não são palavras reservadas: são identificadores que já estão
  no ambiente inicial da análise semântica.
- Os blocos `if` e `for` usam sempre chavetas, por isso não há o problema do *else* pendente.
- Há um `if` por contexto (`scene_if`, `pass_if`), para que a sintaxe impeça itens no sítio errado
  (por exemplo, um `draw` dentro de uma cena é um erro de sintaxe).
- As expressões seguem o esquema `num / term / factor` das aulas, para dar a precedência e a
  associatividade à esquerda.

## Semântica: gramática de atributos

A gramática de atributos está em [caravela/gramatica_ag.lark](caravela/gramatica_ag.lark) e é
executada com LarkAG. Verifica estas propriedades:

| Propriedade | Mensagem de erro |
|---|---|
| Nomes declarados e visíveis | `Nome não declarado` |
| Sem declarações repetidas no mesmo âmbito | `Nome declarado mais de uma vez` |
| As cores pré-definidas não podem ser redeclaradas | `As cores pré-definidas não podem ser declaradas de novo` |
| `let` locais só depois da declaração; âmbitos de `for`, `if` e `template` | `Nome não declarado` |
| `let` globais sem dependências circulares | `Dependência circular entre let` |
| Tipos das referências (`draw` só cenas, `layer` só texturas, `translate v` exige um `vec3`, ...) | `Tipo errado` |
| Argumentos de um template com o tipo dos parâmetros | `Argumentos do template com tipo errado` |
| Templates não recursivos | `Template recursivo` |
| Coerência do material (um só `lighting`, `shininess` só em `phong`, `specular` exige `phong`, ...) | várias |
| Unidades de textura de cada camada | calculadas (atributo `unidades`) |

**Ideia geral: os usos sobem, os nomes locais descem.** Cada sítio onde aparece um nome produz
um *uso* `(nome, tipo esperado)`.

- Os nomes **locais** (`let` dentro de uma cena, variável do `for`, parâmetros de um `template`)
  só são visíveis depois da declaração. Descem da esquerda para a direita no atributo herdado `env`,
  e os usos que encontram um nome em `env` são verificados logo ali.
- Os nomes **globais** podem ser usados antes de serem declarados. Os usos que sobram sobem até à
  raiz no atributo sintetizado `usos`, e é em `start` que são comparados com a tabela de símbolos
  global (`tabela`), também sintetizada.

As regras de `sceneitems` (lista recursiva à esquerda) mostram esta dependência:

```
sceneitems₀ → sceneitems₁ sceneitem
  sceneitems₁.env  = sceneitems₀.env
  sceneitem.env    = sceneitems₀.env ⊕ sceneitems₁.locais
  sceneitems₀.locais = sceneitems₁.locais ⊕ sceneitem.locais
  sceneitems₀.usos   = sceneitems₁.usos ++ sceneitem.usos
```

Por exemplo, em `scene s { let a = 1; box b { translate (a, 0, 0); } }` o primeiro item sintetiza
`locais = {a ↦ num}`, que entra no `env` do segundo. O uso `(a, num)` do `translate` é resolvido
nesse item e não chega à raiz. Com os itens pela ordem inversa, o uso sobe até `start` e dá
`Nome não declarado`. Como cada `env` depende só dos irmãos à esquerda, a gramática é
L-atribuída e avalia-se numa só visita.

Para usar a gramática em LarkAG foi preciso transformá-la sem mudar a linguagem aceite (há um
teste que o confirma): nomes de regras sem `_`, listas com atributos herdados recursivas à
esquerda, o `..` como literal e partes opcionais com atributos passadas a alternativas.

Não verificamos os valores válidos (`near > 0`, `levels >= 2`, ...), porque para isso seria
preciso avaliar as expressões.

## Testes

[tests/test_sintaxe.py](tests/test_sintaxe.py) testa o léxico, programas corretos e com erros de
sintaxe, e que a gramática do LarkAG aceita a mesma linguagem.
[tests/test_semantica.py](tests/test_semantica.py) tem um caso para cada propriedade semântica,
os erros referidos no exemplo 3 (`pilar(3, azl)`, `pilar(azul, 3)`, `ang` fora do ciclo,
`draw templo, cam`, `shininess` sem `phong`) e as unidades de textura do exemplo 4.

## Qualidade

`python -m caravela.metricas` calcula as medidas de tamanho e estrutura de Power e Malloy (2004).
Resultados principais:

| Medida | Gramática | Gramática de atributos |
|---|---|---|
| Não-terminais / terminais | 71 / 76 | — |
| Produções BNF / estados LALR | 174 / 330 | — |
| Complexidade de McCabe (MCC) | 83 | — |
| Profundidade (HEI) | 11 | — |
| Atributos sintetizados / herdados | — | 102 / 6 |
| Equações (cópias / constantes / calculadas) | — | 222 (89 / 41 / 92) |
| Condições de contexto | — | 25 |

O maior nível da gramática (`scene_item`, `scene_for`, `scene_if`, `scene_block`) é o único ciclo
relevante e corresponde ao aninhamento de cenas, ciclos e condições.
