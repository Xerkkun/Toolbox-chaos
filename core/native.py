from __future__ import annotations

import ctypes
from contextlib import contextmanager
import hashlib
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from .paths import user_data_dir
from .system_ids import NATIVE_SYSTEM_CODES
from .time_policy import (
    C_INT_MAX_STEPS,
    MAX_FIXED_STEP_OUTPUT_BYTES,
    checked_fixed_step_samples,
    checked_integer_value,
    fixed_step_count,
)


_METHOD_CODES = {
    'euler': 0,
    'heun': 1,
    'rk4': 2,
}

_EXPECTED_NATIVE_ABI_VERSION = 2

# MinGW otherwise chooses a non-deterministic preferred image base for each DLL.
# The PE header still carries DYNAMIC_BASE/HIGH_ENTROPY_VA, so Windows ASLR stays
# enabled while identical sources and toolchains produce identical bytes.
_WINDOWS_REPRODUCIBLE_BUILD_FLAGS = (
    '-frandom-seed=chaos-core-v2',
    '-Wl,--no-insert-timestamp,--image-base,0x180000000',
)

_REQUIRED_NATIVE_EXPORTS = (
    'chaos_core_abi_version',
    'lorenz_simulate',
    'lorenz_bifurcation_poincare',
    'lorenz_basin_plane',
    'chaos_simulate_system',
    'chaos_bifurcation_generic',
    'chaos_basin_plane_generic',
    'sprott_simulate_polynomial',
)

class NativeChaosError(RuntimeError):
    pass


def _is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


def _shared_library_name() -> str:
    if sys.platform.startswith('win'):
        return 'chaos_core.dll'
    if sys.platform == 'darwin':
        return 'libchaos_core.dylib'
    return 'libchaos_core.so'


def _compile_command(src: Path, out: Path, compiler: str | None = None) -> list[str] | None:
    compiler = compiler or shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        return None

    if sys.platform.startswith('win'):
        return [
            compiler,
            '-O3',
            '-shared',
            '-std=c11',
            *_WINDOWS_REPRODUCIBLE_BUILD_FLAGS,
            str(src),
            '-o',
            str(out),
            '-lm',
        ]
    return [compiler, '-O3', '-shared', '-fPIC', '-std=c11', str(src), '-o', str(out), '-lm']


def _compiler_identity(compiler: str) -> str:
    resolved = str(Path(compiler).resolve())
    try:
        result = subprocess.run(
            [compiler, '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return resolved
    first_line = (result.stdout or result.stderr or '').splitlines()
    return f'{resolved}\n{first_line[0] if first_line else "unknown-version"}'


def _native_cache_key(src_path: Path, compiler: str) -> str:
    fingerprint = hashlib.sha256()
    fingerprint.update(b'chaos-toolbox-native-cache-v2\0')
    ancillary_sources = sorted(
        [*src_path.parent.glob('*.h'), *src_path.parent.glob('*.def')]
    )
    for source in [src_path, *ancillary_sources]:
        fingerprint.update(source.name.encode('utf-8'))
        fingerprint.update(b'\0')
        fingerprint.update(source.read_bytes())
        fingerprint.update(b'\0')
    command = _compile_command(Path('<source>'), Path('<output>'), compiler)
    if command is None:
        raise NativeChaosError('No se pudo construir el comando del compilador C.')
    signature = {
        'command': command,
        'compiler': _compiler_identity(compiler),
        'platform': sys.platform,
        'platform_release': platform.release(),
        'machine': platform.machine(),
        'byteorder': sys.byteorder,
        'pointer_bits': ctypes.sizeof(ctypes.c_void_p) * 8,
        'sizeof_c_int': ctypes.sizeof(ctypes.c_int),
        'sizeof_c_size_t': ctypes.sizeof(ctypes.c_size_t),
        'sizeof_c_double': ctypes.sizeof(ctypes.c_double),
        'expected_native_abi': _EXPECTED_NATIVE_ABI_VERSION,
        'python_abi': getattr(sys.implementation, 'cache_tag', ''),
    }
    for key, value in sorted(signature.items()):
        fingerprint.update(f'{key}={value}\n'.encode('utf-8'))
    return fingerprint.hexdigest()[:24]


def _cache_digest_path(library_path: Path) -> Path:
    return library_path.with_name(f'{library_path.name}.sha256')


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _cache_library_valid(library_path: Path) -> bool:
    digest_path = _cache_digest_path(library_path)
    try:
        if not library_path.is_file() or library_path.stat().st_size <= 0:
            return False
        expected = digest_path.read_text(encoding='ascii').strip().lower()
        return len(expected) == 64 and expected == _file_sha256(library_path)
    except (OSError, UnicodeError):
        return False


def _probe_cached_library(library_path: Path) -> bool:
    """Probe ABI and exports in a child so a rejected DLL is never locked here."""

    probe = (
        "import ctypes,sys;"
        "kernel32=getattr(getattr(ctypes,'windll',None),'kernel32',None);"
        "kernel32 is None or kernel32.SetErrorMode(0x0001|0x8000);"
        "lib=ctypes.CDLL(sys.argv[1]);"
        f"required={_REQUIRED_NATIVE_EXPORTS!r};"
        "[getattr(lib,name) for name in required];"
        "f=lib.chaos_core_abi_version;f.argtypes=[];f.restype=ctypes.c_int;"
        "raise SystemExit(0 if f()==int(sys.argv[2]) else 3)"
    )
    try:
        completed = subprocess.run(
            [
                sys.executable,
                '-I',
                '-B',
                '-c',
                probe,
                str(library_path),
                str(_EXPECTED_NATIVE_ABI_VERSION),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _cache_library_usable(library_path: Path) -> bool:
    return _cache_library_valid(library_path) and _probe_cached_library(library_path)


def validate_precompiled_library(library_path: str | os.PathLike[str]) -> Path:
    """Validate a build-time native library in an isolated Python child.

    Frozen executables must use ``_load_library`` instead: their ``sys.executable``
    is the application binary and cannot be used as a Python probe process.
    """

    requested = Path(library_path)
    is_junction = getattr(requested, 'is_junction', lambda: False)
    if requested.is_symlink() or bool(is_junction()):
        raise NativeChaosError(
            f'La biblioteca nativa precompilada no puede ser un enlace: {requested}.'
        )
    try:
        candidate = requested.resolve(strict=True)
    except OSError as exc:
        raise NativeChaosError(
            f'No se encontro la biblioteca nativa precompilada: {requested}.'
        ) from exc
    expected_name = _shared_library_name()
    if candidate.name.casefold() != expected_name.casefold():
        raise NativeChaosError(
            f'Nombre de biblioteca nativa incompatible: se esperaba {expected_name} '
            f'y se encontro {candidate.name}.'
        )
    try:
        nonempty_file = candidate.is_file() and candidate.stat().st_size > 0
    except OSError as exc:
        raise NativeChaosError(
            f'No se pudo inspeccionar la biblioteca nativa precompilada: {candidate}.'
        ) from exc
    if not nonempty_file:
        raise NativeChaosError(
            f'La biblioteca nativa precompilada esta vacia o no es un archivo: {candidate}.'
        )
    if not _probe_cached_library(candidate):
        raise NativeChaosError(
            'La biblioteca nativa precompilada no supera la comprobacion aislada '
            f'de ABI {_EXPECTED_NATIVE_ABI_VERSION} y simbolos requeridos: {candidate}.'
        )
    return candidate


@contextmanager
def _native_build_lock(
    lock_path: Path,
    library_path: Path,
    *,
    timeout_seconds: float = 30.0,
    stale_seconds: float = 300.0,
    ready_check=None,
):
    ready = ready_check or _cache_library_valid
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        if ready(library_path):
            yield False
            return
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            try:
                stale = time.time() - lock_path.stat().st_mtime > stale_seconds
            except FileNotFoundError:
                continue
            if stale:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise NativeChaosError(
                    f'Tiempo agotado esperando la compilacion nativa: {lock_path}'
                )
            time.sleep(0.05)
    try:
        os.write(descriptor, f'{os.getpid()}\n'.encode('ascii'))
        os.close(descriptor)
        descriptor = None
        yield True
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _ensure_library() -> Path:
    base_dir = Path(__file__).resolve().parent
    bundled_path = base_dir / 'bin' / _shared_library_name()
    src_path = base_dir / 'csrc' / 'chaos_core.c'

    if _is_frozen():
        if bundled_path.is_file() and bundled_path.stat().st_size > 0:
            return bundled_path
        raise NativeChaosError(
            'La biblioteca nativa de Chaos Toolbox no esta instalada: '
            f'no se encontro {bundled_path}. La instalacion esta incompleta; '
            'reinstale la aplicacion o regenere el paquete de distribucion.'
        )

    if not src_path.is_file() and (bundled_path.exists() or bundled_path.is_symlink()):
        return validate_precompiled_library(bundled_path)
    if not src_path.is_file():
        raise NativeChaosError(
            f'No se encontro el fuente nativo necesario: {src_path}.'
        )

    compiler = shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        raise NativeChaosError(
            'No se encontró un compilador C compatible (gcc/clang) y la biblioteca nativa no está precompilada.'
        )

    cache_dir = user_data_dir() / 'native' / _native_cache_key(src_path, compiler)
    cache_dir.mkdir(parents=True, exist_ok=True)
    lib_path = cache_dir / _shared_library_name()
    if _cache_library_usable(lib_path):
        return lib_path
    lock_path = cache_dir / f'.{lib_path.name}.lock'
    with _native_build_lock(
        lock_path, lib_path, ready_check=_cache_library_usable
    ) as owns_lock:
        if not owns_lock or _cache_library_usable(lib_path):
            return lib_path
        lib_path.unlink(missing_ok=True)
        _cache_digest_path(lib_path).unlink(missing_ok=True)
        suffix = ''.join(lib_path.suffixes) or '.bin'
        handle, temporary_name = tempfile.mkstemp(
            prefix=f'.{lib_path.stem}-', suffix=suffix, dir=cache_dir
        )
        os.close(handle)
        temporary_path = Path(temporary_name)
        temporary_path.unlink(missing_ok=True)
        try:
            cmd = _compile_command(src_path, temporary_path, compiler)
            if cmd is None:  # defensive for callers that monkeypatch the helper
                raise NativeChaosError('No se pudo construir el comando del compilador C.')
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise NativeChaosError(
                    'No se pudo compilar la biblioteca nativa C.\n'
                    f'Comando: {" ".join(cmd)}\n'
                    f'STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}'
                )
            if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
                raise NativeChaosError('El compilador C no produjo una biblioteca valida.')
            binary_digest = _file_sha256(temporary_path)
            os.replace(temporary_path, lib_path)
            digest_path = _cache_digest_path(lib_path)
            digest_handle, digest_name = tempfile.mkstemp(
                prefix=f'.{digest_path.name}-', suffix='.tmp', dir=cache_dir
            )
            try:
                with os.fdopen(digest_handle, 'w', encoding='ascii', newline='\n') as handle:
                    handle.write(f'{binary_digest}\n')
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(digest_name, digest_path)
            finally:
                Path(digest_name).unlink(missing_ok=True)
        finally:
            temporary_path.unlink(missing_ok=True)
        if not _cache_library_usable(lib_path):
            lib_path.unlink(missing_ok=True)
            _cache_digest_path(lib_path).unlink(missing_ok=True)
            raise NativeChaosError(
                'La biblioteca nativa compilada no superó la comprobación de ABI y símbolos.'
            )
    return lib_path


def _load_library() -> ctypes.CDLL:
    lib_path = _ensure_library()
    try:
        lib = ctypes.CDLL(str(lib_path))
    except OSError as exc:
        raise NativeChaosError(
            f'No se pudo cargar la biblioteca nativa {lib_path}: {exc}'
        ) from exc
    try:
        abi_version = lib.chaos_core_abi_version
    except AttributeError as exc:
        raise NativeChaosError(
            f'La biblioteca nativa {lib_path} no declara su version ABI.'
        ) from exc
    abi_version.argtypes = []
    abi_version.restype = ctypes.c_int
    actual_abi = int(abi_version())
    if actual_abi != _EXPECTED_NATIVE_ABI_VERSION:
        raise NativeChaosError(
            'ABI nativa incompatible: '
            f'se esperaba {_EXPECTED_NATIVE_ABI_VERSION} y se encontro {actual_abi} '
            f'en {lib_path}.'
        )

    try:
        for export_name in _REQUIRED_NATIVE_EXPORTS[1:]:
            getattr(lib, export_name)

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

        lib.sprott_simulate_polynomial.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int),
    ]
        lib.sprott_simulate_polynomial.restype = ctypes.c_int
    except AttributeError as exc:
        raise NativeChaosError(
            f'La biblioteca nativa {lib_path} no contiene todas las funciones requeridas: {exc}'
        ) from exc
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
    steps = fixed_step_count(T, dt)
    n = checked_fixed_step_samples(steps, 3, name='trayectoria Lorenz nativa')
    state = _state3((x0, y0, z0), name='estado inicial Lorenz')
    parameters = _params_array((sigma, rho, beta))

    t = np.empty(n, dtype=np.float64)
    X = np.empty((n, 3), dtype=np.float64)
    method_code = get_method_code(method_key)

    rc = library().lorenz_simulate(
        float(state[0]), float(state[1]), float(state[2]),
        float(parameters[0]), float(parameters[1]), float(parameters[2]),
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
    fixed_step_count(T_trans, dt, name='T_trans', allow_zero=True)
    fixed_step_count(T_keep, dt, name='T_keep')
    state = _state3((x0, y0, z0), name='estado inicial Lorenz')
    fixed = _params_array((sigma, beta, rho_min, rho_max))
    n_rho = _checked_int(n_rho, 'n_rho', minimum=1, maximum=C_INT_MAX_STEPS)
    max_crossings_per_rho = _checked_int(
        max_crossings_per_rho,
        'max_crossings_per_rho',
        minimum=1,
        maximum=C_INT_MAX_STEPS,
    )
    continuation = _binary_flag(continuation, 'continuation')
    _checked_output_capacity(
        n_rho,
        max_crossings_per_rho,
        arrays=2,
        name='bifurcación Lorenz',
    )
    workers = _effective_workers(workers, n_rho)
    if workers > 1 and not continuation:
        # Load/build once before spawning to avoid concurrent DLL replacement.
        library()
        tasks = [
            (
                state[0], state[1], state[2], fixed[0], fixed[1], lo, hi, count, dt, T_trans, T_keep,
                max_crossings_per_rho, 0, method_key,
            )
            for lo, hi, count in _parameter_chunks(float(fixed[2]), float(fixed[3]), n_rho, workers)
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(_lorenz_bifurcation_chunk, tasks))
        if not parts:
            return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
        return (
            np.concatenate([part[0] for part in parts]),
            np.concatenate([part[1] for part in parts]),
        )

    max_size = n_rho * max_crossings_per_rho
    out_rho = np.empty(max_size, dtype=np.float64)
    out_z = np.empty(max_size, dtype=np.float64)
    out_count = ctypes.c_int(0)
    method_code = get_method_code(method_key)

    rc = library().lorenz_bifurcation_poincare(
        float(state[0]), float(state[1]), float(state[2]),
        float(fixed[0]), float(fixed[1]),
        float(fixed[2]), float(fixed[3]),
        n_rho,
        float(dt), float(T_trans), float(T_keep),
        max_crossings_per_rho,
        continuation,
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
    fixed_step_count(T_total, dt, name='T_total')
    parameters = _params_array((sigma, rho, beta))
    bounds = _params_array((z0_fixed, x_min, x_max, y_min, y_max, hit_radius, esc_radius))
    nx = _checked_int(nx, 'nx', minimum=2, maximum=C_INT_MAX_STEPS)
    ny = _checked_int(ny, 'ny', minimum=2, maximum=C_INT_MAX_STEPS)
    _checked_output_capacity(ny, nx, itemsize=1, name='cuenca Lorenz')
    if not bounds[1] < bounds[2] or not bounds[3] < bounds[4]:
        raise NativeChaosError('Los límites de la cuenca Lorenz deben ser crecientes.')
    if bounds[5] <= 0.0 or bounds[6] <= 0.0:
        raise NativeChaosError('Los radios de la cuenca Lorenz deben ser positivos.')
    basin = np.empty((ny, nx), dtype=np.uint8)
    method_code = get_method_code(method_key)

    rc = library().lorenz_basin_plane(
        float(parameters[0]), float(parameters[1]), float(parameters[2]),
        float(bounds[0]),
        float(bounds[1]), float(bounds[2]),
        float(bounds[3]), float(bounds[4]),
        nx, ny,
        float(dt), float(T_total),
        float(bounds[5]), float(bounds[6]),
        method_code,
        basin.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    if rc != 0:
        raise NativeChaosError('Falló el cálculo nativo de la cuenca de atracción.')
    return basin


def get_system_code(system_key: str) -> int:
    try:
        return NATIVE_SYSTEM_CODES[system_key]
    except KeyError as exc:
        raise NativeChaosError(f'Sistema nativo no implementado: {system_key}') from exc


def _checked_int(
    value,
    name: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    try:
        return checked_integer_value(
            value, name=name, minimum=minimum, maximum=maximum
        )
    except ValueError as exc:
        raise NativeChaosError(str(exc)) from exc


def _binary_flag(value, name: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        return int(value)
    return _checked_int(value, name, minimum=0, maximum=1)


def _finite_scalar(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeChaosError(f'{name} debe ser un número finito.') from exc
    if not np.isfinite(result):
        raise NativeChaosError(f'{name} debe ser un número finito.')
    return result


def _convex_interpolate(left: float, right: float, numerator: int, denominator: int) -> float:
    """Return a finite convex grid point without forming ``right - left`` blindly."""

    if denominator <= 0 or numerator <= 0:
        return float(left)
    if numerator >= denominator:
        return float(right)
    alpha = numerator / denominator
    if np.signbit(left) == np.signbit(right):
        value = left + (right - left) * alpha
    else:
        value = (1.0 - alpha) * left + alpha * right
    if not np.isfinite(value):
        raise NativeChaosError('La interpolación del rango produjo un valor no finito.')
    return float(value)


def _delay_grid_ceiling(tau: float, dt: float, *, name: str = 'tau') -> int:
    tau = _finite_scalar(tau, name)
    dt = _finite_scalar(dt, 'dt')
    if dt <= 0.0 or tau < dt:
        raise NativeChaosError(f'{name} debe ser mayor o igual que dt para el integrador explícito.')
    ratio = tau / dt
    if not np.isfinite(ratio) or ratio > C_INT_MAX_STEPS - 2:
        raise NativeChaosError(f'{name}/dt excede la capacidad entera del backend C.')
    return int(math.ceil(ratio))


def _checked_output_capacity(
    *dimensions: int,
    itemsize: int = 8,
    arrays: int = 1,
    name: str,
) -> int:
    count = 1
    for dimension in dimensions:
        dim = _checked_int(dimension, f'dimensión de {name}', minimum=0)
        if dim and count > C_INT_MAX_STEPS // dim:
            raise NativeChaosError(f'{name} excede la capacidad entera del backend C.')
        count *= dim
    required = count * itemsize * arrays
    if required > MAX_FIXED_STEP_OUTPUT_BYTES:
        raise NativeChaosError(
            f'{name} requiere {required} bytes, por encima del límite de '
            f'{MAX_FIXED_STEP_OUTPUT_BYTES} bytes.'
        )
    return count


def _params_array(params) -> np.ndarray:
    try:
        array = np.asarray(params, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeChaosError('params debe ser un vector numérico finito.') from exc
    if array.ndim != 1 or array.size > C_INT_MAX_STEPS:
        raise NativeChaosError('params debe ser un vector unidimensional de tamaño válido.')
    if not np.all(np.isfinite(array)):
        raise NativeChaosError('params debe contener sólo valores finitos.')
    return np.ascontiguousarray(array)


def _state3(initial, *, name: str = 'initial') -> np.ndarray:
    try:
        state = np.asarray(initial, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeChaosError(f'{name} debe ser un vector numérico de longitud 3.') from exc
    if state.shape != (3,) or not np.all(np.isfinite(state)):
        raise NativeChaosError(f'{name} debe tener forma (3,) y valores finitos.')
    return np.ascontiguousarray(state)


def simulate_system_native(system_key: str, initial, params, dt: float, T: float, method_key: str = 'rk4'):
    get_system_code(system_key)
    method_code = get_method_code(method_key)
    p = _params_array(params)
    state = _state3(initial)
    steps = fixed_step_count(T, dt)
    n = checked_fixed_step_samples(steps, 3, name=f'trayectoria nativa {system_key}')
    if system_key == 'mackey_glass':
        if p.size < 4:
            raise NativeChaosError('Mackey-Glass requiere beta, gamma, n y tau.')
        if p[2] <= 0.0:
            raise NativeChaosError('El exponente n de Mackey-Glass debe ser positivo.')
        tau = p[3] if p.size > 3 else 17.0
        delay_steps = _delay_grid_ceiling(float(tau), float(dt))
        _checked_output_capacity(
            n + delay_steps + 3, name='historia Mackey-Glass'
        )
    elif system_key == 'lorenz96':
        dimension = p[1] if p.size > 1 else 8.0
        _checked_int(dimension, 'J', minimum=4, maximum=256)

    t = np.empty(n, dtype=np.float64)
    X = np.empty((n, 3), dtype=np.float64)

    rc = library().chaos_simulate_system(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        float(state[0]), float(state[1]), float(state[2]),
        float(dt), float(T),
        method_code,
        t.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        X.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(n),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo la simulacion nativa en C para {system_key}.')
    return t, X


def _effective_workers(workers: int | None, jobs: int) -> int:
    jobs = _checked_int(jobs, 'jobs', minimum=1, maximum=C_INT_MAX_STEPS)
    if workers is None:
        configured = os.environ.get('CHAOS_WORKERS')
        if configured:
            try:
                workers = int(configured)
            except ValueError as exc:
                raise NativeChaosError('CHAOS_WORKERS debe ser un entero positivo.') from exc
        elif getattr(sys, 'frozen', False):
            # Disable multiprocessing by default when frozen to prevent recursive process bootstrapping crashes
            workers = 1
        else:
            workers = max(1, (os.cpu_count() or 1) - 1)
    workers = _checked_int(workers, 'workers', minimum=1, maximum=C_INT_MAX_STEPS)
    return min(workers, jobs)



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
        lo = _convex_interpolate(param_min, param_max, start, denom)
        hi = _convex_interpolate(param_min, param_max, end, denom)
        chunks.append((lo, hi, count))
        start = end + 1
    return chunks


def _bifurcation_chunk(args):
    (
        system_key, initial, params, param_idx, param_min, param_max, n_param,
        dt, T_trans, T_keep, max_points, continuation, method_key, observed_var_idx,
    ) = args
    return bifurcation_generic_native(
        system_key, initial, params, param_idx, param_min, param_max, n_param,
        dt, T_trans, T_keep, max_points, continuation=continuation,
        method_key=method_key, observed_var_idx=observed_var_idx, workers=1,
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
    observed_var_idx: int = 2,
    workers: int | None = None,
):
    steps_trans = fixed_step_count(T_trans, dt, name='T_trans', allow_zero=True)
    steps_keep = fixed_step_count(T_keep, dt, name='T_keep')
    if steps_trans > C_INT_MAX_STEPS - steps_keep:
        raise NativeChaosError('T_trans/dt + T_keep/dt excede la capacidad entera.')
    get_system_code(system_key)
    state = _state3(initial)
    p = _params_array(params)
    bounds = _params_array((param_min, param_max))
    if bounds[0] > bounds[1]:
        raise NativeChaosError('param_min no puede ser mayor que param_max.')
    n_param = _checked_int(n_param, 'n_param', minimum=1, maximum=C_INT_MAX_STEPS)
    max_points = _checked_int(max_points, 'max_points', minimum=1, maximum=C_INT_MAX_STEPS)
    param_idx = _checked_int(param_idx, 'param_idx', minimum=0)
    if param_idx >= p.size:
        raise NativeChaosError('param_idx debe referir a un elemento de params.')
    observed_var_idx = _checked_int(
        observed_var_idx, 'observed_var_idx', minimum=0, maximum=2
    )
    continuation = _binary_flag(continuation, 'continuation')
    _checked_output_capacity(
        n_param, max_points, arrays=2, name=f'bifurcación {system_key}'
    )

    if system_key == 'mackey_glass':
        if p.size < 4:
            raise NativeChaosError('Mackey-Glass requiere beta, gamma, n y tau.')
        exponent_values = (bounds if param_idx == 2 else np.asarray((p[2], p[2])))
        if np.min(exponent_values) <= 0.0:
            raise NativeChaosError('El exponente n de Mackey-Glass debe ser positivo.')
        tau_values = bounds if param_idx == 3 else np.asarray((p[3], p[3]))
        delay_steps = _delay_grid_ceiling(float(np.max(tau_values)), float(dt))
        _delay_grid_ceiling(float(np.min(tau_values)), float(dt))
        _checked_output_capacity(
            2 * (delay_steps + 3) + steps_trans + steps_keep + 2,
            name='historia de bifurcación Mackey-Glass',
        )
    elif system_key == 'lorenz96':
        if p.size < 2:
            raise NativeChaosError('Lorenz-96 requiere F y J.')
        if param_idx == 1 and (n_param != 1 or bounds[0] != bounds[1]):
            raise NativeChaosError('J es discreto y no puede usarse como barrido continuo.')
        dimension_value = bounds[0] if param_idx == 1 else p[1]
        dimension = _checked_int(dimension_value, 'J', minimum=4, maximum=256)
        _checked_output_capacity(
            dimension, arrays=8, name='estado de bifurcación Lorenz-96'
        )

    workers = _effective_workers(workers, n_param)
    if workers > 1 and not continuation:
        # Load/build once before spawning to avoid concurrent DLL replacement.
        library()
        tasks = [
            (
                system_key, tuple(state), tuple(p), param_idx, lo, hi, count,
                float(dt), float(T_trans), float(T_keep), max_points, False, method_key, observed_var_idx,
            )
            for lo, hi, count in _parameter_chunks(float(bounds[0]), float(bounds[1]), n_param, workers)
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
    rc = library().chaos_bifurcation_generic(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        param_idx,
        observed_var_idx,
        float(state[0]), float(state[1]), float(state[2]),
        float(bounds[0]), float(bounds[1]),
        n_param,
        float(dt), float(T_trans), float(T_keep),
        max_points,
        continuation,
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
    fixed_step_count(T_total, dt, name='T_total')
    get_system_code(system_key)
    p = _params_array(params)
    try:
        eq = np.asarray(eq_points, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeChaosError('eq_points debe tener forma (n, 3) y valores finitos.') from exc
    if eq.ndim != 2 or eq.shape[1:] != (3,) or not np.all(np.isfinite(eq)):
        raise NativeChaosError('eq_points debe tener forma (n, 3) y valores finitos.')
    if eq.shape[0] >= 240:
        raise NativeChaosError('eq_points admite como máximo 239 equilibrios.')
    eq = np.ascontiguousarray(eq)
    bounds = _params_array((z0_fixed, x_min, x_max, y_min, y_max))
    if not bounds[1] < bounds[2] or not bounds[3] < bounds[4]:
        raise NativeChaosError('Los límites de la cuenca deben ser crecientes.')
    nx = _checked_int(nx, 'nx', minimum=2, maximum=C_INT_MAX_STEPS)
    ny = _checked_int(ny, 'ny', minimum=2, maximum=C_INT_MAX_STEPS)
    row_start = _checked_int(row_start, 'row_start', minimum=0, maximum=ny - 1)
    row_count = (
        ny - row_start
        if row_count is None
        else _checked_int(row_count, 'row_count', minimum=1, maximum=ny)
    )
    if row_start > ny - row_count:
        raise NativeChaosError('row_start + row_count excede ny.')
    _checked_output_capacity(row_count, nx, itemsize=1, name=f'cuenca {system_key}')

    workers = _effective_workers(workers, row_count)
    if workers > 1:
        # Build/load once in the parent.  Otherwise, after a C-source change,
        # several fresh workers can try to replace the same DLL concurrently
        # on Windows.
        library()
        basin = np.empty((row_count, nx), dtype=np.uint8)
        eq_flat = tuple(eq.reshape(-1))
        tasks = [
            (
                system_key, tuple(p), eq_flat,
                float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]), float(bounds[4]),
                nx, ny, start, count, float(dt), float(T_total), method_key,
            )
            for local_start, count in _row_chunks(row_count, workers)
            for start in (row_start + local_start,)
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for start, part in pool.map(_basin_chunk, tasks):
                local_start = start - row_start
                basin[local_start:local_start + part.shape[0], :] = part
        return basin

    out = np.empty((row_count, nx), dtype=np.uint8)
    rc = library().chaos_basin_plane_generic(
        get_system_code(system_key),
        p.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(p.size),
        eq.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(eq.shape[0]),
        float(bounds[0]),
        float(bounds[1]), float(bounds[2]),
        float(bounds[3]), float(bounds[4]),
        nx, ny,
        row_start, row_count,
        float(dt), float(T_total),
        get_method_code(method_key),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo el calculo nativo de cuenca para {system_key}.')
    return out


def sprott_simulate_polynomial_native(
    kind: str,
    dimension: int,
    order: int,
    coefficients,
    initial,
    n_steps: int,
    h: float,
    method_key: str = 'rk4',
    divergence_threshold: float = 1e6,
):
    kind_code = {'map': 0, 'flow': 1}.get(str(kind).lower())
    if kind_code is None:
        raise NativeChaosError(f'Familia Sprott no simulable en C: {kind}')
    dimension = _checked_int(dimension, 'dimension', minimum=1, maximum=4)
    order = _checked_int(order, 'order', minimum=2, maximum=5)
    n_steps = _checked_int(n_steps, 'n_steps', minimum=1, maximum=C_INT_MAX_STEPS)
    h = _finite_scalar(h, 'h')
    divergence_threshold = _finite_scalar(
        divergence_threshold, 'divergence_threshold'
    )
    if h <= 0.0 or divergence_threshold <= 0.0:
        raise NativeChaosError('h y divergence_threshold deben ser positivos.')

    coeff = _params_array(coefficients)
    expected_coefficients = dimension * math.comb(dimension + order, order)
    if coeff.size != expected_coefficients:
        raise NativeChaosError(
            'El número de coeficientes Sprott no coincide con dimension/order: '
            f'se esperaban {expected_coefficients} y se recibieron {coeff.size}.'
        )
    try:
        init = np.asarray(initial, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NativeChaosError('La condición inicial Sprott debe ser numérica.') from exc
    if init.shape != (dimension,) or not np.all(np.isfinite(init)):
        raise NativeChaosError(
            f'La condición inicial Sprott debe tener forma ({dimension},) y ser finita.'
        )
    init = np.ascontiguousarray(init)
    _checked_output_capacity(
        n_steps + 1,
        dimension + 1,
        name='trayectoria Sprott',
    )

    t = np.empty(n_steps + 1, dtype=np.float64)
    X = np.empty((n_steps + 1, dimension), dtype=np.float64)
    status = ctypes.c_int(0)

    rc = library().sprott_simulate_polynomial(
        kind_code,
        dimension,
        order,
        coeff.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        int(coeff.size),
        init.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        n_steps,
        h,
        get_method_code(method_key),
        divergence_threshold,
        t.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        X.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.byref(status),
    )
    if rc != 0:
        raise NativeChaosError(f'Fallo la simulacion nativa C de Sprott, codigo {rc}.')
    return t, X, int(status.value)
