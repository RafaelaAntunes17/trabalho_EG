# Caravela: uma linguagem para descrever cenas 3D

Trabalho da Parte I de Engenharia Gramatical (MEI, Universidade do Minho, 2026/27).

| Grupo | Número |
|---|---|
| Rafaela Antunes | PG62934 |
| Tomás Pinto | PG64038 |
| Mounika Gopi | PG64009 |

A Caravela descreve cenas 3D para o motor Nau e verifica-as antes de chegarem ao Nau. O léxico e a
sintaxe estão em [`caravela/gramatica.lark`](caravela/gramatica.lark), e a semântica está em
[`caravela/gramatica_ag.lark`](caravela/gramatica_ag.lark).

Conteúdo:

1. [A linguagem](#linguagem-caravela): [o problema](#problema), [objetivos](#metas), [construções](#construcoes-caravela), [âmbitos](#ambitos), [exemplo](#exemplo-templo) e [requisitos](#requisitos)
2. [Léxico e gramática](#lexico-gramatica): [tokens](#tokens) e [regras](#regras)
3. [Semântica](#verificacao): [o que é verificado](#verificacoes), [atributos](#atributos-caravela) e [como corre](#corre-larkag)
4. [Avaliação da qualidade](#avaliacao)
5. [Como correr o projeto](#correr): [instalar](#instalar), [usar](#usar), [testar](#testar) e [estrutura](#pastas)
6. [Limitações](#limitacoes)

<a id="linguagem-caravela"></a>
## 1. A linguagem

<a id="problema"></a>
### 1.1 O problema que resolve

A Caravela é uma linguagem para descrever cenas 3D do Nau, o motor gráfico que usamos em
Visualização em Tempo Real (VTR).

No Nau não se programa o motor. Cada trabalho é um conjunto de ficheiros de texto que o Nau lê:
o projeto (`.xml`) com os objetos, a câmara e as luzes, a biblioteca de materiais (`.mlib`) e os
shaders (`.vert` e `.frag`). Estes ficheiros ligam-se uns aos outros por nomes. Se o nome de um
uniform estiver mal escrito, o Nau não pára: a cena abre na mesma, mas com o aspeto errado (cor a
zero ou textura errada). O aviso só aparece no log, depois de o projeto carregar e no meio de muitas
outras mensagens.

A ideia da Caravela é escrever a cena num só ficheiro, com os mesmos conceitos (texturas,
materiais, cenas, câmaras, luzes e passes), e verificar todas essas ligações antes de chegar ao
Nau. Nesta Parte I fizemos o léxico, a gramática e a gramática de atributos. A geração dos
ficheiros do Nau fica para a Parte II.

<a id="metas"></a>
### 1.2 Objetivos

Temos três objetivos:

1. Escrever menos. Cada elemento da cena é declarado uma vez, num bloco com nome, e o que é
   repetitivo (incluindo os shaders) será gerado na Parte II. O projeto mais simples da aula 2 tem 175
   linhas em 4 ficheiros. Em Caravela são 28 linhas
   ([`1_iluminacao_simples.cav`](exemplos/1_iluminacao_simples.cav)).
2. Detetar os erros antes de chegar ao Nau: verificar se cada nome existe e se é do tipo certo
   (um passe só desenha cenas, o `shininess` só existe na iluminação `phong`, ...).
3. Fazer cenas com variáveis, ciclos, condições e templates, que o XML do Nau não tem.

A linguagem é pensada para os alunos de VTR e, em geral, para quem monta no Nau as cenas das aulas,
ou variações delas, e quer saber dos erros nos nomes antes de abrir o Nau, em vez de os procurar à
mão. Hoje, um uniform mal escrito no `.mlib` não pára o Nau: desenha na mesma com um valor por
omissão, e o aviso fica no log, no meio de muitas outras mensagens. A Caravela recusa o programa
antes de chegar ao Nau.

Limitámos a linguagem ao que foi dado nas aulas 2 (iluminação) e 3 (texturas) de VTR, porque o Nau
é muito grande. Sombras, vários passes encadeados e shaders escritos à mão ficam de fora. O nome
vem do próprio motor: a caravela era um barco mais pequeno e mais fácil de manobrar do que a nau.

<a id="construcoes-caravela"></a>
### 1.3 Construções

| Conceito | Em Caravela |
|---|---|
| Variável | `let raio = 4;` |
| Textura | `texture earth = "earthDay.jpg" mipmap;` |
| Material | `material azul { diffuse rgb(0.0, 0.34, 0.72); lighting phong { shininess 60; } }` |
| Iluminação | `lighting per_vertex;`, `lighting phong { ... }`, `lighting toon { levels 4; }`, `lighting none;` |
| Camada de textura | `layer day earth;`, `layer specular spec;`, `layer night eNight;`, `layer clouds noise;` |
| Cena | `scene chao = grid length 20 divisions 2;` ou `scene templo { ... }` |
| Objeto | `box caixa : azul { translate (2, 0, 0); }` |
| Template | `template pilar(h: num, mat: material) { ... }` |
| Ciclo e condição | `for i in 0..n { ... }`, `if i % 2 == 0 { ... } else { ... }` |
| Câmara e luz | `camera cam { position (8, 6, 8); look_at (0, 1, 0); }`, `light sol directional { ... }` |
| Passe | `pass render { draw templo, chao; camera cam; lights sol; }` |

Como estas construções servem o objetivo:

- Declarações com nome. Tudo o que no Nau se liga por nomes (texturas, materiais, cenas,
  câmaras, luzes) é declarado com um nome e usado através dele. Continua a ser uma ligação por
  nomes, mas agora está tudo no mesmo programa, por isso dá para ter uma tabela de símbolos e
  verificar cada referência.
- Efeitos em vez de shaders. Quem usa a Caravela não escreve shaders. No material diz-se só o
  efeito que se quer (`lighting phong`, `layer night`) e o compilador da Parte II escolhe o shader
  e escreve as ligações com o `.mlib`. Assim desaparecem os nomes de uniforms trocados e as
  unidades de textura erradas. Em troca, há combinações que não fazem sentido (por exemplo
  `layer specular` sem `phong`), e a gramática de atributos verifica-as.
- Blocos aninhados. Uma cena tem objetos e cada objeto tem as suas transformações, por isso o
  programa tem a mesma forma em árvore que a própria cena.
- Variáveis, ciclos, condições e templates. O XML só aceita valores fixos. Com `let`, `for`, `if`
  e `template` escreve-se uma vez o que no XML se repete, e o compilador da Parte II desenrola
  tudo antes de gerar os ficheiros.

<a id="ambitos"></a>
### 1.4 Âmbitos e valores

A Caravela tem âmbito estático (léxico): o que um nome quer dizer depende só de onde está escrito
no programa.

- Âmbito global: as declarações de topo (`let`, `texture`, `material`, `scene`, `template`,
  `camera`, `light`, `pass`). Podem ser usadas antes de serem declaradas, porque a ordem das
  declarações é livre, como no XML do Nau. Não pode haver dois nomes globais iguais.
- Âmbitos locais: o corpo de uma cena, o corpo do `for` (com a variável do ciclo), cada ramo do
  `if` e o corpo de um `template` (com os parâmetros). Um `let` local só existe da sua declaração
  até ao fim do bloco, e não pode haver dois `let` com o mesmo nome no mesmo bloco. Os nomes dos
  objetos não são verificados, porque o `box p` de um `for` se repete de propósito.
- Um nome declarado num bloco interior esconde o mesmo nome de fora (um global, ou um local de um
  bloco que o contém).
- O corpo de um `template` vê os nomes globais e os seus parâmetros, mas não os nomes locais de
  quem o chama.
- As cores pré-definidas (`white`, `black`, `red`, `green`, `blue`, `yellow`, `grey`) estão sempre
  visíveis e não podem ser declaradas de novo.

Os valores são números, vetores `(x, y, z)` e cores `rgb(r, g, b)`, e calculam-se com expressões
(`+`, `-`, `*`, `/`, `%`) e comparações (`==`, `!=`, `<`, `<=`, `>`, `>=`). Um `let` dá um nome a
um valor e não se pode reatribuir, tal como nas expressões com `let` da EX04. O "estado" que muda
é o da cena que se vai construindo: dentro de um `for` o `let` volta a ser calculado em cada
iteração (`let ang = i * 360 / n;`).

<a id="exemplo-templo"></a>
### 1.5 Exemplo: o templo

Temos quatro exemplos em [`exemplos/`](exemplos/). Três são projetos das aulas de VTR reescritos e o
templo é uma cena nova, para mostrar os templates, os ciclos e as condições:

```
let n    = 8;
let raio = 4;

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
```

| Exemplo | Original (aulas de VTR) | Caravela |
|---|---|---|
| [`Iluminação simples`](exemplos/1_iluminacao_simples.cav) (aula 2) | 175 linhas, 4 ficheiros | 28 linhas |
| [`Iluminação por píxel`](exemplos/2_iluminacao_por_pixel.cav) (aula 2) | 191 linhas, 4 ficheiros | 34 linhas |
| [`Templo`](exemplos/3_templo.cav) (cena nova) | não existe | 38 linhas |
| [`Texturas da Terra`](exemplos/4_terra.cav) (aula 3) | 232 linhas, 4 ficheiros, mais 133 do `noise.frag` | 33 linhas |

<a id="requisitos"></a>
### 1.6 Requisitos do enunciado

O enunciado pede alguns requisitos mínimos. Estão aqui:

| Requisito | Na Caravela |
|---|---|
| Variáveis e declarações | `let`, `texture`, `material`, `scene`, `camera`, `light`, `pass`, `template` |
| Âmbitos | global, corpo do `for`, ramos do `if`, corpo do `template` (ver "Âmbitos e valores") |
| Expressões | contas em posições, ângulos e cores, comparações nos `if` |
| Construções aninhadas | cena → objeto → transformações; material → iluminação e camadas |
| Ramificação e repetição | `if` / `else if` / `else` e `for i in 0..n` |
| Semântica que a sintaxe não vê | nomes, tipos, argumentos dos templates, ciclos entre `let`, coerência dos materiais |

---

<a id="lexico-gramatica"></a>
## 2. Léxico e gramática

<a id="tokens"></a>
### 2.1 Tokens

O léxico e a gramática estão em [`caravela/gramatica.lark`](caravela/gramatica.lark), escritos em
EBNF do Lark.

#### Estrutura léxica

| Categoria | Expressão regular | Exemplos | Observações |
|---|---|---|---|
| Identificador (`ID`) | `[a-zA-Z_][a-zA-Z0-9_]*` | `teapot_s`, `MainCamera`, `raio` | não pode ser uma palavra reservada |
| Número (`NUMBER`) | `[0-9]+(\.[0-9]+)?` | `8`, `0.01`, `1.46` | sem sinal; o `-` é o operador `SUB` |
| Texto (`STRING`) | `"[^"\n]*"` | `"models/teapot.obj"` | caminhos dos modelos e das texturas |
| Comparação (`CMP_OP`) | `== \| != \| <= \| >= \| < \| >` | `i % 2 == 0` | só nas condições do `if` |
| Soma e subtração | `+` (`ADD`), `-` (`SUB`) | `b + 1`, `-1` | o `-` serve para subtrair e para negar |
| Multiplicação (`MUL_OP`) | `* \| / \| %` | `i * 45`, `i % 2` | multiplicação, divisão e resto |
| Intervalo (`_RANGE`) | `..` | `0..n` | no `for`; não aparece na árvore |
| Pontuação | `; , : = ( ) { }` | `(1, 0, 2)` | blocos, vetores e listas |
| Comentário (`COMMENT`) | `//[^\n]* \| /\*(.\|\n)*?\*/` | `// nota`, `/* bloco */` | ignorado |

Os espaços, tabs e mudanças de linha também são ignorados.

Há 58 palavras reservadas:

- declarações e controlo: `project`, `let`, `texture`, `material`, `scene`, `template`, `camera`,
  `light`, `background`, `pass`, `if`, `else`, `for`, `in`;
- materiais: `diffuse`, `lighting`, `none`, `per_vertex`, `phong`, `toon`, `shininess`, `levels`,
  `layer`, `day`, `specular`, `night`, `clouds`, `noise`, `speed`, `mipmap`;
- cenas e geometria: `model`, `grid`, `length`, `divisions`, `unitize`, `swap_yz`, `box`, `sphere`,
  `square`, `axis`, `translate`, `scale`, `rotate`, `around`;
- câmara, luz e passes: `position`, `look_at`, `direction`, `near`, `far`, `fov`, `directional`,
  `color`, `draw`, `lights`, `all`;
- tipos e valores: `num`, `vec3`, `rgb`.

O `0..n` não se confunde com um número decimal, porque o `NUMBER` obriga a ter dígitos depois do
ponto. E `-2` dá dois tokens (`SUB` e `NUMBER`), por isso `a - 2` e `a -2` leem-se da mesma maneira.

<a id="regras"></a>
### 2.2 Regras

Decisões que tomámos:

- Usamos `parser="lalr"`, porque a gramática é LALR(1) (NB05). Com `strict=True`, o Lark dá
  erro se houver algum conflito, em vez de escolher *shift* sozinho. Assim sabemos que a gramática
  não tem conflitos.
- Usamos `lexer="basic"`, que parte primeiro o texto em tokens inteiros. Sem isto, `drawcam;` era
  lido como `draw cam;`.
- As expressões seguem o esquema `expr` / `term` / `factor` das aulas (aqui `num` / `term` /
  `factor`), recursivo à esquerda, para ter a precedência e a associatividade certas.
- Os blocos do `if` e do `for` levam sempre chavetas, por isso não há o problema do *else* pendente.
  O `else if` é só um `else` seguido de outro `if`.
- Há um `if` para as cenas e outro para os passes. Assim, um `draw` dentro de uma cena é logo um
  erro de sintaxe.
- As cores (`white`, `red`, ...) não são palavras reservadas, são `ID`. Estão no ambiente inicial
  da análise semântica, e para acrescentar uma cor não é preciso mexer na gramática.

#### Gramática completa

A gramática está em EBNF do Lark, tal como em [`gramatica.lark`](caravela/gramatica.lark). Os terminais estão na secção 2.1.

<details>
<summary>Ver as regras da gramática</summary>

```lark
// ---------- Programa ----------
start: project? decl*

project: "project" STRING ";"

decl: let_decl
    | texture_decl
    | material_decl
    | scene_decl
    | template_decl
    | camera_decl
    | light_decl
    | background_decl
    | pass_decl

let_decl: "let" ID "=" value ";"

// ---------- Texturas e materiais ----------
texture_decl: "texture" ID "=" STRING MIPMAP? ";"

material_decl: "material" ID "{" mat_item* "}"

mat_item: diffuse
        | mat_lighting
        | layer

diffuse: "diffuse" color_val ";"

mat_lighting: "lighting" lighting_mode (lighting_params | ";")

lighting_mode: NONE
             | PER_VERTEX
             | PHONG
             | TOON

lighting_params: "{" lighting_param* "}"

lighting_param: shininess
              | levels

shininess: "shininess" num ";"

levels: "levels" num ";"

layer: "layer" layer_role layer_source ";"

layer_role: DAY
          | SPECULAR
          | NIGHT
          | CLOUDS

layer_source: ID
            | noise

noise: "noise" ("speed" num)?

// ---------- Cenas e templates ----------
scene_decl: "scene" ID "=" scene_source ";"
          | "scene" ID "{" scene_item* "}"

scene_source: model
            | grid

model: "model" STRING model_option*

model_option: UNITIZE
            | SWAP_YZ

grid: "grid" "length" num "divisions" num

scene_item: object
          | template_call
          | let_decl
          | scene_for
          | scene_if

object: shape ID (":" ID)? object_body

shape: BOX
     | SPHERE
     | SQUARE
     | AXIS

template_call: ID "(" args? ")" object_body

object_body: "{" transform* "}"
           | ";"

transform: translate
         | scale
         | rotate

translate: "translate" vec3_val ";"

scale: "scale" vec3_val ";"

rotate: "rotate" num "around" vec3_val ";"

scene_for: "for" ID "in" num _RANGE num "{" scene_item* "}"

scene_if: "if" cond scene_block ("else" (scene_block | scene_if))?

scene_block: "{" scene_item* "}"

template_decl: "template" ID "(" params? ")" "{" scene_item* "}"

params: param
      | params "," param

param: ID ":" type

type: NUM
    | VEC3
    | COLOR
    | MATERIAL

args: value
    | args "," value

// ---------- Câmara, luz e fundo ----------
camera_decl: "camera" ID "{" camera_prop* "}"

camera_prop: position
           | look_at
           | direction
           | near
           | far
           | fov

position: "position" vec3_val ";"

look_at: "look_at" vec3_val ";"

direction: "direction" vec3_val ";"

near: "near" num ";"

far: "far" num ";"

fov: "fov" num ";"

light_decl: "light" ID "directional" "{" light_prop* "}"

light_prop: direction
          | light_color

light_color: "color" color_val ";"

background_decl: "background" color_val ";"

// ---------- Passes ----------
pass_decl: "pass" ID "{" pass_item* "}"

pass_item: draw
         | pass_camera
         | pass_lights
         | pass_lighting
         | pass_material
         | pass_if

draw: "draw" id_list ";"

pass_camera: "camera" ID ";"

pass_lights: "lights" id_list ";"

pass_lighting: "lighting" lighting_mode lighting_params? "for" "all" ";"

pass_material: "material" ID "for" "all" ";"

pass_if: "if" cond pass_block ("else" (pass_block | pass_if))?

pass_block: "{" pass_item* "}"

id_list: ID
       | id_list "," ID

// ---------- Valores ----------
// Cada propriedade diz que tipo de valor aceita:
//   num    números e contas      shininess 100;   near 0.1;   rotate i * 45 ...
//   vec3   vetores (x, y, z)     position (1, 2, 3);
//   color  cores                 diffuse rgb(1, 0.87, 0);   background white;
//   cond   condições             if i % 2 == 0 { ... }

// números: como expr / term / factor nas aulas
num: num ADD term
   | num SUB term
   | term

term: term MUL_OP factor
    | factor

factor: NUMBER
      | ID
      | SUB factor
      | "(" num ")"

vec3: "(" num "," num "," num ")"

color: "rgb" vec3

cond: num CMP_OP num

// numa propriedade, em vez do valor pode vir uma variável
// (ou uma cor pré-definida: white, red, ... são ID)
vec3_val: vec3
        | ID

color_val: color
         | ID

// let e argumentos de templates aceitam qualquer tipo
value: num
     | vec3
     | color
```

</details>

<a id="verificacao"></a>
## 3. Semântica

<a id="verificacoes"></a>
### 3.1 O que é verificado

A gramática de atributos está em [`caravela/gramatica_ag.lark`](caravela/gramatica_ag.lark) e corre
com o LarkAG, como na EX04. Verifica estas propriedades (as mensagens são as das condições de
contexto):

| Propriedade | Mensagem |
|---|---|
| Nomes declarados e visíveis | `Nome não declarado` |
| Sem declarações repetidas no mesmo âmbito | `Nome declarado mais de uma vez` |
| As cores pré-definidas não podem ser redeclaradas | `As cores pré-definidas não podem ser declaradas de novo` |
| `let` locais só depois da declaração; âmbitos do `for`, `if` e `template` | `Nome não declarado` |
| `let` globais sem dependências circulares | `Dependência circular entre let` |
| Tipos das referências (`draw` só aceita cenas, `layer` só texturas, ...) | `Tipo errado` |
| Argumentos de um template com o tipo dos parâmetros | `Argumentos do template com tipo errado` |
| Templates não recursivos | `Template recursivo` |
| Coerência dos materiais (um só `lighting`, `shininess` só em `phong`, ...) | várias |

Além disso, a gramática de atributos calcula a unidade de textura de cada camada (atributo
`unidades`). No exemplo da Terra, `day`, `specular` e `night` ficam com as unidades 0, 1 e 2.

Não verificamos os valores (por exemplo `near > 0`), porque para isso era preciso avaliar as
expressões com um atributo `val`, como no exemplo das aulas.

<a id="atributos-caravela"></a>
### 3.2 Gramática de atributos

#### Ideia: os usos sobem, os nomes locais descem

Cada sítio onde aparece um nome dá um *uso*: o nome e o tipo que se espera. Por exemplo,
`draw templo;` dá o uso `(templo, scene)`.

- Os nomes locais (um `let` dentro de uma cena, a variável do `for`, os parâmetros de um
  `template`) só existem depois de declarados. Passam da esquerda para a direita num atributo
  herdado `env`, como o `env` do exemplo das expressões com `let` da EX04. Os usos destes nomes
  são verificados logo ali.
- Os nomes globais podem ser usados antes de serem declarados (a ordem das declarações é livre,
  como no XML do Nau). Por isso os usos que sobram sobem até à raiz no atributo sintetizado `usos`
  e são comparados em `start` com a tabela de símbolos (`tabela`), que também é sintetizada.

Alguns dos atributos, com a notação das aulas:

- `A(start) = { (nomes, sintetizado), (usos, sintetizado), (tabela, sintetizado), (materiais, sintetizado) }`
- `A(sceneitems) = { (usos, sintetizado), (locais, sintetizado), (env, herdado) }`
- `A(sceneitem) = { (usos, sintetizado), (locais, sintetizado), (env, herdado) }`
- `A(scenefor) = { (usos, sintetizado), (env, herdado) }`
- `A(materialdecl) = { (nomes, sintetizado), (usos, sintetizado), (modos, sintetizado), (papeis, sintetizado), (unidades, sintetizado) }`

| Produção | Regras de avaliação | Condições de contexto |
|---|---|---|
| `sceneitems₀ → sceneitems₁ sceneitem` | `sceneitems₁.env = sceneitems₀.env` | `dom(sceneitem.locais) ∩ dom(sceneitems₁.locais) = ∅` |
| | `sceneitem.env = sceneitems₀.env ⊕ sceneitems₁.locais` | |
| | `sceneitems₀.locais = sceneitems₁.locais ⊕ sceneitem.locais` | |
| | `sceneitems₀.usos = sceneitems₁.usos ++ sceneitem.usos` | |
| `sceneitems → ε` | `sceneitems.locais = {}`, `sceneitems.usos = []` | |
| `sceneitem → letdecl` | `sceneitem.locais = {letdecl.nome ↦ letdecl.tipo}` | os usos do `letdecl` que estão em `env` têm o tipo certo |
| | `sceneitem.usos = usos do letdecl que não estão em env` | |
| `scenefor → for ID in num₁ .. num₂ { sceneitems }` | `sceneitems.env = scenefor.env ⊕ {ID ↦ num}` | |
| `start → project? decl*` | `start.tabela = cores ⊕ nomes de todas as declarações` | cada uso de `start.usos` está em `start.tabela` com o tipo certo |

Por exemplo, em `scene s { let a = 1; box b { translate (a, 0, 0); } }` o primeiro item
sintetiza `locais = {a ↦ num}`, que passa a fazer parte do `env` do segundo. O uso `(a, num)` do
`translate` é resolvido aí e não chega à raiz. Se os dois itens estivessem trocados, o `a` não
estava no `env`, o uso subia até `start` e dava `Nome não declarado`.

O `env` de um item usa só o pai e os itens anteriores, por isso a gramática é
L-atribuída (NB06) e os atributos calculam-se numa só visita.

#### Declaração de todos os atributos

`SA` são atributos sintetizados e `IA` são herdados. As regras de avaliação e as condições de contexto estão em [`gramatica_ag.lark`](caravela/gramatica_ag.lark).

<details>
<summary>Ver os atributos de cada símbolo</summary>

```
SA(start)          { nomes : list, usos : list, tabela : dict, materiais : dict }
SA(decl)           { nomes : list, usos : list, unidades : dict }

SA(letdecl)        { nome : str, tipo : any, usos : list }
SA(texturedecl)    { nomes : list }
SA(materialdecl)   { nomes : list, usos : list, modos : list, papeis : list, unidades : dict }
SA(matitem)        { usos : list, modo : str, papel : str, textura : bool }
SA(diffuse)        { usos : list }
SA(matlighting)    { usos : list, modo : str }
SA(lightingmode)   { modo : str }
SA(lightingparams) { usos : list, nomes : list }
IA(lightingparams) { modo : str }
SA(lightingparam)  { usos : list, nome : str }
SA(shininess)      { usos : list }
SA(levels)         { usos : list }
SA(layer)          { usos : list, papel : str, textura : bool }
SA(layerrole)      { papel : str }
SA(layersource)    { usos : list, textura : bool }
SA(noise)          { usos : list }

SA(scenedecl)      { nomes : list, usos : list }
SA(scenesource)    { usos : list }
SA(grid)           { usos : list }
SA(sceneitems)     { usos : list, locais : dict }
IA(sceneitems)     { env : dict }
SA(sceneitem)      { usos : list, locais : dict }
IA(sceneitem)      { env : dict }
SA(object)         { usos : list }
SA(templatecall)   { usos : list }
SA(objectbody)     { usos : list }
SA(transform)      { usos : list }
SA(translate)      { usos : list }
SA(scale)          { usos : list }
SA(rotate)         { usos : list }
SA(scenefor)       { usos : list }
IA(scenefor)       { env : dict }
SA(sceneif)        { usos : list }
IA(sceneif)        { env : dict }
SA(sceneblock)     { usos : list }
IA(sceneblock)     { env : dict }
SA(templatedecl)   { nomes : list, usos : list }
SA(params)         { locais : dict, tipos : tuple }
SA(param)          { nome : str, tipo : str }
SA(type)           { tipo : str }
SA(args)           { usos : list, tipos : tuple }

SA(cameradecl)     { nomes : list, usos : list }
SA(cameraprop)     { usos : list }
SA(position)       { usos : list }
SA(lookat)         { usos : list }
SA(direction)      { usos : list }
SA(near)           { usos : list }
SA(far)            { usos : list }
SA(fov)            { usos : list }
SA(lightdecl)      { nomes : list, usos : list }
SA(lightprop)      { usos : list }
SA(lightcolor)     { usos : list }
SA(backgrounddecl) { usos : list }

SA(passdecl)       { nomes : list, usos : list }
SA(passitem)       { usos : list }
SA(draw)           { usos : list }
SA(passcamera)     { usos : list }
SA(passlights)     { usos : list }
SA(passlighting)   { usos : list }
SA(passmaterial)   { usos : list }
SA(passif)         { usos : list }
SA(passblock)      { usos : list }
SA(idlist)         { nomes : list }

SA(num)            { usos : list, nome : str }
SA(term)           { usos : list, nome : str }
SA(factor)         { usos : list, nome : str }
SA(vec3)           { usos : list }
SA(color)          { usos : list }
SA(cond)           { usos : list }
SA(vec3val)        { usos : list }
SA(colorval)       { usos : list }
SA(value)          { usos : list, tipo : any }
```

</details>

#### Diferenças para a gramática da secção anterior

Para o LarkAG aceitar a gramática tivemos de a mudar um pouco, sem mudar a linguagem aceite (há um
doctest que o confirma):

1. Os nomes das regras não têm `_` (`let_decl` passa a `letdecl`), porque o LarkAG usa o `_` para
   numerar as alternativas.
2. As listas que recebem um atributo herdado passam a recursivas à esquerda
   (`sceneitems: sceneitems sceneitem | ε`), como o `decls` da EX04. Com `scene_item*` não dava
   para passar o `env` a cada item.
3. O `..` do `for` passa a literal, porque o LarkAG não aceita terminais começados por `_`.
4. As partes opcionais que têm atributos passam a alternativas, porque uma regra só pode usar um
   filho que existe sempre.

Nas fichas usa-se `Lark_AG(grammar).process(texto)`. Nós não conseguimos usar isso diretamente:
as regras chamam funções nossas (de `auxiliares.py`) e o `process` corre o interpretador gerado
num sítio onde essas funções não existem. Por isso, em [caravela/semantica.py](caravela/semantica.py),
construímos o parser LALR com `ag.getCFG()` e corremos o interpretador que o LarkAG gera
(`ag.getInterpreterFile()`) junto com as nossas funções.

<a id="corre-larkag"></a>
### 3.3 Como corre

Para executar a gramática de atributos, o módulo [`caravela/semantica.py`](caravela/semantica.py)
constrói o parser LALR com `ag.getCFG()` e executa o interpretador gerado pelo LarkAG junto
com as funções auxiliares do projeto.

<a id="avaliacao"></a>
## 4. Avaliação da qualidade

Usámos os fatores e as métricas da NB07 e da EX05. Os números são os que
`python -m caravela.metricas` imprime.

### Qualidade da linguagem

| Fator | Na Caravela |
|---|---|
| Expressividade | Boa para o domínio. Os conceitos são os de VTR, e o material diz o efeito (`lighting phong`, `layer night`) em vez de como se calcula. Os projetos das aulas ficam cerca de 6 vezes mais curtos. Fora do domínio é fraca: condições sem `and`/`or`, o `for` só avança de 1 em 1. |
| Documentação | Há comentários de linha e de bloco, este README e os doctests. Não há forma de pôr meta-informação nos comentários. |
| Unicidade | Quase sempre há uma só forma de fazer cada coisa. Há duas formas de mudar o aspeto num passe (`lighting X for all` e `material X for all`), mas fazem coisas diferentes: a primeira mantém as cores do modelo e a segunda substitui o material. |
| Consistência | Quase todas as declarações têm a forma `palavra nome { propriedades }` ou `palavra nome = valor;`. As exceções são `background` e `project`, que não têm nome. As propriedades acabam em `;` ou num bloco `{ }`. Os vetores escrevem-se sempre `(x, y, z)`. |
| Extensibilidade | Uma cor nova é só acrescentá-la ao ambiente inicial. Um modo de iluminação novo é um terminal, uma alternativa e, se for preciso, uma condição de contexto. Um tipo de valor novo (por exemplo `vec2`) já obriga a mexer em várias regras. |
| Escalabilidade | É onde se ganha mais face ao XML: com `for`, `if` e `template`, os 8 pilares do templo escrevem-se uma vez, em vez de 8 objetos com as posições calculadas à mão. |
| Fiabilidade | É a principal melhoria. Os erros são apanhados em três níveis: léxico (`let a = 1 @ 2;`, porque `@` não é um token), sintaxe (`position 5;`, ou `texture` usado como nome) e semântica (nome não declarado, `draw cam`, `pilar(azul, 3)`). O ponto fraco são as mensagens: não dizem qual é o nome nem em que linha está. |
| Modularidade | Os templates permitem reutilizar partes de uma cena. Não há módulos nem `import`: um programa é um só ficheiro. |

### Qualidade da gramática

Métricas de tamanho, calculadas sobre as regras BNF que o Lark gera (o Lark cria 9 não-terminais
auxiliares para os `*` e `?`):

| Métrica | Valor |
|---|---|
| Terminais | 76 |
| Não-terminais | 80 (71 escritos e 9 auxiliares) |
| Produções | 174 |
| Produções unitárias | 59 |
| Lado direito | média 2,38, máximo 9 |
| Produções por não-terminal | média 2,17, máximo 9 (`decl`) |
| Subgramáticas importadas | 0 |
| Grafo de dependências | 130 arestas, grau de entrada e de saída médio 1,62 |
| Parser LALR | 330 estados, 1867 entradas nas tabelas ACTION/GOTO |

Métricas de forma e lexicográficas:

| Métrica | Valor |
|---|---|
| Recursividade direta à esquerda | `num`, `term`, `params`, `args`, `id_list` |
| Recursividade direta à direita | `factor` (`- factor`), `scene_if`, `pass_if` (`else if`) |
| Recursividade indireta | os itens das cenas (`scene_item`, `scene_for`, `scene_if`, `scene_block`), os dos passes (`pass_item`, `pass_if`, `pass_block`) e as expressões (`num`, `term`, `factor`, pelos parênteses) |
| Notação | mista: 23 das 71 regras usam EBNF (`*`, `?`, parênteses) e 48 só BNF |
| Palavras reservadas | 58, todas com o nome do conceito (`material`, `camera`, `shininess`, ...) |
| Terminais flexíveis | `ID`, `NUMBER`, `STRING`, `CMP_OP`, `MUL_OP`, `COMMENT` |
| Comentários | de linha e de bloco, sem meta-informação |

O que tiramos destas métricas, com as características da NB07:

- **Compreensão.** Os nomes das regras são os nomes dos conceitos e as regras são curtas (lado
  direito com 2,38 símbolos em média). As 59 produções unitárias vêm sobretudo de dar um nome a cada
  propriedade (`camera_prop → position`, `position → "position" vec3_val ";"`). Ajudam a ler, mas
  tornam a árvore funda: até 18 níveis nos exemplos.
- **Derivação.** A recursividade indireta só aparece onde a linguagem tem coisas aninhadas (blocos
  e parênteses). A recursividade é mista: à esquerda nas listas e nas expressões, como nas aulas,
  e à direita no `else if` e no `- factor`.
- **Manutenção.** A notação é mista. Usamos EBNF (`item*`, `?`) nas listas simples e BNF recursiva
  nas listas separadas por vírgulas (`params`, `args`, `id_list`), e na gramática de atributos
  também em `sceneitems`, porque o LarkAG precisa disso para passar o `env`. A NB07 diz que misturar
  as duas sem critério é mau, por isso fica aqui o critério. O maior problema de manutenção é haver
  duas versões da gramática (a do Lark e a do LarkAG), que um doctest mantém iguais.
- **Reconhecimento e geração.** A gramática é LALR(1) sem conflitos e o parser tem 330 estados.
  O grafo de dependências tem pouca ligação (grau médio 1,62).

### Qualidade da gramática de atributos

| Métrica | Valor |
|---|---|
| Atributos | 108: 102 sintetizados e 6 herdados |
| Tipo dos atributos | 18 atómicos (`str`, `bool`), 88 estruturados (`list`, `dict`, `tuple`), 2 `any` |
| Regras de avaliação | 225, das quais 97 só copiam um atributo de um filho para o pai |
| Condições de contexto | 25 |
| Funções auxiliares | 10 |

- **Compreensão.** Os nomes dos atributos dizem o que guardam (`usos`, `env`, `locais`, `tabela`,
  `unidades`), e as mensagens das condições de contexto dizem qual é a regra violada. Em troca,
  quase todos os atributos são estruturados (listas de usos, dicionários), o que obriga a explicar o
  que cada um contém.
- **Manutenção.** 97 das 225 regras de avaliação só copiam `usos` de um filho para o pai. É o custo
  de recolher os usos de baixo para cima. As regras mais complicadas foram para funções auxiliares
  com nome (`resto`, `tipos_ok`, `tem_ciclo`), para as regras ficarem curtas.
- **Avaliação.** Só há 6 atributos herdados (`env` e `modo`), e a gramática é L-atribuída, por isso
  chega uma visita à árvore.
- **Estilo e especificidade.** As regras são declarativas (cada uma diz quanto vale um atributo) e
  a linguagem é de domínio específico.

<a id="correr"></a>
## 5. Como correr o projeto

<a id="instalar"></a>
### 5.1 Instalar

É preciso Python 3.10 ou mais recente. Todos os comandos correm dentro desta pasta.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

<a id="usar"></a>
### 5.2 Usar

Verificar um programa:

```
$ python -m caravela exemplos/3_templo.cav
exemplos/3_templo.cav: programa correto
  tabela de símbolos: {'n': 'num', 'raio': 'num', 'azul': 'material', 'branco': 'material', 'pilar': ('template', ('num', 'material')), ...}
  unidades de textura: {'azul': {}, 'branco': {}}
```

Se o programa tiver um erro, aparece a mensagem, por exemplo
`erro semântico: Argumentos do template com tipo errado`. Com `--tokens` vê-se o resultado do
analisador léxico e com `--arvore` a árvore sintática.

<a id="testar"></a>
### 5.3 Testar

Correr os testes (são doctests, como nas fichas das aulas):

```bash
python testes.py
```

Calcular as métricas de qualidade:

```bash
python -m caravela.metricas
```

<a id="pastas"></a>
### 5.4 Estrutura

```
caravela/
  gramatica.lark      léxico e gramática independente de contexto
  gramatica_ag.lark   gramática de atributos (LarkAG)
  auxiliares.py       tipos e funções usados nas regras da gramática de atributos
  sintaxe.py          parser LALR
  semantica.py        avalia a gramática de atributos
  metricas.py         métricas de qualidade (NB07)
  __main__.py         linha de comandos
exemplos/             os programas de exemplo
testes.py             doctests
```

<a id="limitacoes"></a>
## 6. Limitações

- As mensagens de erro não dizem qual é o nome nem a linha. No LarkAG a mensagem de uma condição
  de contexto é um texto fixo.
- As condições não têm `and`, `or` nem `not`.
- Não se verificam os valores (`near > 0`, `far > near`, `levels >= 2`).
- Na Parte II vamos gerar os ficheiros do Nau (`.xml`, `.mlib` e shaders) a partir da árvore.
