from __future__ import annotations

import random

import numpy as np

from .codes import SprottCode, coefficient_count, decode_code, encode_coefficients
from .families import PolynomialFlowFamily, PolynomialMapFamily
from .metrics import detect_divergence, detect_fixed_point, estimate_max_lyapunov_two_trajectory
from core.native import NativeChaosError, sprott_simulate_polynomial_native


def _rng_choice(rng, seq):
    return seq[int(rng.integers(0, len(seq)))] if hasattr(rng, 'integers') else rng.choice(seq)


def generate_random_code(kind='map', dimension=2, order=2, rng=None) -> str:
    rng = rng or np.random.default_rng()
    kind = str(kind).lower()
    dimension = int(dimension)
    order = int(order)
    map_letters = {
        1: 'ABCD',
        2: 'EFGH',
        3: 'IJKL',
        4: 'MNOP',
    }
    flow_letters = {
        3: 'QRST',
        4: 'UVWX',
    }
    if kind == 'map':
        letters = map_letters.get(dimension)
    elif kind == 'flow':
        letters = flow_letters.get(dimension)
    else:
        letters = None
    if not letters or not (2 <= order <= 5):
        raise ValueError('unsupported Sprott family request')
    letter = letters[order - 2]
    count = coefficient_count(dimension, order, kind)
    if hasattr(rng, 'integers'):
        values = (rng.integers(-8, 9, size=count) / 10.0).tolist()
    else:
        values = [rng.randint(-8, 8) / 10.0 for _ in range(count)]
    return letter + encode_coefficients(values)


def family_from_code(code: SprottCode):
    if code.kind == 'map':
        return PolynomialMapFamily(code.dimension, code.order, code.coefficients)
    if code.kind == 'flow':
        return PolynomialFlowFamily(code.dimension, code.order, code.coefficients)
    if code.kind == 'special':
        from core.sprott.special_families import SPECIAL_FAMILY_REGISTRY
        family_entry = SPECIAL_FAMILY_REGISTRY.get(code.family_letter)
        if family_entry is None or isinstance(family_entry, dict):
            raise ValueError("Familia especial reconocida pero aún no implementada.")
        return family_entry(code.coefficients)
    raise ValueError(f'code family is not simulable: {code.kind}')


def simulate_candidate(code, n_iter=2000, transient=200, h=0.01, method='rk4', divergence_threshold=1e6, backend='c'):
    code_obj = decode_code(code) if isinstance(code, str) else code
    family = family_from_code(code_obj)
    initial = np.full(code_obj.dimension, 0.1, dtype=float)
    backend_used = 'python'
    native_status = 0
    
    trajectory = None
    times = None
    
    if backend == 'c' and code_obj.kind in ('map', 'flow'):
        try:
            step_h = 1.0 if code_obj.kind == 'map' else float(h)
            times, trajectory, native_status = sprott_simulate_polynomial_native(
                code_obj.kind,
                code_obj.dimension,
                code_obj.order,
                code_obj.coefficients,
                initial,
                int(n_iter),
                step_h,
                method_key='euler' if method == 'euler' else 'rk4',
                divergence_threshold=divergence_threshold,
            )
            backend_used = 'c'
        except NativeChaosError:
            times = None
            trajectory = None

    if trajectory is None:
        if code_obj.kind in ('map', 'special'):
            trajectory = family.simulate(initial=initial, n_iter=int(n_iter), divergence_threshold=divergence_threshold)
            times = np.arange(len(trajectory), dtype=float)
        else:
            times, trajectory = family.simulate(
                initial=initial,
                n_steps=int(n_iter),
                h=float(h),
                method=method,
                divergence_threshold=divergence_threshold,
            )
    keep = trajectory[int(max(0, transient)) :]
    return {
        'code': code_obj,
        'family': family,
        'times': times,
        'trajectory': trajectory,
        'post_transient': keep,
        'equations': family.equations_text(),
        'backend': backend_used,
        'native_status': native_status,
    }


def classify_candidate(trajectory, *, divergence_threshold=1e6, fixed_tol=1e-6):
    values = np.asarray(trajectory, dtype=float)
    if values.size == 0:
        return {'state': 'unknown', 'reason': 'empty trajectory'}
    if detect_divergence(values, threshold=divergence_threshold):
        return {'state': 'divergent', 'reason': 'non-finite or threshold crossing'}
    if detect_fixed_point(values, tol=fixed_tol):
        return {'state': 'fixed_point', 'reason': 'tail collapsed to a fixed point'}
    finite = values[np.all(np.isfinite(values), axis=1)]
    if len(finite) < 64:
        return {'state': 'unknown', 'reason': 'not enough finite samples'}
    tail = finite[-min(256, len(finite)) :]
    spread = float(np.nanmax(np.std(tail, axis=0)))
    if spread < 1e-4:
        return {'state': 'periodic_or_low_complexity', 'reason': 'very small tail spread'}
    if len(tail) > 16:
        rounded = np.round(tail, decimals=5)
        unique_ratio = len(np.unique(rounded, axis=0)) / len(rounded)
        if unique_ratio < 0.2:
            return {'state': 'periodic_or_low_complexity', 'reason': 'many repeated rounded states'}
    return {'state': 'candidate_chaotic', 'reason': 'bounded non-collapsed trajectory; requires stronger diagnostics'}


def quick_lyapunov_estimate(code, steps=1000):
    code_obj = decode_code(code) if isinstance(code, str) else code
    family = family_from_code(code_obj)
    initial = np.full(code_obj.dimension, 0.1, dtype=float)
    if code_obj.kind == 'map':
        return estimate_max_lyapunov_two_trajectory(family.step, initial, steps=steps)
    return estimate_max_lyapunov_two_trajectory(lambda state: family.step(state, h=0.01, method='rk4'), initial, steps=steps)
