from __future__ import annotations

import numpy as np

from .system_ids import NATIVE_SYSTEM_CODES, PYTHON_ONLY_SYSTEM_IDS
from .time_policy import (
    C_INT_MAX_STEPS,
    MAX_FIXED_STEP_OUTPUT_BYTES,
    checked_fixed_step_samples,
    checked_integer_value,
    fixed_step_count,
    fixed_step_grid,
)

from .native import (
    NativeChaosError,
    basin_plane_generic_native,
    bifurcation_generic_native,
    lorenz_basin_plane_native,
    lorenz_bifurcation_poincare_native,
    lorenz_simulate_native,
    simulate_system_native,
)


SYSTEM_REGISTRY = {
    'lorenz': {
        'label': 'Lorenz', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema de Lorenz clasico de 3 EDOs.',
        'param_labels': ('sigma', 'rho', 'beta'),
        'defaults': (10.0, 28.0, 8.0 / 3.0), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': 1, 'bifurcation_range': (0.0, 80.0), 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
        'coexisting_attractors': [
            {
                'id': 'lorenz_pos',
                'label': 'punto fijo estable +',
                'parameters': {'sigma': 10.0, 'rho': 24.4, 'beta': 2.666667},
                'initial_condition': [5.0, 5.0, 20.0],
                'notes': 'punto fijo estable +'
            },
            {
                'id': 'lorenz_neg',
                'label': 'punto fijo estable -',
                'parameters': {'sigma': 10.0, 'rho': 24.4, 'beta': 2.666667},
                'initial_condition': [-5.0, -5.0, 20.0],
                'notes': 'punto fijo estable -'
            }
        ]
    },
    'rossler': {
        'label': 'Rossler', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Rossler.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (0.2, 0.2, 5.7),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 2, 'bifurcation_range': (2.5, 8.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'chua': {
        'label': 'Chua / doble scroll', 'implemented': True, 'kind': 'flow',
        'description': 'Circuito de Chua adimensional con diodo lineal por tramos.',
        'param_labels': ('alpha', 'beta', 'm0', 'm1'),
        'defaults': (15.6, 28.0, -1.143, -0.714), 'initial': (0.1, 0.0, 0.0),
        'bifurcation_param': 0, 'bifurcation_range': (8.0, 18.0), 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
        'coexisting_attractors': [
            {
                'id': 'chua_pos',
                'label': 'scroll positivo',
                'parameters': {'alpha': 15.6, 'beta': 28.0, 'm0': -1.143, 'm1': -0.714},
                'initial_condition': [1.5, 0.0, -1.5],
                'notes': 'scroll positivo'
            },
            {
                'id': 'chua_neg',
                'label': 'scroll negativo',
                'parameters': {'alpha': 15.6, 'beta': 28.0, 'm0': -1.143, 'm1': -0.714},
                'initial_condition': [-1.5, 0.0, 1.5],
                'notes': 'scroll negativo'
            }
        ]
    },
    'chen': {
        'label': 'Chen', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Chen-Ueta.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (35.0, 3.0, 28.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 2, 'bifurcation_range': (15.0, 35.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'wang_chen_no_equilibrium': {
        'label': 'Wang-Chen (equilibrios variables)',
        'implemented': True,
        'kind': 'flow',
        'description': (
            'Sistema de Wang-Chen con cero, uno o dos equilibrios según el '
            'signo de a.'
        ),
        'param_labels': ('a',),
        'defaults': (0.218,),
        'initial': (1.276, -0.190, 0.471),
        'bifurcation_param': 0,
        'bifurcation_range': (-0.078, 5.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
        'reference': {
            'authors': 'Wang, X.; Chen, G.',
            'year': 2013,
            'doi': '10.1007/s11071-012-0669-7',
        },
        'coexisting_attractors': [
            {
                'id': 'wang_chen_periodic',
                'label': 'ciclo límite',
                'parameters': {'a': 0.218},
                'initial_condition': [3.022, 1.196, 1.643],
                'notes': 'Condición inicial publicada por Bayani et al. (2021).',
            },
            {
                'id': 'wang_chen_chaotic',
                'label': 'atractor caótico',
                'parameters': {'a': 0.218},
                'initial_condition': [1.276, -0.190, 0.471],
                'notes': 'Condición inicial publicada por Bayani et al. (2021).',
            },
        ],
    },
    'nazarimehr_line_equilibrium': {
        'label': 'Nazarimehr (línea de equilibrios)',
        'implemented': True,
        'kind': 'flow',
        'description': (
            'Sistema polinómico 3D con la línea de equilibrios '
            'E*={(x,0,0): x real}.'
        ),
        'param_labels': ('k',),
        'defaults': (-0.2,),
        'initial': (-1.53, 0.33, 0.39),
        'bifurcation_param': 0,
        'bifurcation_range': (-1.0, 1.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
        'equilibrium_manifold': {
            'kind': 'x_axis',
            'label': 'E*={(x,0,0): x real}',
        },
        'reference': {
            'authors': (
                'Nazarimehr, F.; Jafari, M.-A.; Jafari, S.; Pham, V.-T.; '
                'Wang, X.; Chen, G.'
            ),
            'year': 2021,
            'doi': '10.1007/978-3-030-75821-9_22',
        },
        'coexisting_attractors': [
            {
                'id': 'nazarimehr_line',
                'label': 'línea de equilibrios',
                'parameters': {'k': -0.2},
                'initial_condition': [-1.0, 0.0, 0.0],
                'notes': 'Punto representativo de E*.',
            },
            {
                'id': 'nazarimehr_chaotic',
                'label': 'atractor caótico oculto',
                'parameters': {'k': -0.2},
                'initial_condition': [-1.53, 0.33, 0.39],
                'notes': 'Condición inicial publicada por Nazarimehr et al. (2021).',
            },
        ],
    },
    'lu': {
        'label': 'Lu', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Lu-Chen.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (36.0, 3.0, 20.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 2, 'bifurcation_range': (10.0, 30.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'henon': {
        'label': 'Henon', 'implemented': True, 'kind': 'map',
        'description': 'Mapa discreto bidimensional de Henon.',
        'param_labels': ('a', 'b'), 'defaults': (1.4, 0.3),
        'initial': (0.1, 0.1, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.8, 1.4),
        'initial_labels': ('x(0)', 'y(0)', '-'),
        'dimension': 2,
    },
    'logistic': {
        'label': 'Logistico', 'implemented': True, 'kind': 'map',
        'description': 'Mapa logistico unidimensional.',
        'param_labels': ('r',), 'defaults': (3.9,),
        'initial': (0.2, 0.0, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (2.5, 4.0),
        'initial_labels': ('x(0)', '-', '-'),
        'dimension': 1,
    },
    'ikeda': {
        'label': 'Ikeda', 'implemented': True, 'kind': 'map',
        'description': 'Mapa optico bidimensional de Ikeda.',
        'param_labels': ('u',), 'defaults': (0.918,),
        'initial': (0.1, 0.1, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.6, 1.0),
        'initial_labels': ('x(0)', 'y(0)', '-'),
        'dimension': 2,
    },
    'mackey_glass': {
        'label': 'Mackey-Glass', 'implemented': True, 'kind': 'dde',
        'description': (
            'Ecuacion diferencial con retardo: historia lineal para Euler/Heun '
            'y cúbica causal por tramos para RK4.'
        ),
        'param_labels': ('beta', 'gamma', 'n', 'tau'),
        'defaults': (0.2, 0.1, 10.0, 17.0), 'initial': (1.2, 0.0, 0.0),
        'bifurcation_param': 3, 'bifurcation_range': (10.0, 30.0),
        'bifurcation_supported': True,
        'initial_labels': ('x(0)', '-', '-'),
        'dimension': 3,
    },
    'duffing_ueda': {
        'label': 'Duffing-Ueda', 'implemented': True, 'kind': 'flow',
        'description': 'Oscilador de Duffing forzado como sistema autonomo extendido.',
        'param_labels': ('delta', 'alpha', 'beta', 'gamma', 'omega'),
        'defaults': (0.2, -1.0, 1.0, 0.3, 1.2), 'initial': (0.1, 0.0, 0.0),
        'bifurcation_param': 3, 'bifurcation_range': (0.1, 0.6), 'initial_labels': ('x(0)', 'y(0)', 'theta(0)'),
        'dimension': 3,
    },
    'rabinovich_fabrikant': {
        'label': 'Rabinovich-Fabrikant', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Rabinovich-Fabrikant.',
        'param_labels': ('alpha', 'gamma'), 'defaults': (1.1, 0.87),
        'initial': (-1.0, 0.0, 0.5), 'bifurcation_param': 1, 'bifurcation_range': (0.5, 1.2),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'rikitake': {
        'label': 'Rikitake', 'implemented': True, 'kind': 'flow',
        'description': 'Modelo de dinamo de discos de Rikitake.',
        'param_labels': ('mu', 'a'), 'defaults': (2.0, 5.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 1, 'bifurcation_range': (1.0, 8.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_a': {
        'label': 'Sprott A', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott A.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'unified_lorenz_chen': {
        'label': 'Unified Lorenz-Chen', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema unificado de Lorenz-Chen parametrizado por alpha.',
        'param_labels': ('alpha',), 'defaults': (0.0,), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': 0, 'bifurcation_range': (0.0, 1.0), 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_b': {
        'label': 'Sprott B', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott B.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_c': {
        'label': 'Sprott C', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott C.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_d': {
        'label': 'Sprott D', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott D.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_e': {
        'label': 'Sprott E', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott E.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_f': {
        'label': 'Sprott F', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott F.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_g': {
        'label': 'Sprott G', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott G.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_h': {
        'label': 'Sprott H', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott H.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_i': {
        'label': 'Sprott I', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott I.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_j': {
        'label': 'Sprott J', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott J.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_k': {
        'label': 'Sprott K', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott K.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_l': {
        'label': 'Sprott L', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott L.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_m': {
        'label': 'Sprott M', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott M.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_n': {
        'label': 'Sprott N', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott N.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_o': {
        'label': 'Sprott O', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott O.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_p': {
        'label': 'Sprott P', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott P.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_q': {
        'label': 'Sprott Q', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott Q.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_r': {
        'label': 'Sprott R', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott R.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'sprott_s': {
        'label': 'Sprott S', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadrático simple Sprott S.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'thomas': {
        'label': 'Thomas / labyrinth', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo ciclico con senos de Thomas.',
        'param_labels': ('b',), 'defaults': (0.18,),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.05, 0.3),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'hindmarsh_rose': {
        'label': 'Hindmarsh-Rose', 'implemented': True, 'kind': 'flow',
        'description': 'Modelo neuronal lento-rapido de Hindmarsh-Rose.',
        'param_labels': ('a', 'b', 'c', 'd', 'r', 's', 'I'),
        'defaults': (1.0, 3.0, 1.0, 5.0, 0.006, 4.0, 3.25),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 6, 'bifurcation_range': (2.0, 4.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
        'dimension': 3,
    },
    'lorenz96': {
        'label': 'Lorenz-96', 'implemented': True, 'kind': 'flow_high_dim',
        'description': 'Modelo atmosferico conceptual en anillo; la vista muestra las tres primeras variables.',
        'param_labels': ('F', 'J'), 'defaults': (8.0, 8.0),
        'initial': (8.01, 8.0, 8.0),
        'bifurcation_param': 0, 'bifurcation_range': (4.0, 12.0),
        'bifurcation_supported': True,
        'initial_labels': ('X1(0)', 'X2(0)', 'X3(0)'),
        'dimension': 3,
    },
    'hyper_lorenz': {
        'label': 'Lorenz Hipercaótico (4D)', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema hipercaótico de Lorenz de 4 dimensiones.',
        'param_labels': ('a', 'b', 'c', 'r'),
        'defaults': (10.0, 8.0 / 3.0, 28.0, 1.0), 'initial': (0.1, 0.1, 0.1, 0.1),
        'bifurcation_param': 2, 'bifurcation_range': (15.0, 40.0), 'initial_labels': ('x(0)', 'y(0)', 'z(0)', 'w(0)'),
        'dimension': 4,
    },
}

_unmapped_systems = set(SYSTEM_REGISTRY) - set(NATIVE_SYSTEM_CODES) - set(PYTHON_ONLY_SYSTEM_IDS)
_unknown_native_systems = set(NATIVE_SYSTEM_CODES) - set(SYSTEM_REGISTRY)
if _unmapped_systems or _unknown_native_systems:
    raise RuntimeError(
        'El registro de sistemas no coincide con la tabla nativa: '
        f'sin backend={sorted(_unmapped_systems)}, '
        f'nativos desconocidos={sorted(_unknown_native_systems)}'
    )
for _system_key, _system_metadata in SYSTEM_REGISTRY.items():
    _system_metadata['backend'] = (
        'python' if _system_key in PYTHON_ONLY_SYSTEM_IDS else 'native'
    )


METHOD_REGISTRY = {
    'euler': {
        'label': 'Euler explícito',
        'implemented': True,
        'family': 'un paso',
        'backend': 'C',
    },
    'heun': {
        'label': 'Heun / Euler mejorado (RK2)',
        'implemented': True,
        'family': 'un paso',
        'backend': 'C',
    },
    'rk4': {
        'label': 'Runge–Kutta 4',
        'implemented': True,
        'family': 'un paso',
        'backend': 'C',
    },
    'midpoint': {
        'label': 'Punto medio explícito (RK2)',
        'implemented': False,
        'family': 'un paso',
        'backend': 'pendiente',
    },
    'rk23': {
        'label': 'RK23 (Bogacki–Shampine)',
        'implemented': False,
        'family': 'un paso adaptativo',
        'backend': 'pendiente',
    },
    'rk45': {
        'label': 'RK45 (Dormand–Prince)',
        'implemented': False,
        'family': 'un paso adaptativo',
        'backend': 'pendiente',
    },
    'dop853': {
        'label': 'DOP853',
        'implemented': False,
        'family': 'un paso adaptativo',
        'backend': 'pendiente',
    },
    'adams_bashforth_2': {
        'label': 'Adams–Bashforth 2',
        'implemented': False,
        'family': 'multistep explícito',
        'backend': 'pendiente',
    },
    'adams_bashforth_3': {
        'label': 'Adams–Bashforth 3',
        'implemented': False,
        'family': 'multistep explícito',
        'backend': 'pendiente',
    },
    'adams_bashforth_4': {
        'label': 'Adams–Bashforth 4',
        'implemented': False,
        'family': 'multistep explícito',
        'backend': 'pendiente',
    },
    'adams_bashforth_moulton': {
        'label': 'Adams–Bashforth–Moulton',
        'implemented': False,
        'family': 'predictor-corrector multistep',
        'backend': 'pendiente',
    },
    'radau': {
        'label': 'Radau IIA',
        'implemented': False,
        'family': 'implícito',
        'backend': 'pendiente',
    },
    'bdf': {
        'label': 'BDF',
        'implemented': False,
        'family': 'multistep implícito',
        'backend': 'pendiente',
    },
    'lsoda': {
        'label': 'LSODA',
        'implemented': False,
        'family': 'automático / stiff-no stiff',
        'backend': 'pendiente',
    },
    'bulirsch_stoer': {
        'label': 'Bulirsch–Stoer',
        'implemented': False,
        'family': 'extrapolación',
        'backend': 'pendiente',
    },
}


class UnsupportedSystemError(RuntimeError):
    pass


class UnsupportedMethodError(RuntimeError):
    pass


def system_is_available(system_key: str) -> bool:
    return SYSTEM_REGISTRY.get(system_key, {}).get('implemented', False)


def method_is_available(method_key: str) -> bool:
    return METHOD_REGISTRY.get(method_key, {}).get('implemented', False)


def require_supported(system_key: str, method_key: str):
    if not system_is_available(system_key):
        raise UnsupportedSystemError(
            f'El sistema {SYSTEM_REGISTRY.get(system_key, {}).get("label", system_key)} todavía no está implementado.'
        )
    if not method_is_available(method_key):
        raise UnsupportedMethodError(
            f'El método {METHOD_REGISTRY.get(method_key, {}).get("label", method_key)} todavía no está implementado.'
        )


def lorenz_simulate(x0, y0, z0, sigma, rho, beta, dt, T, method_key='rk4'):
    return lorenz_simulate_native(x0, y0, z0, sigma, rho, beta, dt, T, method_key)


def system_defaults(system_key: str):
    meta = SYSTEM_REGISTRY[system_key]
    return tuple(meta.get('defaults', ())), tuple(meta.get('initial', (0.1, 0.1, 0.1)))


def _as_params(system_key: str, values):
    defaults = np.asarray(SYSTEM_REGISTRY[system_key].get('defaults', ()), dtype=float)
    try:
        supplied = np.asarray(values, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('params debe ser un vector numérico finito.') from exc
    if supplied.ndim != 1 or not np.all(np.isfinite(supplied)):
        raise ValueError('params debe ser un vector unidimensional finito.')
    out = defaults.copy()
    count = min(supplied.size, out.size)
    out[:count] = supplied[:count]
    return out


def _binary_flag(value, name: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    integer = checked_integer_value(value, name=name, minimum=0, maximum=1)
    return bool(integer)


def _convex_interpolate(left: float, right: float, numerator: int, denominator: int) -> float:
    if denominator <= 0 or numerator <= 0:
        return float(left)
    if numerator >= denominator:
        return float(right)
    alpha = numerator / denominator
    if np.signbit(left) == np.signbit(right):
        value = left + (right - left) * alpha
    else:
        value = (1.0 - alpha) * left + alpha * right
    if not np.isfinite(value):
        raise ValueError('La interpolación del rango produjo un valor no finito.')
    return float(value)


def _convex_grid(left: float, right: float, count: int) -> np.ndarray:
    denominator = max(1, count - 1)
    return np.asarray(
        [_convex_interpolate(left, right, index, denominator) for index in range(count)],
        dtype=np.float64,
    )


def _mackey_delay_ceiling(tau: float, dt: float, *, name: str = 'tau') -> tuple[float, int]:
    if not np.isfinite(tau) or not np.isfinite(dt) or dt <= 0.0 or tau < dt:
        raise ValueError(f'{name} debe ser finito y mayor o igual que dt.')
    ratio = tau / dt
    if not np.isfinite(ratio) or ratio > C_INT_MAX_STEPS - 2:
        raise ValueError(f'{name}/dt excede la capacidad entera del integrador.')
    return float(ratio), int(np.ceil(ratio))


def _mackey_rhs(current: float, delayed: float, beta: float, gamma: float, exponent: float) -> float:
    power = float(np.power(abs(delayed), exponent))
    feedback = 0.0 if np.isinf(power) else beta * delayed / (1.0 + power)
    return feedback - gamma * current


def _mackey_delayed_value(
    history: np.ndarray,
    current_index: int,
    delay_ratio: float,
    stage_fraction: float,
    *,
    cubic: bool = False,
    origin_index: int | None = None,
    constant_before_origin: bool = False,
) -> float:
    position = current_index + stage_fraction - delay_ratio
    position = min(float(current_index), max(0.0, position))
    lower = int(np.floor(position))
    if lower >= current_index:
        return float(history[current_index])
    fraction = position - lower
    if not cubic or current_index < 3 or fraction <= 8.0 * np.finfo(float).eps:
        return float((1.0 - fraction) * history[lower] + fraction * history[lower + 1])

    stencil_min = 0
    stencil_max = current_index
    if origin_index is not None:
        relative = position - origin_index
        tolerance = 64.0 * np.finfo(float).eps * max(1.0, abs(position))
        if constant_before_origin and relative <= tolerance:
            return float(history[origin_index])
        if relative >= -tolerance:
            segment = max(0, int(np.floor(max(0.0, relative) / delay_ratio)))
            left_boundary = origin_index + segment * delay_ratio
            right_boundary = left_boundary + delay_ratio
            stencil_min = max(0, int(np.ceil(left_boundary - tolerance)))
            stencil_max = min(
                current_index, int(np.floor(right_boundary + tolerance))
            )

    available = stencil_max - stencil_min + 1
    degree_count = min(4, available)
    if degree_count < 2:
        closest = min(current_index, max(0, int(round(position))))
        return float(history[closest])
    start = min(max(lower - 1, stencil_min), stencil_max - degree_count + 1)
    result = 0.0
    for node_offset in range(degree_count):
        node = start + node_offset
        weight = 1.0
        for other_offset in range(degree_count):
            if other_offset != node_offset:
                other = start + other_offset
                weight *= (position - other) / (node - other)
        result += weight * history[node]
    return float(result)


def _mackey_step(
    history: np.ndarray,
    current_index: int,
    delay_ratio: float,
    beta: float,
    gamma: float,
    exponent: float,
    dt: float,
    method_key: str,
    origin_index: int,
    constant_before_origin: bool,
) -> float:
    current = float(history[current_index])
    cubic = method_key == 'rk4'
    delayed_1 = _mackey_delayed_value(
        history, current_index, delay_ratio, 0.0, cubic=cubic,
        origin_index=origin_index,
        constant_before_origin=constant_before_origin,
    )
    k1 = _mackey_rhs(current, delayed_1, beta, gamma, exponent)
    if method_key == 'euler':
        return current + dt * k1
    if method_key == 'heun':
        delayed_2 = _mackey_delayed_value(history, current_index, delay_ratio, 1.0)
        k2 = _mackey_rhs(current + dt * k1, delayed_2, beta, gamma, exponent)
        return current + 0.5 * dt * (k1 + k2)
    if method_key != 'rk4':
        raise ValueError(f'Método Python no implementado: {method_key!r}.')
    delayed_half = _mackey_delayed_value(
            history, current_index, delay_ratio, 0.5, cubic=True,
            origin_index=origin_index,
            constant_before_origin=constant_before_origin,
    )
    k2 = _mackey_rhs(current + 0.5 * dt * k1, delayed_half, beta, gamma, exponent)
    k3 = _mackey_rhs(current + 0.5 * dt * k2, delayed_half, beta, gamma, exponent)
    delayed_4 = _mackey_delayed_value(
        history, current_index, delay_ratio, 1.0, cubic=True,
        origin_index=origin_index,
        constant_before_origin=constant_before_origin,
    )
    k4 = _mackey_rhs(current + dt * k3, delayed_4, beta, gamma, exponent)
    return current + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def _mackey_observed(
    history: np.ndarray,
    current_index: int,
    delay_ratio: float,
    beta: float,
    gamma: float,
    exponent: float,
    observed_var_idx: int,
    method_key: str,
    origin_index: int,
    constant_before_origin: bool,
) -> float:
    current = float(history[current_index])
    delayed = _mackey_delayed_value(
        history, current_index, delay_ratio, 0.0, cubic=method_key == 'rk4',
        origin_index=origin_index,
        constant_before_origin=constant_before_origin,
    )
    if observed_var_idx == 0:
        return current
    if observed_var_idx == 1:
        return delayed
    return _mackey_rhs(current, delayed, beta, gamma, exponent)


def vector_field(system_key: str, state, params):
    x = np.asarray(state, dtype=float)
    p = _as_params(system_key, params)

    if system_key == 'lorenz':
        sigma, rho, beta = p[:3]
        return np.array([sigma * (x[1] - x[0]), x[0] * (rho - x[2]) - x[1], x[0] * x[1] - beta * x[2]])
    if system_key == 'rossler':
        a, b, c = p[:3]
        return np.array([-x[1] - x[2], x[0] + a * x[1], b + x[2] * (x[0] - c)])
    if system_key == 'chua':
        alpha, beta, m0, m1 = p[:4]
        fx = m1 * x[0] + 0.5 * (m0 - m1) * (abs(x[0] + 1.0) - abs(x[0] - 1.0))
        return np.array([alpha * (x[1] - x[0] - fx), x[0] - x[1] + x[2], -beta * x[1]])
    if system_key == 'chen':
        a, b, c = p[:3]
        return np.array([a * (x[1] - x[0]), (c - a) * x[0] - x[0] * x[2] + c * x[1], x[0] * x[1] - b * x[2]])
    if system_key == 'wang_chen_no_equilibrium':
        a = p[0]
        return np.array([
            x[1],
            x[2],
            -x[1] + 3.0 * x[1] ** 2 - x[0] ** 2 - x[0] * x[2] + a,
        ])
    if system_key == 'nazarimehr_line_equilibrium':
        k = p[0]
        return np.array([
            x[1],
            0.4 * x[0] * x[2],
            0.3 * x[1] - 0.1 * x[2] - 1.4 * x[1] ** 2
            + k * x[0] * x[1],
        ])
    if system_key == 'lu':
        a, b, c = p[:3]
        return np.array([a * (x[1] - x[0]), -x[0] * x[2] + c * x[1], x[0] * x[1] - b * x[2]])
    if system_key == 'duffing_ueda':
        delta, alpha, beta, gamma, omega = p[:5]
        return np.array([x[1], -delta * x[1] - alpha * x[0] - beta * x[0] ** 3 + gamma * np.cos(x[2]), omega])
    if system_key == 'rabinovich_fabrikant':
        alpha, gamma = p[:2]
        return np.array([
            x[1] * (x[2] - 1.0 + x[0] ** 2) + gamma * x[0],
            x[0] * (3.0 * x[2] + 1.0 - x[0] ** 2) + gamma * x[1],
            -2.0 * x[2] * (alpha + x[0] * x[1]),
        ])
    if system_key == 'rikitake':
        mu, a = p[:2]
        return np.array([-mu * x[0] + x[1] * x[2], -mu * x[1] + x[0] * (x[2] - a), 1.0 - x[0] * x[1]])
    if system_key == 'sprott_a':
        return np.array([x[1], -x[0] + x[1] * x[2], 1.0 - x[1] ** 2])
    if system_key == 'unified_lorenz_chen':
        alpha = p[0]
        return np.array([
            (25.0 * alpha + 10.0) * (x[1] - x[0]),
            (28.0 - 35.0 * alpha) * x[0] + (29.0 * alpha - 1.0) * x[1] - x[0] * x[2],
            -((alpha + 8.0) / 3.0) * x[2] + x[0] * x[1]
        ])
    if system_key == 'sprott_b':
        return np.array([x[1] * x[2], x[0] - x[1], 1.0 - x[0] * x[1]])
    if system_key == 'sprott_c':
        return np.array([x[1] * x[2], x[0] - x[1], 1.0 - x[0] ** 2])
    if system_key == 'sprott_d':
        return np.array([-x[1], x[0] + x[2], x[0] * x[2] + 3.0 * x[1] ** 2])
    if system_key == 'sprott_e':
        return np.array([x[1] * x[2], x[0] ** 2 - x[1], 1.0 - 4.0 * x[0]])
    if system_key == 'sprott_f':
        return np.array([x[1] + x[2], -x[0] + 0.5 * x[1], x[0] ** 2 - x[2]])
    if system_key == 'sprott_g':
        return np.array([0.4 * x[0] + x[2], x[0] * x[2] - x[1], -x[0] + x[1]])
    if system_key == 'sprott_h':
        return np.array([-x[1] + x[2] ** 2, x[0] + 0.5 * x[1], x[0] - x[2]])
    if system_key == 'sprott_i':
        return np.array([0.2 * x[1], x[0] + x[2], x[0] + x[1] ** 2 - x[2]])
    if system_key == 'sprott_j':
        return np.array([2.0 * x[2], -2.0 * x[1] + x[2], -x[0] + x[1] + x[1] ** 2])
    if system_key == 'sprott_k':
        return np.array([x[0] * x[1] - x[2], x[0] - x[1], x[0] + 0.3 * x[2]])
    if system_key == 'sprott_l':
        return np.array([x[1] + 3.9 * x[2], 0.9 * x[0] ** 2 - x[1], 1.0 - x[0]])
    if system_key == 'sprott_m':
        return np.array([-x[2], -x[0] ** 2 - x[1], 1.7 + 1.7 * x[0] + x[1]])
    if system_key == 'sprott_n':
        return np.array([-2.0 * x[1], x[0] + x[2] ** 2, 1.0 + x[1] - 2.0 * x[2]])
    if system_key == 'sprott_o':
        return np.array([x[1], x[0] - x[2], x[0] + x[0] * x[2] + 2.7 * x[1]])
    if system_key == 'sprott_p':
        return np.array([2.7 * x[1] + x[2], -x[0] + x[1] ** 2, x[0] + x[1]])
    if system_key == 'sprott_q':
        return np.array([-x[2], x[0] - x[1], 3.1 * x[0] + x[1] ** 2 + 0.5 * x[2]])
    if system_key == 'sprott_r':
        return np.array([0.9 - x[1], 0.4 + x[2], x[0] * x[1] - x[2]])
    if system_key == 'sprott_s':
        return np.array([x[0] - 4.0 * x[1], x[0] + x[2] ** 2, 1.0 + x[0]])
    if system_key == 'thomas':
        b = p[0]
        return np.array([np.sin(x[1]) - b * x[0], np.sin(x[2]) - b * x[1], np.sin(x[0]) - b * x[2]])
    if system_key == 'hindmarsh_rose':
        a, b, c, d, r, s, current = p[:7]
        x_r = -1.6
        return np.array([x[1] - a * x[0] ** 3 + b * x[0] ** 2 - x[2] + current, c - d * x[0] ** 2 - x[1], r * (s * (x[0] - x_r) - x[2])])
    if system_key == 'lorenz96':
        forcing = p[0]
        dim = checked_integer_value(p[1], name='J', minimum=4, maximum=256)
        if x.shape != (dim,) or not np.all(np.isfinite(x)):
            raise ValueError(f'El estado Lorenz-96 debe tener forma ({dim},) y ser finito.')
        return np.array([(x[(j + 1) % dim] - x[j - 2]) * x[j - 1] - x[j] + forcing for j in range(dim)])
    if system_key == 'hyper_lorenz':
        a, b, c, r = p[:4]
        return np.array([
            a * (x[1] - x[0]) + x[3],
            c * x[0] - x[1] - x[0] * x[2],
            x[0] * x[1] - b * x[2],
            -x[1] * x[2] + r * x[3]
        ])
    raise UnsupportedSystemError(f'Sistema no implementado: {system_key}')


def map_step(system_key: str, state, params):
    x = np.asarray(state, dtype=float)
    p = _as_params(system_key, params)
    if system_key == 'logistic':
        r = p[0]
        return np.array([r * x[0] * (1.0 - x[0]), 0.0, 0.0])
    if system_key == 'henon':
        a, b = p[:2]
        return np.array([1.0 - a * x[0] ** 2 + x[1], b * x[0], 0.0])
    if system_key == 'ikeda':
        u = p[0]
        t = 0.4 - 6.0 / (1.0 + x[0] ** 2 + x[1] ** 2)
        return np.array([1.0 + u * (x[0] * np.cos(t) - x[1] * np.sin(t)), u * (x[0] * np.sin(t) + x[1] * np.cos(t)), 0.0])
    raise UnsupportedSystemError(f'Mapa no implementado: {system_key}')


def _rk_step(system_key: str, state, params, dt, method_key):
    y = np.asarray(state, dtype=float)
    if method_key == 'euler':
        return y + dt * vector_field(system_key, y, params)
    if method_key == 'heun':
        k1 = vector_field(system_key, y, params)
        k2 = vector_field(system_key, y + dt * k1, params)
        return y + 0.5 * dt * (k1 + k2)
    if method_key != 'rk4':
        raise ValueError(f'Método Python no implementado: {method_key!r}.')
    k1 = vector_field(system_key, y, params)
    k2 = vector_field(system_key, y + 0.5 * dt * k1, params)
    k3 = vector_field(system_key, y + 0.5 * dt * k2, params)
    k4 = vector_field(system_key, y + dt * k3, params)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def simulate_system_python(system_key, initial, params, dt, T, method_key='rk4'):
    if system_key not in SYSTEM_REGISTRY:
        raise UnsupportedSystemError(f'Sistema no implementado: {system_key}')
    if method_key not in METHOD_REGISTRY or not METHOD_REGISTRY[method_key]['implemented']:
        raise ValueError(f'Método Python no implementado: {method_key!r}.')
    try:
        initial_array = np.asarray(initial, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('initial debe ser un vector numérico finito.') from exc
    if initial_array.ndim != 1 or not np.all(np.isfinite(initial_array)):
        raise ValueError('initial debe ser un vector unidimensional finito.')
    p = _as_params(system_key, params)
    if p.ndim != 1 or not np.all(np.isfinite(p)):
        raise ValueError('params debe ser un vector unidimensional finito.')
    steps = fixed_step_count(T, dt)

    if system_key == 'mackey_glass':
        if initial_array.shape != (3,):
            raise ValueError('initial de Mackey-Glass debe tener forma (3,).')
        beta, gamma, exponent, tau = p[:4]
        if exponent <= 0.0:
            raise ValueError('El exponente n de Mackey-Glass debe ser positivo.')
        delay_ratio, delay_ceiling = _mackey_delay_ceiling(float(tau), float(dt))
        n = checked_fixed_step_samples(steps, 3, name='trayectoria Mackey-Glass')
        history_count = delay_ceiling + n + 2
        required_bytes = history_count * np.dtype(np.float64).itemsize
        if required_bytes > MAX_FIXED_STEP_OUTPUT_BYTES:
            raise ValueError(
                f'La historia Mackey-Glass requiere {required_bytes} bytes, por encima '
                f'del límite de {MAX_FIXED_STEP_OUTPUT_BYTES} bytes.'
            )
        prefix_count = delay_ceiling + 3
        history = np.full(prefix_count + steps, initial_array[0], dtype=np.float64)
        origin_index = prefix_count - 1
        X = np.empty((n, 3), dtype=np.float64)
        for index in range(n):
            current_index = origin_index + index
            current = float(history[current_index])
            delayed = _mackey_delayed_value(
                history, current_index, delay_ratio, 0.0,
                cubic=method_key == 'rk4',
                origin_index=origin_index,
                constant_before_origin=True,
            )
            derivative = _mackey_rhs(current, delayed, beta, gamma, exponent)
            X[index] = (current, delayed, derivative)
            if index < steps:
                next_value = _mackey_step(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, dt, method_key,
                    origin_index, True,
                )
                if not np.isfinite(next_value):
                    raise ValueError('La trayectoria Mackey-Glass dejó de ser finita.')
                history[current_index + 1] = next_value
        return fixed_step_grid(T, dt), X

    output_dim = initial_array.size
    if system_key == 'lorenz96':
        lorenz96_dim = checked_integer_value(p[1], name='J', minimum=4, maximum=256)
        if initial_array.shape != (3,):
            raise ValueError('initial de Lorenz-96 debe contener las tres coordenadas mostradas.')
        state = np.full(lorenz96_dim, p[0], dtype=float)
        state[:3] = initial_array
        output_dim = 3
    else:
        state = initial_array.copy()
    checked_fixed_step_samples(steps, output_dim, name=f'trayectoria {system_key}')
    t = fixed_step_grid(T, dt)
    n = len(t)
    X = np.empty((n, output_dim), dtype=np.float64)
    X[0] = state[:output_dim]
    
    is_map = SYSTEM_REGISTRY[system_key].get('kind') == 'map'
    
    for i in range(1, n):
        if is_map:
            state = map_step(system_key, state, p)
        else:
            state = _rk_step(system_key, state, p, dt, method_key)
        X[i] = state[:output_dim]
    return t, X


def bifurcation_generic_python(system_key, initial, params, param_idx, param_min, param_max, n_param, dt, T_trans, T_keep, max_points, continuation=False, method_key='rk4', observed_var_idx=0):
    if system_key not in SYSTEM_REGISTRY:
        raise UnsupportedSystemError(f'Sistema no implementado: {system_key}')
    metadata = SYSTEM_REGISTRY[system_key]
    if not metadata.get('bifurcation_supported', True):
        raise UnsupportedSystemError(
            metadata.get(
                'bifurcation_unavailable_reason',
                f'Bifurcación no disponible para {system_key}.',
            )
        )
    if method_key not in METHOD_REGISTRY or not METHOD_REGISTRY[method_key]['implemented']:
        raise ValueError(f'Método Python no implementado: {method_key!r}.')

    steps_trans = fixed_step_count(T_trans, dt, name='T_trans', allow_zero=True)
    steps_keep = fixed_step_count(T_keep, dt, name='T_keep')
    checked_fixed_step_samples(steps_keep, 1, name=f'historia de bifurcación {system_key}')
    if steps_trans > C_INT_MAX_STEPS - steps_keep:
        raise ValueError('T_trans/dt + T_keep/dt excede la capacidad entera.')
    steps_total = steps_trans + steps_keep

    n_param = checked_integer_value(
        n_param, name='n_param', minimum=1, maximum=C_INT_MAX_STEPS
    )
    max_points = checked_integer_value(
        max_points, name='max_points', minimum=1, maximum=C_INT_MAX_STEPS
    )
    param_idx = checked_integer_value(param_idx, name='param_idx', minimum=0)
    state_dimension = int(metadata.get('dimension', len(initial)))
    observed_var_idx = checked_integer_value(
        observed_var_idx,
        name='observed_var_idx',
        minimum=0,
        maximum=state_dimension - 1,
    )
    continuation = _binary_flag(continuation, 'continuation')

    try:
        bounds = np.asarray((param_min, param_max), dtype=float)
        initial_array = np.asarray(initial, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Los límites y el estado inicial deben ser numéricos finitos.') from exc
    if not np.all(np.isfinite(bounds)) or bounds[0] > bounds[1]:
        raise ValueError('param_min y param_max deben ser finitos y estar ordenados.')
    if initial_array.shape != (state_dimension,) or not np.all(np.isfinite(initial_array)):
        raise ValueError(
            f'initial debe tener forma ({state_dimension},) y valores finitos.'
        )
    p = _as_params(system_key, params)
    if param_idx >= p.size:
        raise ValueError('param_idx debe referir a un elemento de params.')

    output_capacity = n_param * max_points
    required_bytes = output_capacity * 2 * np.dtype(np.float64).itemsize
    if required_bytes > MAX_FIXED_STEP_OUTPUT_BYTES:
        raise ValueError(
            f'La bifurcación requiere {required_bytes} bytes, por encima del límite '
            f'de {MAX_FIXED_STEP_OUTPUT_BYTES} bytes.'
        )

    param_vals = _convex_grid(float(bounds[0]), float(bounds[1]), n_param)
    out_param = np.empty(output_capacity, dtype=np.float64)
    out_value = np.empty(output_capacity, dtype=np.float64)
    out_count = 0

    def emit_ring(parameter, maxima, maxima_count, fallback, fallback_count):
        nonlocal out_count
        source = maxima if maxima_count > 0 else fallback
        source_count = maxima_count if maxima_count > 0 else fallback_count
        emit = min(source_count, max_points)
        start = 0 if source_count < max_points else source_count % max_points
        for index in range(emit):
            out_param[out_count] = parameter
            out_value[out_count] = source[(start + index) % max_points]
            out_count += 1

    if system_key == 'mackey_glass':
        exponent_values = bounds if param_idx == 2 else np.asarray((p[2], p[2]))
        if float(np.min(exponent_values)) <= 0.0:
            raise ValueError('El exponente n de Mackey-Glass debe ser positivo.')
        tau_values = bounds if param_idx == 3 else np.asarray((p[3], p[3]))
        _mackey_delay_ceiling(float(np.min(tau_values)), float(dt))
        _, maximum_delay = _mackey_delay_ceiling(float(np.max(tau_values)), float(dt))
        prefix_count = maximum_delay + 3
        required_bytes = (2 * prefix_count + steps_total + 1) * np.dtype(np.float64).itemsize
        if required_bytes > MAX_FIXED_STEP_OUTPUT_BYTES:
            raise ValueError(
                f'La historia de bifurcación Mackey-Glass requiere {required_bytes} '
                f'bytes, por encima del límite de {MAX_FIXED_STEP_OUTPUT_BYTES} bytes.'
            )
        seed_history = np.full(prefix_count, initial_array[0], dtype=np.float64)
        seed_is_constant = True
        fallback = np.empty(max_points, dtype=np.float64)
        maxima = np.empty(max_points, dtype=np.float64)
        for parameter in param_vals:
            p[param_idx] = parameter
            beta, gamma, exponent, tau = p[:4]
            delay_ratio, _ = _mackey_delay_ceiling(float(tau), float(dt))
            history = np.empty(prefix_count + steps_total, dtype=np.float64)
            if continuation:
                history[:prefix_count] = seed_history
            else:
                history[:prefix_count] = initial_array[0]
            current_index = prefix_count - 1
            origin_index = current_index
            constant_before_origin = not continuation or seed_is_constant
            valid = True
            for _ in range(steps_trans):
                next_value = _mackey_step(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, dt, method_key,
                    origin_index, constant_before_origin,
                )
                if not np.isfinite(next_value) or abs(next_value) > 1.0e8:
                    valid = False
                    break
                current_index += 1
                history[current_index] = next_value

            maxima_count = 0
            fallback_count = 0
            if valid:
                previous_previous = _mackey_observed(
                    history, current_index, delay_ratio,
                    beta, gamma, exponent, observed_var_idx, method_key,
                    origin_index, constant_before_origin,
                )
                previous = previous_previous
                for keep_index in range(steps_keep):
                    next_value = _mackey_step(
                        history, current_index, delay_ratio,
                        beta, gamma, exponent, dt, method_key,
                        origin_index, constant_before_origin,
                    )
                    if not np.isfinite(next_value) or abs(next_value) > 1.0e8:
                        valid = False
                        break
                    current_index += 1
                    history[current_index] = next_value
                    value = _mackey_observed(
                        history, current_index, delay_ratio,
                        beta, gamma, exponent, observed_var_idx, method_key,
                        origin_index, constant_before_origin,
                    )
                    if keep_index >= 1 and previous > previous_previous and previous >= value:
                        maxima[maxima_count % max_points] = previous
                        maxima_count += 1
                    fallback[fallback_count % max_points] = value
                    fallback_count += 1
                    previous_previous = previous
                    previous = value
            if valid:
                emit_ring(parameter, maxima, maxima_count, fallback, fallback_count)
                if continuation:
                    seed_history[:] = history[
                        current_index - prefix_count + 1:current_index + 1
                    ]
                    seed_is_constant = False
            elif continuation:
                seed_history.fill(initial_array[0])
                seed_is_constant = True
        return out_param[:out_count].copy(), out_value[:out_count].copy()

    if system_key == 'lorenz96':
        if param_idx == 1 and (n_param != 1 or bounds[0] != bounds[1]):
            raise ValueError('J es discreto y no puede usarse como barrido continuo.')
        dimension_value = bounds[0] if param_idx == 1 else p[1]
        dimension = checked_integer_value(
            dimension_value, name='J', minimum=4, maximum=256
        )
        fallback = np.empty(max_points, dtype=np.float64)
        maxima = np.empty(max_points, dtype=np.float64)
        seed_state = None
        for parameter in param_vals:
            p[param_idx] = parameter
            if continuation and seed_state is not None:
                state = seed_state.copy()
            else:
                state = np.full(dimension, p[0], dtype=np.float64)
                state[:3] = initial_array
            valid = True
            for _ in range(steps_trans):
                state = _rk_step(system_key, state, p, dt, method_key)
                if not np.all(np.isfinite(state)) or np.max(np.abs(state)) > 1.0e8:
                    valid = False
                    break
            maxima_count = 0
            fallback_count = 0
            if valid:
                previous_previous = float(state[observed_var_idx])
                previous = previous_previous
                for keep_index in range(steps_keep):
                    next_state = _rk_step(system_key, state, p, dt, method_key)
                    if not np.all(np.isfinite(next_state)) or np.max(np.abs(next_state)) > 1.0e8:
                        valid = False
                        break
                    state = next_state
                    value = float(state[observed_var_idx])
                    if keep_index >= 1 and previous > previous_previous and previous >= value:
                        maxima[maxima_count % max_points] = previous
                        maxima_count += 1
                    fallback[fallback_count % max_points] = value
                    fallback_count += 1
                    previous_previous = previous
                    previous = value
            if valid:
                emit_ring(parameter, maxima, maxima_count, fallback, fallback_count)
                if continuation:
                    seed_state = state.copy()
            elif continuation:
                seed_state = None
        return out_param[:out_count].copy(), out_value[:out_count].copy()

    state = initial_array.copy()
    is_map = metadata.get('kind') == 'map'
    
    for val in param_vals:
        p[param_idx] = val
        if not continuation:
            state = initial_array.copy()
            
        # Transitorio
        if is_map:
            for _ in range(steps_trans):
                state = map_step(system_key, state, p)
        else:
            for _ in range(steps_trans):
                state = _rk_step(system_key, state, p, dt, method_key)
                
        # Simulación útil
        history = np.empty(steps_keep, dtype=np.float64)
        if is_map:
            for history_index in range(steps_keep):
                state = map_step(system_key, state, p)
                history[history_index] = state[observed_var_idx]
            pts = history[-max_points:]
            for pt in pts:
                out_param[out_count] = val
                out_value[out_count] = pt
                out_count += 1
        else:
            history_pts = history
            for history_index in range(steps_keep):
                state = _rk_step(system_key, state, p, dt, method_key)
                history_pts[history_index] = state[observed_var_idx]

            if len(history_pts) >= 3:
                mask = (history_pts[1:-1] > history_pts[:-2]) & (history_pts[1:-1] >= history_pts[2:])
                maxima = history_pts[1:-1][mask]
            else:
                maxima = np.empty(0, dtype=np.float64)
            
            if len(maxima) == 0:
                maxima = history_pts[-min(max_points, len(history_pts)):]
            else:
                maxima = maxima[-max_points:]
                
            for m in maxima:
                out_param[out_count] = val
                out_value[out_count] = m
                out_count += 1

    return out_param[:out_count].copy(), out_value[:out_count].copy()


def simulate_system(system_key, initial, params, dt, T, method_key='rk4'):
    meta = SYSTEM_REGISTRY[system_key]
    dim = meta.get('dimension', len(initial))
    if dim > 3:
        return simulate_system_python(system_key, initial, params, dt, T, method_key)
    return simulate_system_native(system_key, initial, _as_params(system_key, params), dt, T, method_key)


def _local_maxima_values(values, max_points):
    v = np.asarray(values, dtype=float)
    if len(v) < 3:
        return v
    mask = (v[1:-1] > v[:-2]) & (v[1:-1] >= v[2:])
    out = v[1:-1][mask]
    if len(out) == 0:
        out = v[-min(max_points, len(v)) :]
    return out[-max_points:]


def bifurcation_generic(system_key, initial, params, param_idx, param_min, param_max, n_param, dt, T_trans, T_keep, max_points, continuation=False, method_key='rk4', observed_var_idx=2):
    meta = SYSTEM_REGISTRY[system_key]
    if not meta.get('bifurcation_supported', True):
        raise UnsupportedSystemError(
            meta.get(
                'bifurcation_unavailable_reason',
                f'Bifurcación no disponible para {system_key}.',
            )
        )
    dim = meta.get('dimension', len(initial))
    if dim > 3:
        return bifurcation_generic_python(
            system_key, initial, params, param_idx, param_min, param_max, n_param,
            dt, T_trans, T_keep, max_points, continuation, method_key, observed_var_idx
        )
    return bifurcation_generic_native(
        system_key,
        initial,
        _as_params(system_key, params),
        param_idx,
        param_min,
        param_max,
        n_param,
        dt,
        T_trans,
        T_keep,
        max_points,
        continuation=continuation,
        method_key=method_key,
        observed_var_idx=observed_var_idx,
    )


def numeric_jacobian(system_key, point, params, eps=1e-6):
    point = np.asarray(point, dtype=float)
    n = len(point)
    J = np.empty((n, n), dtype=float)
    for i in range(n):
        step = np.zeros(n)
        step[i] = eps
        J[:, i] = (vector_field(system_key, point + step, params)[:n] - vector_field(system_key, point - step, params)[:n]) / (2.0 * eps)
    return J


def jacobian_for_system(system_key, point, params, eps=1e-6):
    """Return an analytic Jacobian when available, with numeric fallback."""
    x = np.asarray(point, dtype=float)
    p = _as_params(system_key, params)
    if system_key == 'lorenz':
        sigma, rho, beta = p[:3]
        return np.array([
            [-sigma, sigma, 0.0],
            [rho - x[2], -1.0, -x[0]],
            [x[1], x[0], -beta],
        ])
    if system_key == 'wang_chen_no_equilibrium':
        return np.array([
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [-2.0 * x[0] - x[2], -1.0 + 6.0 * x[1], -x[0]],
        ])
    if system_key == 'nazarimehr_line_equilibrium':
        k = p[0]
        return np.array([
            [0.0, 1.0, 0.0],
            [0.4 * x[2], 0.0, 0.4 * x[0]],
            [k * x[1], 0.3 - 2.8 * x[1] + k * x[0], -0.1],
        ])
    return numeric_jacobian(system_key, x, p, eps=eps)


def numeric_equilibria(system_key, params):
    if SYSTEM_REGISTRY[system_key].get('kind') != 'flow':
        return []
    seeds = [np.zeros(3), np.ones(3), -np.ones(3), np.array([2.0, 2.0, 2.0]), np.array([-2.0, -2.0, 2.0])]
    found = []
    for seed in seeds:
        x = seed.astype(float)
        for _ in range(40):
            f = vector_field(system_key, x, params)[:3]
            if np.linalg.norm(f) < 1e-9:
                break
            J = numeric_jacobian(system_key, x, params)
            try:
                dx = np.linalg.solve(J, -f)
            except np.linalg.LinAlgError:
                break
            x = x + np.clip(dx, -2.0, 2.0)
            if np.linalg.norm(dx) < 1e-9:
                break
        if np.linalg.norm(vector_field(system_key, x, params)[:3]) < 1e-6 and np.all(np.isfinite(x)):
            if not any(np.linalg.norm(x - y) < 1e-5 for y in found):
                found.append(x)

    out = []
    for idx, point in enumerate(found, start=1):
        J = numeric_jacobian(system_key, point, params)
        eigvals = np.linalg.eigvals(J)
        out.append({'name': f'E{idx}', 'point': point, 'jacobian': J, 'eigvals': eigvals, 'local_type': classify_equilibrium_type(eigvals), 'classification': classify_equilibrium_from_eigs(eigvals)})
    return out


def equilibria_for_system(system_key, params):
    if system_key == 'lorenz':
        p = _as_params(system_key, params)
        return lorenz_equilibria(p[0], p[1], p[2])
    if system_key == 'wang_chen_no_equilibrium':
        p = _as_params(system_key, params)
        a = float(p[0])
        if a < 0.0:
            return []
        roots = [0.0] if abs(a) <= 1.0e-14 else [np.sqrt(a), -np.sqrt(a)]
        out = []
        for idx, root in enumerate(roots, start=1):
            point = np.array([root, 0.0, 0.0], dtype=float)
            J = numeric_jacobian(system_key, point, p)
            eigvals = np.linalg.eigvals(J)
            out.append({
                'name': f'E{idx}',
                'point': point,
                'jacobian': J,
                'eigvals': eigvals,
                'local_type': classify_equilibrium_type(eigvals),
                'classification': classify_equilibrium_from_eigs(eigvals),
            })
        return out
    if system_key == 'nazarimehr_line_equilibrium':
        p = _as_params(system_key, params)
        point = np.zeros(3, dtype=float)
        J = numeric_jacobian(system_key, point, p)
        eigvals = np.linalg.eigvals(J)
        return [{
            'name': 'E*',
            'point': point,
            'jacobian': J,
            'eigvals': eigvals,
            'local_type': classify_equilibrium_type(eigvals),
            'classification': classify_equilibrium_from_eigs(eigvals),
            'manifold': 'x_axis',
            'manifold_description': 'E*={(x,0,0): x real}',
        }]
    return numeric_equilibria(system_key, params)


def compute_basin_generic(system_key, params, z0_fixed, x_min, x_max, y_min, y_max, nx, ny, dt, T_total, method_key='rk4'):
    equilibria = equilibria_for_system(system_key, params)
    eq_points = [eq['point'][:3] for eq in equilibria]
    return basin_plane_generic_native(
        system_key,
        _as_params(system_key, params),
        eq_points,
        z0_fixed,
        x_min,
        x_max,
        y_min,
        y_max,
        nx,
        ny,
        dt,
        T_total,
        method_key=method_key,
    )


def bifurcation_poincare_lorenz(
    x0,
    y0,
    z0,
    sigma,
    beta,
    rho_min,
    rho_max,
    n_rho,
    dt,
    T_trans,
    T_keep,
    max_crossings_per_rho,
    continuation,
    method_key='rk4',
):
    return lorenz_bifurcation_poincare_native(
        x0,
        y0,
        z0,
        sigma,
        beta,
        rho_min,
        rho_max,
        n_rho,
        dt,
        T_trans,
        T_keep,
        max_crossings_per_rho,
        continuation,
        method_key,
    )


def compute_basin_plane_z_lorenz_xiong(
    sigma,
    rho,
    beta,
    z0_fixed,
    x_min,
    x_max,
    y_min,
    y_max,
    nx,
    ny,
    dt,
    T_total,
    hit_radius,
    esc_radius,
    method_key='rk4',
):
    return lorenz_basin_plane_native(
        sigma,
        rho,
        beta,
        z0_fixed,
        x_min,
        x_max,
        y_min,
        y_max,
        nx,
        ny,
        dt,
        T_total,
        hit_radius,
        esc_radius,
        method_key,
    )


def lorenz_equilibria(sigma, rho, beta, tol=1e-12):
    equilibria = [
        {
            'name': 'O',
            'point': np.array([0.0, 0.0, 0.0], dtype=float),
        }
    ]

    radicand = beta * (rho - 1.0)
    if radicand > tol:
        s = float(np.sqrt(radicand))
        z_eq = float(rho - 1.0)
        equilibria.extend(
            [
                {'name': 'E+', 'point': np.array([s, s, z_eq], dtype=float)},
                {'name': 'E-', 'point': np.array([-s, -s, z_eq], dtype=float)},
            ]
        )

    for item in equilibria:
        point = item['point']
        J = lorenz_jacobian(point[0], point[1], point[2], sigma, rho, beta)
        eigvals = np.linalg.eigvals(J)
        item['jacobian'] = J
        item['eigvals'] = eigvals
        item['local_type'] = classify_equilibrium_type(eigvals)
        item['classification'] = classify_equilibrium_from_eigs(eigvals)

    return equilibria


def lorenz_jacobian(x, y, z, sigma, rho, beta):
    return np.array(
        [
            [-sigma, sigma, 0.0],
            [rho - z, -1.0, -x],
            [y, x, -beta],
        ],
        dtype=float,
    )


def classify_equilibrium_type(eigvals, tol=1e-9):
    eigvals = np.asarray(eigvals, dtype=np.complex128)
    real_parts = np.real(eigvals)
    imag_parts = np.imag(eigvals)

    n_pos = int(np.sum(real_parts > tol))
    n_neg = int(np.sum(real_parts < -tol))
    n_zero = len(eigvals) - n_pos - n_neg
    has_complex = bool(np.any(np.abs(imag_parts) > tol))

    if n_zero > 0:
        return 'no hiperbólico'

    if has_complex:
        if n_pos == 0 and n_neg == len(eigvals):
            return 'foco estable'
        if n_neg == 0 and n_pos == len(eigvals):
            return 'foco inestable'
        if n_pos > 0 and n_neg > 0:
            return 'silla-foco'
    else:
        if n_pos == 0 and n_neg == len(eigvals):
            return 'nodo estable'
        if n_neg == 0 and n_pos == len(eigvals):
            return 'nodo inestable'
        if n_pos > 0 and n_neg > 0:
            return 'silla'

    return 'indeterminado'


def classify_equilibrium_from_eigs(eigvals, tol=1e-9):
    local_type = classify_equilibrium_type(eigvals, tol=tol)
    real_parts = np.real(eigvals)

    if np.all(real_parts < -tol):
        stability = 'asintóticamente estable'
    elif np.any(real_parts > tol) and np.any(real_parts < -tol):
        stability = 'inestable tipo silla'
    elif np.any(real_parts > tol):
        stability = 'inestable'
    else:
        stability = 'no hiperbólico / linealización inconclusa'

    return f'{local_type} ({stability})'


__all__ = [
    'METHOD_REGISTRY',
    'SYSTEM_REGISTRY',
    'NativeChaosError',
    'UnsupportedMethodError',
    'UnsupportedSystemError',
    'bifurcation_generic',
    'bifurcation_poincare_lorenz',
    'classify_equilibrium_from_eigs',
    'classify_equilibrium_type',
    'compute_basin_generic',
    'compute_basin_plane_z_lorenz_xiong',
    'equilibria_for_system',
    'lorenz_equilibria',
    'lorenz_jacobian',
    'lorenz_simulate',
    'method_is_available',
    'require_supported',
    'simulate_system',
    'system_defaults',
    'system_is_available',
    'vector_field',
]
