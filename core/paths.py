from __future__ import annotations

from pathlib import Path
import os
import sys

from core.app_metadata import APP_NAME


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def app_base_dirs() -> list[Path]:
    roots: list[Path] = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            roots.append(Path(meipass))
        roots.append(Path(sys.executable).resolve().parent)
    roots.append(repo_root())
    installed_resources = Path(sys.prefix) / 'share' / 'chaos-toolbox'
    if installed_resources not in roots:
        roots.append(installed_resources)
    return roots


def resource_path(*parts: str) -> Path:
    relative = Path(*parts)
    for base in app_base_dirs():
        candidate = base / relative
        if candidate.exists():
            return candidate
    return app_base_dirs()[0] / relative


def bundled_docs_dir() -> Path:
    return resource_path('resources', 'bundled', 'docs')


def bundled_doc_path(filename: str) -> Path:
    candidates = [
        resource_path('resources', 'bundled', 'docs', filename),
        resource_path('assets', filename),
        resource_path('assets', 'sprott', filename),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def sprott_assets_dir() -> Path:
    bundled = resource_path('resources', 'bundled', 'sprott')
    if bundled.exists():
        return bundled
    return resource_path('assets', 'sprott')


def sprott_asset_path(*parts: str) -> Path:
    return sprott_assets_dir().joinpath(*parts)


def user_data_dir() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
        return base / APP_NAME
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / APP_NAME
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share') / 'chaos-toolbox'


def ensure_user_data_dir() -> Path:
    target = user_data_dir()
    target.mkdir(parents=True, exist_ok=True)
    return target
