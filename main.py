import os
import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def configure_qt_platform():
    if 'QT_QPA_PLATFORM' in os.environ:
        return

    # En escritorio normal, lo más estable es no forzar plugin.
    # Si necesitas fijarlo por despliegue, hazlo por sistema operativo.
    if sys.platform.startswith('linux'):
        pass
    elif sys.platform.startswith('win'):
        pass


def main():
    configure_qt_platform()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
