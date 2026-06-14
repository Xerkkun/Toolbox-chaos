from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LyapunovEstimate:
    value: float
    status: str
    warnings: list[str]


def detect_divergence(trajectory, threshold=1e6) -> bool:
    values = np.asarray(trajectory, dtype=float)
    if values.size == 0:
        return False
    finite = np.all(np.isfinite(values), axis=-1) if values.ndim > 1 else np.isfinite(values)
    if not np.all(finite):
        return True
    norms = np.linalg.norm(values.reshape((values.shape[0], -1)), axis=1) if values.ndim > 1 else np.abs(values)
    return bool(np.nanmax(norms) >= float(threshold))


def detect_fixed_point(trajectory, tol=1e-6, tail=32) -> bool:
    values = np.asarray(trajectory, dtype=float)
    if values.ndim != 2 or len(values) < 4:
        return False
    values = values[np.all(np.isfinite(values), axis=1)]
    if len(values) < 4:
        return False
    tail_values = values[-min(int(tail), len(values)) :]
    spread = np.nanmax(np.linalg.norm(tail_values - tail_values[-1], axis=1))
    return bool(spread <= float(tol))


def estimate_max_lyapunov_two_trajectory(
    step_func,
    initial,
    *,
    steps=1000,
    separation=1e-7,
    renormalize_every=5,
    divergence_threshold=1e6,
):
    warnings: list[str] = []
    x = np.asarray(initial, dtype=float)
    direction = np.zeros_like(x)
    direction[0] = 1.0
    y = x + float(separation) * direction
    total = 0.0
    elapsed = 0
    interval = max(1, int(renormalize_every))
    for step in range(1, int(steps) + 1):
        x = np.asarray(step_func(x), dtype=float)
        y = np.asarray(step_func(y), dtype=float)
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
            return LyapunovEstimate(float('nan'), 'nonfinite', warnings)
        if np.linalg.norm(x) >= divergence_threshold or np.linalg.norm(y) >= divergence_threshold:
            return LyapunovEstimate(float('nan'), 'diverged', warnings)
        if step % interval == 0:
            delta = y - x
            dist = float(np.linalg.norm(delta))
            if dist <= 1e-300:
                warnings.append('neighbor collapsed below numerical resolution')
                return LyapunovEstimate(float('-inf'), 'collapsed', warnings)
            total += np.log(dist / float(separation))
            y = x + float(separation) * delta / dist
            elapsed += interval
    if elapsed == 0:
        return LyapunovEstimate(float('nan'), 'insufficient_steps', warnings)
    return LyapunovEstimate(total / elapsed, 'ok', warnings)


def lyapunov_spectrum_qr_placeholder(*_args, **_kwargs):
    return {'status': 'pending', 'method': 'QR spectrum placeholder'}


def correlation_dimension_placeholder(*_args, **_kwargs):
    return {'status': 'pending', 'method': 'correlation dimension placeholder'}


def kaplan_yorke_dimension_placeholder(*_args, **_kwargs):
    return {'status': 'pending', 'method': 'Kaplan-Yorke placeholder'}


def zero_one_test_placeholder(*_args, **_kwargs):
    return {'status': 'pending', 'method': '0-1 test placeholder'}
