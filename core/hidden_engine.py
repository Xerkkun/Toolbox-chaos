"""Bridge from the desktop application to Hidden Attractors FO.

The GUI owns interaction and rendering. Numerical system definitions and
trajectory generation are delegated to the scientific engine when its
compatible API is available. Import is lazy so a broken scientific install can
be reported through the desktop diagnostics instead of aborting at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as distribution_version
from typing import Any, Mapping

from packaging.version import InvalidVersion, Version


_DISTRIBUTION_NAME = "hidden-attractors-fo"
_ENGINE_SPEC = ">=1.1,<2"


@dataclass(frozen=True)
class EngineStatus:
    available: bool
    version: str | None
    source: str | None
    message: str
    reason: str


_ENGINE: Any | None = None
_ENGINE_STATUS: EngineStatus | None = None


def _load_engine() -> tuple[Any | None, EngineStatus]:
    global _ENGINE, _ENGINE_STATUS
    if _ENGINE_STATUS is not None:
        return _ENGINE, _ENGINE_STATUS

    source = f"Python distribution {_DISTRIBUTION_NAME}"

    def unavailable(reason: str, detail: object, *, version: str | None = None) -> None:
        global _ENGINE, _ENGINE_STATUS
        _ENGINE = None
        _ENGINE_STATUS = EngineStatus(
            False,
            version,
            source,
            "Hidden Attractors FO no esta disponible para Toolbox. "
            f"Instale '{_DISTRIBUTION_NAME}{_ENGINE_SPEC}'. Detalle: {detail}",
            reason,
        )

    try:
        installed_version = distribution_version(_DISTRIBUTION_NAME)
    except PackageNotFoundError as exc:
        unavailable("package_not_found", exc)
        return _ENGINE, _ENGINE_STATUS
    except (OSError, ValueError) as exc:
        unavailable("metadata_error", exc)
        return _ENGINE, _ENGINE_STATUS

    try:
        parsed_version = Version(installed_version)
    except InvalidVersion as exc:
        unavailable("invalid_version", exc, version=installed_version)
        return _ENGINE, _ENGINE_STATUS

    if parsed_version < Version("1.1") or parsed_version >= Version("2"):
        unavailable(
            "incompatible_version",
            f"se requiere {_DISTRIBUTION_NAME}{_ENGINE_SPEC}; se encontro {installed_version}",
            version=installed_version,
        )
        return _ENGINE, _ENGINE_STATUS

    try:
        engine = import_module("hidden_attractors")
    except (ImportError, OSError) as exc:
        unavailable("broken_import", exc, version=installed_version)
        return _ENGINE, _ENGINE_STATUS
    except Exception as exc:
        unavailable("import_error", exc, version=installed_version)
        return _ENGINE, _ENGINE_STATUS

    required = (
        "ExpressionSystemDefinition",
        "compile_expression_system",
        "simulate",
        "trajectory_component_spectra",
    )
    try:
        missing = [name for name in required if not hasattr(engine, name)]
    except Exception as exc:
        unavailable("api_inspection_error", exc, version=installed_version)
        return _ENGINE, _ENGINE_STATUS
    if missing:
        unavailable(
            "missing_api",
            "La version encontrada no ofrece la API de integracion: " + ", ".join(missing),
            version=installed_version,
        )
        return _ENGINE, _ENGINE_STATUS

    _ENGINE = engine
    _ENGINE_STATUS = EngineStatus(
        True,
        installed_version,
        source,
        "Motor cientifico disponible.",
        "available",
    )
    return _ENGINE, _ENGINE_STATUS


def engine_status(*, refresh: bool = False) -> EngineStatus:
    """Return installed-engine compatibility without importing it at startup."""

    global _ENGINE, _ENGINE_STATUS
    if refresh:
        _ENGINE = None
        _ENGINE_STATUS = None
    return _load_engine()[1]


def engine_capability(name: str):
    """Return one typed HAFO capability entry without duplicating its catalog."""

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        catalog = import_module("hidden_attractors.capabilities")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar su catalogo de capacidades: "
            f"{exc}"
        ) from exc
    getter = getattr(catalog, "get_capability", None)
    if getter is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            "hidden_attractors.capabilities.get_capability."
        )
    return getter(name)


def _load_alignment_function(name: str):
    """Resolve one optional SALI/GALI entry point without hard dependency."""

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        alignment = import_module("hidden_attractors.analysis.alignment_indices")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar la API opcional SALI/GALI: "
            f"{exc}"
        ) from exc
    function = getattr(alignment, name, None)
    if function is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            f"hidden_attractors.analysis.alignment_indices.{name}."
        )
    return function


def _require_integer_alignment_order(q) -> None:
    """Reject fractional SALI/GALI until hereditary variational theory exists."""

    import numpy as np

    try:
        orders = np.asarray(q, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("q debe ser un orden escalar o un vector de ordenes finitos.") from exc
    if (
        orders.size == 0
        or not np.all(np.isfinite(orders))
        or not np.allclose(orders, 1.0, rtol=0.0, atol=1.0e-9)
    ):
        raise ValueError(
            "SALI/GALI en Toolbox Chaos solo admite orden entero q=1; "
            "la dinamica variacional fraccionaria hereditaria aun no esta implementada."
        )


def _load_covariant_function(name: str):
    """Resolve one optional CLV entry point without a startup dependency."""

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        covariant = import_module("hidden_attractors.analysis.covariant_lyapunov")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar la API opcional CLV: "
            f"{exc}"
        ) from exc
    function = getattr(covariant, name, None)
    if function is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            f"hidden_attractors.analysis.covariant_lyapunov.{name}."
        )
    return function


def _require_integer_covariant_order(q) -> None:
    """Reject fractional CLV generation before loading the optional engine."""

    import numpy as np

    try:
        orders = np.asarray(q, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("q debe ser un orden escalar o un vector de ordenes finitos.") from exc
    if (
        orders.size == 0
        or not np.all(np.isfinite(orders))
        or not np.allclose(orders, 1.0, rtol=0.0, atol=1.0e-9)
    ):
        raise ValueError(
            "CLV en Toolbox Chaos solo admite orden entero q=1; el cociclo "
            "tangente del espacio de historia fraccionario aun no esta implementado."
        )


def validate_system_definition(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and canonicalise a no-code system definition."""

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    definition = engine.ExpressionSystemDefinition.from_mapping(data)
    model = engine.compile_expression_system(definition)
    model.evaluate(model.initial_state, model.parameters)
    return definition.to_mapping()


def simulate_system_definition(
    data: Mapping[str, Any],
    *,
    step_size: float = 0.01,
    duration: float = 10.0,
    iterations: int | None = None,
    method: str = "rk4",
    divergence_norm: float | None = 1.0e6,
):
    """Compile and simulate a no-code system through Hidden Attractors FO."""

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    definition = engine.ExpressionSystemDefinition.from_mapping(data)
    model = engine.compile_expression_system(definition)
    return engine.simulate(
        model,
        step_size=step_size,
        duration=duration,
        iterations=iterations,
        method=method,
        divergence_norm=divergence_norm,
    )


def integrate_multi_term_caputo_l1(
    rhs,
    initial_state,
    parameters=None,
    *,
    orders,
    coefficients,
    step: float,
    n_steps: int,
    lower_terminal: float = 0.0,
    zero_coefficient_policy: str = "drop",
    corrector_atol: float = 1.0e-12,
    corrector_rtol: float = 1.0e-10,
    corrector_max_iterations: int = 50,
    on_nonconvergence: str = "raise",
    initial_regularity: str = "unknown",
    compatibility_tolerance: float = 1.0e-10,
    use_acceleration: bool = True,
    allow_python_fallback: bool = True,
    divergence_norm: float | None = 120.0,
):
    """Run HAFO's finite multi-term Caputo L1 facade lazily.

    Orders and coefficients describe the equation itself and are forwarded
    unchanged to HAFO.  The returned ``MultiTermCaputoResult`` retains the
    canonical terms, underlying combined-L1 result, backend and solver
    provenance.  It is finite numerical trajectory evidence, not by itself a
    claim of chaos, attraction, stability, or hiddenness.
    """

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        fractional = import_module("hidden_attractors.fractional")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar la API fraccionaria opcional: "
            f"{exc}"
        ) from exc
    integrator = getattr(fractional, "integrate_multi_term_caputo_l1", None)
    if integrator is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            "hidden_attractors.fractional.integrate_multi_term_caputo_l1."
        )
    return integrator(
        rhs,
        initial_state,
        parameters,
        orders=orders,
        coefficients=coefficients,
        step=step,
        n_steps=n_steps,
        lower_terminal=lower_terminal,
        zero_coefficient_policy=zero_coefficient_policy,
        corrector_atol=corrector_atol,
        corrector_rtol=corrector_rtol,
        corrector_max_iterations=corrector_max_iterations,
        on_nonconvergence=on_nonconvergence,
        initial_regularity=initial_regularity,
        compatibility_tolerance=compatibility_tolerance,
        use_acceleration=use_acceleration,
        allow_python_fallback=allow_python_fallback,
        divergence_norm=divergence_norm,
    )


def tempered_convolution_quadrature(
    samples,
    orders,
    *,
    tempering,
    bdf_order: int = 1,
    definition: str = "tempered_riemann_liouville",
    step: float | None = None,
    times=None,
    lower_terminal: float = 0.0,
    initial_condition_semantics: str,
    backend: str = "numba",
):
    """Delegate HAFO's sampled tempered convolution-quadrature operator.

    Every mathematical choice, including the RL/Caputo definition and its
    explicit initial-condition token, is forwarded unchanged.  The typed HAFO
    result is returned without conversion.  This evaluates an operator on an
    already sampled history: it is not an FDE solver and does not establish
    chaos, attraction, stability, or hiddenness.  The ``fft`` backend is a
    one-shot batch convolution, not a streaming fast-history algorithm.
    """

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        fractional = import_module("hidden_attractors.fractional")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar la API fraccionaria opcional: "
            f"{exc}"
        ) from exc
    evaluator = getattr(fractional, "tempered_convolution_quadrature", None)
    if evaluator is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            "hidden_attractors.fractional.tempered_convolution_quadrature."
        )
    return evaluator(
        samples,
        orders,
        tempering=tempering,
        bdf_order=bdf_order,
        definition=definition,
        step=step,
        times=times,
        lower_terminal=lower_terminal,
        initial_condition_semantics=initial_condition_semantics,
        backend=backend,
    )


def tempered_fast_multistep_history(
    samples,
    orders,
    *,
    tempering,
    multistep_method: str = "gngf2",
    definition: str = "tempered_riemann_liouville",
    step: float | None = None,
    times=None,
    lower_terminal: float = 0.0,
    initial_condition_semantics: str,
    local_history_steps: int = 50,
    quadrature_points: int | None = None,
    relative_tolerance: float = 1.0e-8,
    tail_cutoff: float = 1.0e-20,
    max_quadrature_points: int = 2049,
    backend: str = "numba",
):
    """Delegate HAFO's recurrent tempered Fast Method II operator.

    The bridge forwards every mathematical and compression option unchanged
    and returns HAFO's typed ``TemperedFastHistoryResult``.  This is the
    real-axis recurrent FBDF1/GNGF2 sampled operator, not direct or FFT
    convolution and not an FDE solver.  In particular, ``gngf2`` is not
    silently reinterpreted as fractional BDF2, and ``relative_tolerance`` is
    a history-compression check rather than a solution-error tolerance.
    """

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    try:
        fractional = import_module("hidden_attractors.fractional")
    except Exception as exc:
        raise RuntimeError(
            "Hidden Attractors FO no pudo cargar la API fraccionaria opcional: "
            f"{exc}"
        ) from exc
    evaluator = getattr(fractional, "tempered_fast_multistep_history", None)
    if evaluator is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la capacidad "
            "requerida "
            "hidden_attractors.fractional.tempered_fast_multistep_history."
        )
    return evaluator(
        samples,
        orders,
        tempering=tempering,
        multistep_method=multistep_method,
        definition=definition,
        step=step,
        times=times,
        lower_terminal=lower_terminal,
        initial_condition_semantics=initial_condition_semantics,
        local_history_steps=local_history_steps,
        quadrature_points=quadrature_points,
        relative_tolerance=relative_tolerance,
        tail_cutoff=tail_cutoff,
        max_quadrature_points=max_quadrature_points,
        backend=backend,
    )


def tangent_alignment_indices(
    tangent_history,
    *,
    coordinates=None,
    states=None,
    gali_orders=None,
    backend: str = "auto",
    system_kind: str = "precomputed",
    coordinate_kind: str = "sample",
    method: str = "precomputed",
    method_id: str = "alignment_indices_from_tangent_history",
    q=1.0,
    metadata: Mapping[str, Any] | None = None,
    methodological_warnings=None,
):
    """Delegate finite-time SALI/GALI from a precomputed tangent history.

    ``tangent_history`` has the unambiguous public shape
    ``(n_samples, n_vectors, dimension)``.  Toolbox Chaos does not infer
    deviation vectors from a state trajectory or transpose axes implicitly.
    The typed HAFO ``AlignmentIndexResult`` is returned unchanged.
    """

    _require_integer_alignment_order(q)
    analyzer = _load_alignment_function("alignment_indices_from_tangent_history")
    return analyzer(
        tangent_history,
        coordinates=coordinates,
        states=states,
        gali_orders=gali_orders,
        backend=backend,
        system_kind=system_kind,
        coordinate_kind=coordinate_kind,
        method=method,
        method_id=method_id,
        q=q,
        metadata=metadata,
        methodological_warnings=methodological_warnings,
    )


def integer_system_definition_alignment_indices(
    data: Mapping[str, Any],
    *,
    initial_state=None,
    q=1.0,
    **kwargs,
):
    """Compile a no-code integer flow/map and delegate SALI/GALI to HAFO.

    Flow/map-specific options are forwarded to HAFO's dispatcher.  Fractional
    orders are rejected explicitly because an instantaneous state and its
    classical tangent bundle do not encode fractional hereditary dynamics.
    The typed HAFO result is returned unchanged.
    """

    _require_integer_alignment_order(q)
    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    definition = engine.ExpressionSystemDefinition.from_mapping(data)
    model = engine.compile_expression_system(definition)
    state = model.initial_state if initial_state is None else initial_state
    analyzer = _load_alignment_function("integer_system_alignment_indices")
    return analyzer(model, state, q=q, **kwargs)


def integer_qr_history_covariant_lyapunov_vectors(
    orthonormal_bases,
    r_factors,
    *,
    q=1.0,
    **kwargs,
):
    """Reconstruct integer CLVs from explicit positive-diagonal QR histories.

    Toolbox Chaos preserves HAFO's layouts and typed result.  A trajectory of
    states alone is not accepted because it does not define a tangent cocycle.
    """

    _require_integer_covariant_order(q)
    analyzer = _load_covariant_function(
        "integer_covariant_vectors_from_qr_history"
    )
    return analyzer(orthonormal_bases, r_factors, q=q, **kwargs)


def covariant_vector_angles(
    vectors,
    *,
    coordinates=None,
    pairs=None,
    subspaces=None,
    unoriented: bool = True,
    window: int | None = None,
):
    """Delegate geometric pair/subspace angles for an explicit CLV history.

    This postprocessor does not infer how the supplied vectors were generated
    and therefore does not promote an unvalidated fractional CLV method.
    """

    analyzer = _load_covariant_function("covariant_lyapunov_angles")
    return analyzer(
        vectors,
        coordinates=coordinates,
        pairs=pairs,
        subspaces=subspaces,
        unoriented=unoriented,
        window=window,
    )


def integer_system_definition_covariant_lyapunov_vectors(
    data: Mapping[str, Any],
    *,
    initial_state=None,
    q=1.0,
    **kwargs,
):
    """Compile a no-code integer flow/map and delegate CLVs to HAFO."""

    _require_integer_covariant_order(q)
    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    definition = engine.ExpressionSystemDefinition.from_mapping(data)
    model = engine.compile_expression_system(definition)
    state = model.initial_state if initial_state is None else initial_state
    analyzer = _load_covariant_function(
        "integer_system_covariant_lyapunov_vectors"
    )
    return analyzer(model, state, q=q, **kwargs)


def trajectory_spectrum(
    times,
    states,
    *,
    method: str = "psd_welch",
    min_frequency: float | None = None,
    max_frequency: float | None = None,
):
    """Compute comparable component spectra through the scientific engine."""

    import numpy as np

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    t = np.asarray(times, dtype=float)
    values = np.asarray(states, dtype=float)
    if t.ndim != 1 or values.ndim != 2 or len(t) != len(values) or len(t) < 4:
        raise ValueError("Se requieren al menos cuatro muestras temporales alineadas.")
    component_count = min(3, values.shape[1])
    finite = np.isfinite(t) & np.all(np.isfinite(values[:, :component_count]), axis=1)
    trajectory = np.column_stack((t[finite], values[finite, :component_count]))
    if len(trajectory) < 4:
        raise ValueError("No hay suficientes muestras finitas para el espectro.")
    results = engine.trajectory_component_spectra(
        trajectory,
        components=range(component_count),
        method=method,
    )
    if not results or any(len(item.frequency_hz) == 0 for item in results):
        raise ValueError("El motor no pudo calcular un espectro con estas muestras.")
    frequencies = np.asarray(results[0].frequency_hz, dtype=float)
    if any(not np.array_equal(frequencies, np.asarray(item.frequency_hz)) for item in results[1:]):
        raise RuntimeError("Los componentes devolvieron ejes de frecuencia incompatibles.")
    spectra = np.column_stack([np.asarray(item.values, dtype=float) for item in results])
    lo = float(min_frequency) if min_frequency is not None else -np.inf
    hi = float(max_frequency) if max_frequency is not None else np.inf
    keep = (frequencies >= lo) & (frequencies <= hi)
    return frequencies[keep], spectra[keep], results[0].method


def trajectory_correlation_dimension(
    states,
    radii,
    *,
    fit_radius_range: tuple[float, float],
    theiler_window: int = 0,
    metric: str = "euclidean",
    backend: str = "auto",
    minimum_points: int = 3,
    fallback: bool = True,
    sampling: str = "trajectory samples supplied by Toolbox Chaos",
    projection: str = "state coordinates selected in Toolbox Chaos",
):
    """Compute HAFO's finite q=2 curve and caller-selected slope fit.

    The result is a sampled-trajectory diagnostic.  In particular, it is not
    a proof of chaos or hiddenness, and fractional coordinates need not form a
    complete hereditary state.
    """

    import numpy as np

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    estimator = getattr(engine, "estimate_correlation_dimension", None)
    if estimator is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            "estimate_correlation_dimension."
        )
    return estimator(
        np.asarray(states, dtype=float),
        np.asarray(radii, dtype=float),
        fit_radius_range=fit_radius_range,
        theiler_window=theiler_window,
        metric=metric,
        backend=backend,
        minimum_points=minimum_points,
        fallback=fallback,
        sampling=sampling,
        projection=projection,
    )


def trajectory_permutation_entropy(
    signal_or_states,
    *,
    component: int | None = None,
    embedding_dimension: int = 3,
    delay: int = 1,
    tie_policy: str = "stable_index",
    log_base: float = 2.0,
    backend: str = "auto",
    fallback: bool = True,
):
    """Compute HAFO's finite-sample Bandt--Pompe diagnostic.

    ``signal_or_states`` may be either a scalar signal or a state matrix.  A
    matrix requires an explicit ``component``; the selected column is recorded
    as the projection passed to HAFO.  The returned HAFO result includes the
    ordinal distribution, normalized entropy, warnings, and provenance.  It is
    a trajectory diagnostic, not evidence by itself of chaos, attraction, or
    hiddenness.
    """

    import numpy as np

    engine, status = _load_engine()
    if engine is None:
        raise RuntimeError(status.message)
    estimator = getattr(engine, "permutation_entropy", None)
    if estimator is None:
        raise RuntimeError(
            "La version de Hidden Attractors FO no ofrece la API requerida "
            "permutation_entropy."
        )

    values = np.asarray(signal_or_states, dtype=float)
    if values.ndim == 1:
        if component is not None:
            raise ValueError("component solo se admite para una matriz de estados.")
        signal = values
        projection = "scalar signal supplied by Toolbox Chaos"
    elif values.ndim == 2:
        if component is None:
            raise ValueError(
                "component es obligatorio para seleccionar una matriz de estados."
            )
        if isinstance(component, (bool, np.bool_)) or not isinstance(
            component, (int, np.integer)
        ):
            raise TypeError("component debe ser un indice entero.")
        component_index = int(component)
        if component_index < 0 or component_index >= values.shape[1]:
            raise IndexError("component esta fuera de la dimension de estados.")
        signal = values[:, component_index]
        projection = f"Toolbox Chaos state component {component_index}"
    else:
        raise ValueError("Se requiere una senal 1D o una matriz de estados 2D.")

    return estimator(
        signal,
        embedding_dimension=embedding_dimension,
        delay=delay,
        tie_policy=tie_policy,
        log_base=log_base,
        backend=backend,
        fallback=fallback,
        sampling="trajectory samples supplied by Toolbox Chaos",
        projection=projection,
    )


__all__ = [
    "EngineStatus",
    "covariant_vector_angles",
    "engine_capability",
    "engine_status",
    "integrate_multi_term_caputo_l1",
    "integer_qr_history_covariant_lyapunov_vectors",
    "integer_system_definition_alignment_indices",
    "integer_system_definition_covariant_lyapunov_vectors",
    "simulate_system_definition",
    "tangent_alignment_indices",
    "tempered_convolution_quadrature",
    "tempered_fast_multistep_history",
    "trajectory_correlation_dimension",
    "trajectory_permutation_entropy",
    "trajectory_spectrum",
    "validate_system_definition",
]
