import hashlib
import json
import os
import multiprocessing as mp
from pathlib import Path
import sys
import logging

from core.app_metadata import APP_NAME, APP_VERSION


def configure_numba_cache() -> Path:
    """Select a writable cache outside the read-only frozen application."""

    from core.paths import user_data_dir

    configured = os.environ.get("NUMBA_CACHE_DIR", "").strip()
    target = (
        Path(configured).expanduser()
        if configured
        else user_data_dir() / "numba-cache"
    ).resolve()
    if getattr(sys, "frozen", False):
        protected_roots = {
            Path(getattr(sys, "_MEIPASS", "")).resolve(),
            Path(sys.executable).resolve().parent,
        }
        if any(target == root or target.is_relative_to(root) for root in protected_roots):
            raise RuntimeError(
                "NUMBA_CACHE_DIR must be outside the frozen application."
            )
    target.mkdir(parents=True, exist_ok=True)
    if not target.is_dir():
        raise RuntimeError(f"Numba cache path is not a directory: {target}")
    os.environ["NUMBA_CACHE_DIR"] = str(target)
    return target


def run_packaged_self_test(arguments: list[str]) -> int | None:
    """Run native and HAFO/Numba calculations without opening the GUI."""

    option = "--self-test-output"
    if option not in arguments:
        return None
    index = arguments.index(option)
    if index + 1 >= len(arguments):
        print(f"{option} requires an output JSON path.", file=sys.stderr)
        return 2

    output_path = Path(arguments[index + 1]).expanduser().resolve()
    try:
        numba_cache_dir = configure_numba_cache()
        # Keep the release probe portable and deterministic.  A caller may
        # explicitly request OpenMP, but TBB is not part of the reviewed
        # frozen runtime.
        os.environ.setdefault("NUMBA_THREADING_LAYER", "workqueue")
        os.environ.setdefault(
            "NUMBA_NUM_THREADS", str(max(1, min(4, os.cpu_count() or 1)))
        )
        requested_threading_layer = os.environ["NUMBA_THREADING_LAYER"].strip().lower()
        if requested_threading_layer not in {"omp", "workqueue"}:
            raise RuntimeError(
                "The packaged self-test requires NUMBA_THREADING_LAYER=omp or "
                "NUMBA_THREADING_LAYER=workqueue."
            )

        import numba
        import numpy as np
        from importlib import import_module

        from core.hidden_engine import engine_status
        from core.lorenz import simulate_system
        import hidden_attractors as hafo
        from hidden_attractors.fractional.grunwald_letnikov import (
            _gl_derivative_numba,
            grunwald_letnikov_derivative,
        )

        frozen_runtime = bool(getattr(sys, "frozen", False))
        frozen_root = (
            Path(getattr(sys, "_MEIPASS", "")).resolve()
            if frozen_runtime
            else None
        )

        hafo_status = engine_status(refresh=True)
        if not hafo_status.available:
            raise RuntimeError(hafo_status.message)

        times, states = simulate_system(
            "lorenz",
            [1.0, 1.0, 1.0],
            [10.0, 28.0, 8.0 / 3.0],
            0.01,
            1.0,
            "rk4",
        )
        probe_times = np.linspace(0.0, 2.0, 257, dtype=np.float64)
        probe_samples = np.column_stack(
            [
                np.sin((component + 1.0) * probe_times)
                + 0.05 * component
                for component in range(16)
            ]
        )
        probe_scales = np.linspace(0.2, 0.9, probe_samples.shape[1])

        @numba.njit(cache=False, nogil=True, parallel=True)
        def packaged_parallel_probe(samples, scales):
            """Exercise the selected Numba pool without a persistent JIT cache."""

            output = np.empty_like(samples)
            for component in numba.prange(samples.shape[1]):
                running_total = 0.0
                scale = scales[component]
                for row in range(samples.shape[0]):
                    running_total += samples[row, component] * scale
                    output[row, component] = running_total / (row + 1.0)
            return output

        numba_values = packaged_parallel_probe(probe_samples, probe_scales)
        hafo_gl_result = grunwald_letnikov_derivative(
            probe_samples,
            float(probe_times[1] - probe_times[0]),
            probe_scales,
            definition="grunwald_letnikov",
        )
        hafo_gl_values = np.asarray(hafo_gl_result.values, dtype=np.float64)

        definition = hafo.ExpressionSystemDefinition.from_mapping(
            {
                "name": "Packaged self-test linear flow",
                "kind": "flow",
                "variables": ["x", "y"],
                "parameters": {"a": -0.5, "b": -0.25},
                "equations": ["a*x + y", "-x + b*y"],
                "initial_state": [1.0, -0.5],
            }
        )
        model = hafo.compile_expression_system(definition)
        hafo_result = hafo.simulate(
            model,
            step_size=0.01,
            duration=0.05,
            method="rk4",
            divergence_norm=None,
            use_acceleration=False,
        )
        hafo_times = np.asarray(hafo_result.times, dtype=np.float64)
        hafo_states = np.asarray(hafo_result.states, dtype=np.float64)
        hafo_source_modules = {
            "hidden_attractors": hafo,
            "hidden_attractors.systems": import_module("hidden_attractors.systems"),
            "hidden_attractors.simulation": import_module(
                "hidden_attractors.simulation"
            ),
            "hidden_attractors.integrations.numba_kernels": import_module(
                "hidden_attractors.integrations.numba_kernels"
            ),
            "hidden_attractors.fractional.convolution_quadrature": import_module(
                "hidden_attractors.fractional.convolution_quadrature"
            ),
            "hidden_attractors.fractional.grunwald_letnikov": import_module(
                "hidden_attractors.fractional.grunwald_letnikov"
            ),
        }
        hafo_source_paths = {
            name: Path(getattr(module, "__file__", "")).resolve()
            for name, module in hafo_source_modules.items()
        }
        hafo_module_origins = {
            name: (
                path.relative_to(frozen_root).as_posix()
                if frozen_root is not None and path.is_relative_to(frozen_root)
                else str(path)
            )
            for name, path in hafo_source_paths.items()
        }
        hafo_spec_paths = {
            name: Path(getattr(getattr(module, "__spec__", None), "origin", ""))
            .resolve()
            for name, module in hafo_source_modules.items()
        }
        hafo_module_spec_origins = {
            name: (
                path.relative_to(frozen_root).as_posix()
                if frozen_root is not None and path.is_relative_to(frozen_root)
                else str(path)
            )
            for name, path in hafo_spec_paths.items()
        }
        hafo_module_loaders = {
            name: (
                type(getattr(module, "__loader__", None)).__module__
                + "."
                + type(getattr(module, "__loader__", None)).__name__
            )
            for name, module in hafo_source_modules.items()
        }
        hafo_modules_collected_as_source = all(
            path.is_file()
            and path.suffix.casefold() == ".py"
            and (frozen_root is None or path.is_relative_to(frozen_root))
            for path in hafo_source_paths.values()
        ) and all(
            path.is_file()
            and path.suffix.casefold() == ".py"
            and (frozen_root is None or path.is_relative_to(frozen_root))
            for path in hafo_spec_paths.values()
        )
        active_threading_layer = numba.threading_layer()
        if active_threading_layer != requested_threading_layer:
            raise RuntimeError(
                "Numba initialized an unexpected threading layer: "
                f"requested={requested_threading_layer!r}, "
                f"active={active_threading_layer!r}."
            )
        expected_pool_module = (
            "numba.np.ufunc.workqueue"
            if active_threading_layer == "workqueue"
            else "numba.np.ufunc.omppool"
        )
        pool_module = sys.modules.get(expected_pool_module)
        pool_module_file = getattr(pool_module, "__file__", None)
        if pool_module is None or not pool_module_file:
            raise RuntimeError(
                f"Numba did not load the expected pool module {expected_pool_module}."
            )
        loaded_tbbpool_modules = sorted(
            name for name in sys.modules if "tbbpool" in name.casefold()
        )
        if loaded_tbbpool_modules:
            raise RuntimeError(
                "The excluded Numba TBB pool was loaded: "
                + ", ".join(loaded_tbbpool_modules)
            )
        bundled_tbbpool_files: list[Path] = []
        numba_cache_outside_bundle = True
        if frozen_runtime:
            numba_cache_outside_bundle = not numba_cache_dir.is_relative_to(
                frozen_root
            )
            if not numba_cache_outside_bundle:
                raise RuntimeError(
                    "NUMBA_CACHE_DIR must be outside the frozen application."
                )
            bundled_tbbpool_files = sorted(
                (frozen_root / "numba" / "np" / "ufunc").glob("tbbpool*.pyd")
            )
            if bundled_tbbpool_files:
                raise RuntimeError(
                    "The frozen runtime contains the excluded Numba TBB pool: "
                    + ", ".join(path.name for path in bundled_tbbpool_files)
                )

        digest = hashlib.sha256()
        digest.update(np.ascontiguousarray(times).tobytes())
        digest.update(np.ascontiguousarray(states).tobytes())
        numba_digest = hashlib.sha256(
            np.ascontiguousarray(numba_values).tobytes()
        ).hexdigest()
        numba_all_finite = bool(np.all(np.isfinite(numba_values)))
        numba_parallel_target = bool(
            packaged_parallel_probe.targetoptions.get("parallel")
        )
        hafo_digest = hashlib.sha256()
        hafo_digest.update(np.ascontiguousarray(hafo_times).tobytes())
        hafo_digest.update(np.ascontiguousarray(hafo_states).tobytes())
        hafo_all_finite = bool(
            np.all(np.isfinite(hafo_times))
            and np.all(np.isfinite(hafo_states))
        )
        hafo_gl_digest = hashlib.sha256(
            np.ascontiguousarray(hafo_gl_values).tobytes()
        ).hexdigest()
        hafo_gl_all_finite = bool(np.all(np.isfinite(hafo_gl_values)))
        hafo_gl_parallel_target = bool(
            _gl_derivative_numba.targetoptions.get("parallel")
        )
        numba_cache_artifacts = []
        for cache_path in sorted(numba_cache_dir.rglob("*")):
            if not cache_path.is_file() or cache_path.suffix not in {".nbc", ".nbi"}:
                continue
            numba_cache_artifacts.append(
                {
                    "path": cache_path.relative_to(numba_cache_dir).as_posix(),
                    "bytes": cache_path.stat().st_size,
                    "sha256": hashlib.sha256(cache_path.read_bytes()).hexdigest(),
                }
            )
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
            "hafo_engine_available": True,
            "hafo_version": hafo_status.version,
            "hafo_bridge_api": (
                "ExpressionSystemDefinition.from_mapping+"
                "compile_expression_system+simulate"
            ),
            "hafo_bridge_status": hafo_result.status,
            "hafo_bridge_time_shape": list(hafo_times.shape),
            "hafo_bridge_state_shape": list(hafo_states.shape),
            "hafo_bridge_all_finite": hafo_all_finite,
            "hafo_bridge_result_sha256": hafo_digest.hexdigest(),
            "hafo_bridge_use_acceleration": False,
            "hafo_modules_collected_as_source": hafo_modules_collected_as_source,
            "hafo_module_origins": hafo_module_origins,
            "hafo_module_spec_origins": hafo_module_spec_origins,
            "hafo_module_loaders": hafo_module_loaders,
            "hafo_gl_method": hafo_gl_result.method,
            "hafo_gl_numba_persistent_cache_enabled": (
                type(_gl_derivative_numba._cache).__name__ != "NullCache"
            ),
            "hafo_gl_kernel_parallel_target": hafo_gl_parallel_target,
            "hafo_gl_kernel_compiled_signatures": len(
                _gl_derivative_numba.signatures
            ),
            "hafo_gl_result_shape": list(hafo_gl_values.shape),
            "hafo_gl_all_finite": hafo_gl_all_finite,
            "hafo_gl_result_sha256": hafo_gl_digest,
            "frozen_runtime": frozen_runtime,
            "numba_cache_configured": True,
            "numba_cache_outside_bundle": numba_cache_outside_bundle,
            "numba_cache_dir": str(numba_cache_dir),
            "numba_cache_artifact_count": len(numba_cache_artifacts),
            "numba_cache_artifacts": numba_cache_artifacts,
            "numba_threading_layer_requested": requested_threading_layer,
            "numba_threading_layer": active_threading_layer,
            "numba_num_threads": int(numba.get_num_threads()),
            "numba_probe_scope": "backend_only_not_hafo_gl_dispatch",
            "numba_kernel_method": "packaged_parallel_probe_cache_false",
            "numba_kernel_cache_enabled": False,
            "numba_kernel_parallel_target": numba_parallel_target,
            "numba_kernel_compiled_signatures": len(
                packaged_parallel_probe.signatures
            ),
            "numba_result_shape": list(numba_values.shape),
            "numba_all_finite": numba_all_finite,
            "numba_result_sha256": numba_digest,
            "numba_pool_module": expected_pool_module,
            "numba_pool_file": Path(pool_module_file).name,
            "numba_tbbpool_loaded": False,
            "numba_tbbpool_bundled": (
                bool(bundled_tbbpool_files) if frozen_runtime else None
            ),
        }
        if (
            not payload["all_finite"]
            or states.shape[1] != 3
            or hafo_result.status != "ok"
            or not hafo_all_finite
            or hafo_times.shape != (6,)
            or hafo_states.shape != (6, 2)
            or not hafo_modules_collected_as_source
            or not hafo_gl_all_finite
            or hafo_gl_values.shape != (257, 16)
            or not hafo_gl_parallel_target
            or not _gl_derivative_numba.signatures
            or not numba_all_finite
            or numba_values.shape != (257, 16)
            or not numba_parallel_target
            or not packaged_parallel_probe.signatures
        ):
            raise RuntimeError("A packaged native, HAFO, or Numba result is invalid.")
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


def main() -> int:
    # Import the GUI only after ``main_entry`` has selected a writable Numba
    # cache.  This keeps the cache-before-Numba contract independent of the
    # transitive import graph of Qt widgets and future analysis panels.
    from core.qt_binding import configure_pyside6

    configure_pyside6()

    from PySide6.QtWidgets import QApplication
    from core.qt_capabilities import prepare_webengine
    from core.startup_probe import install_startup_probe
    from ui.main_window import MainWindow

    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    logging.getLogger(__name__).info('Starting %s %s', APP_NAME, APP_VERSION)
    configure_qt_platform()
    webengine_status = prepare_webengine()
    if not webengine_status.available:
        logging.getLogger(__name__).info(webengine_status.reason)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    startup_probe = install_startup_probe(window)
    window.show()
    return app.exec()


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


def main_entry() -> None:
    """Installed and frozen GUI entry point."""

    configure_multiprocessing()
    self_test_status = run_packaged_self_test(sys.argv[1:])
    if self_test_status is not None:
        raise SystemExit(self_test_status)
    configure_numba_cache()
    raise SystemExit(main())


if __name__ == '__main__':
    main_entry()
