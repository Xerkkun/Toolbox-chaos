from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

import core.hidden_engine as hidden_engine


def _compatible_fake_engine() -> SimpleNamespace:
    return SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )


def test_tempered_fast_history_bridge_is_lazy_and_forwards_contract_unchanged(
    monkeypatch,
):
    typed_result = SimpleNamespace(result_type="TemperedFastHistoryResult")
    received = {}

    def fake_fast_history(samples, orders, **kwargs):
        received["samples"] = samples
        received["orders"] = orders
        received["kwargs"] = kwargs
        return typed_result

    imported = []

    def fake_import(name):
        imported.append(name)
        if name == "hidden_attractors":
            return _compatible_fake_engine()
        if name == "hidden_attractors.fractional":
            return SimpleNamespace(
                tempered_fast_multistep_history=fake_fast_history
            )
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine, "distribution_version", lambda _name: "1.1.0")
    monkeypatch.setattr(hidden_engine, "import_module", fake_import)

    assert hidden_engine.engine_status(refresh=True).available
    assert imported == ["hidden_attractors"]

    samples = np.arange(12.0).reshape(6, 2)
    orders = np.array([0.45, 0.75])
    tempering = np.array([0.1, 0.3])
    times = np.linspace(2.0, 2.5, 6)
    token = "tempered_caputo_conjugated_point_value_shift"
    result = hidden_engine.tempered_fast_multistep_history(
        samples,
        orders,
        tempering=tempering,
        multistep_method="gngf2",
        definition="tempered_caputo",
        times=times,
        lower_terminal=2.0,
        initial_condition_semantics=token,
        local_history_steps=12,
        quadrature_points=65,
        relative_tolerance=2.0e-7,
        tail_cutoff=3.0e-18,
        max_quadrature_points=513,
        backend="python",
    )

    assert result is typed_result
    assert received["samples"] is samples
    assert received["orders"] is orders
    forwarded = received["kwargs"]
    assert forwarded["tempering"] is tempering
    assert forwarded["times"] is times
    assert forwarded == {
        "tempering": tempering,
        "multistep_method": "gngf2",
        "definition": "tempered_caputo",
        "step": None,
        "times": times,
        "lower_terminal": 2.0,
        "initial_condition_semantics": token,
        "local_history_steps": 12,
        "quadrature_points": 65,
        "relative_tolerance": 2.0e-7,
        "tail_cutoff": 3.0e-18,
        "max_quadrature_points": 513,
        "backend": "python",
    }
    assert imported == ["hidden_attractors", "hidden_attractors.fractional"]


def test_tempered_fast_history_bridge_reports_missing_optional_capability(
    monkeypatch,
):
    def fake_import(name):
        if name == "hidden_attractors":
            return _compatible_fake_engine()
        if name == "hidden_attractors.fractional":
            return SimpleNamespace()
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine, "distribution_version", lambda _name: "1.1.0")
    monkeypatch.setattr(hidden_engine, "import_module", fake_import)

    with pytest.raises(
        RuntimeError,
        match=r"hidden_attractors\.fractional\.tempered_fast_multistep_history",
    ):
        hidden_engine.tempered_fast_multistep_history(
            np.linspace(0.0, 1.0, 8),
            0.6,
            tempering=0.2,
            step=0.1,
            initial_condition_semantics="tempered_operator_only_no_ivp",
            backend="python",
        )


def test_tempered_fast_history_bridge_calls_real_hafo_capability():
    assert "engine_capability" in hidden_engine.__all__
    assert "tempered_fast_multistep_history" in hidden_engine.__all__
    assert hidden_engine.engine_status(refresh=True).available
    capability = hidden_engine.engine_capability(
        "tempered_fast_multistep_history"
    )
    assert capability.fractional_status == "implemented"
    assert capability.backend == "numba/python"
    step = 0.05
    times = step * np.arange(8.0)
    samples = np.sin(times) + 0.2 * times**2

    result = hidden_engine.tempered_fast_multistep_history(
        samples,
        1.0,
        tempering=0.25,
        multistep_method="gngf2",
        definition="tempered_riemann_liouville",
        step=step,
        initial_condition_semantics="tempered_operator_only_no_ivp",
        local_history_steps=2,
        backend="python",
    )

    assert type(result).__name__ == "TemperedFastHistoryResult"
    assert result.multistep_method == "gngf2"
    assert result.formal_order == 2
    assert result.backend == "python"
    assert result.quadrature_points == 0
    assert result.scope == "sampled_fractional_operator_only_not_an_fde_solver"
    assert "recurrent" in result.time_complexity


def test_tempered_fast_history_bridge_does_not_map_fft_to_fast_method_ii():
    with pytest.raises(ValueError, match="backend"):
        hidden_engine.tempered_fast_multistep_history(
            np.linspace(0.0, 1.0, 8),
            0.6,
            tempering=0.2,
            multistep_method="fbdf1",
            definition="tempered_riemann_liouville",
            step=0.1,
            initial_condition_semantics="tempered_operator_only_no_ivp",
            backend="fft",
        )
