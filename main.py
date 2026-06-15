import os
import multiprocessing as mp
import sys
import logging

from PyQt6.QtWidgets import QApplication
from core.app_metadata import APP_NAME, APP_VERSION
from ui.main_window import MainWindow

def configure_qt_platform():
    if 'QT_QPA_PLATFORM' in os.environ:
        return
    if sys.platform.startswith('linux'):
        pass
    elif sys.platform.startswith('win'):
        pass


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    logging.getLogger(__name__).info('Starting %s %s', APP_NAME, APP_VERSION)
    configure_qt_platform()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def configure_multiprocessing():
    mp.freeze_support()

    start_method = os.environ.get('CHAOS_MP_START_METHOD')
    if start_method is None and (sys.platform.startswith('win') or sys.platform == 'darwin'):
        start_method = 'spawn'
    if not start_method:
        return

    try:
        mp.set_start_method(start_method)
    except RuntimeError:
        pass


if __name__ == '__main__':
    configure_multiprocessing()
    main()
