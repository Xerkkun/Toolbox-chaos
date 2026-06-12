import os
import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def configure_qt_platform():
    if 'QT_QPA_PLATFORM' in os.environ:
        return
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
