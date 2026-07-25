import numpy as np

from core.diagnostics import integer_qr_benettin_lyapunov
from core.lorenz import jacobian_for_system, numeric_jacobian


def test_rk4_benettin_lorenz_returns_finite_spectrum_and_metadata():
    result = integer_qr_benettin_lyapunov(
        "lorenz",
        (0.0, 10.0, 0.0),
        (10.0, 28.0, 8.0 / 3.0),
        0.01,
        30.0,
        t_burn=5.0,
        reorthonormalize_every=10,
    )

    assert result.status == "ok"
    assert result.method_id == "integer_qr_benettin_rk4"
    assert result.integrator == "rk4_fixed"
    assert result.derivative_model == "variational_system_jacobian"
    assert result.step_size == 0.01
    assert result.burn_time == 5.0
    assert np.isclose(result.measurement_time, 30.0)
    assert result.reorthonormalize_every == 10
    assert result.exponents.shape == (3,)
    assert np.all(np.isfinite(result.exponents))
    assert result.convergence.shape[1] == 3
    assert result.exponents[0] > 0.0
    assert abs(np.sum(result.exponents) - (-10.0 - 1.0 - 8.0 / 3.0)) < 0.05


def test_rk4_benettin_respects_nazarimehr_constant_divergence():
    result = integer_qr_benettin_lyapunov(
        "nazarimehr_line_equilibrium",
        (-1.53, 0.33, 0.39),
        (-0.2,),
        0.01,
        40.0,
        t_burn=10.0,
        reorthonormalize_every=10,
    )

    assert result.status == "ok"
    assert np.all(np.isfinite(result.exponents))
    assert abs(np.sum(result.exponents) - (-0.1)) < 0.005


def test_research_system_analytic_jacobians_match_numeric_fallback():
    cases = (
        ("lorenz", (0.7, -0.2, 0.4), (10.0, 28.0, 8.0 / 3.0)),
        ("wang_chen_no_equilibrium", (0.7, -0.2, 0.4), (0.218,)),
        ("nazarimehr_line_equilibrium", (0.7, -0.2, 0.4), (-0.2,)),
    )
    for system_key, point, params in cases:
        analytic = jacobian_for_system(system_key, point, params)
        numeric = numeric_jacobian(system_key, point, params, eps=1.0e-6)
        assert np.allclose(analytic, numeric, rtol=1.0e-8, atol=1.0e-8)
