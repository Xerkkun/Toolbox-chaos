from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic, perf_counter_ns
from types import ModuleType

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QImage
from PySide6.QtSvg import QSvgRenderer, QtSvg
from PySide6.QtWidgets import QApplication, QDialog, QTextBrowser, QWidget

from core.qt_binding import QtBindingConflictError, configure_pyside6
from core.qt_image import qimage_rgba_array
from core.startup_probe import StartupReadyProbe
from ui.pdf_viewer import PdfViewerWidget, QT_PDF_AVAILABLE


_APP = QApplication.instance() or QApplication([])


def _process_until(predicate, timeout: float = 3.0) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        _APP.processEvents()
        if predicate():
            return True
    return predicate()


def test_qimage_buffer_uses_pyside_memoryview_without_sip_resize():
    image = QImage(3, 2, QImage.Format.Format_ARGB32)
    image.fill(QColor(255, 255, 255))

    assert isinstance(image.constBits(), memoryview)
    pixels = qimage_rgba_array(image)

    assert pixels.shape == (2, 3, 4)
    assert np.all(pixels[:, :, :3] == 255)


def test_matplotlib_and_pyqtgraph_use_pyside6_exclusively():
    # Import the application's adapter users, which must load PySide6 before
    # either library chooses a Qt binding.
    import ui.canvases  # noqa: F401
    import ui.sprott_canvases  # noqa: F401
    import ui.tab_controls  # noqa: F401
    from matplotlib.backends import qt_compat
    import pyqtgraph

    assert qt_compat.QT_API == "PySide6"
    assert pyqtgraph.Qt.QT_LIB == "PySide6"


def test_qt_binding_overrides_stale_adapter_preferences(monkeypatch):
    monkeypatch.setenv("QT_API", "pyqt6")
    monkeypatch.setenv("PYQTGRAPH_QT_LIB", "PyQt6")

    configure_pyside6()

    assert os.environ["QT_API"] == "pyside6"
    assert os.environ["PYQTGRAPH_QT_LIB"] == "PySide6"


def test_qt_svg_global_parser_uses_restricted_options(monkeypatch):
    captured = []
    monkeypatch.setattr(
        QSvgRenderer,
        "setDefaultOptions",
        lambda options: captured.append(options),
    )
    configure_pyside6()
    options = captured[-1]

    assert options & QtSvg.Option.Tiny12FeaturesOnly
    assert options & QtSvg.Option.DisableAnimations
    assert not options & QtSvg.Option.AssumeTrustedSource


def test_qt_binding_rejects_an_already_loaded_incompatible_binding(monkeypatch):
    monkeypatch.setitem(sys.modules, "PyQt6", ModuleType("PyQt6"))

    with pytest.raises(QtBindingConflictError, match="PyQt6"):
        configure_pyside6()


def test_fresh_ui_import_repairs_hostile_qt_environment():
    environment = os.environ.copy()
    environment.update(
        {
            "QT_API": "pyqt6",
            "PYQTGRAPH_QT_LIB": "PyQt6",
            "QT_QPA_PLATFORM": "offscreen",
        }
    )
    probe = (
        "import os; import ui.tab_controls; "
        "from matplotlib.backends import qt_compat; import pyqtgraph; "
        "assert os.environ['QT_API']=='pyside6'; "
        "assert os.environ['PYQTGRAPH_QT_LIB']=='PySide6'; "
        "assert qt_compat.QT_API=='PySide6'; "
        "assert pyqtgraph.Qt.QT_LIB=='PySide6'; "
        "print('PYSIDE6_BINDING_OK')"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", probe],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PYSIDE6_BINDING_OK" in completed.stdout


def test_startup_probe_records_first_real_paint(tmp_path: Path):
    output = tmp_path / "startup-ready.json"
    window = QWidget()
    window.resize(320, 200)
    probe = StartupReadyProbe(window, output, perf_counter_ns())

    window.show()
    assert _process_until(output.exists), "The first-paint probe did not fire"

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "ready"
    assert payload["startup_seconds"] >= 0.0
    assert probe.parent() is window

    window.close()
    window.deleteLater()
    _APP.processEvents()


def test_pyside_qtpdf_loads_the_bundled_dictionary():
    if not QT_PDF_AVAILABLE:
        pytest.skip("PySide6-Addons is required for the embedded PDF viewer")

    pdf = Path(__file__).resolve().parents[1] / "assets" / "chaos_dictionary.pdf"
    viewer = PdfViewerWidget(pdf, "Diccionario")

    assert viewer._pdf_document is not None
    assert viewer._pdf_document.pageCount() > 0
    assert viewer._pdf_view is not None

    viewer.deleteLater()
    _APP.processEvents()


def test_about_dialog_distinguishes_own_code_from_third_party(monkeypatch):
    from ui.main_window import MainWindow

    captured: dict[str, str] = {}

    def inspect_dialog(dialog: QDialog):
        browser = dialog.findChild(QTextBrowser)
        assert browser is not None
        captured["text"] = browser.toPlainText()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(QDialog, "exec", inspect_dialog)
    window = MainWindow()
    window.show_about_dialog()

    assert "Código propio: MIT" in captured["text"]
    assert "Dependencias de terceros:" in captured["text"]
    assert "THIRD_PARTY_NOTICES.md" in captured["text"]

    window.close()
    window.deleteLater()
    _APP.processEvents()
