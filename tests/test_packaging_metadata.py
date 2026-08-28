from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import core.update_checker as update_checker_module
from core.app_metadata import (
    APP_AUTHOR_DISPLAY,
    APP_BRAND,
    APP_DEVELOPER,
    APP_DOI,
    APP_LICENSE,
    APP_RELEASE_DATE,
    APP_RELEASE_STATUS,
    APP_VERSION,
    DEFAULT_RELEASE_API_URL,
    RELEASE_API_ENV,
)
from core.update_checker import (
    ReleaseAsset,
    UpdateCheckError,
    check_for_updates,
    current_platform_tag,
    is_newer_version,
    parse_semver,
    select_asset,
)
from scripts.validate_self_test_output import (
    SelfTestValidationError,
    load_and_validate_self_test,
    validate_self_test_payload,
)
from scripts.verify_release_tag import ReleaseTagError, verify_release_tag
from ui.main_window import MainWindow


def test_version_metadata_is_semver():
    assert parse_semver(APP_VERSION).release == (0, 2, 0)
    assert APP_DEVELOPER == 'Maria Fernanda Moreno Lopez'
    assert APP_LICENSE == 'MIT'
    assert 'Maria Fernanda Moreno Lopez' in APP_AUTHOR_DISPLAY
    assert 'Fer Moreno' in APP_AUTHOR_DISPLAY
    assert APP_BRAND == 'Fyskode'
    assert APP_RELEASE_STATUS == 'stable release'
    assert APP_RELEASE_DATE == '2026-08-28'
    assert APP_DOI == '10.17605/OSF.IO/GQMJR'


def test_release_identity_is_synchronized_across_public_metadata():
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads(
        (root / 'docs' / 'project_metadata.json').read_text(encoding='utf-8')
    )
    citation = (root / 'CITATION.cff').read_text(encoding='utf-8')

    assert metadata['version'] == APP_VERSION
    assert metadata['latest_published_version'] == APP_VERSION
    assert metadata['release_status'] == 'published_stable'
    assert metadata['release_date'] == APP_RELEASE_DATE
    assert metadata['osf_doi'] == APP_DOI
    assert f'version: "{APP_VERSION}"' in citation
    assert f'date-released: "{APP_RELEASE_DATE}"' in citation
    assert f'doi: {APP_DOI}' in citation


def test_user_manual_is_stable_and_packaged_copies_are_identical():
    root = Path(__file__).resolve().parents[1]
    source = (
        root / 'assets' / 'manuals' / 'manual_usuario_toolbox_chaos.tex'
    ).read_text(encoding='utf-8')
    lowered = source.casefold()
    assert 'referencia candidata' not in lowered
    assert 'todavía no está publicada' not in lowered
    assert 'no se crea un doi nuevo' in lowered

    copies = [
        root / 'assets' / 'manuals' / 'manual_usuario_toolbox_chaos.pdf',
        root / 'output' / 'pdf' / 'manual_usuario_toolbox_chaos.pdf',
        root / 'resources' / 'bundled' / 'docs' / 'manual_usuario_toolbox_chaos.pdf',
    ]
    assert all(path.is_file() for path in copies)
    assert len({path.read_bytes() for path in copies}) == 1


def test_update_version_comparison():
    assert is_newer_version('v0.1.1', '0.1.0')
    assert not is_newer_version('0.1.0', '0.1.0')
    assert not is_newer_version('0.0.9', '0.1.0')
    assert is_newer_version('1.1.0', '1.1.0-rc1')
    assert is_newer_version('1.1.0-rc2', '1.1.0-rc1')
    assert not is_newer_version('1.1.0-rc1', '1.1.0')


def test_update_asset_selection_by_platform():
    assets = [
        ReleaseAsset('chaos-toolbox-v0.1.0-linux-x64.deb', 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.0/linux-x64'),
        ReleaseAsset('chaos-toolbox-v0.1.0-linux-arm64.deb', 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.0/linux-arm64'),
        ReleaseAsset('chaos-toolbox-v0.1.0-macos-x64.dmg', 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.0/macos-x64'),
        ReleaseAsset('chaos-toolbox-v0.1.0-macos-arm64.dmg', 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.0/macos-arm64'),
        ReleaseAsset('chaos-toolbox-v0.1.0-windows-x64-setup.exe', 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.0/windows'),
    ]
    for platform_tag in (
        'windows-x64', 'macos-x64', 'macos-arm64', 'linux-x64', 'linux-arm64',
    ):
        selected = select_asset(assets, platform_tag)
        assert selected is not None
        assert platform_tag in selected.name


@pytest.mark.parametrize(
    ('system', 'machine', 'expected'),
    (
        ('Windows', 'AMD64', 'windows-x64'),
        ('Darwin', 'x86_64', 'macos-x64'),
        ('Darwin', 'arm64', 'macos-arm64'),
        ('Linux', 'aarch64', 'linux-arm64'),
    ),
)
def test_current_platform_tag_maps_only_supported_platforms(
    monkeypatch, system, machine, expected
):
    monkeypatch.setattr(update_checker_module.platform, 'system', lambda: system)
    monkeypatch.setattr(update_checker_module.platform, 'machine', lambda: machine)
    assert current_platform_tag() == expected


@pytest.mark.parametrize(
    ('system', 'machine', 'message'),
    (
        ('Windows', 's390x', 'Arquitectura'),
        ('Plan9', 'x86_64', 'Sistema operativo'),
    ),
)
def test_current_platform_tag_rejects_unknown_platforms(
    monkeypatch, system, machine, message
):
    monkeypatch.setattr(update_checker_module.platform, 'system', lambda: system)
    monkeypatch.setattr(update_checker_module.platform, 'machine', lambda: machine)
    with pytest.raises(UpdateCheckError, match=message):
        current_platform_tag()


def test_update_check_available_and_unavailable_with_mock_fetcher():
    payload = {
        'tag_name': 'v0.1.1',
        'published_at': '2026-06-14T00:00:00Z',
        'html_url': 'https://github.com/Xerkkun/toolbox-chaos/releases/tag/v0.1.1',
        'body': 'Maintenance release.',
        'assets': [
            {
                'name': 'chaos-toolbox-v0.1.1-windows-x64-setup.exe',
                'browser_download_url': 'https://github.com/Xerkkun/toolbox-chaos/releases/download/v0.1.1/chaos-toolbox.exe',
            }
        ],
    }
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url='https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest',
        platform_tag='windows-x64',
        fetcher=lambda _url: payload,
    )
    assert info.update_available
    assert info.download_url.endswith('/chaos-toolbox.exe')

    payload['tag_name'] = 'v0.1.0'
    payload['assets'][0]['name'] = (
        'chaos-toolbox-v0.1.0-windows-x64-setup.exe'
    )
    info = check_for_updates(
        installed_version='0.1.0',
        release_api_url='https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest',
        platform_tag='windows-x64',
        fetcher=lambda _url: payload,
    )
    assert not info.update_available


@pytest.mark.parametrize(
    ('installed_version', 'tag_name'),
    (('0.1.0', 'latest'), ('development', 'v0.1.1')),
)
def test_update_check_wraps_malformed_versions(installed_version, tag_name):
    with pytest.raises(UpdateCheckError) as exc_info:
        check_for_updates(
            installed_version=installed_version,
            release_api_url='https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest',
            platform_tag='windows-x64',
            fetcher=lambda _url: {'tag_name': tag_name, 'assets': []},
        )
    message = str(exc_info.value)
    assert installed_version in message
    assert tag_name in message


def test_clean_settings_use_official_release_source_and_keep_overrides(
    tmp_path, monkeypatch
):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.settings = QSettings(
        str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat
    )
    monkeypatch.delenv(RELEASE_API_ENV, raising=False)
    assert window._release_api_url() == DEFAULT_RELEASE_API_URL

    configured = 'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/test'
    window.settings.setValue('updates/release_api_url', configured)
    assert window._release_api_url() == configured

    environment = 'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/env'
    monkeypatch.setenv(RELEASE_API_ENV, environment)
    assert window._release_api_url() == environment
    window.close()


def test_packaged_self_test_output_and_validator_contract(tmp_path):
    output = tmp_path / 'self-test.json'
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.update(
        {
            'NUMBA_CACHE_DIR': str(tmp_path / 'numba-cache'),
            'NUMBA_NUM_THREADS': '2',
            'NUMBA_THREADING_LAYER': 'workqueue',
            'QT_QPA_PLATFORM': 'offscreen',
        }
    )
    probe = (
        'import sys; '
        'from main import run_packaged_self_test; '
        'raise SystemExit(run_packaged_self_test('
        '["--self-test-output", sys.argv[1]]))'
    )
    completed = subprocess.run(
        [sys.executable, '-B', '-c', probe, str(output)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = load_and_validate_self_test(output)
    assert payload['status'] == 'ok'
    assert payload['time_shape'] == [101]
    assert payload['state_shape'] == [101, 3]
    assert payload['all_finite'] is True
    assert len(payload['result_sha256']) == 64
    assert payload['hafo_engine_available'] is True
    assert payload['hafo_bridge_status'] == 'ok'
    assert payload['hafo_bridge_time_shape'] == [6]
    assert payload['hafo_bridge_state_shape'] == [6, 2]
    assert payload['hafo_bridge_all_finite'] is True
    assert payload['hafo_bridge_use_acceleration'] is False
    assert len(payload['hafo_bridge_result_sha256']) == 64
    assert payload['hafo_modules_collected_as_source'] is True
    assert set(payload['hafo_module_origins']) == {
        'hidden_attractors',
        'hidden_attractors.systems',
        'hidden_attractors.simulation',
        'hidden_attractors.integrations.numba_kernels',
        'hidden_attractors.fractional.convolution_quadrature',
        'hidden_attractors.fractional.grunwald_letnikov',
    }
    assert all(
        origin.casefold().endswith('.py')
        for origin in payload['hafo_module_origins'].values()
    )
    assert set(payload['hafo_module_spec_origins']) == set(
        payload['hafo_module_origins']
    )
    assert all(
        origin.casefold().endswith('.py')
        for origin in payload['hafo_module_spec_origins'].values()
    )
    assert set(payload['hafo_module_loaders']) == set(payload['hafo_module_origins'])
    assert payload['hafo_gl_method'] == 'gl_direct_numba'
    assert payload['hafo_gl_numba_persistent_cache_enabled'] is True
    assert payload['hafo_gl_kernel_parallel_target'] is True
    assert payload['hafo_gl_kernel_compiled_signatures'] >= 1
    assert payload['hafo_gl_result_shape'] == [257, 16]
    assert payload['hafo_gl_all_finite'] is True
    assert len(payload['hafo_gl_result_sha256']) == 64
    assert payload['numba_cache_configured'] is True
    assert payload['numba_cache_outside_bundle'] is True
    assert Path(payload['numba_cache_dir']).is_absolute()
    assert payload['numba_cache_artifact_count'] >= 2
    assert len(payload['numba_cache_artifacts']) == payload['numba_cache_artifact_count']
    assert {
        Path(artifact['path']).suffix
        for artifact in payload['numba_cache_artifacts']
    } == {'.nbc', '.nbi'}
    assert payload['numba_threading_layer'] == 'workqueue'
    assert payload['numba_probe_scope'] == 'backend_only_not_hafo_gl_dispatch'
    assert payload['numba_kernel_method'] == 'packaged_parallel_probe_cache_false'
    assert payload['numba_kernel_cache_enabled'] is False
    assert payload['numba_kernel_parallel_target'] is True
    assert payload['numba_kernel_compiled_signatures'] >= 1
    assert payload['numba_result_shape'] == [257, 16]
    assert payload['numba_all_finite'] is True
    assert len(payload['numba_result_sha256']) == 64
    assert payload['numba_pool_module'] == 'numba.np.ufunc.workqueue'
    assert payload['numba_tbbpool_loaded'] is False

    invalid = dict(payload)
    invalid['result_sha256'] = '0' * 64
    with pytest.raises(SelfTestValidationError, match='all-zero'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['state_shape'] = [101, 2]
    with pytest.raises(SelfTestValidationError, match='state_shape'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_result_sha256'] = '0' * 64
    with pytest.raises(SelfTestValidationError, match='numba_result_sha256'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['hafo_bridge_state_shape'] = [5, 2]
    with pytest.raises(SelfTestValidationError, match='hafo_bridge_state_shape'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_probe_scope'] = 'hafo_gl_dispatch'
    with pytest.raises(SelfTestValidationError, match='scope'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['hafo_gl_numba_persistent_cache_enabled'] = False
    with pytest.raises(SelfTestValidationError, match='external cache'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_tbbpool_loaded'] = True
    with pytest.raises(SelfTestValidationError, match='TBB pool was loaded'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_threading_layer'] = 'omp'
    with pytest.raises(SelfTestValidationError, match='threading-layer mismatch'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_cache_outside_bundle'] = False
    with pytest.raises(SelfTestValidationError, match='cache is inside'):
        validate_self_test_payload(invalid)
    invalid = dict(payload)
    invalid['numba_cache_artifact_count'] = 0
    with pytest.raises(SelfTestValidationError, match='inventory is incomplete'):
        validate_self_test_payload(invalid)


@pytest.mark.parametrize('protected_area', ('internal', 'application'))
def test_numba_cache_rejects_frozen_application_paths(
    tmp_path, monkeypatch, protected_area
):
    from main import configure_numba_cache

    application = tmp_path / 'Chaos Toolbox'
    internal = application / '_internal'
    internal.mkdir(parents=True)
    target_root = internal if protected_area == 'internal' else application
    target = target_root / 'numba-cache'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(internal), raising=False)
    monkeypatch.setattr(sys, 'executable', str(application / 'Chaos Toolbox.exe'))
    monkeypatch.setenv('NUMBA_CACHE_DIR', str(target))

    with pytest.raises(RuntimeError, match='outside the frozen application'):
        configure_numba_cache()
    assert not target.exists()


def test_numba_cache_accepts_writable_path_outside_frozen_application(
    tmp_path, monkeypatch
):
    from main import configure_numba_cache

    application = tmp_path / 'install' / 'Chaos Toolbox'
    internal = application / '_internal'
    internal.mkdir(parents=True)
    target = tmp_path / 'user-data' / 'numba-cache'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(internal), raising=False)
    monkeypatch.setattr(sys, 'executable', str(application / 'Chaos Toolbox.exe'))
    monkeypatch.setenv('NUMBA_CACHE_DIR', str(target))

    assert configure_numba_cache() == target.resolve()
    assert target.is_dir()


def test_importing_entrypoint_does_not_initialize_numba():
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(root)
    completed = subprocess.run(
        [
            sys.executable,
            '-c',
            (
                "import sys; import main; "
                "assert 'numba' not in sys.modules, "
                "'main imported Numba before cache configuration'"
            ),
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_self_test_captures_protected_cache_failure(
    tmp_path, monkeypatch
):
    from main import run_packaged_self_test

    application = tmp_path / 'Chaos Toolbox'
    internal = application / '_internal'
    internal.mkdir(parents=True)
    target = application / 'numba-cache'
    output = tmp_path / 'self-test.json'
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(internal), raising=False)
    monkeypatch.setattr(sys, 'executable', str(application / 'Chaos Toolbox.exe'))
    monkeypatch.setenv('NUMBA_CACHE_DIR', str(target))

    assert run_packaged_self_test(['--self-test-output', str(output)]) == 1
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['status'] == 'failed'
    assert 'outside the frozen application' in payload['error']
    assert not target.exists()


def test_platform_build_scripts_gate_real_packaged_self_test():
    root = Path(__file__).resolve().parents[1]
    scripts = (
        root / 'packaging' / 'windows' / 'build.ps1',
        root / 'scripts' / 'build_macos.sh',
        root / 'scripts' / 'build_linux.sh',
    )
    for script in scripts:
        source = script.read_text(encoding='utf-8')
        assert '--self-test-output' in source, script
        assert 'validate_self_test_output.py' in source, script
    workflow = (root / '.github' / 'workflows' / 'release.yml').read_text(
        encoding='utf-8'
    )
    assert 'build/pyinstaller/*-self-test.json' in workflow


def test_windows_build_waits_for_isolated_packaged_self_test():
    root = Path(__file__).resolve().parents[1]
    source = (root / 'packaging' / 'windows' / 'build.ps1').read_text(
        encoding='utf-8'
    )

    assert 'windows-self-test-runtime' in source
    assert '$env:NUMBA_CACHE_DIR = $selfTestCache' in source
    assert '$env:TEMP = $selfTestTemp' in source
    assert '$env:TMP = $selfTestTemp' in source
    assert 'Start-Process -FilePath $exePath' in source
    assert '-PassThru -Wait -WindowStyle Hidden' in source
    assert '[Environment]::SetEnvironmentVariable(' in source
    assert '$pyInstallerWorkRoot = Join-Path $repoRoot "build\\pyinstaller"' in source
    assert (
        'New-Item -ItemType Directory -Force -Path $pyInstallerWorkRoot'
        in source
    )


def test_windows_native_build_uses_reproducible_pe_flags():
    root = Path(__file__).resolve().parents[1]
    sources = (
        root / 'core' / 'native.py',
        root / 'packaging' / 'windows' / 'build.ps1',
        root / '.github' / 'workflows' / 'ci.yml',
        root / 'benchmarks' / 'run_windows_common.ps1',
    )
    for flag in (
        '-frandom-seed=chaos-core-v2',
        '-Wl,--no-insert-timestamp,--image-base,0x180000000',
    ):
        for source in sources:
            assert flag in source.read_text(encoding='utf-8'), source


def test_official_builds_install_and_probe_qt_webengine():
    root = Path(__file__).resolve().parents[1]
    windows = (root / 'packaging' / 'windows' / 'build.ps1').read_text(
        encoding='utf-8'
    )
    assert '.[build,webengine]' in windows
    assert 'PySide6.QtWebEngineCore' in windows
    assert 'PySide6.QtWebEngineWidgets' in windows

    for relative_path in ('scripts/build_macos.sh', 'scripts/build_linux.sh'):
        source = (root / relative_path).read_text(encoding='utf-8')
        assert '.[build,webengine]' in source, relative_path
        assert 'PySide6.QtWebEngineCore' in source, relative_path
        assert 'PySide6.QtWebEngineWidgets' in source, relative_path

    release = (root / '.github' / 'workflows' / 'release.yml').read_text(
        encoding='utf-8'
    )
    assert '.[build,test,webengine]' in release
    requirements = (root / 'requirements-build.txt').read_text(encoding='utf-8')
    assert 'PySide6-Addons>=6.7' in requirements


def test_release_tag_gate_requires_exact_project_version_tag():
    assert verify_release_tag(f'v{APP_VERSION}', 'tag') == f'v{APP_VERSION}'
    with pytest.raises(ReleaseTagError, match='v9.9.9'):
        verify_release_tag('v9.9.9', 'tag')
    with pytest.raises(ReleaseTagError, match='tag'):
        verify_release_tag(f'v{APP_VERSION}', 'branch')


def test_release_workflow_builds_reproducible_python_distributions_after_tag_gate():
    root = Path(__file__).resolve().parents[1]
    source = (root / '.github' / 'workflows' / 'release.yml').read_text(
        encoding='utf-8'
    )
    assert source.count(
        'python -m build --no-isolation --sdist --wheel'
    ) == 2
    assert source.count('python scripts/normalize_python_sdist.py') == 2
    assert 'cmp -- "$artifact" "$counterpart"' in source
    assert source.count('python -m twine check') == 1
    assert source.count('name: Upload Python distributions and self-test evidence') == 1
    assert 'python scripts/verify_release_tag.py' in source
    assert '--ref-name "$RELEASE_REF_NAME"' in source
    assert '--ref-type "$RELEASE_REF_TYPE"' in source
    assert '"$probe_dir/bin/chaos-toolbox" --self-test-output' in source
    assert 'probe_distribution wheel "$wheel"' in source
    assert 'probe_distribution sdist "$sdist"' in source
    assert source.count('Build and probe installed wheel') == 0


def test_mainwindow_help_menu_contains_packaging_actions():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    help_act = next(act for act in window.menuBar().actions() if act.text() == 'Ayuda')
    actions = [
        action.text()
        for action in help_act.menu().actions()
        if action.text()
    ]
    assert 'Buscar actualizaciones' in actions
    assert 'Revisar actualizaciones automaticamente' in actions
    assert 'Acerca de' in actions
    window.deleteLater()
