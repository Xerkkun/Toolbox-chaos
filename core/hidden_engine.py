"""Optional bridge from the desktop application to Hidden Attractors FO.

The GUI owns interaction and rendering. Numerical system definitions and
trajectory generation are delegated to the scientific engine when its
compatible API is available. Import is lazy so starting the desktop
application is not blocked by scientific dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import sys
from typing import Any, Mapping


@dataclass(frozen=True)
class EngineStatus:
    available: bool
    version: str | None
    source: str | None
    message: str


_ENGINE: Any | None = None
_ENGINE_STATUS: EngineStatus | None = None


def _development_candidates() -> tuple[Path, ...]:
    repo = Path(__file__).resolve().parents[1]
    return (
        repo.parent / "Hidden Attractors Fractional Order" / "version_2",
        repo.parent / "Hidden-Attractors-Localization" / "version_2",
    )


def _load_engine() -> tuple[Any | None, EngineStatus]:
    global _ENGINE, _ENGINE_STATUS
    if _ENGINE_STATUS is not None:
        return _ENGINE, _ENGINE_STATUS

    source = "installed package"
    for candidate in _development_candidates():
        if (candidate / "hidden_attractors" / "__init__.py").is_file():
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            source = candidate_text
            break

    try:
        engine = import_module("hidden_attractors")
        required = (
            "ExpressionSystemDefinition",
            "compile_expression_system",
            "simulate",
            "trajectory_component_spectra",
        )
        missing = [name for name in required if not hasattr(engine, name)]
        if missing:
            raise RuntimeError(
                "La version encontrada no ofrece la API de integracion: "
                + ", ".join(missing)
            )
        version = getattr(engine, "__version__", None)
        _ENGINE = engine
        _ENGINE_STATUS = EngineStatus(
            True,
            str(version) if version else None,
            source,
            "Motor cientifico disponible.",
        )
    except Exception as exc:  # the GUI must remain usable without the optional engine
        _ENGINE = None
        _ENGINE_STATUS = EngineStatus(
            False,
            None,
            source,
            f"Hidden Attractors FO no esta disponible o es incompatible: {exc}",
        )
    return _ENGINE, _ENGINE_STATUS


def engine_status(*, refresh: bool = False) -> EngineStatus:
    """Return availability without making the dependency mandatory."""

    global _ENGINE, _ENGINE_STATUS
    if refresh:
        _ENGINE = None
        _ENGINE_STATUS = None
    return _load_engine()[1]


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


__all__ = [
    "EngineStatus",
    "engine_status",
    "simulate_system_definition",
    "trajectory_spectrum",
    "validate_system_definition",
]
