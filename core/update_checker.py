from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import platform
from typing import Callable, Iterable
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request

from packaging.version import InvalidVersion, Version

from .url_security import build_validating_opener


MAX_RELEASE_RESPONSE_BYTES = 2 * 1024 * 1024
ALLOWED_RELEASE_API_HOSTS = frozenset({'api.github.com'})
ALLOWED_RELEASE_LINK_HOSTS = frozenset({
    'github.com',
    'objects.githubusercontent.com',
    'github-releases.githubusercontent.com',
})


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


def parse_semver(version: str) -> Version:
    raw = str(version).strip()
    if raw[:1].lower() == 'v':
        raw = raw[1:]
    try:
        parsed = Version(raw)
    except InvalidVersion as exc:
        raise ValueError(f'Invalid semantic version: {version!r}') from exc
    if parsed.epoch != 0 or len(parsed.release) != 3:
        raise ValueError(f'Invalid semantic version: {version!r}')
    return parsed


def is_newer_version(remote: str, installed: str) -> bool:
    return parse_semver(remote) > parse_semver(installed)


def current_platform_tag() -> str:
    machine = platform.machine().lower()
    if machine in {'x86_64', 'amd64'}:
        arch = 'x64'
    elif machine in {'arm64', 'aarch64'}:
        arch = 'arm64'
    else:
        raise UpdateCheckError(
            f'Arquitectura no soportada por el actualizador: {machine or "desconocida"}.'
        )
    system = platform.system().lower()
    if system == 'darwin':
        return f'macos-{arch}'
    if system == 'windows':
        return f'windows-{arch}'
    if system == 'linux':
        return f'linux-{arch}'
    raise UpdateCheckError(
        f'Sistema operativo no soportado por el actualizador: {system or "desconocido"}.'
    )


def select_asset(assets: Iterable[ReleaseAsset], platform_tag: str | None = None) -> ReleaseAsset | None:
    tag = (platform_tag or current_platform_tag()).lower()
    preferred_extensions = {
        'windows': ('.exe', '.msi', '.zip'),
        'macos': ('.dmg', '.pkg', '.zip'),
        'linux': ('.deb', '.rpm', '.appimage', '.tar.gz'),
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


def _validated_https_url(url: str, allowed_hosts: frozenset[str], label: str) -> str:
    parsed = urlsplit(str(url).strip())
    host = (parsed.hostname or '').lower()
    if parsed.scheme.lower() != 'https' or host not in allowed_hosts:
        raise UpdateCheckError(
            f'{label} debe usar HTTPS en un host autorizado: {sorted(allowed_hosts)}.'
        )
    try:
        port = parsed.port
    except ValueError as exc:
        raise UpdateCheckError(f'{label} contiene un puerto no válido.') from exc
    if parsed.username or parsed.password or port not in {None, 443}:
        raise UpdateCheckError(f'{label} contiene credenciales o un puerto no autorizado.')
    return parsed.geturl()


def validate_release_api_url(url: str) -> str:
    return _validated_https_url(url, ALLOWED_RELEASE_API_HOSTS, 'La fuente de releases')


def _default_fetcher(url: str) -> dict:
    validated_url = validate_release_api_url(url)
    request = Request(validated_url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'ChaosToolboxUpdater'})
    opener = build_validating_opener(validate_release_api_url)
    with opener.open(request, timeout=8) as response:
        _validated_https_url(response.geturl(), ALLOWED_RELEASE_API_HOSTS, 'La respuesta de releases')
        raw_length = response.headers.get('Content-Length')
        if raw_length:
            try:
                if int(raw_length) > MAX_RELEASE_RESPONSE_BYTES:
                    raise UpdateCheckError('La respuesta de releases excede 2 MiB.')
            except ValueError as exc:
                raise UpdateCheckError('Content-Length de releases no es válido.') from exc
        raw = response.read(MAX_RELEASE_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RELEASE_RESPONSE_BYTES:
            raise UpdateCheckError('La respuesta de releases excede 2 MiB.')
        payload = json.loads(raw.decode('utf-8'))
        if not isinstance(payload, dict):
            raise UpdateCheckError('La respuesta de releases debe ser un objeto JSON.')
        return payload


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
    release_api_url = validate_release_api_url(release_api_url)
    try:
        payload = (fetcher or _default_fetcher)(release_api_url)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError, UnicodeError) as exc:
        raise UpdateCheckError(f'No se pudo consultar la fuente de actualizaciones: {exc}') from exc
    if not isinstance(payload, dict):
        raise UpdateCheckError('La respuesta de releases debe ser un objeto JSON.')

    latest = str(payload.get('tag_name') or payload.get('name') or '').strip()
    if not latest:
        raise UpdateCheckError('La respuesta de releases no contiene tag_name.')
    try:
        update_available = is_newer_version(latest, installed_version)
    except (ValueError, InvalidVersion) as exc:
        raise UpdateCheckError(
            'No se pudo comparar la versión publicada '
            f'{latest!r} con la versión instalada {installed_version!r}: {exc}'
        ) from exc
    published_at = str(payload.get('published_at') or payload.get('created_at') or '')
    if published_at:
        try:
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date().isoformat()
        except ValueError:
            pass
    raw_assets = payload.get('assets', [])
    if not isinstance(raw_assets, list):
        raise UpdateCheckError('assets debe ser una lista.')
    assets = []
    for item in raw_assets[:256]:
        if not isinstance(item, dict) or not item.get('name') or not item.get('browser_download_url'):
            continue
        download_url = _validated_https_url(
            str(item['browser_download_url']),
            ALLOWED_RELEASE_LINK_HOSTS,
            'La URL de descarga',
        )
        assets.append(ReleaseAsset(str(item['name'])[:512], download_url))
    selected = select_asset(assets, platform_tag)
    release_notes_url = str(payload.get('html_url') or '')
    if release_notes_url:
        release_notes_url = _validated_https_url(
            release_notes_url, ALLOWED_RELEASE_LINK_HOSTS, 'La URL de notas'
        )
    return UpdateInfo(
        installed_version=installed_version,
        latest_version=latest.lstrip('v'),
        published_at=published_at or 'fecha no publicada',
        summary=_summarize_release(str(payload.get('body') or '')),
        release_notes_url=release_notes_url,
        download_url=selected.browser_download_url if selected else None,
        asset_name=selected.name if selected else None,
        update_available=update_available,
    )
