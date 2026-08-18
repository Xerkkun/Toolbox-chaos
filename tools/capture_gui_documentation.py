"""Generate current GUI screenshots used by the Toolbox Chaos web guides."""

from __future__ import annotations

import os
import sys
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

REPOSITORY = Path(__file__).resolve().parents[1]
WORKSPACE = REPOSITORY.parent
HAFO_SITE_PACKAGES = (
    WORKSPACE
    / "Hidden Attractors Fractional Order"
    / ".venv"
    / "Lib"
    / "site-packages"
)
OUTPUT = REPOSITORY / "assets" / "screenshots"

sys.path.insert(0, str(REPOSITORY))
if HAFO_SITE_PACKAGES.is_dir():
    sys.path.append(str(HAFO_SITE_PACKAGES))

from core.qt_binding import configure_pyside6  # noqa: E402

configure_pyside6()

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtGui import QFont, QFontDatabase  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.main_window import MainWindow  # noqa: E402


def settle(app: QApplication, cycles: int = 16) -> None:
    for _ in range(cycles):
        app.processEvents()
        QCoreApplication.sendPostedEvents()


def capture(app: QApplication, window: MainWindow, widget, filename: str) -> None:
    window.tabs.setCurrentWidget(widget)
    settle(app)
    pixmap = window.grab()
    destination = OUTPUT / filename
    if not pixmap.save(str(destination), "PNG"):
        raise RuntimeError(f"Could not save {destination}")
    print(f"{destination.name}: {pixmap.width()}x{pixmap.height()}")


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    font_id = QFontDatabase.addApplicationFont(r"C:\Windows\Fonts\segoeui.ttf")
    families = QFontDatabase.applicationFontFamilies(font_id)
    app.setFont(QFont(families[0] if families else "Segoe UI", 9))

    window = MainWindow()
    window.resize(1500, 900)
    window.show()
    settle(app)

    window.tab_3d_widget.run_simulation()
    window.tab_3d_widget.canvas.draw()
    capture(app, window, window.tab_3d_widget, "gui_attractor_3d.png")

    window.tab_2d_widget.use_last_trajectory()
    capture(app, window, window.tab_2d_widget, "gui_phase_portraits_2d.png")

    window.tab_time_widget.use_last_trajectory()
    capture(app, window, window.tab_time_widget, "gui_time_series.png")

    window.tab_fft_widget.use_last_trajectory()
    window.tab_fft_widget.canvas.draw()
    capture(app, window, window.tab_fft_widget, "gui_welch_psd.png")

    window.tab_method_compare_widget.run_comparison()
    window.tab_method_compare_widget.canvas.draw()
    capture(app, window, window.tab_method_compare_widget, "gui_method_comparison.png")

    window.tab_spectrum_widget.run_spectrum()
    window.tab_spectrum_widget.canvas.draw()
    capture(app, window, window.tab_spectrum_widget, "gui_equilibria_eigenvalues.png")

    # Real finite-time Lyapunov spectrum and convergence curves for Lorenz.
    window.tab_lyap_widget.dt.setValue(0.01)
    window.tab_lyap_widget.t_burn.setValue(5.0)
    window.tab_lyap_widget.t_final.setValue(40.0)
    window.tab_lyap_widget.reorth.setValue(10)
    window.tab_lyap_widget.run_lyapunov()
    if "no calculados" in window.tab_lyap_widget.lyap_info.text().lower():
        raise RuntimeError("Lyapunov capture did not produce a finite-time result")
    window.tab_lyap_widget.canvas.draw()
    capture(app, window, window.tab_lyap_widget, "gui_lyapunov.png")

    # A moderate-density Lorenz rho sweep keeps documentation generation fast
    # while still executing the same Poincare-event calculation as the GUI.
    window.tab_bif_widget.bif_n.setValue(100)
    window.tab_bif_widget.bif_trans.setValue(40.0)
    window.tab_bif_widget.bif_keep.setValue(60.0)
    window.tab_bif_widget.max_points.setValue(80)
    window.tab_bif_widget.run_bifurcation()
    window.tab_bif_widget.canvas.draw()
    capture(app, window, window.tab_bif_widget, "gui_bifurcation.png")

    # Compute the current default Lorenz x0-y0 basin at the documented 60x60
    # resolution and retain its equilibrium overlay.
    window.tab_basin_widget.nx.setValue(60)
    window.tab_basin_widget.ny.setValue(60)
    window.tab_basin_widget.run_basin()
    if window.tab_basin_widget.last_basin is None:
        raise RuntimeError("Basin capture did not produce a classification grid")
    window.tab_basin_widget.canvas.draw()
    capture(app, window, window.tab_basin_widget, "gui_basin.png")

    # Use the registered Lorenz rho=24.4 coexistence case and plot every
    # published initial condition with the same parameters.
    lorenz_case = window.tab_coexistence_widget.case_combo.findText("Lorenz")
    if lorenz_case < 0:
        raise RuntimeError("Registered Lorenz coexistence case was not found")
    window.tab_coexistence_widget.case_combo.setCurrentIndex(lorenz_case)
    window.tab_coexistence_widget.simulate_all()
    window.tab_coexistence_widget.canvas.draw()
    capture(app, window, window.tab_coexistence_widget, "gui_coexistence.png")

    # The dictionary is the real bundled PDF viewer. Give QtPdf enough event
    # time to render its first page before grabbing the offscreen window.
    window.tabs.setCurrentWidget(window.tab_dict)
    settle(app, cycles=24)
    QTest.qWait(750)
    settle(app, cycles=24)
    capture(app, window, window.tab_dict, "gui_dictionary.png")

    window.tabs.setCurrentWidget(window.tab_custom_system)
    settle(app)
    window.tab_custom_system.simulate()
    window.tab_custom_system.canvas.draw()
    capture(app, window, window.tab_custom_system, "gui_custom_system.png")

    window.tabs.setCurrentWidget(window.tab_sprott)
    settle(app)
    window.tab_sprott.load_quick_example_for_preset("Mapas discretos")
    settle(app, cycles=24)
    capture(app, window, window.tab_sprott, "gui_sprott_explorer.png")

    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
