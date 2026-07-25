from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import tempfile
import time

from PyQt6.QtCore import QEvent, QObject, QTimer
from PyQt6.QtWidgets import QApplication

from core.app_metadata import APP_NAME, APP_VERSION
from core.performance_metrics import process_memory_snapshot


READY_FILE_ENV = "CHAOS_BENCHMARK_READY_FILE"
START_NS_ENV = "CHAOS_BENCHMARK_START_NS"
EXIT_AFTER_READY_ENV = "CHAOS_BENCHMARK_EXIT_AFTER_READY"


class StartupReadyProbe(QObject):
    """Optional first-paint probe enabled only by the benchmark launcher."""

    def __init__(self, window, ready_path: Path, start_ns: int | None):
        super().__init__(window)
        self._window = window
        self._ready_path = ready_path
        self._start_ns = start_ns
        self._reported = False
        window.installEventFilter(self)

    def eventFilter(self, watched, event):  # noqa: N802 - Qt API
        if (
            watched is self._window
            and event.type() == QEvent.Type.Paint
            and not self._reported
        ):
            self._reported = True
            QTimer.singleShot(0, self._write_ready_record)
        return False

    def _write_ready_record(self) -> None:
        ready_ns = time.perf_counter_ns()
        memory = process_memory_snapshot()
        payload = {
            "schema_version": 1,
            "status": "ready",
            "application": APP_NAME,
            "application_version": APP_VERSION,
            "pid": os.getpid(),
            "ready_perf_counter_ns": ready_ns,
            "start_perf_counter_ns": self._start_ns,
            "startup_seconds": (
                (ready_ns - self._start_ns) / 1_000_000_000
                if self._start_ns is not None
                else None
            ),
            "memory_at_ready": memory.as_dict(),
            "platform": platform.platform(),
        }
        self._ready_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f"{self._ready_path.name}.",
            suffix=".tmp",
            dir=self._ready_path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
            os.replace(temporary_name, self._ready_path)
        finally:
            temporary_path = Path(temporary_name)
            if temporary_path.exists():
                temporary_path.unlink()

        if os.environ.get(EXIT_AFTER_READY_ENV) == "1":
            app = QApplication.instance()
            if app is not None:
                QTimer.singleShot(100, app.quit)


def install_startup_probe(window) -> StartupReadyProbe | None:
    raw_path = os.environ.get(READY_FILE_ENV)
    if not raw_path:
        return None
    raw_start = os.environ.get(START_NS_ENV)
    try:
        start_ns = int(raw_start) if raw_start else None
    except ValueError:
        start_ns = None
    return StartupReadyProbe(window, Path(raw_path).resolve(), start_ns)
