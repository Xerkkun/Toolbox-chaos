from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral

import numpy as np

from .lorenz import (
    METHOD_REGISTRY,
    SYSTEM_REGISTRY,
    jacobian_for_system,
    simulate_system,
    vector_field,
)
from .hidden_engine import trajectory_spectrum as engine_trajectory_spectrum
from .time_policy import fixed_step_count


@dataclass(frozen=True)
class LyapunovDiagnosticResult:
    exponents: np.ndarray
    times: np.ndarray
    convergence: np.ndarray
    status: str
    method_id: str = 'integer_qr_benettin_rk4'
    derivative_model: str = 'variational_system_jacobian'
    q: float = 1.0
    orthonormalization: str = 'qr'
    integrator: str = 'rk4_fixed'
    step_size: float = 0.0
    burn_time: float = 0.0
    measurement_time: float = 0.0
    reorthonormalize_every: int = 1


def comparable_methods() -> list[str]:
    return [key for key, meta in METHOD_REGISTRY.items() if meta.get('implemented')]


def compare_integrator_methods(system_key, initial, params, dt, T, methods=None):
    methods = methods or comparable_methods()
    out = []
    for method_key in methods:
        if not METHOD_REGISTRY.get(method_key, {}).get('implemented'):
            continue
        t, X = simulate_system(system_key, initial, params, dt, T, method_key=method_key)
        out.append((METHOD_REGISTRY[method_key]['label'], t, X[:, :3]))
    return out


def normalized_fft(t, X, min_frequency=None, max_frequency=None):
    t = np.asarray(t, dtype=float)
    X = np.asarray(X, dtype=float)
    if t.ndim != 1 or X.ndim != 2 or len(t) != len(X) or len(t) < 4:
        raise ValueError('Se requiere una trayectoria temporal con al menos 4 puntos.')

    finite_mask = np.all(np.isfinite(X[:, :3]), axis=1) & np.isfinite(t)
    t = t[finite_mask]
    X = X[finite_mask, :3]
    if len(t) < 4:
        raise ValueError('No hay suficientes muestras finitas para FFT.')

    dt_values = np.diff(t)
    dt = float(np.median(dt_values))
    if dt <= 0:
        raise ValueError('El paso temporal debe ser positivo para FFT.')

    signal = X - np.mean(X, axis=0, keepdims=True)
    window = np.hanning(len(signal))
    if np.allclose(window, 0.0):
        window = np.ones(len(signal))
    weighted = signal * window[:, None]
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(weighted, axis=0), axes=0))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(signal), d=dt))
    max_per_col = np.max(spectrum, axis=0)
    max_per_col[max_per_col <= 1e-300] = 1.0
    spectrum = spectrum / max_per_col[None, :]

    if min_frequency is not None or max_frequency is not None:
        lo = float(min_frequency) if min_frequency is not None else float(np.min(freqs))
        hi = float(max_frequency) if max_frequency is not None else float(np.max(freqs))
        keep = (freqs >= lo) & (freqs <= hi)
        freqs = freqs[keep]
        spectrum = spectrum[keep]
    return freqs, spectrum


def trajectory_spectrum(
    t,
    X,
    *,
    method='psd_welch',
    min_frequency=None,
    max_frequency=None,
):
    """Return a physical amplitude spectrum or Welch PSD from the shared engine."""

    return engine_trajectory_spectrum(
        t,
        X,
        method=method,
        min_frequency=min_frequency,
        max_frequency=max_frequency,
    )


def integer_qr_benettin_lyapunov(
    system_key,
    initial,
    params,
    h,
    t_final,
    *,
    t_burn=0.0,
    reorthonormalize_every=10,
    jacobian_eps=1e-6,
    div_threshold=1e6,
    q=1.0,
):
    q_value = float(q)
    if not np.isfinite(q_value) or abs(q_value - 1.0) > 1e-9:
        raise ValueError('integer_qr_benettin solo es valido para q=1 en ODE de orden entero.')
    meta = SYSTEM_REGISTRY[system_key]
    if meta.get('kind') != 'flow' or int(meta.get('dimension', 0)) != 3:
        raise ValueError('El espectro de Lyapunov entero esta disponible para flujos ODE 3D.')

    h = float(h)
    if not np.isfinite(h) or h <= 0.0:
        raise ValueError('h debe ser finito y positivo.')
    if isinstance(reorthonormalize_every, bool) or not isinstance(
        reorthonormalize_every, Integral
    ) or reorthonormalize_every <= 0:
        raise ValueError('reorthonormalize_every debe ser un entero positivo.')
    interval = int(reorthonormalize_every)
    jacobian_eps = float(jacobian_eps)
    if not np.isfinite(jacobian_eps) or jacobian_eps <= 0.0:
        raise ValueError('jacobian_eps debe ser finito y positivo.')
    div_threshold = float(div_threshold)
    if not np.isfinite(div_threshold) or div_threshold <= 0.0:
        raise ValueError('div_threshold debe ser finito y positivo.')
    x = np.asarray(initial, dtype=float).copy()
    if x.shape != (3,) or not np.all(np.isfinite(x)):
        raise ValueError('initial debe contener exactamente tres valores finitos.')
    p = np.asarray(params, dtype=float)
    if p.ndim != 1 or not np.all(np.isfinite(p)):
        raise ValueError('params debe ser un vector de valores finitos.')
    n = x.size
    burn_steps = fixed_step_count(t_burn, h, name='t_burn', allow_zero=True)
    total_steps = fixed_step_count(t_final, h, name='t_final')

    def rhs(state):
        return np.asarray(vector_field(system_key, state, p)[:3], dtype=float)

    def rk4_state_step(state):
        k1 = rhs(state)
        k2 = rhs(state + 0.5 * h * k1)
        k3 = rhs(state + 0.5 * h * k2)
        k4 = rhs(state + h * k3)
        return state + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    def rk4_variational_step(state, tangent):
        def coupled_derivative(stage_state, stage_tangent):
            field = rhs(stage_state)
            jacobian = jacobian_for_system(
                system_key, stage_state, p, eps=jacobian_eps
            )[:n, :n]
            return field, jacobian @ stage_tangent

        k1_x, k1_v = coupled_derivative(state, tangent)
        k2_x, k2_v = coupled_derivative(
            state + 0.5 * h * k1_x,
            tangent + 0.5 * h * k1_v,
        )
        k3_x, k3_v = coupled_derivative(
            state + 0.5 * h * k2_x,
            tangent + 0.5 * h * k2_v,
        )
        k4_x, k4_v = coupled_derivative(
            state + h * k3_x,
            tangent + h * k3_v,
        )
        next_state = state + (h / 6.0) * (
            k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x
        )
        next_tangent = tangent + (h / 6.0) * (
            k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v
        )
        return next_state, next_tangent

    for _ in range(burn_steps):
        x = rk4_state_step(x)
        if not np.all(np.isfinite(x)) or np.linalg.norm(x) >= div_threshold:
            return LyapunovDiagnosticResult(
                np.full(n, np.nan),
                np.empty(0),
                np.empty((0, n)),
                'burn_diverged',
                step_size=h,
                burn_time=burn_steps * h,
                measurement_time=0.0,
                reorthonormalize_every=interval,
            )

    basis = np.eye(n, dtype=float)
    sums = np.zeros(n, dtype=float)
    times = []
    convergence = []
    elapsed = 0.0
    status = 'ok'
    last_qr_step = 0

    def record_qr(current_time):
        nonlocal basis, sums
        qmat, rmat = np.linalg.qr(basis)
        diag = np.abs(np.diag(rmat))
        diag[diag <= 1.0e-300] = 1.0e-300
        sums += np.log(diag)
        basis = qmat
        times.append(current_time)
        convergence.append(sums / max(current_time, 1.0e-300))

    for step in range(1, total_steps + 1):
        x, basis = rk4_variational_step(x, basis)
        elapsed += h

        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(basis)):
            status = 'nonfinite_solution'
            break
        if np.linalg.norm(x) >= div_threshold:
            status = 'diverged'
            break

        if step % interval == 0:
            record_qr(elapsed)
            last_qr_step = step

    if status == 'ok' and last_qr_step < total_steps:
        record_qr(elapsed)

    exponents = (
        sums / max(elapsed, 1.0e-300)
        if status == 'ok' and elapsed > 0.0
        else np.full(n, np.nan)
    )
    return LyapunovDiagnosticResult(
        np.asarray(exponents, dtype=float),
        np.asarray(times, dtype=float),
        np.asarray(convergence, dtype=float) if convergence else np.empty((0, n), dtype=float),
        status,
        step_size=h,
        burn_time=burn_steps * h,
        measurement_time=elapsed,
        reorthonormalize_every=interval,
    )
