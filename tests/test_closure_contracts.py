from __future__ import annotations

import importlib
import importlib.util
from email.parser import Parser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from core.lorenz import (
    SYSTEM_REGISTRY,
    bifurcation_generic,
    bifurcation_generic_python,
    simulate_system,
    simulate_system_python,
)
from core.qt_capabilities import create_webengine_view, prepare_webengine
from core.sprott.families import PolynomialFlowFamily
from core.sprott.gallery import (
    GallerySecurityError,
    delete_gallery_entry,
    list_gallery_entries,
)
from core.sprott.reading_log import ReadingLogError, load_reading_log, save_reading_log
from core.time_policy import fixed_step_count, fixed_step_grid
import core.native as native_module
import core.app_metadata as app_metadata_module
import core.sprott.reading_log as reading_log_module
import core.update_checker as update_checker_module
import tools.download_sprott_site as sprott_downloader_module
from core.native import (
    NativeChaosError,
    basin_plane_generic_native,
    bifurcation_generic_native,
    simulate_system_native,
)
from core.system_ids import (
    NATIVE_SYSTEM_CODES,
    NATIVE_SYSTEM_DEFINITIONS,
    NATIVE_SYSTEM_IDS,
    PYTHON_ONLY_SYSTEM_IDS,
)
from core.update_checker import UpdateCheckError, check_for_updates
from core.url_security import ValidatingRedirectHandler
from tools.download_sprott_site import (
    DownloadRecord,
    ValidatingSiteRedirectHandler,
    download_assets_from_manifest,
    download_file,
    load_manifest,
    safe_local_path,
    write_manifest,
)
from scripts.verify_hafo_release import compatible_public_versions


def test_uniform_time_policy_accepts_exact_grid_and_rejects_partial_step():
    assert np.allclose(
        fixed_step_grid(0.9, 0.3), [0.0, 0.3, 0.6, 0.9], rtol=0.0, atol=1.0e-15
    )
    times, states = simulate_system_python(
        'hyper_lorenz', [0.1] * 4, [10.0, 8.0 / 3.0, 28.0, 1.0], 0.3, 0.9
    )
    assert times[-1] == pytest.approx(0.9)
    assert states.shape == (4, 4)
    with pytest.raises(ValueError, match='T/dt debe ser entero'):
        simulate_system_python(
            'hyper_lorenz', [0.1] * 4, [10.0, 8.0 / 3.0, 28.0, 1.0], 0.3, 1.0
        )
    with pytest.raises(ValueError, match='T/dt debe ser entero'):
        fixed_step_count(1.0 + 5.0e-11, 1.0)
    with pytest.raises(ValueError, match='T/dt debe ser finito'):
        fixed_step_count(np.finfo(np.float64).max, np.nextafter(0.0, 1.0))
    with pytest.raises(ValueError, match='por encima del límite'):
        fixed_step_grid(100_000_000.0, 1.0)


def test_checkout_version_takes_precedence_over_unrelated_installed_metadata(
    tmp_path, monkeypatch
):
    (tmp_path / 'pyproject.toml').write_text(
        '[project]\nname="chaos-toolbox"\nversion="9.8.7"\n', encoding='utf-8'
    )
    monkeypatch.setattr(app_metadata_module, 'project_root', lambda: tmp_path)
    monkeypatch.setattr(
        app_metadata_module, 'distribution_version', lambda _name: '0.0.1'
    )
    assert app_metadata_module.project_version() == '9.8.7'


def test_native_time_policy_accepts_exact_grid_and_rejects_partial_step():
    try:
        times, states = simulate_system_native(
            'lorenz', [0.1, 0.1, 0.1], [10.0, 28.0, 8.0 / 3.0], 0.3, 0.9
        )
    except NativeChaosError as exc:
        pytest.skip(str(exc))
    assert times[-1] == pytest.approx(0.9)
    assert states.shape == (4, 3)
    with pytest.raises(ValueError, match='T/dt debe ser entero'):
        simulate_system_native(
            'lorenz', [0.1, 0.1, 0.1], [10.0, 28.0, 8.0 / 3.0], 0.3, 1.0
        )


def test_sprott_native_heun_matches_python_when_compiler_is_available():
    from core.native import sprott_simulate_polynomial_native

    coefficients = [0.0, 1.0, 0.0]
    family = PolynomialFlowFamily(1, 2, coefficients)
    expected = family.step([0.1], h=0.2, method='heun')[0]
    try:
        _times, states, status = sprott_simulate_polynomial_native(
            'flow', 1, 2, coefficients, [0.1], 1, 0.2, method_key='heun'
        )
    except NativeChaosError as exc:
        pytest.skip(str(exc))
    assert status == 0
    assert states[1, 0] == pytest.approx(expected, rel=0.0, abs=1.0e-14)


def test_c_backend_rejects_invalid_method_enum_when_compiler_is_available():
    try:
        lib = native_module.library()
    except NativeChaosError as exc:
        pytest.skip(str(exc))
    times = np.empty(4, dtype=np.float64)
    states = np.empty((4, 3), dtype=np.float64)
    rc = lib.lorenz_simulate(
        0.1, 0.1, 0.1,
        10.0, 28.0, 8.0 / 3.0,
        0.3, 0.9,
        99,
        times.ctypes.data_as(native_module.ctypes.POINTER(native_module.ctypes.c_double)),
        states.ctypes.data_as(native_module.ctypes.POINTER(native_module.ctypes.c_double)),
        4,
    )
    assert rc != 0
    rc = lib.lorenz_simulate(
        0.1, 0.1, 0.1,
        10.0, 28.0, 8.0 / 3.0,
        1.0, 1.0 + 5.0e-11,
        2,
        times.ctypes.data_as(native_module.ctypes.POINTER(native_module.ctypes.c_double)),
        states.ctypes.data_as(native_module.ctypes.POINTER(native_module.ctypes.c_double)),
        2,
    )
    assert rc != 0


def test_system_ids_are_single_source_and_cover_the_public_registry():
    root = Path(__file__).resolve().parents[1]
    c_source = (root / 'core' / 'csrc' / 'chaos_core.c').read_text(encoding='utf-8')
    assert '#include "system_ids.def"' in c_source
    assert 'SYS_LORENZ = 0' not in c_source
    assert tuple(NATIVE_SYSTEM_CODES) == NATIVE_SYSTEM_IDS
    assert [code for _key, _symbol, code in NATIVE_SYSTEM_DEFINITIONS] == list(
        range(len(NATIVE_SYSTEM_DEFINITIONS))
    )
    assert set(SYSTEM_REGISTRY) == set(NATIVE_SYSTEM_IDS) | set(PYTHON_ONLY_SYSTEM_IDS)
    assert {
        key for key, metadata in SYSTEM_REGISTRY.items() if metadata['backend'] == 'python'
    } == set(PYTHON_ONLY_SYSTEM_IDS)


@pytest.mark.parametrize(
    'system_key',
    [key for key in NATIVE_SYSTEM_IDS if key not in {'mackey_glass', 'lorenz96'}],
)
@pytest.mark.parametrize('method_key', ('euler', 'heun', 'rk4'))
def test_all_ordinary_native_systems_match_the_python_reference(system_key, method_key):
    metadata = SYSTEM_REGISTRY[system_key]
    params = list(metadata['defaults'])
    if params:
        params[0] = float(params[0]) + 0.0137
    dt = 1.0 if metadata['kind'] == 'map' else 1.0e-3
    expected_times, expected_states = simulate_system_python(
        system_key, metadata['initial'], params, dt, dt, method_key
    )
    try:
        actual_times, actual_states = simulate_system_native(
            system_key, metadata['initial'], params, dt, dt, method_key
        )
    except NativeChaosError as exc:
        pytest.skip(str(exc))
    assert np.array_equal(actual_times, expected_times), system_key
    assert np.allclose(
        actual_states, expected_states, rtol=1.0e-12, atol=1.0e-12
    ), system_key


@pytest.mark.parametrize('method_key', ('euler', 'heun', 'rk4'))
def test_special_native_systems_match_explicit_reference_steps(method_key):
    x0 = 1.2
    beta, gamma, exponent, tau = 0.23, 0.11, 9.5, 13.7
    dt = 0.1
    try:
        mackey_times, mackey_states = simulate_system_native(
            'mackey_glass', [x0, 0.0, 0.0],
            [beta, gamma, exponent, tau], dt, dt, method_key
        )
    except NativeChaosError as exc:
        pytest.skip(str(exc))
    python_mackey_times, python_mackey_states = simulate_system_python(
        'mackey_glass', [x0, 0.0, 0.0],
        [beta, gamma, exponent, tau], dt, dt, method_key
    )
    assert np.array_equal(mackey_times, python_mackey_times)
    assert np.allclose(mackey_states, python_mackey_states, rtol=1.0e-13, atol=1.0e-13)

    forcing = 7.75
    state = np.full(7, forcing, dtype=float)
    state[:3] = [7.81, 7.72, 7.69]

    def rhs(values):
        return np.asarray([
            (values[(j + 1) % len(values)] - values[j - 2]) * values[j - 1]
            - values[j] + forcing
            for j in range(len(values))
        ])

    k1 = rhs(state)
    if method_key == 'euler':
        expected = state + dt * k1
    elif method_key == 'heun':
        expected = state + 0.5 * dt * (k1 + rhs(state + dt * k1))
    else:
        k2 = rhs(state + 0.5 * dt * k1)
        k3 = rhs(state + 0.5 * dt * k2)
        k4 = rhs(state + dt * k3)
        expected = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    _times, lorenz96_states = simulate_system_native(
        'lorenz96', state[:3], [forcing, 7.0], dt, dt, method_key
    )
    assert np.allclose(lorenz96_states[1], expected[:3], rtol=1.0e-12, atol=1.0e-12)
    python_times, python_states = simulate_system_python(
        'lorenz96', state[:3], [forcing, 7.0], dt, dt, method_key
    )
    assert python_times == pytest.approx([0.0, dt])
    assert np.allclose(python_states[1], expected[:3], rtol=1.0e-12, atol=1.0e-12)

    with pytest.raises((ValueError, NativeChaosError), match='J'):
        simulate_system_native(
            'lorenz96', state[:3], [forcing, 7.2], dt, dt, method_key
        )
    with pytest.raises(ValueError, match='J'):
        simulate_system_python(
            'lorenz96', state[:3], [forcing, 7.2], dt, dt, method_key
        )

    with pytest.raises(NativeChaosError):
        simulate_system_native(
            'mackey_glass', [x0, 0.0, 0.0],
            [beta, gamma, exponent, 1.0e308], dt, dt, method_key
        )


@pytest.mark.parametrize(
    ('method_key', 'minimum_ratio'),
    [('euler', 1.7), ('heun', 3.2), ('rk4', 10.0)],
)
def test_mackey_glass_pre_delay_convergence_matches_exact_linear_solution(
    method_key, minimum_ratio
):
    x0 = 1.2
    beta, gamma, exponent, tau = 0.7, 1.3, 2.0, 2.37
    duration = 0.8
    forcing = beta * x0 / (1.0 + abs(x0) ** exponent)
    equilibrium = forcing / gamma
    exact = equilibrium + (x0 - equilibrium) * np.exp(-gamma * duration)
    errors = []
    for dt in (0.2, 0.1, 0.05):
        _times, states = simulate_system_python(
            'mackey_glass', [x0, 0.0, 0.0],
            [beta, gamma, exponent, tau], dt, duration, method_key,
        )
        errors.append(abs(states[-1, 0] - exact))
        assert np.allclose(states[:, 1], x0, rtol=0.0, atol=0.0)
    assert errors[0] / errors[1] > minimum_ratio
    assert errors[1] / errors[2] > minimum_ratio


@pytest.mark.parametrize('method_key', ('euler', 'heun', 'rk4'))
def test_mackey_glass_nonintegral_delay_native_python_trajectory_parity(method_key):
    args = ('mackey_glass', [1.2, 0.0, 0.0], [0.2, 0.1, 10.0, 0.25], 0.1, 1.0)
    expected_times, expected_states = simulate_system_python(*args, method_key)
    actual_times, actual_states = simulate_system_native(*args, method_key)
    assert np.array_equal(actual_times, expected_times)
    assert np.all(np.isfinite(actual_states))
    assert np.allclose(actual_states, expected_states, rtol=2.0e-13, atol=2.0e-13)


def test_mackey_glass_rk4_cubic_history_converges_after_crossing_delay():
    initial = [1.2, 0.0, 0.0]
    params = [2.0, 1.3, 3.0, 0.25]
    duration = 0.5
    reference = simulate_system_python(
        'mackey_glass', initial, params, 0.0000625, duration, 'rk4'
    )[1][-1, 0]
    errors = []
    for dt in (0.05, 0.025, 0.0125):
        expected_times, expected_states = simulate_system_python(
            'mackey_glass', initial, params, dt, duration, 'rk4'
        )
        actual_times, actual_states = simulate_system_native(
            'mackey_glass', initial, params, dt, duration, 'rk4'
        )
        assert np.array_equal(actual_times, expected_times)
        assert np.allclose(actual_states, expected_states, rtol=2.0e-13, atol=2.0e-13)
        errors.append(abs(expected_states[-1, 0] - reference))
    assert errors[0] / errors[1] > 8.0
    assert errors[1] / errors[2] > 10.0


@pytest.mark.parametrize('system_key', ('mackey_glass', 'lorenz96'))
@pytest.mark.parametrize('method_key', ('euler', 'heun', 'rk4'))
@pytest.mark.parametrize('continuation', (False, True))
def test_special_bifurcations_are_finite_nonempty_and_match_python(
    system_key, method_key, continuation
):
    if system_key == 'mackey_glass':
        initial = [1.2, 0.0, 0.0]
        params = [0.2, 0.1, 10.0, 0.23]
        param_idx, lower, upper = 3, 0.23, 0.37
        dt, transient, keep = 0.05, 0.5, 1.0
    else:
        initial = [8.01, 8.0, 8.0]
        params = [8.0, 7.0]
        param_idx, lower, upper = 0, 7.9, 8.1
        dt, transient, keep = 0.01, 0.05, 0.1
    arguments = (
        system_key, initial, params, param_idx, lower, upper, 3,
        dt, transient, keep, 4,
    )
    expected_parameter, expected_value = bifurcation_generic_python(
        *arguments, continuation=continuation, method_key=method_key,
        observed_var_idx=0,
    )
    actual_parameter, actual_value = bifurcation_generic_native(
        *arguments, continuation=continuation, method_key=method_key,
        observed_var_idx=0, workers=1,
    )
    assert actual_parameter.size > 0
    assert np.all(np.isfinite(actual_parameter))
    assert np.all(np.isfinite(actual_value))
    assert np.array_equal(actual_parameter, expected_parameter)
    assert np.allclose(actual_value, expected_value, rtol=2.0e-11, atol=2.0e-11)
    assert len(np.unique(actual_parameter)) == 3


def test_special_bifurcation_metadata_and_public_index_validation():
    assert SYSTEM_REGISTRY['mackey_glass']['bifurcation_supported'] is True
    assert SYSTEM_REGISTRY['mackey_glass']['bifurcation_param'] == 3
    assert SYSTEM_REGISTRY['lorenz96']['bifurcation_supported'] is True
    assert SYSTEM_REGISTRY['lorenz96']['bifurcation_param'] == 0
    with pytest.raises((ValueError, NativeChaosError), match='param_idx'):
        bifurcation_generic(
            'lorenz', [0.1, 0.1, 0.1], [10.0, 28.0, 8.0 / 3.0],
            1.7, 20.0, 21.0, 2, 0.01, 0.0, 0.02, 1,
        )


@pytest.mark.parametrize(
    ('system_key', 'initial', 'params', 'param_idx', 'lower', 'upper'),
    (
        ('logistic', [0.2], [3.9], 0, 3.7, 3.9),
        ('henon', [0.1, 0.1], [1.4, 0.3], 0, 1.2, 1.4),
    ),
)
def test_low_dimensional_map_initials_are_padded_for_native_simulation_and_bifurcation(
    system_key, initial, params, param_idx, lower, upper
):
    padded = [*initial, *([0.0] * (3 - len(initial)))]
    time_active, states_active = simulate_system(
        system_key, initial, params, 1.0, 8.0, method_key='euler'
    )
    time_padded, states_padded = simulate_system(
        system_key, padded, params, 1.0, 8.0, method_key='euler'
    )
    assert np.array_equal(time_active, time_padded)
    assert np.array_equal(states_active, states_padded)

    parameter_active, values_active = bifurcation_generic(
        system_key, initial, params, param_idx, lower, upper, 3,
        1.0, 3.0, 5.0, 4, observed_var_idx=0,
    )
    parameter_padded, values_padded = bifurcation_generic(
        system_key, padded, params, param_idx, lower, upper, 3,
        1.0, 3.0, 5.0, 4, observed_var_idx=0,
    )
    assert np.array_equal(parameter_active, parameter_padded)
    assert np.array_equal(values_active, values_padded)


def test_extreme_finite_ranges_use_convex_interpolation_without_overflow():
    parameters, values = bifurcation_generic_native(
        'lorenz', [0.1, 0.1, 0.1], [10.0, 28.0, 8.0 / 3.0],
        1, -1.0e308, 1.0e308, 3, 0.01, 0.0, 0.01, 1,
        method_key='euler', observed_var_idx=0, workers=1,
    )
    assert np.all(np.isfinite(parameters))
    assert np.all(np.isfinite(values))
    assert 0.0 in parameters
    basin = basin_plane_generic_native(
        'lorenz', [10.0, 28.0, 8.0 / 3.0], [[0.0, 0.0, 0.0]], 0.0,
        -1.0e308, 1.0e308, -1.0e308, 1.0e308,
        3, 3, 0.01, 0.01, method_key='euler', workers=1,
    )
    assert basin.shape == (3, 3)


def test_native_source_build_uses_atomic_user_cache(tmp_path, monkeypatch):
    if not (shutil.which('gcc') or shutil.which('clang')):
        pytest.skip('No C compiler is available.')
    monkeypatch.setattr(native_module, 'user_data_dir', lambda: tmp_path / 'appdata')
    library_path = native_module._ensure_library()
    assert library_path.is_file()
    assert library_path.stat().st_size > 0
    assert library_path.is_relative_to(tmp_path / 'appdata' / 'native')
    assert library_path != Path(native_module.__file__).resolve().parent / 'bin' / library_path.name
    assert not list(library_path.parent.glob(f'.{library_path.stem}-*'))


def test_native_cache_serializes_concurrent_builds(tmp_path, monkeypatch):
    build_count = 0
    count_lock = Lock()

    def fake_run(command, **_kwargs):
        nonlocal build_count
        if '--version' in command:
            return SimpleNamespace(returncode=0, stdout='audit-gcc 1.0\n', stderr='')
        output = Path(command[command.index('-o') + 1])
        with count_lock:
            build_count += 1
        time.sleep(0.1)
        output.write_bytes(b'audit-native-library')
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(native_module, 'user_data_dir', lambda: tmp_path / 'appdata')
    monkeypatch.setattr(native_module.shutil, 'which', lambda _name: 'audit-gcc')
    monkeypatch.setattr(native_module.subprocess, 'run', fake_run)
    monkeypatch.setattr(native_module, '_probe_cached_library', lambda _path: True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: native_module._ensure_library(), range(2)))
    assert results[0] == results[1]
    assert results[0].read_bytes() == b'audit-native-library'
    assert build_count == 1
    assert not list(results[0].parent.glob('*.lock'))


def test_native_cache_rebuilds_a_corrupted_content_addressed_binary(tmp_path, monkeypatch):
    build_count = 0

    def fake_run(command, **_kwargs):
        nonlocal build_count
        if '--version' in command:
            return SimpleNamespace(returncode=0, stdout='audit-gcc 1.0\n', stderr='')
        build_count += 1
        Path(command[command.index('-o') + 1]).write_bytes(
            f'audit-native-library-{build_count}'.encode('ascii')
        )
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(native_module, 'user_data_dir', lambda: tmp_path / 'appdata')
    monkeypatch.setattr(native_module.shutil, 'which', lambda _name: 'audit-gcc')
    monkeypatch.setattr(native_module.subprocess, 'run', fake_run)
    monkeypatch.setattr(
        native_module,
        '_probe_cached_library',
        lambda path: path.read_bytes().startswith(b'audit-native-library-'),
    )
    first = native_module._ensure_library()
    assert native_module._cache_library_valid(first)
    first.write_bytes(b'corrupted')
    native_module._cache_digest_path(first).write_text(
        native_module._file_sha256(first) + '\n', encoding='ascii'
    )
    second = native_module._ensure_library()
    assert second == first
    assert second.read_bytes() == b'audit-native-library-2'
    assert native_module._cache_library_valid(second)
    assert build_count == 2


def test_native_cache_rebuilds_abi_only_library_missing_required_exports(
    tmp_path, monkeypatch
):
    compiler = shutil.which('gcc') or shutil.which('clang')
    if compiler is None:
        pytest.skip('No C compiler is available.')
    poison_source = tmp_path / 'abi_only.c'
    poison_source.write_text(
        '#if defined(_WIN32) || defined(__CYGWIN__)\n'
        '#define EXPORT __declspec(dllexport)\n'
        '#else\n'
        '#define EXPORT __attribute__((visibility("default")))\n'
        '#endif\n'
        f'EXPORT int chaos_core_abi_version(void) '
        f'{{ return {native_module._EXPECTED_NATIVE_ABI_VERSION}; }}\n',
        encoding='ascii',
    )
    poison_library = tmp_path / native_module._shared_library_name()
    command = native_module._compile_command(poison_source, poison_library, compiler)
    assert command is not None
    subprocess.run(command, check=True, capture_output=True, text=True)

    monkeypatch.setattr(native_module, 'user_data_dir', lambda: tmp_path / 'appdata')
    native_source = Path(native_module.__file__).resolve().parent / 'csrc' / 'chaos_core.c'
    cache_directory = (
        tmp_path / 'appdata' / 'native'
        / native_module._native_cache_key(native_source, compiler)
    )
    cache_directory.mkdir(parents=True)
    cached_library = cache_directory / native_module._shared_library_name()
    shutil.copy2(poison_library, cached_library)
    native_module._cache_digest_path(cached_library).write_text(
        native_module._file_sha256(cached_library) + '\n', encoding='ascii'
    )
    assert native_module._cache_library_valid(cached_library)
    assert not native_module._probe_cached_library(cached_library)

    rebuilt_library = native_module._ensure_library()
    assert rebuilt_library == cached_library
    assert native_module._cache_library_usable(rebuilt_library)
    loaded = native_module.ctypes.CDLL(str(rebuilt_library))
    for export_name in native_module._REQUIRED_NATIVE_EXPORTS:
        assert hasattr(loaded, export_name)


def test_native_cache_recovers_only_stale_build_lock(tmp_path):
    library_path = tmp_path / 'chaos_core.dll'
    lock_path = tmp_path / '.chaos_core.dll.lock'
    lock_path.write_text('orphan\n', encoding='ascii')
    stale = time.time() - 600.0
    os.utime(lock_path, (stale, stale))
    with native_module._native_build_lock(
        lock_path, library_path, timeout_seconds=0.5, stale_seconds=1.0
    ) as owns_lock:
        assert owns_lock
    assert not lock_path.exists()


def test_native_loader_rejects_mismatched_abi(tmp_path, monkeypatch):
    library_path = tmp_path / native_module._shared_library_name()
    library_path.write_bytes(b'not-loaded-by-this-test')

    def fake_abi():
        return native_module._EXPECTED_NATIVE_ABI_VERSION + 1

    fake_library = type('FakeLibrary', (), {})()
    fake_library.chaos_core_abi_version = fake_abi
    monkeypatch.setattr(native_module, '_ensure_library', lambda: library_path)
    monkeypatch.setattr(native_module.ctypes, 'CDLL', lambda _path: fake_library)
    with pytest.raises(native_module.NativeChaosError, match='ABI nativa incompatible'):
        native_module._load_library()


def test_native_loader_translates_missing_required_export(tmp_path, monkeypatch):
    library_path = tmp_path / native_module._shared_library_name()
    library_path.write_bytes(b'not-loaded-by-this-test')
    fake_library = type('FakeLibrary', (), {})()
    fake_library.chaos_core_abi_version = lambda: native_module._EXPECTED_NATIVE_ABI_VERSION
    monkeypatch.setattr(native_module, '_ensure_library', lambda: library_path)
    monkeypatch.setattr(native_module.ctypes, 'CDLL', lambda _path: fake_library)
    with pytest.raises(native_module.NativeChaosError, match='funciones requeridas'):
        native_module._load_library()


def test_real_native_library_declares_expected_abi():
    if not (shutil.which('gcc') or shutil.which('clang')):
        pytest.skip('No C compiler is available.')
    library = native_module._load_library()
    assert library.chaos_core_abi_version() == native_module._EXPECTED_NATIVE_ABI_VERSION


def test_gallery_refuses_deletion_outside_configured_root(tmp_path):
    root = tmp_path / 'gallery'
    root.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'metadata.json').write_text('{}', encoding='utf-8')
    with pytest.raises(GallerySecurityError):
        delete_gallery_entry(outside, base=root)
    assert outside.is_dir()


def test_gallery_skips_metadata_paths_that_escape_entry(tmp_path, caplog):
    root = tmp_path / 'gallery'
    entry = root / 'entry'
    entry.mkdir(parents=True)
    (root / 'secret.png').write_bytes(b'secret')
    (entry / 'thumbnail.png').write_bytes(b'thumb')
    (entry / 'metadata.json').write_text(
        json.dumps({'render': '../secret.png', 'thumbnail': 'thumbnail.png'}),
        encoding='utf-8',
    )
    with caplog.at_level('WARNING', logger='core.sprott.gallery'):
        assert list_gallery_entries(root) == []
    assert 'Se omitió una entrada inválida' in caplog.text
    assert 'ruta relativa confinada' in caplog.text


def test_reading_log_reports_corruption_and_atomic_save(tmp_path):
    target = tmp_path / 'reading.json'
    target.write_text('{broken', encoding='utf-8')
    with pytest.raises(ReadingLogError):
        load_reading_log(target)
    save_reading_log({'entry': {'marks': ['visto']}}, target)
    assert load_reading_log(target)['entry']['marks'] == ['visto']
    assert not list(tmp_path.glob('*.tmp'))


def test_reading_log_failed_replace_preserves_previous_file(tmp_path, monkeypatch):
    target = tmp_path / 'reading.json'
    target.write_text('{"old": true}\n', encoding='utf-8')

    def fail_replace(_source, _target):
        raise OSError('simulated replace failure')

    monkeypatch.setattr(reading_log_module.os, 'replace', fail_replace)
    with pytest.raises(ReadingLogError, match='simulated replace failure'):
        save_reading_log({'new': True}, target)
    assert json.loads(target.read_text(encoding='utf-8')) == {'old': True}
    assert not list(tmp_path.glob('*.tmp'))


def test_reading_log_wraps_temporary_file_permission_errors(tmp_path, monkeypatch):
    target = tmp_path / 'reading.json'

    def fail_mkstemp(**_kwargs):
        raise PermissionError('simulated temporary-file denial')

    monkeypatch.setattr(reading_log_module.tempfile, 'mkstemp', fail_mkstemp)
    with pytest.raises(ReadingLogError, match='simulated temporary-file denial'):
        save_reading_log({'new': True}, target)
    assert not target.exists()


def test_reading_log_ui_blocks_overwrite_after_corrupt_load(monkeypatch):
    from ui import sprott_explorer_tab as explorer_module
    from ui.sprott_explorer_tab import SprottExplorerTab

    warnings = []
    writes = []
    model = SimpleNamespace(_reading_log={'old': True})
    monkeypatch.setattr(
        explorer_module,
        'load_reading_log',
        lambda: (_ for _ in ()).throw(ReadingLogError('corrupt JSON')),
    )
    monkeypatch.setattr(
        explorer_module.QMessageBox,
        'warning',
        lambda *_args: warnings.append(_args[-1]),
    )
    monkeypatch.setattr(
        explorer_module,
        'save_reading_log',
        lambda payload: writes.append(payload),
    )

    SprottExplorerTab._reload_reading_log(model)
    assert model._reading_log == {}
    assert model._reading_log_load_error == 'corrupt JSON'
    assert not SprottExplorerTab._persist_reading_log(model, {'new': True})
    assert writes == []
    assert any('no se sobrescribirá' in message for message in warnings)


def test_reading_log_ui_rolls_back_note_and_mark_when_persistence_fails():
    from ui.sprott_explorer_tab import SprottExplorerTab

    original = {
        'BOOK.DIC:1': {
            'marks': [], 'note': 'old', 'last_updated': '',
            'code': 'ABC', 'source_name': 'BOOK.DIC', 'line': 1,
        }
    }
    note_model = SimpleNamespace(
        _reading_log=json.loads(json.dumps(original)),
        _current_reading_key=lambda: 'BOOK.DIC:1',
        _current_reading_entry=lambda: {
            'code': 'ABC', 'source_name': 'BOOK.DIC', 'line': 1,
        },
        reading_note_edit=SimpleNamespace(text=lambda: 'new'),
        _persist_reading_log=lambda _candidate: False,
    )
    SprottExplorerTab.save_reading_note(note_model)
    assert note_model._reading_log == original

    button_calls = []
    button = SimpleNamespace(
        blockSignals=lambda value: button_calls.append(('block', value)),
        setChecked=lambda value: button_calls.append(('checked', value)),
    )
    refresh_calls = []
    mark_model = SimpleNamespace(
        _reading_log=json.loads(json.dumps(original)),
        _current_reading_key=lambda: 'BOOK.DIC:1',
        _current_reading_entry=note_model._current_reading_entry,
        _persist_reading_log=lambda _candidate: False,
        _mark_buttons={'favorito': button},
        _refresh_reading_row_marks=lambda *_args: refresh_calls.append(True),
    )
    SprottExplorerTab.toggle_reading_mark(mark_model, 'favorito', True)
    assert mark_model._reading_log == original
    assert button_calls == [('block', True), ('checked', False), ('block', False)]
    assert refresh_calls == []


def test_updater_rejects_untrusted_source_and_asset_hosts():
    with pytest.raises(UpdateCheckError, match='host autorizado'):
        check_for_updates(
            installed_version='0.1.0',
            release_api_url='https://example.invalid/latest',
            fetcher=lambda _url: {},
        )
    with pytest.raises(UpdateCheckError, match='URL de descarga'):
        check_for_updates(
            installed_version='0.1.0',
            release_api_url='https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest',
            fetcher=lambda _url: {
                'tag_name': 'v0.1.1',
                'html_url': 'https://github.com/Xerkkun/toolbox-chaos/releases/tag/v0.1.1',
                'assets': [{'name': 'chaos-toolbox-v0.1.1-windows-x64.exe', 'browser_download_url': 'https://evil.invalid/payload.exe'}],
            },
        )


@pytest.mark.parametrize(
    'oversized_content_length',
    [True, False],
)
def test_updater_limits_release_response_size(monkeypatch, oversized_content_length):
    if oversized_content_length:
        headers = {
            'Content-Length': str(update_checker_module.MAX_RELEASE_RESPONSE_BYTES + 1)
        }
        body = b'{}'
    else:
        headers = {}
        body = b'x' * (update_checker_module.MAX_RELEASE_RESPONSE_BYTES + 1)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return 'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest'

        def read(self, limit):
            return body[:limit]

    response = FakeResponse()
    response.headers = headers
    fake_opener = SimpleNamespace(open=lambda *_args, **_kwargs: response)
    monkeypatch.setattr(
        update_checker_module, 'build_validating_opener', lambda _validator: fake_opener
    )
    with pytest.raises(UpdateCheckError, match='excede 2 MiB'):
        update_checker_module._default_fetcher(
            'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest'
        )


def test_redirect_handlers_reject_external_target_before_following():
    request = SimpleNamespace(full_url='https://api.github.com/repos/example/project')
    update_handler = ValidatingRedirectHandler(
        update_checker_module.validate_release_api_url
    )
    with pytest.raises(UpdateCheckError, match='host autorizado'):
        update_handler.redirect_request(
            request, None, 302, 'Found', {}, 'https://evil.invalid/payload'
        )

    site_request = SimpleNamespace(full_url='https://sprott.physics.wisc.edu/index.html')
    site_handler = ValidatingSiteRedirectHandler('sprott.physics.wisc.edu')
    with pytest.raises(ValueError, match='sólo puede usar HTTPS'):
        site_handler.redirect_request(
            site_request, None, 302, 'Found', {}, 'https://evil.invalid/payload'
        )


def test_downloader_confines_paths_and_rejects_external_manifest(tmp_path):
    with pytest.raises(ValueError, match='segmentos'):
        safe_local_path(
            tmp_path, 'https://sprott.physics.wisc.edu/%2e%2e/escape.txt', 'files'
        )
    with pytest.raises(ValueError, match='sólo puede usar HTTPS'):
        download_file(
            'https://evil.invalid/payload.exe', tmp_path, 'test-agent', 1.0, False
        )

    pages = tmp_path / 'pages'
    pages.mkdir()
    page = pages / 'index.html'
    page.write_text('<a href="https://evil.invalid/payload.png">x</a>', encoding='utf-8')
    write_manifest(
        tmp_path,
        [DownloadRecord('https://evil.invalid/index.html', str(page), 'page_saved', 200, 'text/html', page.stat().st_size, None, None)],
    )
    with pytest.raises(ValueError, match='sólo puede usar HTTPS'):
        download_assets_from_manifest(
            tmp_path,
            max_files=1,
            delay=0.0,
            timeout=1.0,
            user_agent='test-agent',
            overwrite=False,
            include_extensions={'.png'},
            exclude_extensions=None,
            download_unknown=False,
        )


def test_downloader_limits_manifest_bytes_rows_and_saved_page_size(
    tmp_path, monkeypatch
):
    manifest = tmp_path / 'manifest.csv'
    monkeypatch.setattr(sprott_downloader_module, 'MANIFEST_MAX_BYTES', 32)
    manifest.write_bytes(b'x' * 33)
    with pytest.raises(ValueError, match='manifiesto excede el límite de 32 bytes'):
        load_manifest(tmp_path)

    monkeypatch.setattr(
        sprott_downloader_module, 'MANIFEST_MAX_BYTES', 1024 * 1024
    )
    monkeypatch.setattr(sprott_downloader_module, 'MANIFEST_MAX_ROWS', 1)
    records = [
        DownloadRecord(
            f'https://sprott.physics.wisc.edu/page-{index}.html', '',
            'skipped', None, None, 0, None, None,
        )
        for index in range(2)
    ]
    write_manifest(tmp_path, records)
    with pytest.raises(ValueError, match='manifiesto excede el límite de 1 filas'):
        load_manifest(tmp_path)

    monkeypatch.setattr(sprott_downloader_module, 'MANIFEST_MAX_ROWS', 100_000)
    pages = tmp_path / 'pages'
    pages.mkdir()
    page = pages / 'large.html'
    page.write_text(
        '<img src="https://sprott.physics.wisc.edu/image.png">' + 'x' * 128,
        encoding='utf-8',
    )
    page_url = 'https://sprott.physics.wisc.edu/large.html'
    write_manifest(
        tmp_path,
        [DownloadRecord(
            page_url, str(page), 'page_saved', 200, 'text/html',
            page.stat().st_size, None, None,
        )],
    )
    result = download_assets_from_manifest(
        tmp_path,
        max_files=1,
        delay=0.0,
        timeout=1.0,
        user_agent='test-agent',
        overwrite=False,
        include_extensions={'.png'},
        exclude_extensions=None,
        download_unknown=False,
        max_page_bytes=64,
    )
    page_result = next(record for record in result if record.url == page_url)
    assert page_result.status == 'page_asset_parse_error'
    assert 'límite de 64 bytes' in (page_result.error or '')


def test_webengine_probe_falls_back_cleanly_offscreen(monkeypatch):
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    view, status = create_webengine_view()
    assert view is None
    assert not status.available


def test_webengine_extra_imports_with_application_entrypoint():
    if importlib.util.find_spec('PySide6.QtWebEngineWidgets') is None:
        pytest.skip('Install the webengine extra to run this capability gate.')
    platform_name = os.environ.get('QT_QPA_PLATFORM', '').strip().lower()
    if platform_name in {'offscreen', 'minimal'}:
        pytest.skip(f'Qt WebEngine bootstrap is unavailable on {platform_name}.')
    preparation = prepare_webengine()
    assert preparation.available, preparation.reason
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import main

    assert QWebEnginePage is not None
    assert QWebEngineView is not None
    assert callable(main.main_entry)


def test_webengine_bootstrap_works_in_a_fresh_process_before_qapplication():
    if importlib.util.find_spec('PySide6.QtWebEngineWidgets') is None:
        pytest.skip('Install the webengine extra to run this capability gate.')
    if os.environ.get('CHAOS_TEST_WEBENGINE_RUNTIME') != '1':
        pytest.skip('La creación WebEngine real se ejecuta sólo en el gate CI/xvfb.')
    platform_name = os.environ.get('QT_QPA_PLATFORM', '').strip().lower()
    if platform_name in {'offscreen', 'minimal'}:
        pytest.skip(f'Qt WebEngine runtime is unavailable on {platform_name}.')
    probe = (
        "from core.qt_capabilities import prepare_webengine,create_webengine_view;"
        "s=prepare_webengine(); assert s.available,s.reason;"
        "from PySide6.QtWidgets import QApplication; app=QApplication([]);"
        "view,status=create_webengine_view(); assert status.available,status.reason;"
        "assert view is not None; view.deleteLater(); app.processEvents();"
        "print('WEBENGINE_FRESH_PROCESS_OK')"
    )
    completed = subprocess.run(
        [sys.executable, '-B', '-c', probe],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert 'WEBENGINE_FRESH_PROCESS_OK' in completed.stdout


def test_webengine_runtime_creates_page_on_viable_platform():
    if importlib.util.find_spec('PySide6.QtWebEngineWidgets') is None:
        pytest.skip('Install the webengine extra to run this capability gate.')
    if os.environ.get('CHAOS_TEST_WEBENGINE_RUNTIME') != '1':
        pytest.skip('La creación WebEngine real se ejecuta sólo en el gate CI/xvfb.')
    platform_name = os.environ.get('QT_QPA_PLATFORM', '').strip().lower()
    if platform_name in {'offscreen', 'minimal'}:
        pytest.skip(f'Qt WebEngine runtime is unavailable on {platform_name}.')
    preparation = prepare_webengine()
    assert preparation.available, preparation.reason
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebEngineCore import QWebEnginePage

    app = QApplication.instance() or QApplication([])
    view, status = create_webengine_view()
    assert status.available, status.reason
    assert view is not None
    assert isinstance(view.page(), QWebEnginePage)
    view.deleteLater()
    app.processEvents()


def test_scratch_smoke_modules_have_no_import_side_effects(monkeypatch):
    previous = os.environ.get('QT_QPA_PLATFORM')
    importlib.import_module('scratch.test_bif')
    importlib.import_module('scratch.test_coex')
    assert os.environ.get('QT_QPA_PLATFORM') == previous


def test_wang_generator_uses_runtime_dispatch_and_distinct_status_fields():
    source = (
        Path(__file__).resolve().parents[1] / 'tools' / 'calculate_wang_equilibria.py'
    ).read_text(encoding='utf-8')
    assert 'eval(' not in source
    assert "vector_field(key, x, p)" in source
    assert "'runtime_status'" in source
    assert "'equilibrium_scan_status'" in source
    assert "'status': 'completo'" not in source


def test_wang_generator_import_has_no_filesystem_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sys.modules.pop('tools.calculate_wang_equilibria', None)

    module = importlib.import_module('tools.calculate_wang_equilibria')

    assert callable(module.generate_catalog)
    assert callable(module.main)
    assert not (tmp_path / 'data').exists()
    assert not (tmp_path / 'docs').exists()
    assert not (tmp_path / 'reports').exists()


def test_windows_packaging_scripts_propagate_failures_without_archive_overwrite():
    root = Path(__file__).resolve().parents[1]
    script_names = (
        'package_all.ps1', 'build_windows.ps1', 'build_windows_installer.ps1',
    )
    sources = {
        name: (root / 'scripts' / name).read_text(encoding='utf-8')
        for name in script_names
    }
    for name, source in sources.items():
        assert 'Invoke-CheckedPython' in source, name
        assert '$LASTEXITCODE:' not in source, name
        assert '${LASTEXITCODE}:' in source, name
    installer = sources['build_windows_installer.ps1']
    assert 'Move-ToInstallerArchive' in installer
    assert '[Guid]::NewGuid()' in installer
    assert 'Move-Item -LiteralPath $source.FullName -Destination $destination -Force' not in installer


def test_windows_workflows_expose_msys2_ucrt64_compiler_to_host_path():
    root = Path(__file__).resolve().parents[1]
    cases = (
        ('ci.yml', 'test', (
            'Install Toolbox and test dependencies',
            'Run full test suite',
            'Build and probe installed wheel',
        )),
        ('release.yml', 'build', (
            'Install Toolbox and build dependencies',
            'Run package metadata tests',
            'Build Windows Executable & Installer',
        )),
    )
    for workflow_name, job_name, later_steps in cases:
        path = root / '.github' / 'workflows' / workflow_name
        payload = yaml.safe_load(path.read_text(encoding='utf-8'))
        assert isinstance(payload, dict), workflow_name
        steps = payload['jobs'][job_name]['steps']
        setup_index, setup = next(
            (index, step) for index, step in enumerate(steps)
            if str(step.get('uses', '')).startswith('msys2/setup-msys2@')
        )
        assert setup['id'] == 'msys2', workflow_name
        path_index, path_step = next(
            (index, step) for index, step in enumerate(steps)
            if step.get('name') == 'Expose Windows native compiler to host processes'
        )
        assert path_step['env']['MSYS2_LOCATION'] == (
            '${{ steps.msys2.outputs.msys2-location }}'
        ), workflow_name
        run = path_step['run']
        assert "'ucrt64\\bin'" in run, workflow_name
        assert '$env:GITHUB_PATH' in run, workflow_name
        assert '$env:PATH = "$ucrt64Bin;$env:PATH"' in run, workflow_name
        assert setup_index < path_index, workflow_name
        indices = {step.get('name'): index for index, step in enumerate(steps)}
        assert all(path_index < indices[name] for name in later_steps), workflow_name


def test_release_workflow_assets_include_updater_platform_tags():
    source = (
        Path(__file__).resolve().parents[1] / '.github' / 'workflows' / 'release.yml'
    ).read_text(encoding='utf-8')
    assert 'platform_arch=x64' in source
    assert 'platform_arch=arm64' in source
    assert 'macos-${platform_arch}.dmg' in source
    assert 'linux-${platform_arch}.deb' in source
    assert 'linux-x64.AppImage' not in source


def test_hafo_release_gate_accepts_only_the_declared_public_range():
    payload = {
        'releases': {
            '1.0.0': [{'filename': 'old.whl'}],
            '1.1.0rc1': [{'filename': 'candidate.whl'}],
            '1.1.0': [{'filename': 'current.whl'}],
            '2.0.0': [{'filename': 'future.whl'}],
            '1.2.0': [],
        }
    }
    assert [str(version) for version in compatible_public_versions(payload)] == ['1.1.0']


def test_built_wheel_installs_entrypoint_metadata_and_resources(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / 'source'
    source.mkdir()
    for name in (
        'pyproject.toml', 'main.py', 'README.md', 'LICENSE', 'NOTICE.md',
        'THIRD_PARTY_NOTICES.md', 'AUTHORS.md', 'RELEASE_NOTES.md',
    ):
        shutil.copy2(root / name, source / name)
    for directory in ('core', 'ui', 'docs', 'resources', 'LICENSES'):
        shutil.copytree(
            root / directory,
            source / directory,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
        )

    wheelhouse = tmp_path / 'wheelhouse'
    subprocess.run(
        [sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', str(wheelhouse)],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(wheelhouse.glob('chaos_toolbox-*.whl'))
    assert wheel.name.endswith('-py3-none-any.whl')
    with zipfile.ZipFile(wheel) as archive:
        members = archive.namelist()
        third_party = archive.read(
            next(name for name in members if name.endswith('/THIRD_PARTY_NOTICES.md'))
        ).decode('utf-8')
        source_manifest = archive.read(
            next(
                name for name in members
                if name.endswith('/Qt-PySide-6.11.1-Corresponding-Source.txt')
            )
        ).decode('utf-8')
        security_inventory = archive.read(
            next(
                name for name in members
                if name.endswith('/Qt-6.11.1-Security-Inventory.txt')
            )
        ).decode('utf-8')
        metadata_text = archive.read(
            next(name for name in members if name.endswith('.dist-info/METADATA'))
        ).decode('utf-8')
    assert any(name.endswith('core/csrc/chaos_core.c') for name in members)
    assert not any(name.startswith('core/bin/') for name in members)
    assert 'PySide6-Essentials' in third_party and 'Pillow: HPND' in third_party
    assert '252acef8c5ae68074d91cadba2ee4a83465051bbb970dd26e8f0daa0f3904e03' in source_manifest
    assert 'CVE-2026-8168-qtsvg-6.11' in security_inventory
    metadata = Parser().parsestr(metadata_text)
    assert tuple(int(part) for part in metadata['Metadata-Version'].split('.')) >= (2, 4)
    assert metadata['License-Expression'] == 'MIT'
    assert {
        'LICENSE',
        'NOTICE.md',
        'THIRD_PARTY_NOTICES.md',
        'LICENSES/LGPL-3.0-only.txt',
        'LICENSES/GPL-3.0-only.txt',
        'LICENSES/Chromium-BSD-3-Clause.txt',
        'LICENSES/QtWebEngine-Third-Party-NOTICE.txt',
        'LICENSES/Qt-PySide-6.11.1-Corresponding-Source.txt',
        'LICENSES/Qt-6.11.1-Security-Inventory.txt',
    } <= set(metadata.get_all('License-File', []))
    installed = tmp_path / 'installed'
    subprocess.run(
        [
            sys.executable, '-m', 'pip', '--disable-pip-version-check', 'install',
            '--no-index', '--no-deps', '--target', str(installed), str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    probe = (
        f"import sys; sys.path.insert(0,{str(installed)!r}); sys.prefix={str(installed)!r}; "
        "import main; import core.lorenz; import numpy as np; "
        "from importlib.metadata import distribution; "
        "from core.app_metadata import APP_VERSION,DOCUMENTATION_ENTRY; "
        "from core.paths import resource_path; "
        "from core.system_ids import NATIVE_SYSTEM_CODES; "
        "from core.native import simulate_system_native; "
        "d=distribution('chaos-toolbox'); "
        "assert APP_VERSION=='0.1.0'; "
        "assert callable(main.main_entry); assert len(NATIVE_SYSTEM_CODES)==37; "
        "assert any(e.group=='gui_scripts' and e.name=='chaos-toolbox' and e.value=='main:main_entry' for e in d.entry_points); "
        "assert any(r.lower().replace(' ','').startswith('hidden-attractors-fo') and '>=1.1' in r for r in (d.requires or [])); "
        "assert resource_path(DOCUMENTATION_ENTRY).is_file(); "
        "assert resource_path('docs','installation.md').is_file(); "
        "assert resource_path('docs','troubleshooting.md').is_file(); "
        "assert resource_path('docs','license.md').is_file(); "
        "times,states=simulate_system_native('lorenz',[0.1,0.1,0.1],[10.0,28.0,8.0/3.0],0.01,0.02,'rk4'); "
        "assert times.shape==(3,) and states.shape==(3,3); "
        "assert np.isfinite(times).all() and np.isfinite(states).all(); "
        "print('WHEEL_INSTALL_OK')"
    )
    result = subprocess.run(
        [sys.executable, '-I', '-c', probe],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == 'WHEEL_INSTALL_OK'
