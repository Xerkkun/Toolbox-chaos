import hashlib
import json
import os
import multiprocessing as mp
from pathlib import Path
import sys
import logging

from PyQt6.QtWidgets import QApplication
from core.app_metadata import APP_NAME, APP_VERSION
from core.startup_probe import install_startup_probe
from ui.main_window import MainWindow


def run_packaged_self_test(arguments: list[str]) -> int | None:
    """Run a small native numerical calculation without opening the GUI."""

    option = "--self-test-output"
    if option not in arguments:
        return None
    index = arguments.index(option)
    if index + 1 >= len(arguments):
        print(f"{option} requires an output JSON path.", file=sys.stderr)
        return 2

    output_path = Path(arguments[index + 1]).expanduser().resolve()
    try:
        import numpy as np

        from core.lorenz import simulate_system

        times, states = simulate_system(
            "lorenz",
            [1.0, 1.0, 1.0],
            [10.0, 28.0, 8.0 / 3.0],
            0.01,
            1.0,
            "rk4",
        )
        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(times).tobytes())
        digest.update(np.ascontiguousarray(states).tobytes())
        payload = {
            "schema_version": 1,
            "status": "ok",
            "application": APP_NAME,
            "version": APP_VERSION,
            "time_shape": list(times.shape),
            "state_shape": list(states.shape),
            "all_finite": bool(
                np.all(np.isfinite(times)) and np.all(np.isfinite(states))
            ),
            "result_sha256": digest.hexdigest(),
        }
        if not payload["all_finite"] or states.shape[1] != 3:
            raise RuntimeError("The native Lorenz result is invalid.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "status": "failed",
            "application": APP_NAME,
            "version": APP_VERSION,
            "error": f"{type(exc).__name__}: {exc}",
        }
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        return 1


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
    startup_probe = install_startup_probe(window)
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
    self_test_status = run_packaged_self_test(sys.argv[1:])
    if self_test_status is not None:
        raise SystemExit(self_test_status)
    main()
