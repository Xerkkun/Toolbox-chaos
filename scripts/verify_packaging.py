from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.app_metadata import APP_DEVELOPER, APP_LICENSE, APP_VERSION
from core.paths import bundled_doc_path, sprott_asset_path
from scripts.verify_distribution_compliance import verify_source_contract


FORBIDDEN_BUNDLE_PATTERNS = (
    '*.tex', '*.aux', '*.log', '*.out', '*.toc', '*.bbl', '*.blg',
    '*.fls', '*.fdb_latexmk', '*.synctex.gz',
)


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def verify() -> None:
    verify_source_contract()
    pyproject_text = _read(ROOT / 'pyproject.toml')
    pyproject = tomllib.loads(pyproject_text)
    project = pyproject.get('project', {})
    _check(project.get('version') == APP_VERSION, 'pyproject.toml is not the version source of truth.')
    _check(project.get('license') == APP_LICENSE, 'pyproject.toml does not declare the MIT SPDX license.')
    _check(
        set(project.get('license-files', []))
        == {'LICENSE', 'NOTICE.md', 'THIRD_PARTY_NOTICES.md', 'LICENSES/*.txt'},
        'pyproject.toml does not declare the reviewed PEP 639 license files.',
    )
    authors = [item.get('name') for item in project.get('authors', [])]
    _check(APP_DEVELOPER in authors, 'pyproject.toml does not declare the application developer.')
    _check(project.get('requires-python') == '>=3.11', 'Toolbox Chaos must require Python >=3.11, matching HAFO 1.1.')
    dependencies = project.get('dependencies', [])
    _check('hidden-attractors-fo>=1.1,<2' in dependencies, 'HAFO must be a normal, bounded runtime dependency.')
    _check(project.get('gui-scripts', {}).get('chaos-toolbox') == 'main:main_entry', 'The installable GUI entry point is missing.')
    setuptools = pyproject.get('tool', {}).get('setuptools', {})
    _check(
        'license-files' not in setuptools,
        'Legacy tool.setuptools.license-files shadows PEP 639 metadata.',
    )
    _check(setuptools.get('py-modules') == ['main'], 'The main module is not packaged explicitly.')
    _check('share/chaos-toolbox/docs' in setuptools.get('data-files', {}), 'Operational documentation is not installed by the wheel.')
    _check('share/chaos-toolbox/resources/bundled/docs' in setuptools.get('data-files', {}), 'Bundled runtime data is not installed by the wheel.')
    package_data = setuptools.get('package-data', {}).get('core', [])
    _check('csrc/*.def' in package_data, 'The canonical Python/C system-ID table is not packaged.')

    license_text = _read(ROOT / 'LICENSE')
    _check('MIT License' in license_text and 'Permission is hereby granted' in license_text, 'LICENSE is not MIT.')

    changelog = ROOT / 'CHANGELOG.md'
    _check(changelog.exists(), 'CHANGELOG.md is missing.')

    custom_text = _read(ROOT / 'docs' / 'custom_systems.md')
    _check('editor' in custom_text.lower() and 'Hidden Attractors FO' in custom_text, 'The custom-system guide does not describe the current editor contract.')

    hidden_bridge = _read(ROOT / 'core' / 'hidden_engine.py')
    _check('_development_candidates' not in hidden_bridge, 'The HAFO bridge still searches sibling checkouts.')
    _check('sys.path.insert' not in hidden_bridge, 'The HAFO bridge mutates sys.path.')
    _check('hidden-attractors-fo' in hidden_bridge and '>=1.1,<2' in hidden_bridge, 'The HAFO bridge does not enforce the declared compatibility range.')

    paths_source = _read(ROOT / 'core' / 'paths.py')
    _check("'share' / 'chaos-toolbox'" in paths_source, 'Installed-wheel resource lookup is missing.')

    spec_text = _read(ROOT / 'packaging' / 'pyinstaller' / 'chaos_toolbox.spec')
    _check(
        "collect_data_files('hidden_attractors')" in spec_text
        and "collect_dynamic_libs('hidden_attractors')" in spec_text,
        'PyInstaller does not collect the supported HAFO package surface.',
    )
    _check(
        "collect_all('hidden_attractors')" not in spec_text
        and 'hidden_attractors.validation' not in spec_text,
        'PyInstaller still scans unsupported HAFO submodules.',
    )
    _check(
        "copy_metadata('chaos-toolbox', recursive=True)" in spec_text
        and "copy_metadata('PySide6-Addons', recursive=True)" in spec_text,
        'PyInstaller does not collect the recursive runtime metadata closure.',
    )
    _check(
        'validate_precompiled_library(native_library)' in spec_text,
        'PyInstaller does not validate the precompiled native backend.',
    )
    _check(
        "'pyqtgraph.opengl'" in spec_text
        and "'numba.np.ufunc.tbbpool'" in spec_text,
        'PyInstaller does not exclude unused pyqtgraph/Numba surfaces.',
    )
    _check("'system_ids.def'" in spec_text, 'PyInstaller does not collect the canonical system-ID table.')
    _check("'THIRD_PARTY_NOTICES.md'" in spec_text, 'PyInstaller omits third-party notices.')
    _check("'LGPL-3.0-only.txt'" in spec_text and "'GPL-3.0-only.txt'" in spec_text, 'PyInstaller omits LGPL/GPL license texts.')

    release_gate = _read(ROOT / 'scripts' / 'verify_hafo_release.py')
    _check('hidden-attractors-fo' in release_gate and "Version('1.1')" in release_gate, 'The HAFO public-release gate is missing or incompatible.')

    for doc_name in ('chaos_dictionary.pdf', 'sprott_theory.pdf', 'sprott_explorer_guide.pdf'):
        _check(bundled_doc_path(doc_name).exists(), f'Bundled PDF missing: {doc_name}')
    _check(sprott_asset_path('examples', 'synthetic_examples.json').exists(), 'Bundled Sprott examples missing.')

    bundle = ROOT / 'resources' / 'bundled'
    _check(bundle.exists(), 'resources/bundled was not prepared.')
    forbidden = []
    for pattern in FORBIDDEN_BUNDLE_PATTERNS:
        forbidden.extend(bundle.rglob(pattern))
    _check(not forbidden, f'Forbidden source files found in runtime bundle: {forbidden}')

    scripts = [
        ROOT / 'packaging' / 'windows' / 'build.ps1',
        ROOT / 'scripts' / 'build_windows.ps1',
        ROOT / 'scripts' / 'build_windows_installer.ps1',
        ROOT / 'scripts' / 'build_macos.sh',
        ROOT / 'scripts' / 'build_linux.sh',
        ROOT / 'scripts' / 'package_all.ps1',
        ROOT / 'scripts' / 'prepare_runtime_resources.py',
        ROOT / 'scripts' / 'bundle_size_report.py',
    ]
    for script in scripts:
        _check(script.exists(), f'Documented build command is missing: {script}')
    for build_script in (
        ROOT / 'packaging' / 'windows' / 'build.ps1',
        ROOT / 'scripts' / 'build_macos.sh',
        ROOT / 'scripts' / 'build_linux.sh',
    ):
        _check(
            'validate_precompiled_library(sys.argv[1])' in _read(build_script),
            f'Build does not explicitly validate its precompiled native library: {build_script}',
        )
    installer_builder = _read(ROOT / 'scripts' / 'build_windows_installer.ps1')
    _check(
        'Get-FreeSubstDrive' in installer_builder
        and 'Invoke-InnoCompiler' in installer_builder
        and 'subst.exe $substDrive /D' in installer_builder,
        'Windows installer build lacks automatic long-path shortening and cleanup.',
    )

    scan_targets = [
        ROOT / 'packaging',
        ROOT / 'scripts',
        ROOT / 'resources',
        ROOT / 'core' / 'app_metadata.py',
        ROOT / 'core' / 'paths.py',
    ]
    win_users_prefix = 'C:' + '\\' + 'Users' + '\\'
    linux_home_prefix = '/' + 'home' + '/'
    mac_users_prefix = '/' + 'Users' + '/'
    absolute_user_path = re.compile(
        re.escape(win_users_prefix) + r'[^\\\s]+|'
        + re.escape(linux_home_prefix) + r'[^/\s]+|'
        + re.escape(mac_users_prefix) + r'[^/\s]+'
    )
    offenders = []
    for target in scan_targets:
        paths = [target] if target.is_file() else [
            path for path in target.rglob('*')
            if path.is_file() and '__pycache__' not in path.parts
        ]
        for path in paths:
            if path.suffix.lower() in {'.pdf', '.png', '.dll', '.exe', '.pyc'}:
                continue
            text = path.read_text(encoding='utf-8', errors='ignore')
            if absolute_user_path.search(text):
                offenders.append(path)
    _check(not offenders, f'Absolute development paths found in packaging/runtime files: {offenders}')


def main() -> int:
    verify()
    print('Packaging verification OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
