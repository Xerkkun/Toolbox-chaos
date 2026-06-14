from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .codes import coefficient_count
from .monomials import evaluate_monomials, monomial_label, multi_indices


def _coefficient_matrix(dimension: int, order: int, coefficients) -> np.ndarray:
    indices = multi_indices(dimension, order)
    expected = coefficient_count(dimension, order)
    data = np.zeros(expected, dtype=float)
    incoming = np.asarray(list(coefficients), dtype=float)
    n = min(expected, incoming.size)
    if n:
        data[:n] = incoming[:n]
    return data.reshape((dimension, len(indices)))


@dataclass
class PolynomialMapFamily:
    dimension: int
    order: int
    coefficients: list[float]

    def __post_init__(self):
        self.dimension = int(self.dimension)
        self.order = int(self.order)
        self.indices = multi_indices(self.dimension, self.order)
        self.matrix = _coefficient_matrix(self.dimension, self.order, self.coefficients)

    def step(self, state) -> np.ndarray:
        x = np.asarray(state, dtype=float)[: self.dimension]
        terms = evaluate_monomials(x, self.indices)
        return self.matrix @ terms

    def simulate(self, initial=None, n_iter=1000, divergence_threshold=1e6) -> np.ndarray:
        n_iter = int(n_iter)
        x = np.asarray(initial if initial is not None else np.full(self.dimension, 0.1), dtype=float)[: self.dimension]
        out = np.empty((max(0, n_iter) + 1, self.dimension), dtype=float)
        out[0] = x
        for idx in range(1, len(out)):
            x = self.step(x)
            out[idx] = x
            if not np.all(np.isfinite(x)) or np.linalg.norm(x) > divergence_threshold:
                out[idx + 1 :] = np.nan
                break
        return out

    def equations_text(self) -> str:
        labels = ('x', 'y', 'z', 'w')[: self.dimension]
        lines = []
        for row, target in zip(self.matrix, labels):
            terms = _terms_text(row, self.indices, labels)
            lines.append(f"{target}' = {terms}")
        return '\n'.join(lines)


@dataclass
class PolynomialFlowFamily:
    dimension: int
    order: int
    coefficients: list[float]

    def __post_init__(self):
        self.dimension = int(self.dimension)
        self.order = int(self.order)
        self.indices = multi_indices(self.dimension, self.order)
        self.matrix = _coefficient_matrix(self.dimension, self.order, self.coefficients)

    def rhs(self, state) -> np.ndarray:
        x = np.asarray(state, dtype=float)[: self.dimension]
        terms = evaluate_monomials(x, self.indices)
        return self.matrix @ terms

    def step(self, state, h=0.01, method='rk4') -> np.ndarray:
        y = np.asarray(state, dtype=float)[: self.dimension]
        h = float(h)
        method = str(method).lower()
        if method == 'euler':
            return y + h * self.rhs(y)
        if method != 'rk4':
            raise ValueError('method must be euler or rk4')
        k1 = self.rhs(y)
        k2 = self.rhs(y + 0.5 * h * k1)
        k3 = self.rhs(y + 0.5 * h * k2)
        k4 = self.rhs(y + h * k3)
        return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    def simulate(self, initial=None, n_steps=1000, h=0.01, method='rk4', divergence_threshold=1e6):
        n_steps = int(n_steps)
        x = np.asarray(initial if initial is not None else np.full(self.dimension, 0.1), dtype=float)[: self.dimension]
        t = np.arange(max(0, n_steps) + 1, dtype=float) * float(h)
        out = np.empty((len(t), self.dimension), dtype=float)
        out[0] = x
        for idx in range(1, len(out)):
            x = self.step(x, h=h, method=method)
            out[idx] = x
            if not np.all(np.isfinite(x)) or np.linalg.norm(x) > divergence_threshold:
                out[idx + 1 :] = np.nan
                break
        return t, out

    def equations_text(self) -> str:
        labels = ('x', 'y', 'z', 'w')[: self.dimension]
        lines = []
        for row, target in zip(self.matrix, labels):
            terms = _terms_text(row, self.indices, labels)
            lines.append(f'd{target}/dt = {terms}')
        return '\n'.join(lines)


def _terms_text(row, indices, variable_names) -> str:
    parts = []
    for coeff, index in zip(row, indices):
        if abs(coeff) < 1e-12:
            continue
        label = monomial_label(index, variable_names)
        if label == '1':
            parts.append(f'{coeff:.3g}')
        else:
            parts.append(f'{coeff:.3g}*{label}')
    return '0' if not parts else ' + '.join(parts).replace('+ -', '- ')
