from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np


_METHOD_CODES = {
    'euler': 0,
    'heun': 1,
    'rk4': 2,
}

_SYSTEM_CODES = {
    'lorenz': 0,
    'rossler': 1,
    'chua': 2,
    'chen': 3,
    'lu': 4,
    'henon': 5,
    'logistic': 6,
    'ikeda': 7,
    'mackey_glass': 8,
    'duffing_ueda': 9,
    'rabinovich_fabrikant': 10,
    'rikitake': 11,
    'sprott_a': 12,
    'thomas': 13,
    'hindmarsh_rose': 14,
    'lorenz96': 15,
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

    if lib_path.exists() and lib_path.stat().st_mtime >= src_path.stat().st_mtime:
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

    lib.chaos_simulate_system.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
    ]
    lib.chaos_simulate_system.restype = ctypes.c_int

    lib.chaos_bifurcation_generic.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
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
    lib.chaos_bifurcation_generic.restype = ctypes.c_int

    lib.chaos_basin_plane_generic.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int,
        ctypes.c_double, ctypes.c_double,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.chaos_basin_plane_generic.restype = ctypes.c_int
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
    workers: int | None = None,
):
    workers = _effective_workers(workers, int(n_rho))
    if workers > 1 and not int(continuation):
        tasks = [
            (
                x0, y0, z0, sigma, beta, lo, hi, count, dt, T_trans, T_keep,
                max_crossings_per_rho, 0, method_key,
            )
            for lo, hi, count in _parameter_chunks(float(rho_min), float(rho_max), int(n_rho), workers)
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(_lorenz_bifurcation_chunk, tasks))
        if not parts:
            return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
        return (
            np.concatenate([part[0] for part in parts]),
            np.concatenate([part[1] for part in parts]),
        )

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


def get_system_code(system_key: str) -> int:
    try:
        return _SYSTEM_CODES[system_key]
    except KeyError as exc:
        raise NativeChaosError(f'Sistema nativo no implementado: {system_key}') from exc


def _params_array(params) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(params, dtype=np.float64))


def simulate_system_native(system_key: str, initial, params, dt: float, T: float, method_key: str = 'rk4'):
    n = int(T / dt) + 1
    if n < 2:
        n = 2

    t = np.empty(n, dtype=np.float64)
    X = np.empty((n, 3), dtype=np.float64)
    p = _params_array(params)

    rc = library().chaos_simulate_system(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        float(initial[0]), float(initial[1]), float(initial[2]),
        float(dt), float(T),
        get_method_code(method_key),
        t.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        X.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(n),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo la simulacion nativa en C para {system_key}.')
    return t, X


def _effective_workers(workers: int | None, jobs: int) -> int:
    if workers is None:
        workers = max(1, (os.cpu_count() or 1) - 1)
    return min(max(1, int(workers)), max(1, int(jobs)))


def _parameter_chunks(param_min: float, param_max: float, n_param: int, workers: int):
    if n_param <= 1:
        return [(param_min, param_max, n_param)]
    denom = n_param - 1
    chunks = []
    base = n_param // workers
    extra = n_param % workers
    start = 0
    for idx in range(workers):
        count = base + (1 if idx < extra else 0)
        if count <= 0:
            continue
        end = start + count - 1
        lo = param_min + (param_max - param_min) * (start / denom)
        hi = param_min + (param_max - param_min) * (end / denom)
        chunks.append((lo, hi, count))
        start = end + 1
    return chunks


def _bifurcation_chunk(args):
    (
        system_key, initial, params, param_idx, param_min, param_max, n_param,
        dt, T_trans, T_keep, max_points, continuation, method_key,
    ) = args
    return bifurcation_generic_native(
        system_key, initial, params, param_idx, param_min, param_max, n_param,
        dt, T_trans, T_keep, max_points, continuation=continuation,
        method_key=method_key, workers=1,
    )


def _lorenz_bifurcation_chunk(args):
    (
        x0, y0, z0, sigma, beta, rho_min, rho_max, n_rho, dt, T_trans, T_keep,
        max_crossings_per_rho, continuation, method_key,
    ) = args
    return lorenz_bifurcation_poincare_native(
        x0, y0, z0, sigma, beta, rho_min, rho_max, n_rho, dt, T_trans, T_keep,
        max_crossings_per_rho, continuation, method_key, workers=1,
    )


def bifurcation_generic_native(
    system_key: str,
    initial,
    params,
    param_idx: int,
    param_min: float,
    param_max: float,
    n_param: int,
    dt: float,
    T_trans: float,
    T_keep: float,
    max_points: int,
    continuation: bool = False,
    method_key: str = 'rk4',
    workers: int | None = None,
):
    n_param = int(n_param)
    max_points = int(max_points)
    if n_param < 1 or max_points < 1:
        raise NativeChaosError('Parametros nativos invalidos para bifurcacion.')

    workers = _effective_workers(workers, n_param)
    if workers > 1 and not continuation:
        tasks = [
            (
                system_key, tuple(initial), tuple(params), int(param_idx), lo, hi, count,
                float(dt), float(T_trans), float(T_keep), max_points, False, method_key,
            )
            for lo, hi, count in _parameter_chunks(param_min, param_max, n_param, workers)
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(_bifurcation_chunk, tasks))
        if not parts:
            return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
        return (
            np.concatenate([part[0] for part in parts]),
            np.concatenate([part[1] for part in parts]),
        )

    max_size = n_param * max_points
    out_param = np.empty(max_size, dtype=np.float64)
    out_value = np.empty(max_size, dtype=np.float64)
    out_count = ctypes.c_int(0)
    p = _params_array(params)

    rc = library().chaos_bifurcation_generic(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        int(param_idx),
        float(initial[0]), float(initial[1]), float(initial[2]),
        float(param_min), float(param_max),
        n_param,
        float(dt), float(T_trans), float(T_keep),
        max_points,
        1 if continuation else 0,
        get_method_code(method_key),
        out_param.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        out_value.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.byref(out_count),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo el calculo nativo de bifurcacion para {system_key}.')

    count = int(out_count.value)
    return out_param[:count].copy(), out_value[:count].copy()


def _row_chunks(ny: int, workers: int):
    base = ny // workers
    extra = ny % workers
    chunks = []
    start = 0
    for idx in range(workers):
        count = base + (1 if idx < extra else 0)
        if count <= 0:
            continue
        chunks.append((start, count))
        start += count
    return chunks


def _basin_chunk(args):
    (
        system_key, params, eq_points_flat, z0_fixed, x_min, x_max, y_min, y_max,
        nx, ny, row_start, row_count, dt, T_total, method_key,
    ) = args
    eq_points = np.asarray(eq_points_flat, dtype=np.float64).reshape(-1, 3)
    return row_start, basin_plane_generic_native(
        system_key, params, eq_points, z0_fixed, x_min, x_max, y_min, y_max,
        nx, ny, dt, T_total, method_key=method_key,
        row_start=row_start, row_count=row_count, workers=1,
    )


def basin_plane_generic_native(
    system_key: str,
    params,
    eq_points,
    z0_fixed: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    nx: int,
    ny: int,
    dt: float,
    T_total: float,
    method_key: str = 'rk4',
    row_start: int = 0,
    row_count: int | None = None,
    workers: int | None = None,
):
    nx = int(nx)
    ny = int(ny)
    row_start = int(row_start)
    row_count = ny - row_start if row_count is None else int(row_count)
    if nx < 2 or ny < 2 or row_count < 1:
        raise NativeChaosError('Parametros nativos invalidos para cuenca.')

    workers = _effective_workers(workers, row_count)
    if workers > 1:
        basin = np.empty((ny, nx), dtype=np.uint8)
        eq_flat = tuple(np.asarray(eq_points, dtype=np.float64).reshape(-1))
        tasks = [
            (
                system_key, tuple(params), eq_flat,
                float(z0_fixed), float(x_min), float(x_max), float(y_min), float(y_max),
                nx, ny, start, count, float(dt), float(T_total), method_key,
            )
            for start, count in _row_chunks(ny, workers)
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for start, part in pool.map(_basin_chunk, tasks):
                basin[start:start + part.shape[0], :] = part
        return basin

    out = np.empty((row_count, nx), dtype=np.uint8)
    p = _params_array(params)
    eq = np.ascontiguousarray(np.asarray(eq_points, dtype=np.float64).reshape(-1, 3))

    rc = library().chaos_basin_plane_generic(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        eq.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(eq.shape[0]),
        float(z0_fixed),
        float(x_min), float(x_max),
        float(y_min), float(y_max),
        nx, ny,
        row_start, row_count,
        float(dt), float(T_total),
        get_method_code(method_key),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo el calculo nativo de cuenca para {system_key}.')
    return out
