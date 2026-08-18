import numpy as np
import pytest

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


def test_integer_qr_rejects_four_dimensional_flow_explicitly():
    with pytest.raises(ValueError, match='flujos ODE 3D'):
        integer_qr_benettin_lyapunov(
            'hyper_lorenz',
            (0.1, 0.1, 0.1, 0.1),
            (10.0, 8.0 / 3.0, 28.0, 1.0),
            0.01,
            1.0,
        )


def test_integer_qr_records_the_final_partial_reorthonormalization_interval():
    result = integer_qr_benettin_lyapunov(
        'lorenz',
        (1.0, 1.0, 1.0),
        (10.0, 28.0, 8.0 / 3.0),
        0.01,
        0.11,
        reorthonormalize_every=4,
    )
    assert result.status == 'ok'
    assert result.times == pytest.approx([0.04, 0.08, 0.11])
    assert result.convergence.shape == (3, 3)
    assert result.exponents == pytest.approx(result.convergence[-1])


def test_integer_qr_does_not_report_biased_exponents_after_early_divergence():
    result = integer_qr_benettin_lyapunov(
        'lorenz',
        (1.0, 1.0, 1.0),
        (10.0, 28.0, 8.0 / 3.0),
        0.01,
        0.2,
        reorthonormalize_every=10,
        div_threshold=1.75,
    )
    assert result.status == 'diverged'
    assert result.times.size == 0
    assert np.all(np.isnan(result.exponents))


@pytest.mark.parametrize('interval', [0, -1, 1.5, True])
def test_integer_qr_rejects_invalid_reorthonormalization_interval(interval):
    with pytest.raises(ValueError, match='entero positivo'):
        integer_qr_benettin_lyapunov(
            'lorenz', (1.0, 1.0, 1.0), (10.0, 28.0, 8.0 / 3.0),
            0.01, 0.1, reorthonormalize_every=interval,
        )


@pytest.mark.parametrize(
    ('keyword', 'value', 'message'),
    [
        ('jacobian_eps', 0.0, 'jacobian_eps'),
        ('jacobian_eps', np.nan, 'jacobian_eps'),
        ('div_threshold', 0.0, 'div_threshold'),
        ('div_threshold', np.inf, 'div_threshold'),
        ('q', np.nan, 'q=1'),
    ],
)
def test_integer_qr_rejects_nonfinite_or_nonpositive_controls(keyword, value, message):
    with pytest.raises(ValueError, match=message):
        integer_qr_benettin_lyapunov(
            'lorenz', (1.0, 1.0, 1.0), (10.0, 28.0, 8.0 / 3.0),
            0.01, 0.1, **{keyword: value},
        )
