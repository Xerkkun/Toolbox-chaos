from __future__ import annotations

import numpy as np

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
    },
    'rossler': {
        'label': 'Rossler', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Rossler.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (0.2, 0.2, 5.7),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 2, 'bifurcation_range': (2.5, 8.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'chua': {
        'label': 'Chua / doble scroll', 'implemented': True, 'kind': 'flow',
        'description': 'Circuito de Chua adimensional con diodo lineal por tramos.',
        'param_labels': ('alpha', 'beta', 'm0', 'm1'),
        'defaults': (15.6, 28.0, -1.143, -0.714), 'initial': (0.1, 0.0, 0.0),
        'bifurcation_param': 0, 'bifurcation_range': (8.0, 18.0), 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'chen': {
        'label': 'Chen', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Chen-Ueta.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (35.0, 3.0, 28.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 2, 'bifurcation_range': (15.0, 35.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'lu': {
        'label': 'Lu', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Lu-Chen.',
        'param_labels': ('a', 'b', 'c'), 'defaults': (36.0, 3.0, 20.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 2, 'bifurcation_range': (10.0, 30.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'henon': {
        'label': 'Henon', 'implemented': True, 'kind': 'map',
        'description': 'Mapa discreto bidimensional de Henon.',
        'param_labels': ('a', 'b'), 'defaults': (1.4, 0.3),
        'initial': (0.1, 0.1, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.8, 1.4),
        'initial_labels': ('x(0)', 'y(0)', '-'),
    },
    'logistic': {
        'label': 'Logistico', 'implemented': True, 'kind': 'map',
        'description': 'Mapa logistico unidimensional.',
        'param_labels': ('r',), 'defaults': (3.9,),
        'initial': (0.2, 0.0, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (2.5, 4.0),
        'initial_labels': ('x(0)', '-', '-'),
    },
    'ikeda': {
        'label': 'Ikeda', 'implemented': True, 'kind': 'map',
        'description': 'Mapa optico bidimensional de Ikeda.',
        'param_labels': ('u',), 'defaults': (0.918,),
        'initial': (0.1, 0.1, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.6, 1.0),
        'initial_labels': ('x(0)', 'y(0)', '-'),
    },
    'mackey_glass': {
        'label': 'Mackey-Glass', 'implemented': True, 'kind': 'dde',
        'description': 'Ecuacion diferencial con retardo integrada por Euler historico.',
        'param_labels': ('beta', 'gamma', 'n', 'tau'),
        'defaults': (0.2, 0.1, 10.0, 17.0), 'initial': (1.2, 0.0, 0.0),
        'bifurcation_param': 3, 'bifurcation_range': (10.0, 30.0), 'initial_labels': ('x(0)', '-', '-'),
    },
    'duffing_ueda': {
        'label': 'Duffing-Ueda', 'implemented': True, 'kind': 'flow',
        'description': 'Oscilador de Duffing forzado como sistema autonomo extendido.',
        'param_labels': ('delta', 'alpha', 'beta', 'gamma', 'omega'),
        'defaults': (0.2, -1.0, 1.0, 0.3, 1.2), 'initial': (0.1, 0.0, 0.0),
        'bifurcation_param': 3, 'bifurcation_range': (0.1, 0.6), 'initial_labels': ('x(0)', 'y(0)', 'theta(0)'),
    },
    'rabinovich_fabrikant': {
        'label': 'Rabinovich-Fabrikant', 'implemented': True, 'kind': 'flow',
        'description': 'Sistema autonomo 3D de Rabinovich-Fabrikant.',
        'param_labels': ('alpha', 'gamma'), 'defaults': (1.1, 0.87),
        'initial': (-1.0, 0.0, 0.5), 'bifurcation_param': 1, 'bifurcation_range': (0.5, 1.2),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'rikitake': {
        'label': 'Rikitake', 'implemented': True, 'kind': 'flow',
        'description': 'Modelo de dinamo de discos de Rikitake.',
        'param_labels': ('mu', 'a'), 'defaults': (2.0, 5.0),
        'initial': (0.1, 0.1, 0.1), 'bifurcation_param': 1, 'bifurcation_range': (1.0, 8.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'sprott_a': {
        'label': 'Sprott A', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo cuadratico simple Sprott A.',
        'param_labels': (), 'defaults': (), 'initial': (0.1, 0.1, 0.1),
        'bifurcation_param': None, 'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'thomas': {
        'label': 'Thomas / labyrinth', 'implemented': True, 'kind': 'flow',
        'description': 'Flujo ciclico con senos de Thomas.',
        'param_labels': ('b',), 'defaults': (0.18,),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 0, 'bifurcation_range': (0.05, 0.3),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'hindmarsh_rose': {
        'label': 'Hindmarsh-Rose', 'implemented': True, 'kind': 'flow',
        'description': 'Modelo neuronal lento-rapido de Hindmarsh-Rose.',
        'param_labels': ('a', 'b', 'c', 'd', 'r', 's', 'I'),
        'defaults': (1.0, 3.0, 1.0, 5.0, 0.006, 4.0, 3.25),
        'initial': (0.1, 0.0, 0.0), 'bifurcation_param': 6, 'bifurcation_range': (2.0, 4.0),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'lorenz96': {
        'label': 'Lorenz-96', 'implemented': True, 'kind': 'flow_high_dim',
        'description': 'Modelo atmosferico conceptual en anillo; la vista muestra las tres primeras variables.',
        'param_labels': ('F', 'J'), 'defaults': (8.0, 8.0),
        'initial': (8.01, 8.0, 8.0), 'bifurcation_param': 0, 'bifurcation_range': (4.0, 12.0),
        'initial_labels': ('X1(0)', 'X2(0)', 'X3(0)'),
    },
}


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
    out = defaults.copy()
    for idx, value in enumerate(values[: len(out)]):
        out[idx] = float(value)
    return out


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
    if system_key == 'thomas':
        b = p[0]
        return np.array([np.sin(x[1]) - b * x[0], np.sin(x[2]) - b * x[1], np.sin(x[0]) - b * x[2]])
    if system_key == 'hindmarsh_rose':
        a, b, c, d, r, s, current = p[:7]
        x_r = -1.6
        return np.array([x[1] - a * x[0] ** 3 + b * x[0] ** 2 - x[2] + current, c - d * x[0] ** 2 - x[1], r * (s * (x[0] - x_r) - x[2])])
    if system_key == 'lorenz96':
        forcing = p[0]
        dim = max(4, int(round(p[1])))
        xx = np.resize(x, dim).astype(float)
        return np.array([(xx[(j + 1) % dim] - xx[j - 2]) * xx[j - 1] - xx[j] + forcing for j in range(dim)])
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
    k1 = vector_field(system_key, y, params)
    k2 = vector_field(system_key, y + 0.5 * dt * k1, params)
    k3 = vector_field(system_key, y + 0.5 * dt * k2, params)
    k4 = vector_field(system_key, y + dt * k3, params)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def simulate_system(system_key, initial, params, dt, T, method_key='rk4'):
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


def bifurcation_generic(system_key, initial, params, param_min, param_max, n_param, dt, T_trans, T_keep, max_points, continuation=False, method_key='rk4'):
    meta = SYSTEM_REGISTRY[system_key]
    param_idx = meta.get('bifurcation_param')
    if param_idx is None:
        raise UnsupportedSystemError('Este sistema no tiene parametro de bifurcacion configurable.')

    return bifurcation_generic_native(
        system_key,
        initial,
        _as_params(system_key, params),
        int(param_idx),
        param_min,
        param_max,
        n_param,
        dt,
        T_trans,
        T_keep,
        max_points,
        continuation=continuation,
        method_key=method_key,
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
