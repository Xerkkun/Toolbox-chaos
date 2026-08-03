from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

import core.hidden_engine as hidden_engine_module
from core.hidden_engine import (
    covariant_vector_angles,
    engine_status,
    integrate_multi_term_caputo_l1,
    integer_qr_history_covariant_lyapunov_vectors,
    integer_system_definition_alignment_indices,
    integer_system_definition_covariant_lyapunov_vectors,
    simulate_system_definition,
    tangent_alignment_indices,
    tempered_convolution_quadrature,
    trajectory_correlation_dimension,
    trajectory_permutation_entropy,
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


def test_multi_term_caputo_bridge_calls_real_hafo_facade():
    def zero_rhs(time, state):
        del time
        return np.zeros_like(state)

    result = integrate_multi_term_caputo_l1(
        zero_rhs,
        np.array([1.25]),
        orders=[0.8, 0.4, 0.8],
        coefficients=[0.3, 0.4, 0.3],
        step=0.01,
        n_steps=4,
        initial_regularity="smooth",
        use_acceleration=False,
        allow_python_fallback=True,
        divergence_norm=None,
    )

    assert result.status == "ok"
    assert result.method == "multi_term_caputo_l1"
    assert result.states.shape == (5, 1)
    np.testing.assert_allclose(result.states[:, 0], 1.25, rtol=0.0, atol=1.0e-14)
    np.testing.assert_array_equal(result.orders, np.array([0.4, 0.8]))
    np.testing.assert_allclose(result.coefficients, np.array([0.4, 0.6]))
    assert result.solver_info["underlying_method"] == "distributed_order_caputo_l1"
    assert result.solver_info["implementation_reuse"] == (
        "distributed_order_combined_l1_kernel_without_solver_reconstruction"
    )
    assert result.scope == "finite_numerical_trajectory_only"


def test_multi_term_caputo_api_is_loaded_only_when_called_and_fails_clearly(
    monkeypatch,
):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )
    imported = []

    def fake_import(name):
        imported.append(name)
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.fractional":
            raise ModuleNotFoundError("fractional facade unavailable")
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    status = engine_status(refresh=True)
    assert status.available
    assert imported == ["hidden_attractors"]

    with pytest.raises(RuntimeError, match="no pudo cargar la API fraccionaria opcional"):
        integrate_multi_term_caputo_l1(
            lambda _time, state: np.zeros_like(state),
            [1.0],
            orders=[0.5],
            coefficients=[1.0],
            step=0.01,
            n_steps=1,
        )
    assert imported == ["hidden_attractors", "hidden_attractors.fractional"]


def test_tempered_cq_bridge_is_lazy_and_forwards_contract_unchanged(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )
    typed_result = SimpleNamespace(result_type="TemperedConvolutionQuadratureResult")
    received = {}

    def fake_tempered_cq(samples, orders, **kwargs):
        received["samples"] = samples
        received["orders"] = orders
        received["kwargs"] = kwargs
        return typed_result

    fake_fractional = SimpleNamespace(
        tempered_convolution_quadrature=fake_tempered_cq,
    )
    imported = []

    def fake_import(name):
        imported.append(name)
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.fractional":
            return fake_fractional
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    assert engine_status(refresh=True).available
    assert imported == ["hidden_attractors"]

    samples = np.arange(8.0).reshape(4, 2)
    orders = np.array([0.8, 0.9])
    tempering = np.array([0.1, 0.2])
    times = np.linspace(2.0, 2.3, 4)
    token = "tempered_caputo_conjugated_point_value_shift"
    result = tempered_convolution_quadrature(
        samples,
        orders,
        tempering=tempering,
        bdf_order=2,
        definition="tempered_caputo",
        times=times,
        lower_terminal=2.0,
        initial_condition_semantics=token,
        backend="fft",
    )

    assert result is typed_result
    assert received["samples"] is samples
    assert received["orders"] is orders
    assert received["kwargs"] == {
        "tempering": tempering,
        "bdf_order": 2,
        "definition": "tempered_caputo",
        "step": None,
        "times": times,
        "lower_terminal": 2.0,
        "initial_condition_semantics": token,
        "backend": "fft",
    }
    assert imported == ["hidden_attractors", "hidden_attractors.fractional"]


def test_tempered_cq_bridge_fails_clearly_when_hafo_api_is_missing(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )

    def fake_import(name):
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.fractional":
            return SimpleNamespace()
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    with pytest.raises(
        RuntimeError,
        match=r"hidden_attractors\.fractional\.tempered_convolution_quadrature",
    ):
        tempered_convolution_quadrature(
            np.array([0.0, 0.1]),
            0.8,
            tempering=0.2,
            step=0.1,
            initial_condition_semantics="tempered_operator_only_no_ivp",
            backend="python",
        )


def test_tempered_cq_bridge_calls_real_hafo_sampled_operator():
    step = 0.1
    tempering = 0.25
    times = np.arange(6.0) * step
    samples = np.exp(-tempering * times) * times

    result = tempered_convolution_quadrature(
        samples,
        1.0,
        tempering=tempering,
        bdf_order=1,
        definition="tempered_riemann_liouville",
        step=step,
        initial_condition_semantics="tempered_operator_only_no_ivp",
        backend="python",
    )

    assert type(result).__name__ == "TemperedConvolutionQuadratureResult"
    np.testing.assert_allclose(
        result.values[1:],
        np.exp(-tempering * times[1:]),
        rtol=2.0e-15,
        atol=2.0e-15,
    )
    assert result.definition == "tempered_riemann_liouville"
    assert result.scope == "sampled_fractional_operator_only_not_an_fde_solver"
    assert result.backend == "python"


def test_alignment_api_is_lazy_and_returns_hafo_result_unchanged(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )
    typed_result = SimpleNamespace(result_type="AlignmentIndexResult")
    received = {}

    def fake_tangent_alignment(tangent_history, **kwargs):
        received["history"] = tangent_history
        received["kwargs"] = kwargs
        return typed_result

    fake_alignment = SimpleNamespace(
        alignment_indices_from_tangent_history=fake_tangent_alignment,
    )
    imported = []

    def fake_import(name):
        imported.append(name)
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.analysis.alignment_indices":
            return fake_alignment
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    status = engine_status(refresh=True)
    assert status.available
    assert imported == ["hidden_attractors"]

    history = np.ones((4, 2, 3), dtype=float)
    result = tangent_alignment_indices(
        history,
        coordinates=np.arange(4.0),
        gali_orders=(2,),
        backend="numpy",
    )

    assert result is typed_result
    assert received["history"] is history
    assert received["kwargs"]["gali_orders"] == (2,)
    assert received["kwargs"]["backend"] == "numpy"
    assert received["kwargs"]["coordinate_kind"] == "sample"
    assert received["kwargs"]["method"] == "precomputed"
    assert received["kwargs"]["method_id"] == (
        "alignment_indices_from_tangent_history"
    )
    assert received["kwargs"]["metadata"] is None
    assert received["kwargs"]["methodological_warnings"] is None
    assert received["kwargs"]["q"] == 1.0
    assert imported == [
        "hidden_attractors",
        "hidden_attractors.analysis.alignment_indices",
    ]


def test_alignment_bridge_reports_missing_optional_symbol(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )

    def fake_import(name):
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.analysis.alignment_indices":
            return SimpleNamespace()
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    with pytest.raises(
        RuntimeError,
        match="alignment_indices_from_tangent_history",
    ):
        tangent_alignment_indices(np.ones((2, 2, 2)))


def test_tangent_alignment_bridge_preserves_hafo_shape_error(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )

    def reject_shape(_tangent_history, **_kwargs):
        raise ValueError(
            "tangent_history must have shape (n_samples, n_vectors, dimension)"
        )

    fake_alignment = SimpleNamespace(
        alignment_indices_from_tangent_history=reject_shape,
    )

    def fake_import(name):
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.analysis.alignment_indices":
            return fake_alignment
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    with pytest.raises(ValueError, match="n_samples, n_vectors, dimension"):
        tangent_alignment_indices(np.ones((4, 2)))


def test_integer_system_alignment_bridge_compiles_and_delegates(monkeypatch):
    received = {}

    class FakeDefinition:
        @classmethod
        def from_mapping(cls, data):
            received["definition_data"] = data
            return SimpleNamespace(name=data["name"])

    model = SimpleNamespace(kind="flow", initial_state=(1.0, 2.0), dimension=2)

    def fake_compile(definition):
        received["definition"] = definition
        return model

    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=FakeDefinition,
        compile_expression_system=fake_compile,
        simulate=object(),
        trajectory_component_spectra=object(),
    )
    typed_result = SimpleNamespace(result_type="AlignmentIndexResult")

    def fake_system_alignment(system, initial_state, *, q, **kwargs):
        received["model"] = system
        received["initial_state"] = initial_state
        received["q"] = q
        received["kwargs"] = kwargs
        return typed_result

    fake_alignment = SimpleNamespace(
        integer_system_alignment_indices=fake_system_alignment,
    )

    def fake_import(name):
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.analysis.alignment_indices":
            return fake_alignment
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    definition = {"name": "stub flow"}
    deviations = np.eye(2)
    result = integer_system_definition_alignment_indices(
        definition,
        q=np.ones(2),
        t_final=0.2,
        initial_deviations=deviations,
    )

    assert result is typed_result
    assert received["definition_data"] is definition
    assert received["model"] is model
    assert received["initial_state"] is model.initial_state
    np.testing.assert_array_equal(received["q"], np.ones(2))
    assert received["kwargs"]["t_final"] == 0.2
    assert received["kwargs"]["initial_deviations"] is deviations


def test_alignment_bridges_reject_fractional_orders_before_loading_hafo(monkeypatch):
    def unexpected_import(name):
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "import_module", unexpected_import)

    with pytest.raises(ValueError, match="solo admite orden entero q=1"):
        tangent_alignment_indices(np.ones((2, 2, 2)), q=0.95)
    with pytest.raises(ValueError, match="solo admite orden entero q=1"):
        integer_system_definition_alignment_indices(
            {"name": "fractional request"},
            q=[1.0, 0.9],
            t_final=0.1,
        )


def test_tangent_alignment_bridge_calls_real_hafo_api():
    history = np.repeat(np.eye(2, dtype=float)[None, :, :], 3, axis=0)
    coordinates = np.array([0.0, 0.5, 1.0])

    result = tangent_alignment_indices(
        history,
        coordinates=coordinates,
        gali_orders=(2,),
        backend="numpy",
    )

    assert type(result).__name__ == "AlignmentIndexResult"
    np.testing.assert_array_equal(result.coordinates, coordinates)
    np.testing.assert_allclose(result.sali, np.sqrt(2.0))
    np.testing.assert_allclose(result.gali[:, 0], 1.0)
    np.testing.assert_allclose(result.log_gali[:, 0], 0.0)
    assert result.system_kind == "precomputed"
    assert result.method_id == "alignment_indices_from_tangent_history"


def test_integer_map_alignment_bridge_calls_real_hafo_dispatcher():
    identity_map = {
        "name": "Identity map SALI/GALI bridge",
        "kind": "map",
        "variables": ["x", "y"],
        "parameters": {},
        "equations": ["x", "y"],
        "initial_state": [1.0, -2.0],
    }

    result = integer_system_definition_alignment_indices(
        identity_map,
        iterations=3,
        initial_deviations=np.eye(2),
        gali_orders=(2,),
        method="variational",
        backend="numpy",
    )

    assert type(result).__name__ == "AlignmentIndexResult"
    assert result.status == "ok"
    assert result.system_kind == "map"
    np.testing.assert_array_equal(result.coordinates, np.arange(4.0))
    np.testing.assert_allclose(result.sali, np.sqrt(2.0), atol=1.0e-12)
    np.testing.assert_allclose(result.gali[:, 0], 1.0, atol=1.0e-12)
    assert result.metadata["jacobian_source"] == "central_relative_componentwise"


def test_covariant_qr_bridge_is_lazy_and_returns_typed_result_unchanged(monkeypatch):
    fake_engine = SimpleNamespace(
        ExpressionSystemDefinition=object(),
        compile_expression_system=object(),
        simulate=object(),
        trajectory_component_spectra=object(),
    )
    typed_result = SimpleNamespace(result_type="CovariantQRHistoryResult")
    received = {}

    def fake_core(q_history, r_history, **kwargs):
        received["q_history"] = q_history
        received["r_history"] = r_history
        received["kwargs"] = kwargs
        return typed_result

    imported = []

    def fake_import(name):
        imported.append(name)
        if name == "hidden_attractors":
            return fake_engine
        if name == "hidden_attractors.analysis.covariant_lyapunov":
            return SimpleNamespace(
                integer_covariant_vectors_from_qr_history=fake_core
            )
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "_development_candidates", lambda: ())
    monkeypatch.setattr(hidden_engine_module, "import_module", fake_import)

    q_history = np.repeat(np.eye(2)[None, :, :], 2, axis=0)
    r_history = np.eye(2)[None, :, :]
    result = integer_qr_history_covariant_lyapunov_vectors(
        q_history,
        r_history,
        backend="numpy",
    )

    assert result is typed_result
    assert received["q_history"] is q_history
    assert received["r_history"] is r_history
    assert received["kwargs"] == {"q": 1.0, "backend": "numpy"}
    assert imported == [
        "hidden_attractors",
        "hidden_attractors.analysis.covariant_lyapunov",
    ]


def test_clv_bridges_reject_fractional_order_before_importing_hafo(monkeypatch):
    def unexpected_import(name):
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(hidden_engine_module, "_ENGINE", None)
    monkeypatch.setattr(hidden_engine_module, "_ENGINE_STATUS", None)
    monkeypatch.setattr(hidden_engine_module, "import_module", unexpected_import)

    with pytest.raises(ValueError, match="solo admite orden entero q=1"):
        integer_qr_history_covariant_lyapunov_vectors(
            np.repeat(np.eye(2)[None, :, :], 2, axis=0),
            np.eye(2)[None, :, :],
            q=0.95,
        )
    with pytest.raises(ValueError, match="solo admite orden entero q=1"):
        integer_system_definition_covariant_lyapunov_vectors(
            {"name": "fractional request"},
            q=[1.0, 0.9],
            iterations=2,
        )


def test_covariant_qr_and_angle_bridges_call_real_hafo_api():
    q_history = np.repeat(np.eye(2)[None, :, :], 4, axis=0)
    r_history = np.repeat(np.diag([2.0, 0.5])[None, :, :], 3, axis=0)
    result = integer_qr_history_covariant_lyapunov_vectors(
        q_history,
        r_history,
        terminal_coefficients=np.eye(2),
        backend="numpy",
    )

    assert type(result).__name__ == "CovariantQRHistoryResult"
    assert result.vectors.shape == (4, 2, 2)
    np.testing.assert_allclose(result.vectors, q_history)
    angles = covariant_vector_angles(
        result.vectors,
        pairs=((0, 1),),
        window=2,
    )
    assert type(angles).__name__ == "CovariantAngleResult"
    np.testing.assert_allclose(angles.pair_angles[:, 0], np.pi / 2.0)
    assert angles.window_pair_angles.shape == (3, 1)


def test_integer_map_clv_bridge_compiles_no_code_definition():
    diagonal_map = {
        "name": "Diagonal map CLV bridge",
        "kind": "map",
        "variables": ["x", "y"],
        "parameters": {},
        "equations": ["2*x", "0.5*y"],
        "initial_state": [1.0, 1.0],
    }

    result = integer_system_definition_covariant_lyapunov_vectors(
        diagonal_map,
        iterations=4,
        backward_transient_iterations=4,
        initial_basis=np.eye(2),
        terminal_coefficients=np.eye(2),
        backend="numpy",
    )

    assert type(result).__name__ == "CovariantLyapunovResult"
    assert result.status == "ok"
    assert result.system_kind == "map"
    np.testing.assert_allclose(result.exponents, np.log([2.0, 0.5]), atol=2.0e-9)
    np.testing.assert_allclose(result.vectors, np.repeat(np.eye(2)[None, :, :], 5, axis=0))
    assert result.metadata["jacobian_source"] == "central_relative_componentwise"


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


def test_correlation_dimension_bridge_uses_hafo_finite_contract():
    points = np.array(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0], [0.0, 2.0]]
    )
    result = trajectory_correlation_dimension(
        points,
        np.array([1.0, 1.1, 1.5, 2.0, 2.1, 2.3]),
        fit_radius_range=(1.1, 2.1),
        theiler_window=1,
        backend="python",
        fallback=False,
        sampling="six ordered synthetic samples",
        projection="identity projection in R2",
    )

    assert result.curve.counts.tolist() == [0, 4, 6, 6, 8, 10]
    assert result.curve.eligible_pairs == 10
    assert result.curve.backend == "python"
    assert result.fit_radius_range == (1.1, 2.1)
    assert result.evidence_scope == "finite_sample_empirical_trajectory_diagnostic"
    assert "hereditary state" in result.fractional_state_caveat


def test_permutation_entropy_bridge_accepts_scalar_signal():
    result = trajectory_permutation_entropy(
        np.arange(8.0),
        embedding_dimension=3,
        delay=1,
        tie_policy="stable_index",
        log_base=2.0,
        backend="python",
        fallback=False,
    )

    assert result.entropy == pytest.approx(0.0)
    assert result.normalized_entropy == pytest.approx(0.0)
    assert result.distribution.valid_windows == 6
    assert result.distribution.projection == "scalar signal supplied by Toolbox Chaos"
    assert any("not by itself proof of chaos" in item for item in result.warnings)


def test_permutation_entropy_bridge_selects_explicit_state_component():
    states = np.column_stack((np.arange(9.0), np.arange(9.0)[::-1]))
    result = trajectory_permutation_entropy(
        states,
        component=1,
        embedding_dimension=3,
        delay=2,
        tie_policy="omit",
        log_base=np.e,
        backend="python",
        fallback=False,
    )

    assert result.entropy == pytest.approx(0.0)
    assert result.log_base == pytest.approx(np.e)
    assert result.distribution.delay == 2
    assert result.distribution.tie_policy == "omit"
    assert result.distribution.projection == "Toolbox Chaos state component 1"


def test_permutation_entropy_bridge_requires_component_for_state_matrix():
    with pytest.raises(ValueError, match="component es obligatorio"):
        trajectory_permutation_entropy(
            np.ones((8, 2)),
            backend="python",
            fallback=False,
        )
