from __future__ import annotations

import numpy as np

from core.hidden_engine import (
    engine_status,
    simulate_system_definition,
    trajectory_spectrum,
    validate_system_definition,
)


LORENZ = {
    "name": "Lorenz from Toolbox",
    "kind": "flow",
    "variables": ["x", "y", "z"],
    "parameters": {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
    "equations": ["sigma*(y-x)", "x*(rho-z)-y", "x*y-beta*z"],
    "initial_state": [1.0, 1.0, 1.0],
}


def test_hidden_engine_is_discoverable_from_sibling_checkout():
    status = engine_status(refresh=True)
    assert status.available, status.message


def test_definition_validation_and_structured_simulation():
    canonical = validate_system_definition(LORENZ)
    assert canonical["variables"] == ["x", "y", "z"]

    result = simulate_system_definition(
        canonical,
        step_size=0.01,
        duration=0.05,
        method="rk4",
    )
    assert result.status == "ok"
    assert result.states.shape == (6, 3)
    assert np.all(np.isfinite(result.states))


def test_discrete_map_uses_same_bridge():
    result = simulate_system_definition(
        {
            "name": "Logistic map",
            "kind": "map",
            "variables": ["x"],
            "parameters": {"r": 3.9},
            "equations": ["r*x*(1-x)"],
            "initial_state": [0.2],
        },
        iterations=12,
    )
    assert result.method == "map_iteration"
    assert result.completed_steps == 12
    assert result.states.shape == (13, 1)


def test_welch_psd_has_physical_one_sided_frequency_axis():
    times = np.arange(0.0, 4.0, 0.01)
    signal = np.sin(2.0 * np.pi * 5.0 * times)
    states = np.column_stack((signal, 0.5 * signal, 2.0 * signal))
    frequencies, spectra, method = trajectory_spectrum(
        times,
        states,
        method="psd_welch",
    )
    assert method == "psd_welch"
    assert frequencies[0] == 0.0
    assert np.all(frequencies >= 0.0)
    assert spectra.shape == (len(frequencies), 3)
    peak = frequencies[int(np.argmax(spectra[:, 0]))]
    assert abs(float(peak) - 5.0) < 0.3
