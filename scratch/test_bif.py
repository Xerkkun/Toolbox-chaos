"""Manual offscreen smoke check for the bifurcation tab.

This file is intentionally inert when imported. Run it directly from the
repository root when an interactive smoke check is needed.
"""


def main() -> int:
    import os

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from core.qt_binding import configure_pyside6

    configure_pyside6()

    from PySide6.QtWidgets import QApplication, QMessageBox

    from ui.tab_controls import TabBifurcationWidget

    app = QApplication.instance() or QApplication([])
    original_critical = QMessageBox.critical
    try:
        QMessageBox.critical = staticmethod(
            lambda parent, title, message, *args, **kwargs: print(
                f"CRITICAL DIALOG: {title} - {message}"
            )
        )
        tab = TabBifurcationWidget()
        for system_key, compare in (
            ('rossler', False),
            ('lorenz', False),
            ('lorenz', True),
        ):
            tab.param_panel.system_combo.setCurrentIndex(
                tab.param_panel.system_combo.findData(system_key)
            )
            tab.chk_compare.setChecked(compare)
            tab.run_bifurcation()
            print(system_key, compare, tab.lbl_warning.text())
    finally:
        QMessageBox.critical = original_critical
        app.processEvents()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
