"""Manual offscreen smoke check for the coexistence tab.

Importing this module does not create a QApplication, patch Qt, or simulate.
"""


def main() -> int:
    import os

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from core.qt_binding import configure_pyside6

    configure_pyside6()

    from PySide6.QtWidgets import QApplication, QMessageBox

    from ui.tab_controls import TabCoexistenceWidget

    app = QApplication.instance() or QApplication([])
    original_critical = QMessageBox.critical
    original_information = QMessageBox.information
    try:
        QMessageBox.critical = staticmethod(
            lambda parent, title, message, *args, **kwargs: print(
                f"CRITICAL DIALOG: {title} - {message}"
            )
        )
        QMessageBox.information = staticmethod(
            lambda parent, title, message, *args, **kwargs: print(
                f"INFO DIALOG: {title} - {message}"
            )
        )
        tab = TabCoexistenceWidget()
        print('cases', len(tab.cases), 'items', tab.case_combo.count())
        if tab.case_combo.count() > 0:
            tab.case_combo.setCurrentIndex(0)
            tab.simulate_one()
            tab.simulate_all()
    finally:
        QMessageBox.critical = original_critical
        QMessageBox.information = original_information
        app.processEvents()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
