"""Runtime probes for optional Qt components."""

from __future__ import annotations

from dataclasses import dataclass
import os

from core.qt_binding import configure_pyside6

configure_pyside6()


@dataclass(frozen=True)
class QtCapabilityStatus:
    available: bool
    reason: str


_WEBENGINE_TYPES = None


def prepare_webengine() -> QtCapabilityStatus:
    """Prepare Qt WebEngine before any QCoreApplication is constructed."""

    global _WEBENGINE_TYPES
    platform_name = os.environ.get('QT_QPA_PLATFORM', '').strip().lower()
    if platform_name in {'offscreen', 'minimal'}:
        return QtCapabilityStatus(
            False, f"Qt WebEngine no se habilita con QT_QPA_PLATFORM={platform_name}."
        )
    if _WEBENGINE_TYPES is not None:
        return QtCapabilityStatus(True, "Qt WebEngine preparado.")
    try:
        from PySide6.QtCore import QCoreApplication, Qt
        from PySide6.QtWidgets import QApplication

        if QApplication.instance() is not None:
            return QtCapabilityStatus(
                False,
                "Qt WebEngine debe prepararse antes de crear QApplication.",
            )
        QCoreApplication.setAttribute(
            Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True
        )
        from PySide6.QtWebEngineCore import QWebEnginePage
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except (ImportError, OSError, RuntimeError) as exc:
        return QtCapabilityStatus(False, f"Qt WebEngine no esta instalado: {exc}")
    _WEBENGINE_TYPES = (QWebEnginePage, QWebEngineView)
    return QtCapabilityStatus(True, "Qt WebEngine preparado.")


def create_webengine_view():
    """Create and validate a WebEngine view, returning a text-safe fallback status."""

    platform_name = os.environ.get('QT_QPA_PLATFORM', '').strip().lower()
    if platform_name in {'offscreen', 'minimal'}:
        return None, QtCapabilityStatus(
            False, f"Qt WebEngine no se habilita con QT_QPA_PLATFORM={platform_name}."
        )
    preparation = prepare_webengine()
    if not preparation.available:
        return None, preparation
    from PySide6.QtWidgets import QApplication

    QWebEnginePage, QWebEngineView = _WEBENGINE_TYPES

    if QApplication.instance() is None:
        return None, QtCapabilityStatus(
            False, "Qt WebEngine requiere una QApplication activa."
        )
    try:
        view = QWebEngineView()
        page = view.page()
        if page is None or not isinstance(page, QWebEnginePage):
            view.deleteLater()
            return None, QtCapabilityStatus(
                False, "Qt WebEngine no pudo crear una pagina funcional."
            )
    except (RuntimeError, OSError) as exc:
        return None, QtCapabilityStatus(
            False, f"Qt WebEngine no pudo inicializar su motor: {exc}"
        )
    return view, QtCapabilityStatus(True, "Qt WebEngine operativo.")


__all__ = ['QtCapabilityStatus', 'create_webengine_view', 'prepare_webengine']
