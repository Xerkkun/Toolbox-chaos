# Prompt para Codex: catálogo de sistemas del libro de Wang, Kuznetsov y Chen (2021)

Quiero que construyas incrementalmente un catálogo computable de los sistemas dinámicos mencionados en el libro ubicado en `sources/`:

`Chaotic Systems with Multistability and Hidden Attractors`, Xiong Wang, Nikolay V. Kuznetsov y Guanrong Chen (eds.), Springer, 2021, DOI `10.1007/978-3-030-75821-9`.

El objetivo es agregar al proyecto, capítulo por capítulo, los sistemas citados en el libro junto con sus ecuaciones, parámetros, condiciones iniciales reportadas, equilibrios, clasificación de equilibrios, configuración para cuencas de atracción y configuración para diagramas de bifurcación. El trabajo debe ser trazable, reproducible y verificable. No hagas una extracción superficial: cada ecuación debe quedar vinculada a página/capítulo/referencia y cada sistema debe tener una prueba mínima que confirme que su implementación reproduce el campo vectorial y los equilibrios esperados.

## Reglas de trabajo

1. Primero audita la estructura actual del repositorio. Localiza dónde están definidos los sistemas, presets, validadores, ejemplos, documentación y pruebas. No dupliques catálogos existentes; extiéndelos.
2. Trabaja por capítulos y registra avance en `docs/sources/wang2021_progress.md`. No intentes completar todo el libro en una sola modificación.
3. Usa el PDF solo como fuente de extracción. No confíes ciegamente en OCR para ecuaciones: revisa visualmente la página renderizada cuando haya ambigüedad entre variables como `x`, `z`, signos, puntos decimales, exponentes, parámetros o funciones por tramos.
4. No copies párrafos largos del libro. Extrae solamente metadatos técnicos: ecuaciones, parámetros, condiciones iniciales, equilibrios, exponentes de Lyapunov reportados, dimensiones, rangos de bifurcación, referencias y notas de clasificación.
5. Cada sistema debe tener un `system_id` estable en snake_case, por ejemplo `sprott_a`, `wang_chen_stable_equilibrium`, `wei_no_equilibrium`, `hu_multiscroll_i`.
6. Si un sistema tiene varias variantes, usa un sistema base y variantes explícitas. Ejemplo: `sprott_a`, `sprott_a_pham_shifted`, `sprott_a_hu_sine`, `sprott_a_hu_sign_sine`.
7. Diferencia entre lo reportado por el libro y lo calculado por el código. Usa campos separados: `reported_equilibria`, `computed_equilibria`, `reported_les`, `computed_les`, `reported_classification`, `computed_classification`.
8. Todo cálculo simbólico o numérico debe ser reproducible mediante scripts/CLI y pruebas.
9. Para sistemas con retardos, impulsos, fraccionarios, memristivos, discontinuos o por tramos, no fuerces su integración en el mismo motor ODE estándar. Regístralos con `model_type` apropiado y marca `simulation_status: pending_engine` si aún no existe integrador adecuado.
10. Si el libro reporta “hidden attractor”, regístralo como `reported_hidden`; no lo conviertas en `verified_hidden` hasta que se pasen pruebas de vecindad de equilibrios/cuencas.

## Entregables por capítulo

Para cada capítulo procesado entrega:

1. Archivo de datos en Markdown: `data/wang2021/chXX_<slug>.md`.
2. Archivo de datos estructurado: `data/wang2021/chXX_<slug>.yaml` o `.json`.
3. Implementaciones de sistemas en el módulo apropiado del repositorio.
4. Presets mínimos de simulación por sistema.
5. Pruebas unitarias de:
   - evaluación del campo vectorial;
   - Jacobiano, cuando aplique;
   - equilibrios calculados;
   - clasificación local por autovalores;
   - carga del preset;
   - ausencia de duplicados de `system_id`.
6. Pruebas de humo para integrar al menos una trayectoria corta por sistema ODE estándar.
7. Actualización de `docs/sources/wang2021_progress.md` con casillas de avance por sistema.

## Esquema obligatorio para cada sistema

Usa este esquema como mínimo:

```yaml
system_id: string
name: string
aliases: []
source:
  book: "Wang, Kuznetsov & Chen (eds.), 2021"
  chapter_number: int
  chapter_title: string
  pages: []
  equation_numbers: []
  table_numbers: []
  figure_numbers: []
primary_reference:
  authors: string
  year: int | null
  title: string | null
  venue: string | null
  doi: string | null
model:
  model_type: ode | dde | fractional_ode | memristive_ode | impulsive_dde | piecewise_affine | jerk | hyperchaotic | map | other
  dimension: int | null
  state_variables: []
  parameters: {}
  equations_latex: string
  equations_machine:
    x: string
    y: string
    z: string
    w: string | null
reported_dynamics:
  attractor_type: self_excited | hidden | hidden_candidate | multistable | conservative_chaotic_sea | periodic | torus | unknown
  lyapunov_exponents: []
  kaplan_yorke_dimension: float | null
  entropy: float | null
  notes: string
initial_conditions:
  reported: []
  recommended_for_reproduction: []
equilibria:
  reported: []
  computed_symbolic: []
  computed_numeric: []
  classification: []
classification_rules:
  local_equilibrium: string
  hidden_attractor_rule: string
basin_analysis:
  status: pending | configured | computed
  sections:
    - plane: string
      fixed_values: {}
      ranges: {}
      resolution: []
  outcome_labels:
    - equilibrium_i
    - periodic_orbit_i
    - chaotic_attractor_i
    - torus_i
    - unbounded
    - transient_unknown
  classifier_features:
    - final_distance_to_equilibria
    - finite_time_lyapunov
    - poincare_signature
    - rms_amplitude
    - spectral_entropy
bifurcation:
  status: pending | configured | computed
  parameter: string | null
  range: []
  samples: int | null
  observable: string
  transient_time: float | null
  sample_time: float | null
  section: string | null
implementation:
  file: string | null
  preset_file: string | null
  test_file: string | null
  simulation_status: implemented | pending | pending_engine
validation:
  equation_verified_against_pdf: false
  equilibria_verified: false
  smoke_simulation_passed: false
  notes: string
```

## Cálculo de equilibrios y clasificación

Para cada sistema ODE estándar:

1. Construye `f(x, p)`.
2. Calcula el Jacobiano `J = Df(x, p)` con SymPy cuando sea posible.
3. Resuelve `f(x, p)=0`:
   - solución simbólica si es simple;
   - solución numérica para parámetros reportados si lo simbólico no es viable;
   - si no hay solución real, marcar `no_real_equilibria`;
   - si hay línea, curva o superficie de equilibrios, representar paramétricamente.
4. Clasifica cada equilibrio por autovalores:
   - `stable_node`, `stable_focus`, `stable_node_focus`, `unstable_node`, `unstable_focus`, `saddle`, `saddle_focus`, `center`, `degenerate`, `nonhyperbolic`, `line_equilibrium`, `surface_equilibrium`, `complex_only`, `none`.
5. Para sistemas fraccionarios, agrega también condición de estabilidad tipo Matignon cuando aplique.

## Clasificación de trayectorias para cuencas de atracción

Implementa un clasificador numérico común. Cada trayectoria debe clasificarse con reglas explícitas:

1. `unbounded`: si `||x(t)||` excede un umbral configurado.
2. `equilibrium_i`: si la distancia final al equilibrio `i` es menor que una tolerancia y la velocidad final es pequeña.
3. `periodic_orbit_i`: si el retorno de Poincaré o autocorrelación muestra periodicidad estable y el mayor exponente de Lyapunov finito no es positivo.
4. `chaotic_attractor_i`: si la trayectoria queda acotada, no converge a equilibrio, y el mayor exponente de Lyapunov finito es positivo dentro de tolerancia.
5. `torus_i`: si queda acotada, no converge, tiene espectro cuasiperiódico y exponente mayor aproximadamente cero.
6. `transient_unknown`: si no hay tiempo suficiente para decidir.

Genera cuencas en cortes 2D de forma reproducible:

```yaml
basin_grid:
  plane: "z = z0"
  axes: [x, y]
  ranges:
    x: [-5, 5]
    y: [-5, 5]
  fixed_values:
    z: 0
  resolution: [400, 400]
  t_transient: 500
  t_final: 1000
  dt: 0.01
  integrator: auto
```

Para sistemas con múltiples atractores, guarda también semillas representativas por clase.

## Diagramas de bifurcación

Para cada sistema:

1. Usa el parámetro reportado en el libro si existe.
2. Si no existe, usa un parámetro natural del sistema y marca `bifurcation_parameter_inferred: true`.
3. Guarda configuración:
   - parámetro;
   - rango;
   - número de muestras;
   - observable (`x`, `y`, `z`, norma o sección de Poincaré);
   - tiempo transitorio;
   - tiempo de muestreo;
   - condición inicial;
   - estrategia de continuación: reinicio fijo o continuación por último estado.
4. Calcula y exporta puntos de bifurcación a CSV/Parquet y figura a PNG/PDF.

## Avance sugerido por fases

Fase 1. Capítulo 1 e índice base:
- Lorenz, Rössler, Chua, Chen, sistema unificado Lorenz-Chen, Sprott A-S.
- Crear catálogo base, validadores y pruebas.

Fase 2. Capítulo 3:
- Sistemas con equilibrios estables: Wang-Chen, Wei, Wang-Chen con retardos, Lao, Kingni, sistema derivado de línea de equilibrios, jerk SE1-SE23, Yang-Chen, Yang-Wei y variantes.

Fase 3. Capítulo 4:
- Sistemas sin equilibrios: Sprott A, Wei, Wang-Chen sin equilibrio, Maaita, Akgul, Pham, Wang, Jafari multiscroll, Hu I y Hu II.

Fase 4. Capítulos 5-7:
- Curvas, superficies y número arbitrario de equilibrios.

Fase 5. Capítulos 8-11:
- Sistemas hipercaóticos, fraccionarios, memristivos y jerk.

Fase 6. Capítulos 12-16:
- Multiestabilidad, simetría, asimetría, simetría condicional, autorreproducción y detección.

Fase 7. Capítulos 17-27:
- Sistemas impulsivos con retardo, algoritmos, sistema con seno, 4D con infinitos equilibrios, sistemas por tramos, sistemas nuevos de capítulos 22-24 y atractores globales.

## Criterios de aceptación

Una fase queda aceptada solo si:

1. Los sistemas del capítulo tienen entrada Markdown y YAML/JSON.
2. Las ecuaciones fueron revisadas contra el PDF renderizado.
3. Los equilibrios reportados y calculados coinciden, o las diferencias están documentadas.
4. Las clasificaciones locales están calculadas por autovalores.
5. Hay al menos un preset de trayectoria por sistema implementable.
6. Hay configuración de cuencas y bifurcación, aunque el cálculo pesado puede quedar en `pending`.
7. La documentación de progreso muestra qué está implementado, qué está pendiente y qué requiere motor especial.

## Primera tarea concreta

Empieza con Fase 1. Crea el catálogo base y agrega los sistemas clásicos y Sprott A-S. Después ejecuta pruebas de equilibrios y clasificación. Entrega un resumen con:

- archivos creados/modificados;
- sistemas agregados;
- sistemas que requieren verificación manual de ecuaciones por posible error OCR;
- pruebas ejecutadas;
- pendientes para el siguiente capítulo.
