from __future__ import annotations

import numpy as np
import pytest

from core.lorenz import (
    SYSTEM_REGISTRY,
    equilibria_for_system,
    simulate_system,
    system_defaults,
    vector_field,
)


CH01_SYSTEMS = [
    'lorenz',
    'rossler',
    'chua',
    'chen',
    'unified_lorenz_chen',
    'sprott_a',
    'sprott_b',
    'sprott_c',
    'sprott_d',
    'sprott_e',
    'sprott_f',
    'sprott_g',
    'sprott_h',
    'sprott_i',
    'sprott_j',
    'sprott_k',
    'sprott_l',
    'sprott_m',
    'sprott_n',
    'sprott_o',
    'sprott_p',
    'sprott_q',
    'sprott_r',
    'sprott_s',
]


def test_no_duplicate_system_ids():
    """Verify that the registered systems have unique ids (python dict keys are unique by design, but double check list of IDs)."""
    assert len(CH01_SYSTEMS) == len(set(CH01_SYSTEMS))
    for sys_id in CH01_SYSTEMS:
        assert sys_id in SYSTEM_REGISTRY


def test_presets_load():
    """Verify that defaults and initial conditions can be retrieved for all Chapter 1 systems."""
    for sys_id in CH01_SYSTEMS:
        defaults, initial = system_defaults(sys_id)
        assert isinstance(defaults, tuple)
        assert isinstance(initial, tuple)
        assert len(initial) == 3


@pytest.mark.parametrize('system_key', CH01_SYSTEMS)
def test_vector_field_python_vs_c(system_key):
    """Verify that Python vector field matches the C implementation at a test state.

    We do this by running a 1-step Euler simulation in C and comparing the delta
    with Python's vector_field.
    """
    defaults, initial = system_defaults(system_key)
    state = np.array(initial, dtype=float)
    if np.allclose(state, 0.0):
        state = np.array([0.5, -0.3, 0.8], dtype=float)

    # Evaluate Python vector field
    f_py = vector_field(system_key, state, defaults)

    # Run a 1-step Euler simulation in C
    dt = 1e-6
    t, X = simulate_system(system_key, state, defaults, dt=dt, T=dt, method_key='euler')

    # Compute vector field from C simulation step
    f_c = (X[1] - X[0]) / dt

    # Assert they are close
    assert np.allclose(f_py, f_c, rtol=1e-3, atol=1e-3)


@pytest.mark.parametrize('system_key', CH01_SYSTEMS)
def test_smoke_simulation(system_key):
    """Verify that we can integrate each Chapter 1 system for a short trajectory in C without errors or NaN values."""
    defaults, initial = system_defaults(system_key)
    state = np.array(initial, dtype=float)
    if np.allclose(state, 0.0):
        state = np.array([0.1, 0.1, 0.1], dtype=float)

    t, X = simulate_system(system_key, state, defaults, dt=0.01, T=1.0, method_key='rk4')

    assert len(t) == 101
    assert X.shape == (101, 3)
    assert np.all(np.isfinite(X))


@pytest.mark.parametrize('system_key', CH01_SYSTEMS)
def test_equilibria_computation_and_classification(system_key):
    """Verify that the equilibria search and eigenvalue classification runs for each system.

    Note: Sprott A has no equilibria, so we assert it returns an empty list.
    """
    defaults, _ = system_defaults(system_key)
    eqs = equilibria_for_system(system_key, defaults)

    if system_key == 'sprott_a':
        assert len(eqs) == 0
    else:
        # Most of these systems should find at least one equilibrium point from standard seeds
        assert isinstance(eqs, list)
        for eq in eqs:
            assert 'point' in eq
            assert 'eigvals' in eq
            assert 'local_type' in eq
            assert 'classification' in eq
            assert len(eq['point']) == 3
            assert len(eq['eigvals']) == 3

            # Verify that the vector field is close to zero at the computed equilibrium
            f_eq = vector_field(system_key, eq['point'], defaults)
            # Chua piecewise linear might have slight discontinuities, so we allow slightly larger tolerance
            atol = 1e-4 if system_key == 'chua' else 1e-5
            assert np.allclose(f_eq, 0.0, atol=atol)
