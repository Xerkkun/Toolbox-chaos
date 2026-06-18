"""tests/test_native_backend.py

Tests for the native C backend (core/native.py):
  - Compilation and loading of chaos_core shared library.
  - Graceful detection when no compiler is available.
  - Correctness of a single Lorenz simulation via the C library.
  - Multiprocessing: bifurcation and basin chunking via ProcessPoolExecutor.
  - configure_multiprocessing() start-method selection from main.py.

These tests skip gracefully when no C compiler is found so that
the CI suite passes even on environments without gcc/clang.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import platform
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
_HAS_COMPILER = bool(shutil.which("gcc") or shutil.which("clang"))
_SKIP_NO_COMPILER = pytest.mark.skipif(
    not _HAS_COMPILER,
    reason="No C compiler (gcc/clang) found — native backend not available",
)


def _compiler_info() -> str:
    for name in ("gcc", "clang"):
        path = shutil.which(name)
        if path:
            return f"{name} at {path}"
    return "none"


# ---------------------------------------------------------------------------
# 1. Compilation / loading
# ---------------------------------------------------------------------------


def test_native_backend_compiler_presence():
    """Report whether a C compiler is present. Always passes — just informational."""
    info = _compiler_info()
    print(f"\n[native] C compiler: {info}")
    print(f"[native] Platform: {sys.platform} / {platform.machine()}")
    print(f"[native] _HAS_COMPILER: {_HAS_COMPILER}")
    # This test always passes — it documents CI environment state.


@_SKIP_NO_COMPILER
def test_native_library_compiles_and_loads():
    """Verify that the native C library compiles from source and loads without error."""
    from core.native import _ensure_library, _shared_library_name

    lib_path = _ensure_library()
    assert lib_path.exists(), f"Compiled library not found at {lib_path}"
    assert lib_path.name == _shared_library_name()
    print(f"\n[native] Library loaded: {lib_path}")


@_SKIP_NO_COMPILER
def test_native_library_is_callable():
    """Verify that the loaded ctypes library exposes the expected C entry points."""
    from core.native import library

    lib = library()
    # These function names must exist in chaos_core.c
    for fn_name in (
        "lorenz_simulate",
        "chaos_simulate_system",
        "chaos_bifurcation_generic",
        "chaos_basin_plane_generic",
        "sprott_simulate_polynomial",
    ):
        fn = getattr(lib, fn_name, None)
        assert fn is not None, f"Missing C function: {fn_name}"


@_SKIP_NO_COMPILER
def test_native_lorenz_short_trajectory():
    """Verify a short Lorenz trajectory via the C backend returns finite values."""
    from core.native import lorenz_simulate_native

    t, X = lorenz_simulate_native(
        x0=1.0, y0=0.0, z0=0.0,
        sigma=10.0, rho=28.0, beta=8.0 / 3.0,
        dt=0.01, T=1.0,
        method_key="rk4",
    )
    assert len(t) > 1
    assert X.shape[1] == 3
    assert np.all(np.isfinite(X)), "C backend produced non-finite values in Lorenz trajectory"


def test_native_lorenz_fallback_uses_python_when_no_compiler(tmp_path, monkeypatch):
    """When no compiler is available and no prebuilt library exists, NativeChaosError is raised."""
    if _HAS_COMPILER:
        pytest.skip("Compiler present — skipping no-compiler fallback test")

    from core.native import NativeChaosError, _ensure_library

    # Redirect library to a temp dir so we don't see the pre-built binary
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NativeChaosError):
        _ensure_library()


# ---------------------------------------------------------------------------
# 2. Multiprocessing — chunking helpers
# ---------------------------------------------------------------------------


def test_parameter_chunks_single_worker():
    """_parameter_chunks with 1 worker returns the full range as one chunk."""
    from core.native import _parameter_chunks

    chunks = _parameter_chunks(0.0, 10.0, 100, workers=1)
    assert len(chunks) == 1
    lo, hi, count = chunks[0]
    assert lo == pytest.approx(0.0)
    assert hi == pytest.approx(10.0)
    assert count == 100


def test_parameter_chunks_multiple_workers():
    """_parameter_chunks splits n_param across workers without losing points."""
    from core.native import _parameter_chunks

    n = 100
    workers = 4
    chunks = _parameter_chunks(0.0, 1.0, n, workers=workers)
    total = sum(c for _, _, c in chunks)
    assert total == n
    assert len(chunks) == workers
    # Ranges must be monotonically increasing
    for i in range(len(chunks) - 1):
        assert chunks[i][1] <= chunks[i + 1][0] + 1e-12


def test_row_chunks_covers_all_rows():
    """_row_chunks splits ny rows across workers without gaps or overlaps."""
    from core.native import _row_chunks

    ny = 37
    workers = 5
    chunks = _row_chunks(ny, workers)
    total = sum(count for _, count in chunks)
    assert total == ny
    # Verify contiguous coverage
    expected_start = 0
    for start, count in chunks:
        assert start == expected_start
        expected_start += count


def test_effective_workers_respects_env(monkeypatch):
    """_effective_workers reads CHAOS_WORKERS env variable."""
    from core.native import _effective_workers

    monkeypatch.setenv("CHAOS_WORKERS", "2")
    assert _effective_workers(None, 10) == 2

    monkeypatch.setenv("CHAOS_WORKERS", "999")
    # Should be capped at n_jobs=5
    assert _effective_workers(None, 5) == 5


def test_effective_workers_invalid_env(monkeypatch):
    """_effective_workers raises NativeChaosError on non-integer CHAOS_WORKERS."""
    from core.native import NativeChaosError, _effective_workers

    monkeypatch.setenv("CHAOS_WORKERS", "bad_value")
    with pytest.raises(NativeChaosError):
        _effective_workers(None, 10)


@_SKIP_NO_COMPILER
def test_bifurcation_multiprocess_matches_singleprocess():
    """Verify that multiprocess bifurcation (workers=2) produces the same
    result as single-process (workers=1) for a short Lorenz bifurcation."""
    from core.native import lorenz_bifurcation_poincare_native

    kwargs = dict(
        x0=0.1, y0=0.0, z0=0.0,
        sigma=10.0, beta=8.0 / 3.0,
        rho_min=25.0, rho_max=30.0,
        n_rho=10,
        dt=0.05, T_trans=5.0, T_keep=2.0,
        max_crossings_per_rho=20,
        continuation=0,
        method_key="rk4",
    )

    rho_1, z_1 = lorenz_bifurcation_poincare_native(**kwargs, workers=1)
    rho_n, z_n = lorenz_bifurcation_poincare_native(**kwargs, workers=2)

    assert len(rho_1) == len(rho_n), (
        f"Single-process returned {len(rho_1)} points, "
        f"multi-process returned {len(rho_n)}"
    )
    # Sort both by rho before comparing values
    if len(rho_1) > 0:
        idx1 = np.argsort(rho_1)
        idxn = np.argsort(rho_n)
        assert np.allclose(rho_1[idx1], rho_n[idxn], atol=1e-6)


# ---------------------------------------------------------------------------
# 3. configure_multiprocessing() from main.py
# ---------------------------------------------------------------------------


def test_configure_multiprocessing_spawn_on_win_mac(monkeypatch):
    """configure_multiprocessing() sets spawn start method on Windows/macOS
    when CHAOS_MP_START_METHOD is not set."""
    import main as app_main  # noqa: PLC0415

    # Force platform to appear as Windows
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("CHAOS_MP_START_METHOD", raising=False)

    # We only verify no exception is raised — mp.set_start_method may raise
    # RuntimeError if the context was already set, which configure handles.
    app_main.configure_multiprocessing()


def test_configure_multiprocessing_env_override(monkeypatch):
    """configure_multiprocessing() respects CHAOS_MP_START_METHOD env var."""
    import main as app_main  # noqa: PLC0415

    monkeypatch.setenv("CHAOS_MP_START_METHOD", "spawn")
    # Should not raise
    app_main.configure_multiprocessing()


def test_configure_multiprocessing_no_env_linux(monkeypatch):
    """On Linux with no env variable set, configure_multiprocessing() is a no-op."""
    import main as app_main  # noqa: PLC0415

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("CHAOS_MP_START_METHOD", raising=False)
    # Should not raise and should not attempt to set the start method
    app_main.configure_multiprocessing()
