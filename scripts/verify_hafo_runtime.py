#!/usr/bin/env python3
"""Verify the installed HAFO distribution required by Toolbox builds."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version

from packaging.version import InvalidVersion, Version


DISTRIBUTION = "hidden-attractors-fo"
MINIMUM = Version("1.1")
MAXIMUM = Version("2")
REQUIRED_API = (
    "ExpressionSystemDefinition",
    "compile_expression_system",
    "simulate",
    "trajectory_component_spectra",
)


def verify() -> str:
    try:
        installed = version(DISTRIBUTION)
    except PackageNotFoundError as exc:
        raise RuntimeError(f"No está instalada la distribución {DISTRIBUTION}.") from exc
    try:
        parsed = Version(installed)
    except InvalidVersion as exc:
        raise RuntimeError(f"{DISTRIBUTION} declara una versión inválida: {installed!r}.") from exc
    if not MINIMUM <= parsed < MAXIMUM:
        raise RuntimeError(
            f"Se requiere {DISTRIBUTION}>=1.1,<2; se encontró {installed}."
        )
    try:
        engine = import_module("hidden_attractors")
    except (ImportError, OSError) as exc:
        raise RuntimeError(f"{DISTRIBUTION} {installed} no puede importarse: {exc}") from exc
    missing = [name for name in REQUIRED_API if not hasattr(engine, name)]
    if missing:
        raise RuntimeError(
            f"{DISTRIBUTION} {installed} no ofrece la API requerida: "
            + ", ".join(missing)
        )
    return installed


def main() -> int:
    try:
        installed = verify()
    except RuntimeError as exc:
        print(f"HAFO_RUNTIME_ERROR: {exc}")
        return 1
    print(f"HAFO_RUNTIME_OK {installed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
