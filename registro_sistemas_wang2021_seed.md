# Registro inicial en Markdown: sistemas extraídos del libro de Wang, Kuznetsov y Chen (2021)

Fuente base: X. Wang, N. V. Kuznetsov y G. Chen (eds.), *Chaotic Systems with Multistability and Hidden Attractors*, Springer, 2021. DOI: `10.1007/978-3-030-75821-9`.

Este archivo es un registro inicial para entregar a Codex. Debe ser completado capítulo por capítulo. Las ecuaciones marcadas con `VERIFICAR_PDF` deben revisarse contra la página renderizada del PDF, porque la extracción de texto puede confundir `x` con `z`, signos, exponentes o funciones por tramos.

## Estado de avance por capítulos

| Capítulo | Tema | Estado inicial |
|---:|---|---|
| 1 | Introducción: Lorenz, Rössler, Chua, Chen, sistema unificado, Sprott A-S | Semilla parcial incluida |
| 2 | Teorema de Šil'nikov | No es catálogo de sistemas; extraer criterios matemáticos |
| 3 | Sistemas caóticos con equilibrios estables | Semilla parcial incluida |
| 4 | Sistemas caóticos sin equilibrios | Semilla parcial incluida |
| 5 | Sistemas con curvas de equilibrios | Pendiente |
| 6 | Sistemas con superficies de equilibrios | Pendiente |
| 7 | Sistemas con cualquier número y varios tipos de equilibrios | Pendiente |
| 8 | Sistemas hipercaóticos con atractores ocultos | Pendiente |
| 9 | Sistemas fraccionarios con atractores ocultos | Pendiente |
| 10 | Sistemas memristivos con atractores ocultos | Pendiente |
| 11 | Sistemas jerk con atractores ocultos | Pendiente |
| 12-16 | Multiestabilidad y detección | Pendiente |
| 17-27 | Sistemas especiales, aplicaciones y avances | Pendiente |

## Esquema breve para cada sistema

```yaml
system_id:
name:
source_chapter:
book_pages:
primary_reference:
model_type:
dimension:
equations_latex:
parameters_reported:
initial_conditions_reported:
equilibria_reported:
equilibria_to_compute:
equilibrium_classification_reported:
equilibrium_classification_to_compute:
reported_les:
reported_dimension:
basin_classification_plan:
bifurcation_plan:
implementation_status:
notes:
```

---

# Capítulo 1. Introducción

## ch01_lorenz

```yaml
system_id: ch01_lorenz
name: Lorenz system
source_chapter: 1
book_pages: [3]
primary_reference:
  authors: "Edward N. Lorenz"
  year: 1963
  title: "Deterministic nonperiodic flow"
  venue: "Journal of the Atmospheric Sciences"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=\rho(y-x) \quad \text{VERIFICAR_PDF: la extracción puede mostrar } \rho(y-z)\\
  \dot{y}=rx-y-xz\\
  \dot{z}=-bz+xy
parameters_reported:
  rho: 10
  r: 28
  b: "8/3"
initial_conditions_reported: []
equilibria_reported: []
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Usar vecindades de equilibrios y semillas estándar; clasificar self-excited."
bifurcation_plan: "Parámetro natural r; observable máximos de z o sección de Poincaré."
implementation_status: seed
notes: "Sistema clásico incluido como referencia. Verificar la primera ecuación contra el PDF renderizado y contra Lorenz (1963)."
```

## ch01_rossler

```yaml
system_id: ch01_rossler
name: Rössler system
source_chapter: 1
book_pages: [4]
primary_reference:
  authors: "Otto E. Rössler"
  year: 1976
  title: null
  venue: null
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=-y-z\\
  \dot{y}=x+ay\\
  \dot{z}=-b+z(x-c)
parameters_reported:
  a: 0.20
  b: 0.20
  c: 5.7
initial_conditions_reported: []
equilibria_reported: []
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Registrar coexistencia de atractores si se estudian parámetros multistables."
bifurcation_plan: "Parámetro natural c; observable máximos locales de x."
implementation_status: seed
notes: "El libro menciona atractores de una sola lóbulo y tipo screw."
```

## ch01_chua_circuit

```yaml
system_id: ch01_chua_circuit
name: Chua circuit, piecewise-linear form
source_chapter: 1
book_pages: [4, 5]
primary_reference:
  authors: "Leon O. Chua and collaborators"
  year: null
  title: null
  venue: null
model_type: ode_piecewise
dimension: 3
equations_latex: |
  \dot{x}=\alpha(-x+y-h(x))\\
  \dot{y}=x-y+z\\
  \dot{z}=-\beta y\\
  h(x)=m_1x+\frac{1}{2}(m_0-m_1)(|x+1|-|x-1|)
parameters_reported:
  alpha: 10.0
  beta: 14.87
  m0: -1.27
  m1: -0.68
initial_conditions_reported: []
equilibria_reported: "Tres equilibrios visibles tipo saddle-focus, según el libro."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Separar vecindades de los tres equilibrios y cuencas de doble scroll."
bifurcation_plan: "Parámetros naturales alpha, beta, m0, m1; iniciar con alpha o beta."
implementation_status: seed
notes: "Sistema no suave; implementar h(x) por valor absoluto y, opcionalmente, por tramos."
```

## ch01_chen

```yaml
system_id: ch01_chen
name: Chen system
source_chapter: 1
book_pages: [5]
primary_reference:
  authors: "G. Chen and T. Ueta"
  year: 1999
  title: "Yet another chaotic attractor"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=a(y-x) \quad \text{VERIFICAR_PDF: la extracción puede mostrar } a(y-z)\\
  \dot{y}=(c-a)x+cy-xz\\
  \dot{z}=-bz+xy
parameters_reported:
  a: 35
  b: 3
  c: 28
initial_conditions_reported: []
equilibria_reported: []
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Clasificar como self-excited respecto a equilibrios inestables."
bifurcation_plan: "Parámetro natural c o a; observable máximos de z."
implementation_status: seed
notes: "Verificar primera ecuación contra PDF renderizado y referencia original."
```

## ch01_unified_lorenz_chen

```yaml
system_id: ch01_unified_lorenz_chen
name: Unified Lorenz-Chen system
source_chapter: 1
book_pages: [5]
primary_reference:
  authors: "J. Lü, G. Chen and S. Zhang"
  year: 2002
  title: "The compound structure of a new chaotic attractor"
  venue: "Chaos, Solitons & Fractals"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=(25\alpha+10)(y-x) \quad \text{VERIFICAR_PDF}\\
  \dot{y}=(28-35\alpha)x+(29\alpha-1)y-xz\\
  \dot{z}=-\frac{\alpha+8}{3}z+xy
parameters_reported:
  alpha: "0 gives Lorenz; 1 gives Chen; 0<alpha<1 remains chaotic according to book"
initial_conditions_reported: []
equilibria_reported: []
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Usar alpha como parámetro de familia."
bifurcation_plan: "Parámetro alpha en [0,1]."
implementation_status: seed
notes: "Verificar primera ecuación."
```

## ch01_sprott_A_to_S

Referencia principal: J. C. Sprott, "Some simple chaotic flows", *Physical Review E*, 50(2), R647, 1994.

| id | ecuaciones | equilibrios reportados | LEs reportados | dimensión |
|---|---|---|---|---|
| sprott_a | `dx=y; dy=-x+yz; dz=1-y^2` | none | `(0.014,0,-0.014)` | 3.000 |
| sprott_b | `dx=yz; dy=x-y; dz=1-xy` | `(1,1,0), (-1,-1,0)` | `(0.210,0,-1.210)` | 2.174 |
| sprott_c | `dx=yz; dy=x-y; dz=1-x^2` | `(1,1,0), (-1,-1,0)` | `(0.163,0,-0.163)` | 2.140 |
| sprott_d | `dx=-y; dy=x+z; dz=xz+3y^2` | `(0,0,0)` | `(0.103,0,-1.320)` | 2.078 |
| sprott_e | `dx=yz; dy=x^2-y; dz=1-4x` | `(0.25,0.063,0)` | `(0.078,0,-1.078)` | 2.072 |
| sprott_f | `dx=y+z; dy=-x+0.5y; dz=x^2-z` | `(0,0,0), (-2,-4,4)` | `(0.117,0,-0.617)` | 2.190 |
| sprott_g | `dx=0.4x+z; dy=xz-y; dz=-x+y` | `(0,0,0), (-2.5,-2.5,1)` | `(0.034,0,-0.634)` | 2.054 |
| sprott_h | `dx=-y+z^2; dy=x+0.5y; dz=x-z` | `(0,0,0), (-2,4,-2)` | `(0.117,0,-0.617)` | 2.190 |
| sprott_i | `dx=0.2y; dy=x+z; dz=x+y^2-z` | `(0,0,0)` | `(0.012,0,-1.012)` | 0.012 `VERIFICAR` |
| sprott_j | `dx=2z; dy=-2y+z; dz=-x+y+y^2` | `(0,0,0)` | `(0.076,0,-2.076)` | 2.037 |
| sprott_k | `dx=xy-z; dy=x-y; dz=x+0.3z` | `(0,0,0), (-3.333,-3.333,11.111)` | `(0.038,0,-0.890)` | 2.042 |
| sprott_l | `dx=y+3.9z; dy=0.9x^2-y; dz=1-x` | `(1,1.111,-0.231)` | `(0.061,0,-1.061)` | 2.057 |
| sprott_m | `dx=-z; dy=-x^2-y; dz=1.7+1.7x+y` | `(2.406,-5.791,0), (-0.706,-0.499,0)` | `(0.044,0,-1.044)` | 2.042 |
| sprott_n | `dx=-2y; dy=x+z^2; dz=1+y-2z` | `(-0.25,0,0.5)` | `(0.076,0,-2.076)` | 2.037 |
| sprott_o | `dx=y; dy=x-z; dz=x+xz+2.7y` | `(0,0,0), (-1,0,-1)` | `(0.049,0,-0.319)` | 2.154 |
| sprott_p | `dx=2.7y+z; dy=-x+y^2; dz=x+y` | `(0,0,0), (1,-1,2.7)` | `(0.087,0,-0.481)` | 2.181 |
| sprott_q | `dx=-z; dy=x-y; dz=3.1x+y^2+0.5z` | `(0,0,0), (-3.1,-3.1,0)` | `(0.109,0,-0.609)` | 2.179 |
| sprott_r | `dx=0.9-y; dy=0.4+z; dz=xy-z` | `(-0.444,1.111,-0.4)` | `(0.062,0,-1.062)` | 2.058 |
| sprott_s | `dx=x-4y; dy=x+z^2; dz=1+x` | `(-1,0.25,1), (-1,0.25,-1)` | `(0.188,0,-1.188)` | 2.151 |

Tareas para Codex en Sprott A-S:

- Verificar todas las ecuaciones contra la tabla renderizada.
- Calcular equilibrios con SymPy y comparar con la tabla.
- Clasificar cada equilibrio por autovalores.
- Crear presets mínimos de simulación.
- Para Sprott A registrar además coexistencia de mar caótico y toros anidados si se usa como sistema sin equilibrio en el capítulo 4.

---

# Capítulo 3. Sistemas caóticos con equilibrios estables

## ch03_wang_chen_stable_equilibrium

```yaml
system_id: ch03_wang_chen_stable_equilibrium
name: Wang-Chen system with one stable equilibrium
source_chapter: 3
book_pages: [30, 31, 32, 33]
primary_reference:
  authors: "X. Wang and G. Chen"
  year: 2012
  title: "A chaotic system with only one stable equilibrium"
  venue: "Communications in Nonlinear Science and Numerical Simulation"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=yz+a\\
  \dot{y}=x^2-y\\
  \dot{z}=1-4x
parameters_reported:
  a_examples: [-0.005, 0.006, 0.022, 0.030, 0.050]
  canonical_a: 0.006
initial_conditions_reported: []
equilibria_reported:
  - "E=(1/4,1/16,-16a)"
equilibrium_classification_reported:
  - "Para a>0, node-focus estable en los ejemplos reportados."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les:
  a_0_006: [0.0489, 0, -1.0485]
reported_dimension: null
basin_classification_plan: "Probar que pequeñas vecindades del equilibrio estable convergen al punto; buscar cuenca del atractor caótico lejos del equilibrio."
bifurcation_plan: "Parámetro a; reproducir ventanas periódicas/caóticas si se reportan."
implementation_status: seed
notes: "Deriva de Sprott E agregando parámetro constante a. No clasificar como hidden verificado sin prueba de vecindades."
```

## ch03_wei_extended_sprott_e

```yaml
system_id: ch03_wei_extended_sprott_e
name: Wei extended Sprott E system
source_chapter: 3
book_pages: [34, 35]
primary_reference:
  authors: "Z. Wei"
  year: 2013
  title: "Chaotic behavior and modified function projective synchronization of a simple system with one stable equilibrium"
  venue: "Kybernetika"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=yz+h(x)\\
  \dot{y}=x^2-y\\
  \dot{z}=1-4x\\
  h(x)=ex^2+fx+g
parameters_reported:
  e: null
  f: null
  g: null
  example_scan: "f=-0.1, g=0.02, e variable"
initial_conditions_reported: []
equilibria_reported:
  - "E=(1/4,1/16,-e-4f-16g)"
equilibrium_classification_reported: "Condiciones de Routh-Hurwitz reportadas en el capítulo."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Mismo protocolo que Wang-Chen; distinguir punto estable y atractor caótico."
bifurcation_plan: "Parámetro e con f=-0.1, g=0.02; reproducir ventanas periódicas."
implementation_status: seed
notes: "Incluye como casos h(x)=g, h(x)=ex^2 y h(x)=fx."
```

## ch03_wang_chen_multiple_delays

```yaml
system_id: ch03_wang_chen_multiple_delays
name: Multiple-delayed Wang-Chen system
source_chapter: 3
book_pages: [35, 36]
primary_reference:
  authors: "Z. Wei, V.-T. Pham, T. Kapitaniak and Z. Wang"
  year: 2016
  title: "Bifurcation analysis and circuit realization for multiple-delayed Wang-Chen system with hidden chaotic attractors"
  venue: "Nonlinear Dynamics"
model_type: dde
dimension: 3
equations_latex: |
  \dot{x}=yz+a+k_1x(t-\tau_1)+k_2x(t-\tau_2)\\
  \dot{y}=x^2-y\\
  \dot{z}=1-4x
parameters_reported:
  tau1: null
  tau2: null
  k1: null
  k2: null
initial_conditions_reported: []
equilibria_reported:
  - "E=(1/4,1/16,-16a-4(k1+k2))"
equilibrium_classification_reported: "Estabilidad y Hopf por ecuación característica con retardos."
equilibria_to_compute: true
equilibrium_classification_to_compute: "DDE: requiere análisis de ecuación característica."
reported_les: []
reported_dimension: null
basin_classification_plan: "Pendiente hasta tener motor DDE."
bifurcation_plan: "Parámetro tau o k; Hopf por retardo."
implementation_status: pending_engine
notes: "No integrar con solver ODE estándar."
```

## ch03_lao

```yaml
system_id: ch03_lao
name: Lao system
source_chapter: 3
book_pages: [36, 37]
primary_reference:
  authors: "S.-K. Lao, Y. Shekofteh, S. Jafari and J. C. Sprott"
  year: 2014
  title: "Cost function based on Gaussian mixture model for parameter estimation of a chaotic circuit with a hidden attractor"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=-z\\
  \dot{y}=-x-z\\
  \dot{z}=2x-1.3y-2z+x^2+z^2-xz
parameters_reported: {}
initial_conditions_reported: []
equilibria_reported:
  - "E=(0,0,0)"
equilibrium_classification_reported:
  - "stable focus; eigenvalues approximately -1.9783, -0.0108±0.8106i"
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: [0.018, 0, -2.018]
reported_dimension: null
basin_classification_plan: "Corte z=0; clases: no acotado, punto estable, atractor extraño."
bifurcation_plan: "No especificado en semilla; inferir parámetro si se generaliza."
implementation_status: seed
notes: "El libro muestra corte de cuencas con región no acotada, punto y atractor extraño."
```

## ch03_kingni

```yaml
system_id: ch03_kingni
name: Kingni system
source_chapter: 3
book_pages: [37, 38]
primary_reference:
  authors: "S. Kingni, S. Jafari, H. Simo and P. Woafo"
  year: 2014
  title: "Three-dimensional chaotic autonomous system with only one stable equilibrium"
  venue: "European Physical Journal Plus"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=-z\\
  \dot{y}=-x-z\\
  \dot{z}=3x-ay+x^2-z^2-yz+b
parameters_reported:
  a: 1.3
  b: 1.01
initial_conditions_reported: []
equilibria_reported:
  - "E=(0,b/a,0), a != 0"
equilibrium_classification_reported:
  - "Para a=1.3, b=1.01: stable node-focus; eigenvalues -0.7678519459, -0.004535565486±1.301158769i"
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Distinguir equilibrio estable y atractor caótico; barrer parámetros a,b."
bifurcation_plan: "Parámetros a o b; incluir región de estabilidad por Routh-Hurwitz."
implementation_status: seed
notes: "Registrar condiciones A>0, C>0, AB-C>0."
```

## ch03_line_equilibrium_to_one_stable

```yaml
system_id: ch03_line_equilibrium_to_one_stable
name: Controlled LE1 system from infinite equilibria to one stable equilibrium
source_chapter: 3
book_pages: [38, 39, 40]
primary_reference:
  authors: "V.-T. Pham et al.; base line-equilibrium system by S. Jafari and J. C. Sprott"
  year: 2013
  title: null
  venue: null
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x+yz+c\\
  \dot{z}=-x-axy-bxz
parameters_reported:
  a: 15
  b: 1
  c: 0.001
initial_conditions_reported:
  - [0, 0.5, 0.5]
equilibria_reported:
  - "E=(c,0,-1/b)"
equilibrium_classification_reported:
  - "eigenvalues: -bc, -0.5±0.866i"
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Comparar sistema base con línea E=(0,0,z) y sistema controlado con equilibrio único."
bifurcation_plan: "Parámetro c."
implementation_status: seed
notes: "El sistema base sin c tiene infinitos equilibrios E=(0,0,z)."
```

## ch03_simple_stable_equilibrium_jerk_SE1_to_SE23

```yaml
system_id: ch03_simple_stable_equilibrium_jerk_SE1_to_SE23
name: 23 simple chaotic flows with one stable equilibrium, SE1-SE23
source_chapter: 3
book_pages: [40, 41, 42, 44, 45, 46]
primary_reference:
  authors: "M. Molaie, S. Jafari and collaborators"
  year: 2013
  title: "Simple chaotic flows with one stable equilibrium"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: "Ver tablas 3 y 4 del capítulo 3; extraer cada caso SE1-SE23 como sistema independiente."
parameters_reported: {}
initial_conditions_reported: "Tablas 3 y 4 reportan una condición inicial por caso."
equilibria_reported: "Tablas 3 y 4 reportan equilibrio por caso."
equilibrium_classification_reported: "Todos reportados con un equilibrio estable; eigenvalores en tablas."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: "Tablas 3 y 4."
reported_dimension: "Tablas 3 y 4."
basin_classification_plan: "Generar presets por caso; usar el equilibrio como punto estable y buscar atractor caótico con la condición inicial reportada."
bifurcation_plan: "No inferir hasta extraer parámetros; muchos casos no tienen parámetro explícito."
implementation_status: pending_table_extraction
notes: "Extraer tabla completa con verificación visual; no confiar solo en OCR por orientación de tabla."
```

## ch03_yang_chen

```yaml
system_id: ch03_yang_chen
name: Yang-Chen system
source_chapter: 3
book_pages: [43, 47, 48]
primary_reference:
  authors: "Q. Yang and G. Chen"
  year: 2008
  title: "A chaotic system with one saddle and two stable node-foci"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=a(y-x) \quad \text{VERIFICAR_PDF}\\
  \dot{y}=cx-xz\\
  \dot{z}=-bz+xy
parameters_reported:
  a: 35
  b: 3
  c: 35
initial_conditions_reported:
  - [1.15, 3.5, 3]
equilibria_reported:
  - "E1=(0,0,0)"
  - "E2=(sqrt(105),sqrt(105),35)"
  - "E3=(-sqrt(105),-sqrt(105),35)"
equilibrium_classification_reported:
  - "E1 saddle"
  - "E2,E3 stable node-foci"
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Tres clases locales: saddle no atractor, dos node-foci estables, atractor caótico si existe fuera de vecindades."
bifurcation_plan: "Parámetro c o a."
implementation_status: seed
notes: "Verificar primera ecuación porque el texto extraído puede confundir x/z."
```

## ch03_yang_wei

```yaml
system_id: ch03_yang_wei
name: Yang-Wei system
source_chapter: 3
book_pages: [48, 49]
primary_reference:
  authors: "Q. Yang, Z. Wei and G. Chen"
  year: 2010
  title: "An unusual 3D autonomous quadratic chaotic system with two stable node-foci"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=a(y-x)\\
  \dot{y}=-cy-xz\\
  \dot{z}=-b+xy
parameters_reported:
  a: 10
  b: 100
  c: 11.2
initial_conditions_reported: []
equilibria_reported:
  - "E1=(sqrt(b),sqrt(b),-c)"
  - "E2=(-sqrt(b),-sqrt(b),-c)"
  - "For reported parameters: E1=(10,10,-11.2), E2=(-10,-10,-11.2)"
equilibrium_classification_reported:
  - "stable node-foci; eigenvalues -20.9778, -0.1111±9.7635i"
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Cuencas de los dos focos estables y posible atractor caótico."
bifurcation_plan: "Parámetros a,b,c; reproducir Hopf si se implementa análisis."
implementation_status: seed
notes: "Tiene variantes con retardo y control por realimentación."
```

---

# Capítulo 4. Sistemas caóticos sin equilibrios

## ch04_sprott_a_no_equilibrium

```yaml
system_id: ch04_sprott_a_no_equilibrium
name: Sprott A no-equilibrium system
source_chapter: 4
book_pages: [56, 57]
primary_reference:
  authors: "J. C. Sprott"
  year: 1994
  title: "Some simple chaotic flows"
  venue: "Physical Review E"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x+yz\\
  \dot{z}=1-y^2
parameters_reported: {}
initial_conditions_reported:
  - [0, 5, 0]
  - [0, 1, 0]
equilibria_reported: []
equilibrium_classification_reported: "No equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: [0.0139, 0, -0.0139]
reported_dimension: 3.0
basin_classification_plan: "Clasificar mar caótico y toros anidados; no hay vecindades de equilibrio."
bifurcation_plan: "Usar variante con parámetro a si se requiere."
implementation_status: seed
notes: "No uniformemente conservativo; el libro reporta coexistencia de mar caótico y toros."
```

## ch04_wei_no_equilibrium

```yaml
system_id: ch04_wei_no_equilibrium
name: Wei no-equilibrium system
source_chapter: 4
book_pages: [57, 58]
primary_reference:
  authors: "Z. Wei"
  year: 2011
  title: "Dynamical behaviors of a chaotic system with no equilibria"
  venue: "Physics Letters A"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=-y\\
  \dot{y}=cx+z\\
  \dot{z}=ay^2+xz-d
parameters_reported:
  a: 2
  c: 1
  d: 0.35
initial_conditions_reported:
  - [-1.6, 0.82, 1.9]
equilibria_reported: []
equilibrium_classification_reported: "No equilibria when d>0."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: [0.0793, 0, -1.5034]
reported_dimension: 2.0528
basin_classification_plan: "Clases: atractor caótico, no acotado/transitorio."
bifurcation_plan: "Parámetro d; transición de equilibrio degenerado a no equilibrio."
implementation_status: seed
notes: "Deriva de Sprott D por perturbación constante."
```

## ch04_wang_chen_no_equilibrium

```yaml
system_id: ch04_wang_chen_no_equilibrium
name: Wang-Chen no-equilibrium system
source_chapter: 4
book_pages: [58, 59]
primary_reference:
  authors: "X. Wang and G. Chen"
  year: 2013
  title: "Constructing a chaotic system with any number of equilibria"
  venue: "Nonlinear Dynamics"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=z\\
  \dot{z}=-y+3y^2-x^2-xz+a
parameters_reported:
  a: -0.05
initial_conditions_reported:
  - [0.5, 0.5, 0.5]
equilibria_reported: "No equilibrium when a<0."
equilibrium_classification_reported: "No real equilibria for a<0."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Muestreo global porque no hay equilibrio."
bifurcation_plan: "Parámetro a; cambio según signo de a."
implementation_status: seed
notes: "Verificar si la forma en tablas posteriores usa coeficientes simplificados."
```

## ch04_maaita

```yaml
system_id: ch04_maaita
name: Maaita cubic no-equilibrium system
source_chapter: 4
book_pages: [59, 60]
primary_reference:
  authors: "J. Maaita, C. K. Volos, I. Kyprianidis and I. Stouboulos"
  year: 2015
  title: "The dynamics of a cubic nonlinear system with no equilibrium point"
  venue: "Nonlinear Dynamics"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x^3-zy\\
  \dot{z}=y^2-a
parameters_reported:
  a_examples: [5.16, 0.6]
initial_conditions_reported:
  - [-0.8, 0, 1.0]
  - [-1.2, 0, 0]
equilibria_reported: "No equilibria when a>0."
equilibrium_classification_reported: "No real equilibria for a>0."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: "Para a=5.16: un exponente positivo, uno cero, uno negativo; para a=0.6: tres exponentes cero."
reported_dimension: null
basin_classification_plan: "Distinguir caos, órbitas regulares y 3-toros."
bifurcation_plan: "Parámetro a; usar mapas de Poincaré."
implementation_status: seed
notes: "Sistema cúbico derivado de Sprott A."
```

## ch04_akgul

```yaml
system_id: ch04_akgul
name: Akgul no-equilibrium system
source_chapter: 4
book_pages: [60, 61, 62]
primary_reference:
  authors: "A. Akgul, H. Calgan, I. Koyuncu, I. Pehlivan and A. Istanbullu"
  year: 2016
  title: "Chaos-based engineering applications with a 3D chaotic system without equilibrium points"
  venue: "Nonlinear Dynamics"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=ay-x+zy\\
  \dot{y}=-bxz-cx+zy+d\\
  \dot{z}=e-fxy-x^2
parameters_reported:
  a: 2.8
  b: 0.2
  c: 1.4
  d: 1
  e: 10
  f: 2
initial_conditions_reported:
  - [0, 0, 0]
equilibria_reported: "Cuatro equilibrios complejos, no reales, para parámetros reportados."
equilibrium_classification_reported: "complex_only; no real equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Muestreo global; no hay equilibrios reales."
bifurcation_plan: "Parámetros a,b,c,d,e,f; iniciar con a o e."
implementation_status: seed
notes: "El libro reporta matriz Jacobiana y autovalores para un equilibrio complejo."
```

## ch04_pham_modified_LE5_LE6

```yaml
system_id: ch04_pham_modified_le5_le6
name: Pham modified Jafari LE5/LE6 systems
source_chapter: 4
book_pages: [62, 63, 64]
primary_reference:
  authors: "V.-T. Pham, C. Volos and T. Kapitaniak"
  year: 2017
  title: "Systems with stable equilibria"
  venue: "Springer"
model_type: ode
dimension: 3
equations_latex: |
  \text{Modified LE5:}\quad
  \dot{x}=y,\quad \dot{y}=-1.5x+zy,\quad \dot{z}=-x^2+y^2-5xy+a.\\
  \text{Modified LE6:}\quad
  \dot{x}=y,\quad \dot{y}=-x+zy,\quad \dot{z}=0.04y^2-xy-0.1xz+a.
parameters_reported:
  a: 0.001
initial_conditions_reported:
  modified_LE5: [0.7, 1, 0]
  modified_LE6: [1, 2, 0]
equilibria_reported: "No equilibria for a != 0."
equilibrium_classification_reported: "No real equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Separar LE5 y LE6 como variantes independientes."
bifurcation_plan: "Parámetro a."
implementation_status: seed
notes: "Codex debe separar en `pham_modified_le5` y `pham_modified_le6`."
```

## ch04_pham_special_hidden

```yaml
system_id: ch04_pham_special_hidden
name: Pham special hidden-attractor system
source_chapter: 4
book_pages: [63, 64, 65]
primary_reference:
  authors: "V.-T. Pham et al."
  year: null
  title: null
  venue: null
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=0.4xz-a\\
  \dot{z}=0.3y-0.1z-1.4y^2-bxy-c
parameters_reported:
  a: 0.005
  b: 0.2
  c: 0
initial_conditions_reported:
  - [-1.53, 0.33, 0.39]
equilibria_reported:
  - "a=c=0: infinite equilibria E=(x,0,0)"
  - "a!=0 and c!=0: one equilibrium E=(-a/(4c),0,-10c)"
  - "a!=0 and c=0: no equilibria"
equilibrium_classification_reported: "Depends on a,b,c."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Tratar tres regímenes: línea de equilibrios, equilibrio único y no equilibrio."
bifurcation_plan: "Parámetros a y c."
implementation_status: seed
notes: "No clasificar como hidden verificado sin prueba de cuencas."
```

## ch04_pham_akgul_boostable

```yaml
system_id: ch04_pham_akgul_boostable
name: Pham-Akgul no-equilibrium system with boostable variable
source_chapter: 4
book_pages: [64, 65, 66]
primary_reference:
  authors: "V.-T. Pham, A. Akgul, C. Volos, S. Jafari and T. Kapitaniak"
  year: 2017
  title: "Dynamics and circuit realization of a no-equilibrium chaotic system with a boostable variable"
  venue: "AEU - International Journal of Electronics and Communications"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y+a\\
  \dot{y}=-x+z\\
  \dot{z}=-bx^2+z^2+c
parameters_reported:
  a: 1
  b: 0.8
  c: 2
initial_conditions_reported:
  - [0, 3, 0]
equilibria_reported: "No equilibria when b<1 for reported relation x^2=c/(b-1)."
equilibrium_classification_reported: "No real equilibria for b<1."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: [0.026, 0, -6.8624]
reported_dimension: 2.0038
basin_classification_plan: "Muestreo global; incluir variable boostable si se implementa."
bifurcation_plan: "Parámetro b alrededor de 1."
implementation_status: seed
notes: "Verificar relación de equilibrio y signo con PDF renderizado."
```

## ch04_wang_no_equilibrium_cubic

```yaml
system_id: ch04_wang_no_equilibrium_cubic
name: Wang no-equilibrium cubic system
source_chapter: 4
book_pages: [65, 66]
primary_reference:
  authors: "Z. Wang, A. Akgul, V.-T. Pham and S. Jafari"
  year: 2017
  title: "Chaos-based application of a novel no-equilibrium chaotic system with coexisting attractors"
  venue: "Nonlinear Dynamics"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=z\\
  \dot{z}=k_1xy+k_2xz+k_3yz+k_4y^3+k_5z^3+k_6
parameters_reported:
  k6: "nonzero"
  a: 0.49
  b: 0.75
initial_conditions_reported:
  - [0, 3, 0]
equilibria_reported: "No equilibria if k6 != 0."
equilibrium_classification_reported: "No equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: [0.034, 0, -0.173]
reported_dimension: null
basin_classification_plan: "Coexistencia de atractores: usar múltiples semillas y clustering."
bifurcation_plan: "Parámetros k_i; extraer parametrización exacta del capítulo."
implementation_status: seed_incomplete_parameters
notes: "La semilla conserva la forma general; Codex debe extraer los parámetros exactos usados en Fig. 10."
```

## ch04_NE1_to_NE17_table

```yaml
system_id: ch04_no_equilibrium_NE1_to_NE17
name: 17 simple chaotic systems without equilibria, NE1-NE17
source_chapter: 4
book_pages: [68, 69, 70, 71]
primary_reference:
  authors: "S. Jafari, J. C. Sprott and collaborators"
  year: 2013
  title: "Elementary quadratic chaotic flows with no equilibria"
  venue: "Physics Letters A"
model_type: ode
dimension: 3
equations_latex: "Ver tablas 1 y 2 del capítulo 4; extraer NE1-NE17 como sistemas independientes."
parameters_reported: "Parámetro a por caso en tablas."
initial_conditions_reported: "Tablas 1 y 2 reportan condición inicial por caso."
equilibria_reported: "No equilibria."
equilibrium_classification_reported: "No real equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: "Tablas 1 y 2."
reported_dimension: "Tablas 1 y 2."
basin_classification_plan: "Clasificar atractor caótico, toros si aparecen, transitorios y no acotados."
bifurcation_plan: "Usar parámetro a cuando exista."
implementation_status: pending_table_extraction
notes: "Extraer tabla completa con verificación visual."
```

## ch04_jafari_multiscroll

```yaml
system_id: ch04_jafari_multiscroll_no_equilibrium
name: Jafari multiscroll chaotic sea without equilibrium
source_chapter: 4
book_pages: [70, 72]
primary_reference:
  authors: "S. Jafari, V.-T. Pham and T. Kapitaniak"
  year: 2016
  title: "Multiscroll chaotic sea obtained from a simple 3D system without equilibrium"
  venue: "International Journal of Bifurcation and Chaos"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x+ayz+b y\sin(z)\\
  \dot{z}=1-y^2
parameters_reported:
  a: 0.1
  b: 2.9
initial_conditions_reported:
  torus: [0, 1, 0]
  multiscroll: [0, 5, 0]
equilibria_reported: "No equilibria."
equilibrium_classification_reported: "No equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Distinguir torus y mar caótico multiscroll por condición inicial."
bifurcation_plan: "Parámetros a,b; observable z o número de scrolls."
implementation_status: seed
notes: "Sistema basado en Sprott A con función seno."
```

## ch04_hu_multiscroll_i

```yaml
system_id: ch04_hu_multiscroll_i
name: Hu System I, sine improved Sprott A
source_chapter: 4
book_pages: [71, 73]
primary_reference:
  authors: "X. Hu, C. Liu, L. Liu, J. Ni and S. Li"
  year: 2016
  title: "Multi-scroll hidden attractors in improved Sprott A system"
  venue: "Nonlinear Dynamics"
model_type: ode
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x+yz-a\sin(2\pi b x)\\
  \dot{z}=1-y^2
parameters_reported:
  a: 25
  b: 1
initial_conditions_reported:
  - [0, 0.1, 0]
equilibria_reported: "No equilibria."
equilibrium_classification_reported: "No equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Número de scrolls depende del tiempo transitorio; registrar como fenómeno de transitorios largos."
bifurcation_plan: "Parámetros a,b y tiempo transitorio; observar número de scrolls."
implementation_status: seed
notes: "No confundir número de scrolls con atractores distintos sin análisis de cuencas."
```

## ch04_hu_multiscroll_ii

```yaml
system_id: ch04_hu_multiscroll_ii
name: Hu System II, sign-sine improved Sprott A
source_chapter: 4
book_pages: [73, 74]
primary_reference:
  authors: "X. Hu, C. Liu, L. Liu, J. Ni and S. Li"
  year: 2016
  title: "Multi-scroll hidden attractors in improved Sprott A system"
  venue: "Nonlinear Dynamics"
model_type: ode_discontinuous
dimension: 3
equations_latex: |
  \dot{x}=y\\
  \dot{y}=-x+yz-\frac{1}{2}a\sin(2\pi bx)[\operatorname{sgn}(x-c)-\operatorname{sgn}(x-d)]
  +x[2-\operatorname{sgn}(x-c)+\operatorname{sgn}(x-d)]\\
  \dot{z}=1-y^2
parameters_reported:
  c_d_examples:
    - {c: -1.5, d: 1.5, scrolls: 3}
    - {c: -2.5, d: 3.5, scrolls: 6}
    - {c: -4.5, d: 4.5, scrolls: 9}
initial_conditions_reported: []
equilibria_reported: "No equilibria."
equilibrium_classification_reported: "No equilibria."
equilibria_to_compute: true
equilibrium_classification_to_compute: true
reported_les: []
reported_dimension: null
basin_classification_plan: "Sistema discontinuo; usar integrador robusto y clasificar número de scrolls por rango."
bifurcation_plan: "Parámetros c,d; observable número de scrolls."
implementation_status: pending_piecewise_engine
notes: "Implementar sgn con cuidado y documentar discontinuidades."
```

---

# Referencias iniciales extraídas o mencionadas

- Lorenz, E. N. (1963). Deterministic nonperiodic flow. *Journal of the Atmospheric Sciences*, 20(2), 130-141.
- Rössler, O. E. (1976/1979). Sistemas de Rössler reportados en el capítulo de introducción; verificar referencia exacta en bibliografía del capítulo 1.
- Chen, G., & Ueta, T. (1999). Yet another chaotic attractor. *International Journal of Bifurcation and Chaos*, 9(7), 1465-1466.
- Lü, J., Chen, G., & Zhang, S. (2002). The compound structure of a new chaotic attractor. *Chaos, Solitons & Fractals*, 14(5), 669-672.
- Sprott, J. C. (1994). Some simple chaotic flows. *Physical Review E*, 50(2), R647.
- Wang, X., & Chen, G. (2012). A chaotic system with only one stable equilibrium. *Communications in Nonlinear Science and Numerical Simulation*, 17(3), 1264-1272.
- Sprott, J. C., Wang, X., & Chen, G. (2013). Coexistence of point, periodic and strange attractors. *International Journal of Bifurcation and Chaos*, 23(05), 1350093.
- Molaie, M., Jafari, S., & Golpayegani, S. M. R. H. (2013). Simple chaotic flows with one stable equilibrium. *International Journal of Bifurcation and Chaos*, 23(11).
- Wei, Z. (2011). Dynamical behaviors of a chaotic system with no equilibria. *Physics Letters A*, 376(2), 102-108.
- Jafari, S., Sprott, J. C., & Golpayegani, S. M. R. H. (2013). Elementary quadratic chaotic flows with no equilibria. *Physics Letters A*, 377(9), 699-702.
- Hu, X., Liu, C., Liu, L., Ni, J., & Li, S. (2016). Multi-scroll hidden attractors in improved Sprott A system. *Nonlinear Dynamics*, 86(3), 1725-1734.

# Pendientes críticos para Codex

1. Completar extracción de tablas SE1-SE23 y NE1-NE17 con verificación visual.
2. Procesar capítulos 5-27 con el mismo esquema.
3. Resolver referencias exactas desde la bibliografía de cada capítulo.
4. Agregar DOI de cada referencia cuando aparezca o pueda resolverse de forma confiable.
5. No marcar ningún atractor como `hidden_verified` sin pruebas de cuencas y vecindades de equilibrios.
