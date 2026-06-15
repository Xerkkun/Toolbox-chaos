from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import platform
import re
from typing import Callable, Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen


SEMVER_RE = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$')


class UpdateCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    browser_download_url: str


@dataclass(frozen=True)
class UpdateInfo:
    installed_version: str
    latest_version: str
    published_at: str
    summary: str
    release_notes_url: str
    download_url: str | None
    asset_name: str | None
    update_available: bool


def parse_semver(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise ValueError(f'Invalid semantic version: {version!r}')
    return tuple(int(part) for part in match.groups())


def is_newer_version(remote: str, installed: str) -> bool:
    return parse_semver(remote) > parse_semver(installed)


def current_platform_tag() -> str:
    machine = platform.machine().lower()
    arch = 'arm64' if machine in {'arm64', 'aarch64'} else 'x64'
    system = platform.system().lower()
    if system == 'darwin':
        return f'macos-{arch}'
    if system == 'windows':
        return f'windows-{arch}'
    return f'linux-{arch}'


def select_asset(assets: Iterable[ReleaseAsset], platform_tag: str | None = None) -> ReleaseAsset | None:
    tag = (platform_tag or current_platform_tag()).lower()
    preferred_extensions = {
        'windows': ('.exe', '.msi', '.zip'),
        'macos': ('.dmg', '.pkg', '.zip'),
        'linux': ('.appimage', '.deb', '.rpm', '.tar.gz'),
    }
    os_key = tag.split('-', 1)[0]
    extensions = preferred_extensions.get(os_key, ())
    matches = [
        asset for asset in assets
        if tag in asset.name.lower()
    ]
    for ext in extensions:
        for asset in matches:
            if asset.name.lower().endswith(ext):
                return asset
    return matches[0] if matches else None


def _default_fetcher(url: str) -> dict:
    request = Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'ChaosToolboxUpdater'})
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode('utf-8'))


def _summarize_release(body: str, limit: int = 320) -> str:
    text = ' '.join((body or '').split())
    if not text:
        return 'Sin resumen de cambios publicado.'
    return text[:limit - 1] + '...' if len(text) > limit else text


def check_for_updates(
    *,
    installed_version: str,
    release_api_url: str,
    platform_tag: str | None = None,
    fetcher: Callable[[str], dict] | None = None,
) -> UpdateInfo:
    if not release_api_url:
        raise UpdateCheckError('No hay una fuente de releases configurada.')
    try:
        payload = (fetcher or _default_fetcher)(release_api_url)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise UpdateCheckError(f'No se pudo consultar la fuente de actualizaciones: {exc}') from exc

    latest = str(payload.get('tag_name') or payload.get('name') or '').strip()
    if not latest:
        raise UpdateCheckError('La respuesta de releases no contiene tag_name.')
    published_at = str(payload.get('published_at') or payload.get('created_at') or '')
    if published_at:
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date().isoformat()
        except ValueError:
            pass
    assets = [
        ReleaseAsset(name=str(item.get('name', '')), browser_download_url=str(item.get('browser_download_url', '')))
        for item in payload.get('assets', [])
        if item.get('name') and item.get('browser_download_url')
    ]
    selected = select_asset(assets, platform_tag)
    update_available = is_newer_version(latest, installed_version)
    return UpdateInfo(
        installed_version=installed_version,
        latest_version=latest.lstrip('v'),
        published_at=published_at or 'fecha no publicada',
        summary=_summarize_release(str(payload.get('body') or '')),
        release_notes_url=str(payload.get('html_url') or ''),
        download_url=selected.browser_download_url if selected else None,
        asset_name=selected.name if selected else None,
        update_available=update_available,
    )
