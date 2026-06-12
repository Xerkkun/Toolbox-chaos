from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lorenz import METHOD_REGISTRY, SYSTEM_REGISTRY, numeric_jacobian, simulate_system, vector_field


@dataclass(frozen=True)
class LyapunovDiagnosticResult:
    exponents: np.ndarray
    times: np.ndarray
    convergence: np.ndarray
    status: str
    method_id: str = 'integer_qr_benettin'
    derivative_model: str = 'integer'
    q: float = 1.0
    orthonormalization: str = 'qr'


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
    if abs(float(q) - 1.0) > 1e-9:
        raise ValueError('integer_qr_benettin solo es valido para q=1 en ODE de orden entero.')
    if SYSTEM_REGISTRY[system_key].get('kind') != 'flow':
        raise ValueError('El espectro de Lyapunov entero esta disponible para flujos ODE 3D.')

    h = float(h)
    if h <= 0.0:
        raise ValueError('h debe ser positivo.')
    x = np.asarray(initial[:3], dtype=float).copy()
    p = np.asarray(params, dtype=float)
    n = x.size
    burn_steps = int(max(0, round(float(t_burn) / h)))
    total_steps = int(max(0, round(float(t_final) / h)))
    interval = max(1, int(reorthonormalize_every))

    def rhs(state):
        return np.asarray(vector_field(system_key, state, p)[:3], dtype=float)

    for _ in range(burn_steps):
        x = x + h * rhs(x)
        if not np.all(np.isfinite(x)) or np.linalg.norm(x) >= float(div_threshold):
            return LyapunovDiagnosticResult(
                np.full(n, np.nan), np.empty(0), np.empty((0, n)), 'burn_diverged'
            )

    basis = np.eye(n, dtype=float)
    sums = np.zeros(n, dtype=float)
    times = []
    convergence = []
    elapsed = 0.0
    status = 'ok'

    for step in range(1, total_steps + 1):
        J = numeric_jacobian(system_key, x, p, eps=jacobian_eps)[:n, :n]
        basis = basis + h * J @ basis
        x = x + h * rhs(x)
        elapsed += h

        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(basis)):
            status = 'nonfinite_solution'
            break
        if np.linalg.norm(x) >= float(div_threshold):
            status = 'diverged'
            break

        if step % interval == 0:
            qmat, rmat = np.linalg.qr(basis)
            diag = np.abs(np.diag(rmat))
            diag[diag <= 1.0e-300] = 1.0e-300
            sums += np.log(diag)
            basis = qmat
            times.append(elapsed)
            convergence.append(sums / max(elapsed, 1.0e-300))

    exponents = sums / max(elapsed, 1.0e-300) if elapsed > 0.0 else np.full(n, np.nan)
    return LyapunovDiagnosticResult(
        np.asarray(exponents, dtype=float),
        np.asarray(times, dtype=float),
        np.asarray(convergence, dtype=float) if convergence else np.empty((0, n), dtype=float),
        status,
    )
