from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.app_metadata import APP_DEVELOPER, APP_LICENSE, APP_VERSION
from core.paths import bundled_doc_path, sprott_asset_path


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
    pyproject = _read(ROOT / 'pyproject.toml')
    _check(f'version = "{APP_VERSION}"' in pyproject, 'pyproject.toml is not the version source of truth.')

    license_text = _read(ROOT / 'LICENSE')
    _check('MIT License' in license_text and 'Permission is hereby granted' in license_text, 'LICENSE is not MIT.')

    changelog = ROOT / 'CHANGELOG.md'
    _check(changelog.exists(), 'CHANGELOG.md is missing.')

    for doc in (
        'README.md',
        'docs/installation.md',
        'docs/packaging.md',
        'docs/updates.md',
        'docs/versioning.md',
        'docs/license.md',
        'docs/custom_systems_future.md',
    ):
        text = _read(ROOT / doc)
        _check(APP_VERSION in text, f'{doc} does not mention version {APP_VERSION}.')
        _check(APP_LICENSE in text, f'{doc} does not mention license {APP_LICENSE}.')
        _check(APP_DEVELOPER in text, f'{doc} does not mention developer {APP_DEVELOPER}.')
    custom_text = _read(ROOT / 'docs' / 'custom_systems_future.md')
    _check('does not implement' in custom_text, 'custom systems doc must not promise current support.')
    _check('.DIC' in custom_text and 'not redistributed' in custom_text, 'custom systems doc must preserve local .DIC exception.')

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
