"""Select PySide6 before any Qt adapter is imported."""

from __future__ import annotations

import os
import sys


class QtBindingConflictError(RuntimeError):
    """Raised when another Qt binding already owns the current process."""


def configure_pyside6() -> None:
    """Make PySide6 the only Qt binding used by the application process.

    Matplotlib and pyqtgraph both support several bindings and consult
    environment variables during their first import.  Override stale global
    preferences before either adapter loads, and fail clearly if a different
    binding is already active because mixing QObject implementations is unsafe.
    """

    conflicting_modules = tuple(
        name
        for name in ("PyQt5", "PyQt6", "PySide2")
        if name in sys.modules
    )
    matplotlib_compat = sys.modules.get("matplotlib.backends.qt_compat")
    matplotlib_binding = getattr(matplotlib_compat, "QT_API", None)
    pyqtgraph_qt = sys.modules.get("pyqtgraph.Qt")
    pyqtgraph_binding = getattr(pyqtgraph_qt, "QT_LIB", None)

    conflicts = list(conflicting_modules)
    if matplotlib_binding not in (None, "PySide6"):
        conflicts.append(f"Matplotlib/{matplotlib_binding}")
    if pyqtgraph_binding not in (None, "PySide6"):
        conflicts.append(f"pyqtgraph/{pyqtgraph_binding}")
    if conflicts:
        joined = ", ".join(conflicts)
        raise QtBindingConflictError(
            "Chaos Toolbox requiere un proceso PySide6 limpio; ya se cargó "
            f"una biblioteca Qt incompatible: {joined}."
        )

    # QtSvg remains required by Matplotlib/pyqtgraph. Constrain its process-wide
    # parser before either adapter imports it; never enable AssumeTrustedSource.
    from PySide6.QtSvg import QSvgRenderer, QtSvg

    svg_options = (
        QtSvg.Option.Tiny12FeaturesOnly
        | QtSvg.Option.DisableAnimations
    )
    QSvgRenderer.setDefaultOptions(svg_options)

    os.environ["QT_API"] = "pyside6"
    os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"


configure_pyside6()


__all__ = ["QtBindingConflictError", "configure_pyside6"]
