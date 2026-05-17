from __future__ import annotations

import numpy as np

from .native import (
    NativeChaosError,
    lorenz_basin_plane_native,
    lorenz_bifurcation_poincare_native,
    lorenz_simulate_native,
)


SYSTEM_REGISTRY = {
    'lorenz': {
        'label': 'Lorenz',
        'implemented': True,
        'description': 'Sistema de Lorenz clásico de 3 EDOs con parámetros σ, ρ y β.',
        'param_labels': ('σ', 'ρ', 'β'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'rossler': {
        'label': 'Rössler',
        'implemented': False,
        'description': 'Placeholder para el sistema de Rössler.',
        'param_labels': ('a', 'b', 'c'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'lu': {
        'label': 'Lü',
        'implemented': False,
        'description': 'Placeholder para el sistema de Lü.',
        'param_labels': ('a', 'b', 'c'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'chua': {
        'label': 'Chua',
        'implemented': False,
        'description': 'Placeholder para el circuito/sistema de Chua.',
        'param_labels': ('α', 'β', 'm0/m1'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'chen': {
        'label': 'Chen',
        'implemented': False,
        'description': 'Placeholder para el sistema de Chen.',
        'param_labels': ('a', 'b', 'c'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
    },
    'rabinovich_fabrikant': {
        'label': 'Rabinovich–Fabrikant',
        'implemented': False,
        'description': 'Placeholder para el sistema de Rabinovich–Fabrikant.',
        'param_labels': ('a', 'b', 'c'),
        'initial_labels': ('x(0)', 'y(0)', 'z(0)'),
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
    'bifurcation_poincare_lorenz',
    'classify_equilibrium_from_eigs',
    'classify_equilibrium_type',
    'compute_basin_plane_z_lorenz_xiong',
    'lorenz_equilibria',
    'lorenz_jacobian',
    'lorenz_simulate',
    'method_is_available',
    'require_supported',
    'system_is_available',
]
