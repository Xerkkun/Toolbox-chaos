from __future__ import annotations

import ctypes
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


_METHOD_CODES = {
    'euler': 0,
    'heun': 1,
    'rk4': 2,
}


class NativeChaosError(RuntimeError):
    pass


def _shared_library_name() -> str:
    if sys.platform.startswith('win'):
        return 'chaos_core.dll'
    if sys.platform == 'darwin':
        return 'libchaos_core.dylib'
    return 'libchaos_core.so'


def _compile_command(src: Path, out: Path) -> list[str] | None:
    compiler = shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        return None

    if sys.platform.startswith('win'):
        return [compiler, '-O3', '-shared', '-std=c11', str(src), '-o', str(out), '-lm']
    return [compiler, '-O3', '-shared', '-fPIC', '-std=c11', str(src), '-o', str(out), '-lm']


def _ensure_library() -> Path:
    base_dir = Path(__file__).resolve().parent
    lib_dir = base_dir / 'bin'
    lib_dir.mkdir(parents=True, exist_ok=True)
    lib_path = lib_dir / _shared_library_name()
    src_path = base_dir / 'csrc' / 'chaos_core.c'

    if lib_path.exists():
        return lib_path

    cmd = _compile_command(src_path, lib_path)
    if cmd is None:
        raise NativeChaosError(
            'No se encontró un compilador C compatible (gcc/clang) y la biblioteca nativa no está precompilada.'
        )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise NativeChaosError(
            'No se pudo compilar la biblioteca nativa C.\n'
            f'Comando: {" ".join(cmd)}\n'
            f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}'
        )
    return lib_path


def _load_library() -> ctypes.CDLL:
    lib_path = _ensure_library()
    lib = ctypes.CDLL(str(lib_path))

    lib.lorenz_simulate.argtypes = [
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
    ]
    lib.lorenz_simulate.restype = ctypes.c_int

    lib.lorenz_bifurcation_poincare.argtypes = [
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
    lib.lorenz_bifurcation_poincare.restype = ctypes.c_int

    lib.lorenz_basin_plane.argtypes = [
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int, ctypes.c_int,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.lorenz_basin_plane.restype = ctypes.c_int
    return lib


_LIB = None


def library() -> ctypes.CDLL:
    global _LIB
    if _LIB is None:
        _LIB = _load_library()
    return _LIB


def get_method_code(method_key: str) -> int:
    try:
        return _METHOD_CODES[method_key]
    except KeyError as exc:
        raise NativeChaosError(f'Método nativo no implementado: {method_key}') from exc


def lorenz_simulate_native(
    x0: float,
    y0: float,
    z0: float,
    sigma: float,
    rho: float,
    beta: float,
    dt: float,
    T: float,
    method_key: str,
):
    n = int(T / dt) + 1
    if n < 2:
        n = 2

    t = np.empty(n, dtype=np.float64)
    X = np.empty((n, 3), dtype=np.float64)
    method_code = get_method_code(method_key)

    rc = library().lorenz_simulate(
        float(x0), float(y0), float(z0),
        float(sigma), float(rho), float(beta),
        float(dt), float(T),
        method_code,
        t.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        X.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(n),
    )
    if rc != 0:
        raise NativeChaosError('Falló la simulación nativa en C.')
    return t, X


def lorenz_bifurcation_poincare_native(
    x0: float,
    y0: float,
    z0: float,
    sigma: float,
    beta: float,
    rho_min: float,
    rho_max: float,
    n_rho: int,
    dt: float,
    T_trans: float,
    T_keep: float,
    max_crossings_per_rho: int,
    continuation: int,
    method_key: str,
):
    max_size = int(n_rho) * int(max_crossings_per_rho)
    out_rho = np.empty(max_size, dtype=np.float64)
    out_z = np.empty(max_size, dtype=np.float64)
    out_count = ctypes.c_int(0)
    method_code = get_method_code(method_key)

    rc = library().lorenz_bifurcation_poincare(
        float(x0), float(y0), float(z0),
        float(sigma), float(beta),
        float(rho_min), float(rho_max),
        int(n_rho),
        float(dt), float(T_trans), float(T_keep),
        int(max_crossings_per_rho),
        int(continuation),
        method_code,
        out_rho.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        out_z.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.byref(out_count),
    )
    if rc != 0:
        raise NativeChaosError('Falló el cálculo nativo del diagrama de bifurcación.')

    count = int(out_count.value)
    return out_rho[:count].copy(), out_z[:count].copy()


def lorenz_basin_plane_native(
    sigma: float,
    rho: float,
    beta: float,
    z0_fixed: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    nx: int,
    ny: int,
    dt: float,
    T_total: float,
    hit_radius: float,
    esc_radius: float,
    method_key: str,
):
    basin = np.empty((ny, nx), dtype=np.uint8)
    method_code = get_method_code(method_key)

    rc = library().lorenz_basin_plane(
        float(sigma), float(rho), float(beta),
        float(z0_fixed),
        float(x_min), float(x_max),
        float(y_min), float(y_max),
        int(nx), int(ny),
        float(dt), float(T_total),
        float(hit_radius), float(esc_radius),
        method_code,
        basin.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    if rc != 0:
        raise NativeChaosError('Falló el cálculo nativo de la cuenca de atracción.')
    return basin
