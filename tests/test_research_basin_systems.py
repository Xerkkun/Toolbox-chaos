from __future__ import annotations

import os

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from core.coexistence import load_coexisting_attractors
from core.lorenz import (
    SYSTEM_REGISTRY,
    compute_basin_generic,
    equilibria_for_system,
    simulate_system,
    vector_field,
)
from ui.parameter_panels import SystemParameterPanel
from ui.tab_controls import BASIN_DEFAULTS


_APP = QApplication.instance() or QApplication([])

RESEARCH_SYSTEMS = (
    "wang_chen_no_equilibrium",
    "nazarimehr_line_equilibrium",
)


def test_research_systems_are_available_in_all_system_dropdowns():
    panel = SystemParameterPanel()
    try:
        for system_key in RESEARCH_SYSTEMS:
            assert system_key in SYSTEM_REGISTRY
            assert SYSTEM_REGISTRY[system_key]["implemented"] is True
            assert panel.system_combo.findData(system_key) >= 0
            assert system_key in BASIN_DEFAULTS
    finally:
        panel.deleteLater()


def test_coexistence_menu_contains_research_systems():
    keys = {case["system_key"] for case in load_coexisting_attractors()}
    assert set(RESEARCH_SYSTEMS) <= keys


def test_wang_chen_vector_field_and_analytic_equilibria():
    state = np.array([0.7, -0.2, 0.4])
    a = 0.218
    expected = np.array([
        -0.2,
        0.4,
        0.2 + 3.0 * 0.2**2 - 0.7**2 - 0.7 * 0.4 + a,
    ])
    assert np.allclose(
        vector_field("wang_chen_no_equilibrium", state, (a,)),
        expected,
    )

    equilibria = equilibria_for_system("wang_chen_no_equilibrium", (a,))
    roots = sorted(float(eq["point"][0]) for eq in equilibria)
    assert np.allclose(roots, [-np.sqrt(a), np.sqrt(a)])
    origin = equilibria_for_system("wang_chen_no_equilibrium", (0.0,))
    assert len(origin) == 1
    assert np.allclose(origin[0]["point"], 0.0)
    assert equilibria_for_system("wang_chen_no_equilibrium", (-0.05,)) == []


def test_nazarimehr_vector_field_and_equilibrium_manifold():
    state = np.array([0.7, -0.2, 0.4])
    k = -0.2
    expected = np.array([
        -0.2,
        0.4 * 0.7 * 0.4,
        0.3 * -0.2 - 0.1 * 0.4 - 1.4 * (-0.2) ** 2
        + k * 0.7 * -0.2,
    ])
    assert np.allclose(
        vector_field("nazarimehr_line_equilibrium", state, (k,)),
        expected,
    )

    equilibria = equilibria_for_system(
        "nazarimehr_line_equilibrium", (k,)
    )
    assert len(equilibria) == 1
    assert equilibria[0]["manifold"] == "x_axis"
    for x_value in (-10.0, -1.0, 0.0, 2.5, 10.0):
        assert np.allclose(
            vector_field(
                "nazarimehr_line_equilibrium",
                (x_value, 0.0, 0.0),
                (k,),
            ),
            0.0,
        )


def test_python_and_native_fields_match_for_research_systems():
    samples = {
        "wang_chen_no_equilibrium": ((0.218,), (0.7, -0.2, 0.4)),
        "nazarimehr_line_equilibrium": ((-0.2,), (0.7, -0.2, 0.4)),
    }
    dt = 1.0e-7
    for system_key, (params, state) in samples.items():
        state_array = np.asarray(state, dtype=float)
        expected = vector_field(system_key, state_array, params)
        _, trajectory = simulate_system(
            system_key,
            state_array,
            params,
            dt=dt,
            T=dt,
            method_key="euler",
        )
        native = (trajectory[1] - trajectory[0]) / dt
        assert np.allclose(native, expected, rtol=1.0e-7, atol=1.0e-7)


def test_native_basin_smoke_and_line_manifold_class():
    wang_basin = compute_basin_generic(
        "wang_chen_no_equilibrium",
        (0.218,),
        0.4716,
        -1.0,
        1.0,
        -1.0,
        1.0,
        17,
        13,
        0.02,
        2.0,
    )
    assert wang_basin.shape == (13, 17)

    line_basin = compute_basin_generic(
        "nazarimehr_line_equilibrium",
        (-0.2,),
        0.0,
        -2.0,
        4.0,
        -0.1,
        0.1,
        17,
        9,
        0.02,
        2.0,
    )
    assert line_basin.shape == (9, 17)
    assert np.all(line_basin[4] == 2)


def _class_near_seed(system_key, params, seed, dt=0.01, time_total=200.0):
    x0, y0, z0 = (float(value) for value in seed)
    epsilon = 1.0e-8
    basin = compute_basin_generic(
        system_key,
        params,
        z0,
        x0 - epsilon,
        x0 + epsilon,
        y0 - epsilon,
        y0 + epsilon,
        2,
        2,
        dt,
        time_total,
    )
    values, counts = np.unique(basin, return_counts=True)
    return int(values[np.argmax(counts)])


def test_published_wang_chen_initial_conditions_are_separated():
    assert _class_near_seed(
        "wang_chen_no_equilibrium",
        (0.218,),
        (3.022, 1.196, 1.643),
    ) == 4
    assert _class_near_seed(
        "wang_chen_no_equilibrium",
        (0.218,),
        (1.276, -0.190, 0.471),
    ) == 1


def test_published_nazarimehr_initial_conditions_are_separated():
    assert _class_near_seed(
        "nazarimehr_line_equilibrium",
        (-0.2,),
        (-1.0, 0.0, 0.0),
    ) == 2
    assert _class_near_seed(
        "nazarimehr_line_equilibrium",
        (-0.2,),
        (-1.53, 0.33, 0.39),
    ) == 1
