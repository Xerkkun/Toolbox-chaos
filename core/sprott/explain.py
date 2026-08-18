"""explain.py — pipeline educativo para el Explorador Sprott.

Proporciona una explicación textual paso a paso del proceso completo que
la toolbox lleva a cabo para transformar un código de tipo Sprott en una
trayectoria visualizable.  El contenido es una reimplementación educativa
propia; se cita a Sprott únicamente como referencia de inspiración.

Referencia de inspiración:
    Julien C. Sprott, *Strange Attractors: Creating Patterns in Chaos*,
    M&T Books, 1993.  Esta implementación no reproduce texto del libro.

Uso:
    from core.sprott.explain import explain_code_pipeline, format_explanation_markdown

    data = explain_code_pipeline("EWMWAMMMPMMMM", n_iter=900, transient=150,
                                  h=0.01, method="rk4", visual_config=None)
    md = format_explanation_markdown(data)
"""
from __future__ import annotations

from math import comb

from .codes import SprottCode, decode_code, describe_family
from .monomials import monomial_label, multi_indices
from .visual import SprottVisualConfig, sanitize_visual_config


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _clean_code_text(raw: str) -> str:
    """Replica la limpieza interna de decode_code sin importar el privado."""
    return ''.join(ch for ch in str(raw).strip().upper() if not ch.isspace() and ch not in {'-', '_'})


def _coefficient_table(raw_text: str, code: SprottCode) -> list[dict]:
    """Construye la tabla char → valor para los coeficientes del código."""
    cleaned = _clean_code_text(raw_text)
    coeff_chars = cleaned[1:]  # sin la primera letra de familia
    table = []
    for idx, ch in enumerate(coeff_chars[:len(code.coefficients)]):
        table.append({
            'index': idx,
            'char': ch,
            'ord': ord(ch),
            'value': round((ord(ch) - 77) / 10.0, 6),
        })
    return table


def _monomial_basis(dimension: int, order: int) -> list[str]:
    """Devuelve las etiquetas de los monomios en el orden canónico de la toolbox."""
    if dimension < 1 or order < 0:
        return []
    labels = ('x', 'y', 'z', 'w')[:dimension]
    indices = multi_indices(dimension, order)
    return [monomial_label(idx, labels) for idx in indices]


def _coefficient_matrix_as_list(code: SprottCode) -> list[list[float]]:
    """Devuelve la matriz de coeficientes como lista de listas (serializable)."""
    if code.kind not in {'map', 'flow'} or code.dimension < 1:
        return []
    try:
        indices = multi_indices(code.dimension, code.order)
    except Exception:
        return []
    n_monomials = len(indices)
    expected_total = code.dimension * n_monomials
    coeffs = list(code.coefficients) + [0.0] * max(0, expected_total - len(code.coefficients))
    matrix = []
    for row_idx in range(code.dimension):
        start = row_idx * n_monomials
        matrix.append([round(v, 6) for v in coeffs[start:start + n_monomials]])
    return matrix


def _equations_text(code: SprottCode) -> str:
    """Reconstruye las ecuaciones a partir del código; no requiere simulación."""
    if code.kind == 'special':
        from core.sprott.special_families import SPECIAL_FAMILY_REGISTRY
        family_entry = SPECIAL_FAMILY_REGISTRY.get(code.family_letter)
        if family_entry is not None and not isinstance(family_entry, dict):
            try:
                family = family_entry(code.coefficients)
                return family.equations_text()
            except Exception as exc:
                return f'(no se pudieron reconstruir las ecuaciones especiales: {exc})'
        else:
            return '(ecuaciones no disponibles: familia especial no implementada o pendiente de validación)'
    if code.kind not in {'map', 'flow'} or code.dimension < 1:
        return '(ecuaciones no disponibles para esta familia)'
    try:
        from .families import PolynomialMapFamily, PolynomialFlowFamily
        if code.kind == 'map':
            family = PolynomialMapFamily(code.dimension, code.order, code.coefficients)
        else:
            family = PolynomialFlowFamily(code.dimension, code.order, code.coefficients)
        return family.equations_text()
    except Exception as exc:
        return f'(no se pudieron reconstruir las ecuaciones: {exc})'


def _classification_rules() -> list[dict]:
    """Devuelve una descripción de los cuatro criterios de clasificación."""
    return [
        {
            'rule': 'divergente',
            'condition': 'norma del estado ≥ umbral o aparece NaN/Inf',
            'description': (
                'La trayectoria sale del espacio acotado definido por el umbral de divergencia. '
                'Esto suele ocurrir cuando los coeficientes generan retroalimentación explosiva '
                'o cuando el paso de integración h es demasiado grande para un flujo.'
            ),
        },
        {
            'rule': 'punto fijo',
            'condition': 'spread de la cola < tolerancia (default 1e-6)',
            'description': (
                'Los últimos estados de la trayectoria convergen a un único punto en el espacio '
                'de fase. Es la situación más simple: el sistema "muere" en un equilibrio estable.'
            ),
        },
        {
            'rule': 'baja complejidad',
            'condition': 'spread de la cola < 1e-4 ó ratio de estados únicos < 20%',
            'description': (
                'La órbita es acotada pero se repite con demasiada regularidad. '
                'Puede indicar periodicidad, quasi-periodicidad simple, o que se necesitan '
                'más iteraciones para revelar estructura caótica.'
            ),
        },
        {
            'rule': 'candidato caótico',
            'condition': 'acotado, no colapsado, ratio de estados únicos ≥ 20%',
            'description': (
                'La trayectoria permanece dentro del umbral, no colapsa a un punto fijo '
                'y muestra variedad suficiente de estados. Esto es necesario pero no suficiente '
                'para confirmar caos: se requeriría calcular el exponente de Lyapunov máximo '
                'o la dimensión de correlación para mayor certeza.'
            ),
        },
    ]


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def explain_code_pipeline(
    code: str,
    n_iter: int,
    transient: int,
    h: float,
    method: str,
    visual_config: 'SprottVisualConfig | dict | None' = None,
) -> dict:
    """Genera un diccionario serializable con el pipeline completo.

    Parameters
    ----------
    code:
        Cadena de código estilo Sprott, p.ej. ``"EWMWAMMMPMMMM"``.
    n_iter:
        Número total de iteraciones o pasos de integración solicitados.
    transient:
        Número de puntos iniciales que se descartan antes de graficar.
    h:
        Paso temporal para flujos (ignorado para mapas).
    method:
        Método numérico: ``"rk4"`` o ``"euler"`` (solo relevante para flujos).
    visual_config:
        Configuración visual activa (``SprottVisualConfig``, dict o ``None``).

    Returns
    -------
    dict
        Diccionario completamente serializable (sin objetos numpy ni tipos
        de datos Qt) con todas las etapas del pipeline documentadas.
    """
    # --- Paso 1 & 2: código original y limpieza ---
    raw_code = str(code)
    cleaned_code = _clean_code_text(raw_code)

    # --- Paso 3: primera letra y familia ---
    decoded: SprottCode = decode_code(raw_code)
    family_letter = decoded.family_letter
    family_name = decoded.family_name
    kind = decoded.kind
    dimension = decoded.dimension
    order = decoded.order

    # --- Paso 5 & 6: dimensión y orden; ya en el SprottCode ---

    # --- Paso 7: número de monomios C(D+O, O) ---
    monomial_count = comb(dimension + order, order) if dimension > 0 and order >= 0 else 0

    # --- Paso 8: coeficientes esperados D × C(D+O, O) ---
    coefficient_count_expected = dimension * monomial_count if dimension > 0 else 0

    # --- Paso 9: tabla letra → coeficiente ---
    coefficient_table = _coefficient_table(raw_code, decoded)
    coefficient_count_received = len(decoded.coefficients)

    # --- Paso 10: base de monomios ---
    monomial_basis = _monomial_basis(dimension, order) if dimension > 0 and order >= 0 else []

    # --- Paso 11: matriz de coeficientes ---
    coefficient_matrix = _coefficient_matrix_as_list(decoded)

    # --- Paso 12: ecuaciones reconstruidas ---
    equations_text = _equations_text(decoded)

    # --- Paso 13: condición inicial ---
    initial_condition = [0.1] * dimension if dimension > 0 else []

    # --- Paso 14: modo de simulación y método numérico ---
    if kind == 'map':
        simulation_mode = 'iteración directa'
        numerical_method = 'N/A (mapas no integran EDO)'
    elif kind == 'flow':
        simulation_mode = 'integración numérica (EDO)'
        numerical_method = 'RK4 (Runge-Kutta de 4° orden)' if method.lower() == 'rk4' else 'Euler (método de primer orden)'
    else:
        simulation_mode = 'no simulable'
        numerical_method = 'N/A'

    # --- Paso 15 & 16: iteraciones y transitorio ---
    n_iter_int = int(n_iter)
    transient_int = int(transient)

    # --- Paso 17: criterios de clasificación ---
    classification_rules = _classification_rules()

    # --- Paso 18: configuración visual ---
    vcfg = sanitize_visual_config(visual_config)
    visual_projection = vcfg.projection
    visual_color_by = vcfg.color_by
    visual_palette = vcfg.palette
    visual_max_points = vcfg.max_points

    return {
        # Código
        'raw_code': raw_code,
        'cleaned_code': cleaned_code,
        # Familia
        'family_letter': family_letter,
        'family_name': family_name,
        'kind': kind,
        # Estructura polinomial
        'dimension': dimension,
        'order': order,
        'monomial_count': monomial_count,
        'coefficient_count_expected': coefficient_count_expected,
        'coefficient_count_received': coefficient_count_received,
        # Coeficientes
        'coefficient_table': coefficient_table,
        'monomial_basis': monomial_basis,
        'coefficient_matrix': [[float(v) for v in row] for row in coefficient_matrix],
        # Ecuaciones
        'equations_text': equations_text,
        # Simulación
        'initial_condition': [float(v) for v in initial_condition],
        'simulation_mode': simulation_mode,
        'numerical_method': numerical_method,
        'n_iter': n_iter_int,
        'transient': transient_int,
        # Clasificación
        'classification_rules': classification_rules,
        # Visual
        'visual_projection': visual_projection,
        'visual_color_by': visual_color_by,
        'visual_palette': visual_palette,
        'visual_max_points': int(visual_max_points),
        # Advertencias del decodificador
        'warnings': list(decoded.warnings),
    }


def format_explanation_markdown(explanation: dict) -> str:
    """Convierte el dict de ``explain_code_pipeline`` en texto Markdown didáctico.

    El texto está redactado con lenguaje propio y cita a Sprott únicamente
    como fuente de inspiración en el encabezado.

    Parameters
    ----------
    explanation:
        Diccionario devuelto por ``explain_code_pipeline``.

    Returns
    -------
    str
        Texto Markdown listo para mostrar o exportar.
    """
    e = explanation
    kind = e.get('kind', 'unknown')
    dim = e.get('dimension', 0)
    order = e.get('order', 0)
    var_names = ('x', 'y', 'z', 'w')[:dim] if dim > 0 else ('x',)

    lines: list[str] = []

    # --- Encabezado ---
    lines += [
        '# Pipeline completo del Explorador Sprott',
        '',
        '> **Referencia de inspiración:** Julien C. Sprott, *Strange Attractors: Creating Patterns in Chaos*,',
        '> M\\&T Books, 1993.  Esta explicación es una reimplementación educativa propia y',
        '> no reproduce texto ni figuras del libro.',
        '',
        '---',
        '',
    ]

    # --- Paso 1 & 2: código ---
    lines += [
        '## 1 · Código original y limpieza',
        '',
        f'**Código original:** `{e.get("raw_code", "")}`',
        '',
        f'**Código limpio:** `{e.get("cleaned_code", "")}`',
        '',
        'Antes de cualquier operación, la toolbox normaliza el texto: convierte a mayúsculas,',
        'elimina espacios, guiones y subrayados.  Esto permite que el usuario escriba códigos',
        'con separadores visuales sin afectar la decodificación.',
        '',
    ]

    # --- Paso 3: familia ---
    lines += [
        '## 2 · Primera letra y familia detectada',
        '',
        f'**Letra de familia:** `{e.get("family_letter", "?")}`',
        '',
        f'**Nombre de familia:** {e.get("family_name", "desconocida")}',
        '',
        f'**Tipo:** `{kind}`',
        '',
        'La primera letra del código actúa como índice en una tabla de 26 familias predefinidas.',
        'Las familias A–D son mapas 1D; E–H, mapas 2D; I–L, mapas 3D; M–P, mapas 4D;',
        'Q–T, flujos 3D; U–X, flujos 4D; Y–Z son familias especiales con funciones no polinomiales.',
        '',
    ]

    # --- Paso 4: tipo ---
    # --- Paso 4: tipo ---
    if kind == 'map':
        tipo_desc = (
            'Un **mapa** es una regla de recurrencia discreta: dado el estado actual, '
            'la siguiente iteración se obtiene aplicando directamente el polinomio.  '
            'No hay integración de tiempo continuo.'
        )
    elif kind == 'flow':
        tipo_desc = (
            'Un **flujo** es un sistema de ecuaciones diferenciales ordinarias (EDO).  '
            'La evolución continua en el tiempo se aproxima discretamente mediante un '
            'integrador numérico (Euler o RK4).'
        )
    elif kind == 'special':
        tipo_desc = (
            'Una **familia especial** utiliza funciones no polinomiales (valores absolutos, senos, rotaciones, etc.). '
            'La Chaos Toolbox implementa soporte y simulación nativa en Python/NumPy para las familias '
            'Y (Valores absolutos), `[` (Potencias de valores absolutos), `\\` (Senos), `]` (Rotaciones) y `^` (Oscilador forzado).'
        )
    else:
        tipo_desc = 'Familia especial o desconocida; no implementada en este ciclo.'

    lines += [
        '## 3 · Tipo: mapa / flujo / especial',
        '',
        tipo_desc,
        '',
    ]

    # --- Pasos 5 & 6: D y O ---
    lines += [
        '## 4 · Dimensión D y orden O',
        '',
        f'**Dimensión D = {dim}** — número de variables del sistema: {", ".join(var_names)}.',
        '',
        f'**Orden O = {order}** — grado máximo de los monomios en el polinomio.',
        '',
        'Juntos determinan el tamaño de la base polinomial y, por tanto, la cantidad de',
        'coeficientes que el código debe proporcionar.',
        '',
    ]

    # --- Pasos 7 & 8: conteos ---
    mono = e.get('monomial_count', 0)
    coeff_exp = e.get('coefficient_count_expected', 0)
    coeff_rec = e.get('coefficient_count_received', 0)

    if kind == 'special':
        lines += [
            '## 5 · Conteo de coeficientes especiales',
            '',
            f'**Coeficientes esperados para esta familia especial:** **{coeff_exp}**',
            '',
            f'**Coeficientes recibidos en el código:** **{coeff_rec}**',
            '',
        ]
    else:
        lines += [
            '## 5 · Conteo de monomios y coeficientes',
            '',
            f'**Número de monomios por ecuación:** C(D+O, O) = C({dim}+{order}, {order}) = **{mono}**',
            '',
            f'**Coeficientes esperados:** D × C(D+O, O) = {dim} × {mono} = **{coeff_exp}**',
            '',
            f'**Coeficientes recibidos en el código:** **{coeff_rec}**',
            '',
        ]
        
    if coeff_rec < coeff_exp:
        lines.append(
            f'> ⚠️ Faltan {coeff_exp - coeff_rec} coeficiente(s); se tratan como cero.'
        )
    elif coeff_rec > coeff_exp:
        lines.append(
            f'> ℹ️ Hay {coeff_rec - coeff_exp} coeficiente(s) extra; se ignoran en la simulación.'
        )
    else:
        lines.append('> ✔️ El conteo de coeficientes es exacto.')
    lines.append('')

    # --- Paso 9: tabla letra → coeficiente ---
    lines += [
        '## 6 · Tabla letra → coeficiente',
        '',
        'Cada carácter del código (excepto la primera letra de familia) representa un número',
        'real mediante la fórmula: **valor = (ord(letra) − 77) / 10**.  La letra M (ASCII 77)',
        'equivale a 0.0; letras anteriores son negativas, posteriores son positivas.',
        '',
        '| # | Letra | ord | Valor |',
        '|---|-------|-----|-------|',
    ]
    for entry in e.get('coefficient_table', []):
        lines.append(f'| {entry["index"]:3d} | `{entry["char"]}` | {entry["ord"]} | {entry["value"]:+.4f} |')
    lines.append('')

    # --- Paso 10: base de monomios ---
    if kind == 'special':
        lines += [
            '## 7 · Estructura matemática especial',
            '',
            'Esta familia no es polinomial y, por lo tanto, no genera una base de monomios standard. '
            'En su lugar, las variables del estado actual `(X, Y)` se mapean directamente utilizando '
            'funciones no lineales, y se acompañan de variables auxiliares `Z` y `W`.',
            '',
        ]
    else:
        basis = e.get('monomial_basis', [])
        lines += [
            '## 7 · Base de monomios generada',
            '',
            f'Con D={dim} y O={order} se obtienen **{mono}** monomios en orden canónico:',
            '',
            ', '.join(f'`{m}`' for m in basis) if basis else '*(sin monomios)*',
            '',
            'El orden sigue el patrón de grado creciente: primero el término constante (1),',
            'luego los lineales, cuadráticos, etc., con las variables en orden lexicográfico inverso.',
            '',
        ]

    # --- Paso 11: matriz de coeficientes ---
    if kind == 'special':
        lines += [
            '## 8 · Vector de coeficientes especiales',
            '',
            'Los coeficientes recibidos se aplican secuencialmente como parámetros '
            'específicos de las ecuaciones no lineales de la familia.',
            '',
        ]
    else:
        matrix = e.get('coefficient_matrix', [])
        lines += [
            '## 8 · Matriz de coeficientes',
            '',
            f'La matriz tiene forma **{dim} × {mono}** (una fila por variable de salida, una columna por monomio):',
            '',
        ]
        if matrix and basis:
            header = '| Var | ' + ' | '.join(f'`{m}`' for m in basis) + ' |'
            sep = '|-----|' + '|'.join(['------'] * len(basis)) + '|'
            lines += [header, sep]
            for row_idx, row in enumerate(matrix):
                var = var_names[row_idx] if row_idx < len(var_names) else f'x{row_idx}'
                cells = ' | '.join(f'{v:+.4f}' for v in row)
                lines.append(f'| **{var}** | {cells} |')
        else:
            lines.append('*(matriz no disponible para esta familia)*')
        lines.append('')

    # --- Paso 12: ecuaciones ---
    if kind == 'special':
        lines += [
            '## 9 · Ecuaciones y variables auxiliares',
            '',
            'Las ecuaciones no lineales del sistema definen la evolución de las variables de estado.',
            'Adicionalmente, se calculan dos variables auxiliares para la visualización en 3D o 4D:',
            '- **Z**: Representa la distancia radial cuadrática (`X^2 + Y^2`) o una fase angular modulo `2*pi`.',
            '- **W**: Indica el progreso relativo de la iteración (`(N - 1000) / (NMAX - 1000)`), '
            'el cual es útil para aplicar paletas de color dependientes del tiempo o el progreso de simulación.',
            '',
            '```',
            e.get('equations_text', '(no disponible)'),
            '```',
            '',
        ]
    else:
        lines += [
            '## 9 · Ecuaciones reconstruidas',
            '',
            'Las ecuaciones se forman multiplicando cada fila de la matriz por el vector de monomios:',
            '',
            '```',
            e.get('equations_text', '(no disponible)'),
            '```',
            '',
        ]

    # --- Paso 13: condición inicial ---
    ic = e.get('initial_condition', [])
    lines += [
        '## 10 · Condición inicial',
        '',
        f'**x₀ = [{", ".join(str(v) for v in ic)}]**',
        '',
        'Esta toolbox usa la condición inicial estándar x₀ = 0.1 en cada dimensión.',
        'Se eligió un valor pequeño y no nulo para evitar que el sistema quede atrapado',
        'en el origen en sistemas con simetría.',
        '',
    ]

    # --- Paso 14: método de simulación ---
    lines += [
        '## 11 · Método de simulación',
        '',
        f'**Modo:** {e.get("simulation_mode", "desconocido")}',
        '',
        f'**Método numérico:** {e.get("numerical_method", "N/A")}',
        '',
    ]
    if kind == 'map':
        lines += [
            'Para mapas se aplica la función polinomial directamente en cada paso:',
            'el estado siguiente es simplemente F(estado actual), sin integración.',
            '',
        ]
    elif kind == 'flow':
        method_used = e.get('numerical_method', '')
        if 'RK4' in method_used:
            lines += [
                'El integrador RK4 evalúa el campo vectorial cuatro veces por paso,',
                'combinando las evaluaciones con pesos 1/6, 1/3, 1/3, 1/6.',
                'Esto da un error de truncamiento de orden O(h⁵) por paso, mucho',
                'más preciso que Euler para la misma longitud de paso h.',
                '',
            ]
        else:
            lines += [
                'El método de Euler avanza el estado con un solo paso lineal:',
                'x(t+h) ≈ x(t) + h·F(x(t)).  Es el esquema más simple, útil para',
                'exploración rápida, pero puede acumular error significativo.',
                '',
            ]

    # --- Paso 15 & 16: iteraciones y transitorio ---
    n_iter_val = e.get('n_iter', 0)
    transient_val = e.get('transient', 0)
    used = max(0, n_iter_val - transient_val)

    lines += [
        '## 12 · Iteraciones y transitorio',
        '',
        f'**Total de pasos calculados:** {n_iter_val}',
        '',
        f'**Transitorio descartado:** {transient_val} pasos ({100.0 * transient_val / max(1, n_iter_val):.1f}%)',
        '',
        f'**Pasos usados para análisis y visualización:** ≈ {used}',
        '',
        'El transitorio es el período inicial durante el cual la órbita aún no ha alcanzado',
        'su comportamiento asintótico típico.  Descartarlo evita que el arranque contamine',
        'la gráfica y los cálculos estadísticos.',
        '',
    ]

    # --- Paso 17: criterios de clasificación ---
    lines += [
        '## 13 · Criterios de clasificación',
        '',
        'Una vez descartado el transitorio, la toolbox aplica cuatro filtros rápidos en orden:',
        '',
    ]
    for rule in e.get('classification_rules', []):
        lines += [
            f'### {rule["rule"].capitalize()}',
            '',
            f'**Condición:** {rule["condition"]}',
            '',
            rule['description'],
            '',
        ]

    # --- Paso 18: visualización ---
    lines += [
        '## 14 · Configuración de visualización',
        '',
        f'**Proyección:** `{e.get("visual_projection", "x-y")}`  ',
        f'**Color por:** `{e.get("visual_color_by", "constante")}`  ',
        f'**Paleta:** `{e.get("visual_palette", "Sprott clasica")}`  ',
        f'**Máx. puntos:** {e.get("visual_max_points", 20000)}',
        '',
        'La proyección determina qué par de variables (o cuál variable vs. tiempo) se traza.',
        'El color puede codificar tiempo, radio, velocidad o el valor de una variable,',
        'añadiendo una dimensión extra de información a la gráfica 2D.',
        '',
    ]

    # --- Advertencias ---
    warnings = e.get('warnings', [])
    if warnings:
        lines += [
            '## ⚠️ Advertencias del decodificador',
            '',
        ]
        for w in warnings:
            lines.append(f'- {w}')
        lines.append('')

    # --- Pie ---
    lines += [
        '---',
        '',
        '*Explicación generada por Chaos Toolbox — reimplementación educativa propia.*',
        '*Referencia: Sprott (1993). No redistribuye archivos ni texto originales del libro.*',
    ]

    return '\n'.join(lines)
