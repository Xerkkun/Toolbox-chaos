"""Shared time-grid and UTC timestamp policy for Toolbox Chaos."""

from __future__ import annotations

from datetime import datetime, timezone
import math

import numpy as np


C_INT_MAX_STEPS = 2_147_483_645
MAX_FIXED_STEP_OUTPUT_BYTES = 512 * 1024 * 1024


def checked_integer_value(
    value: object,
    *,
    name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Convert an integer-valued scalar without truncation or bool coercion."""

    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f'{name} debe ser un entero, no un booleano.')
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'{name} debe ser un entero finito.') from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError(f'{name} debe ser un entero finito; se recibió {value!r}.')
    result = int(numeric)
    if minimum is not None and result < minimum:
        raise ValueError(f'{name} debe ser mayor o igual que {minimum}.')
    if maximum is not None and result > maximum:
        raise ValueError(f'{name} debe ser menor o igual que {maximum}.')
    return result


def fixed_step_count(
    duration: float,
    step: float,
    *,
    name: str = "T",
    allow_zero: bool = False,
) -> int:
    """Return the exact number of uniform steps or reject an ambiguous grid."""

    try:
        duration_value = float(duration)
        step_value = float(step)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'{name} y dt deben ser números finitos.') from exc
    if not math.isfinite(step_value) or step_value <= 0.0:
        raise ValueError("dt debe ser finito y positivo.")
    if not math.isfinite(duration_value):
        raise ValueError(f"{name} debe ser finito.")
    if duration_value < 0.0 or (duration_value == 0.0 and not allow_zero):
        qualifier = "no negativo" if allow_zero else "positivo"
        raise ValueError(f"{name} debe ser {qualifier}.")

    ratio = duration_value / step_value
    if not math.isfinite(ratio):
        raise ValueError(f'{name}/dt debe ser finito.')
    nearest = int(round(ratio))
    if nearest > C_INT_MAX_STEPS:
        raise ValueError(
            f'{name}/dt excede el límite del backend C ({C_INT_MAX_STEPS} pasos).'
        )
    reconstructed = nearest * step_value
    scale = max(abs(duration_value), abs(reconstructed), abs(step_value))
    tolerance = max(
        64.0 * float(np.finfo(np.float64).eps) * scale,
        8.0 * math.ulp(duration_value),
        8.0 * math.ulp(reconstructed),
    )
    if abs(reconstructed - duration_value) > tolerance:
        raise ValueError(
            f"{name}/dt debe ser entero para una malla uniforme; "
            f"se obtuvo {ratio:.16g}."
        )
    if nearest == 0 and not allow_zero:
        raise ValueError(f"{name} debe contener al menos un paso dt.")
    return int(nearest)


def checked_fixed_step_samples(
    steps: int,
    state_dimension: int,
    *,
    name: str = 'salida',
) -> int:
    """Validate a time/state output shape before allocating NumPy arrays."""

    step_count = int(steps)
    dimension = int(state_dimension)
    if step_count < 0 or dimension < 0:
        raise ValueError('steps y state_dimension deben ser no negativos.')
    samples = step_count + 1
    required_bytes = samples * (dimension + 1) * np.dtype(np.float64).itemsize
    if required_bytes > MAX_FIXED_STEP_OUTPUT_BYTES:
        raise ValueError(
            f'{name} requiere {required_bytes} bytes, por encima del límite '
            f'de {MAX_FIXED_STEP_OUTPUT_BYTES} bytes.'
        )
    return samples


def fixed_step_grid(duration: float, step: float, *, name: str = "T") -> np.ndarray:
    """Build a uniformly spaced grid whose final label matches integrated time."""

    steps = fixed_step_count(duration, step, name=name)
    samples = checked_fixed_step_samples(steps, 0, name=f'malla {name}')
    return np.arange(samples, dtype=np.float64) * float(step)


def utc_now_iso() -> str:
    """Return one canonical second-resolution UTC timestamp."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_today_iso() -> str:
    """Return the current calendar date in UTC."""

    return datetime.now(timezone.utc).date().isoformat()
