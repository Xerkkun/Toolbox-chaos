from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

import core.sprott.metrics as metrics_module
import core.sprott.search as search_module
from core.sprott.codes import decode_code, explain_support_status
from core.sprott.metrics import LyapunovEstimate, estimate_max_lyapunov_two_trajectory
from core.sprott.references import classify_dic_entry
from core.sprott.search import quick_lyapunov_estimate, simulate_candidate
from core.sprott.special_families import SPECIAL_FAMILY_REGISTRY


def test_decode_code_ypsrtgnd():
    code = decode_code("YPSRTGND")
    assert code.kind == "special"
    assert code.dimension == 4
    
    meta = classify_dic_entry("YPSRTGND")
    assert meta["support"] == "simulable especial"


def test_simulate_family_y():
    # Y requires 10 coefficients.
    res = simulate_candidate("YMMMMMMMMMM", n_iter=100, transient=0)
    assert res["trajectory"].shape == (100, 4)
    assert "equations" in res
    assert "X'" in res["equations"]
    assert "Z'" in res["equations"]


def test_simulate_family_bracket():
    # Family [ has 14 coefficients. Code length 15: "[MMMMMMMMMMMMMM"
    res = simulate_candidate("[MMMMMMMMMMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "|X|^" in res["equations"]


def test_simulate_family_backslash():
    # Family \ has 18 coefficients. Code length 19: "\MMMMMMMMMMMMMMMMMM"
    res = simulate_candidate("\\MMMMMMMMMMMMMMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "sin" in res["equations"]


def test_simulate_family_bracket_right():
    # Family ] has 6 coefficients. Code length 7: "]MMMMMM"
    res = simulate_candidate("]MMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "theta" in res["equations"]


def test_simulate_family_caret():
    # Family ^ has 9 coefficients. Code length 10: "^MMMMMMMMM"
    res = simulate_candidate("^MMMMMMMMM", n_iter=100, transient=0)
    assert res["trajectory"].shape == (100, 4)
    # verify Z (index 2) stays in [0, 2*pi)
    z_vals = res["trajectory"][:, 2]
    for z in z_vals:
        assert 0.0 <= z < 2.0 * math.pi
    assert "equations" in res
    assert "mod 2*pi" in res["equations"]


def test_family_z_pending():
    # Z has 10 coefficients.
    res = explain_support_status("ZMMMMMMMMMM")
    assert res["support"] == "special_pending"
    assert "Z (AND/OR)" in res["reason"] or "Z" in res["reason"]
    
    entry = classify_dic_entry("ZMMMMMMMMMM")
    assert entry["support"] == "especial pendiente: validar AND/OR"
    assert entry["kind"] == "special"
    assert 'Y' in SPECIAL_FAMILY_REGISTRY
    assert 'Z' not in SPECIAL_FAMILY_REGISTRY


def test_two_trajectory_lyapunov_uses_map_iterations_or_physical_time():
    step = lambda state: 2.0 * np.asarray(state, dtype=float)
    per_iteration = estimate_max_lyapunov_two_trajectory(
        step, [0.1], steps=6, renormalize_every=1, time_per_step=1.0
    )
    per_time = estimate_max_lyapunov_two_trajectory(
        step, [0.1], steps=6, renormalize_every=1, time_per_step=0.25
    )
    assert per_iteration.status == per_time.status == 'ok'
    assert per_iteration.value == pytest.approx(math.log(2.0), rel=1e-8)
    assert per_time.value == pytest.approx(4.0 * math.log(2.0), rel=1e-8)


def test_quick_lyapunov_normalizes_flow_by_h_and_map_by_iteration(monkeypatch):
    flow_code = SimpleNamespace(kind='flow', dimension=1)

    class ExponentialFlow:
        @staticmethod
        def step(state, *, h, method):
            assert method == 'rk4'
            return np.exp(1.5 * h) * np.asarray(state, dtype=float)

    monkeypatch.setattr(search_module, 'family_from_code', lambda _code: ExponentialFlow())
    flow = quick_lyapunov_estimate(flow_code, steps=20, h=0.05, method='rk4')
    assert isinstance(flow, LyapunovEstimate)
    assert flow.status == 'ok'
    assert flow.value == pytest.approx(1.5, rel=1e-7)

    map_code = SimpleNamespace(kind='map', dimension=1)

    class DoublingMap:
        @staticmethod
        def step(state):
            return 2.0 * np.asarray(state, dtype=float)

    monkeypatch.setattr(search_module, 'family_from_code', lambda _code: DoublingMap())
    mapped = quick_lyapunov_estimate(map_code, steps=10, h=0.001)
    assert mapped.status == 'ok'
    assert mapped.value == pytest.approx(math.log(2.0), rel=1e-7)


@pytest.mark.parametrize(
    'code',
    (
        'Y' + 'M' * 10,
        '[' + 'M' * 14,
        '\\' + 'M' * 18,
        ']' + 'M' * 6,
        '^' + 'M' * 9,
    ),
)
def test_quick_lyapunov_reports_index_dependent_specials_as_unavailable(code):
    estimate = quick_lyapunov_estimate(code, steps=10)
    assert estimate.status == 'not_available_special_family'
    assert np.isnan(estimate.value)
    assert estimate.warnings and 'índice' in estimate.warnings[0]


def test_sprott_metrics_has_no_pending_placeholder_functions():
    for name in (
        'lyapunov_spectrum_qr_placeholder',
        'correlation_dimension_placeholder',
        'kaplan_yorke_dimension_placeholder',
        'zero_one_test_placeholder',
    ):
        assert not hasattr(metrics_module, name)
