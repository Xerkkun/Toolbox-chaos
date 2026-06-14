from __future__ import annotations

from functools import lru_cache
from math import comb

import numpy as np


def _degree_indices(dimension: int, degree: int):
    if dimension == 1:
        yield (degree,)
        return
    for first in range(degree, -1, -1):
        for rest in _degree_indices(dimension - 1, degree - first):
            yield (first, *rest)


@lru_cache(maxsize=None)
def multi_indices(dimension: int, order: int) -> tuple[tuple[int, ...], ...]:
    dimension = int(dimension)
    order = int(order)
    if dimension < 1:
        raise ValueError('dimension must be positive')
    if order < 0:
        raise ValueError('order must be non-negative')
    indices = []
    for degree in range(order + 1):
        indices.extend(_degree_indices(dimension, degree))
    expected = comb(dimension + order, order)
    if len(indices) != expected:
        raise RuntimeError('internal monomial count mismatch')
    return tuple(indices)


def evaluate_monomials(x, indices) -> np.ndarray:
    values = np.asarray(x, dtype=float)
    out = []
    for index in indices:
        if len(index) > values.size:
            raise ValueError('state dimension is smaller than monomial index')
        term = 1.0
        for value, power in zip(values, index):
            if power:
                term *= float(value) ** int(power)
        out.append(term)
    return np.asarray(out, dtype=float)


def monomial_label(index, variable_names=('x', 'y', 'z', 'w')) -> str:
    parts = []
    for variable, power in zip(variable_names, index):
        if power == 0:
            continue
        if power == 1:
            parts.append(variable)
        else:
            parts.append(f'{variable}^{power}')
    return '1' if not parts else '*'.join(parts)
