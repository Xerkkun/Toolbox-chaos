from __future__ import annotations

import numpy as np

from core.sprott.monomials import evaluate_monomials, monomial_label, multi_indices


def test_monomial_counts():
    assert len(multi_indices(1, 2)) == 3
    assert len(multi_indices(2, 2)) == 6
    assert len(multi_indices(3, 2)) == 10
    assert len(multi_indices(4, 2)) == 15


def test_monomial_evaluation_and_labels():
    indices = multi_indices(2, 2)
    values = evaluate_monomials([2.0, 3.0], indices)
    assert np.allclose(values, [1.0, 2.0, 3.0, 4.0, 6.0, 9.0])
    assert monomial_label((0, 0)) == '1'
    assert monomial_label((1, 1)) == 'x*y'
