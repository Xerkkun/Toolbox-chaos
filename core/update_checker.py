from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import tempfile
from threading import Event
from time import monotonic
from typing import Callable, Iterable
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request

from packaging.version import InvalidVersion, Version

from .url_security import build_validating_opener


MAX_RELEASE_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_CHECKSUM_MANIFEST_BYTES = 1024 * 1024
MAX_UPDATE_ASSET_BYTES = 1024 * 1024 * 1024
UPDATE_DOWNLOAD_DEADLINE_SECONDS = 20 * 60
ALLOWED_RELEASE_API_HOSTS = frozenset({'api.github.com'})
ALLOWED_RELEASE_LINK_HOSTS = frozenset({
    'github.com',
    'objects.githubusercontent.com',
    'github-releases.githubusercontent.com',
    'release-assets.githubusercontent.com',
})
CHECKSUM_ASSET_NAMES = (
    'SHA256SUMS',
    'SHA256SUMS.txt',
    'checksums.sha256',
    'checksums.txt',
)


class UpdateCheckError(RuntimeError):
    pass


class UpdateDownloadError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    browser_download_url: str
    size: int | None = None


@dataclass(frozen=True)
class UpdateInfo:
    installed_version: str
    latest_version: str
    published_at: str
    summary: str
    release_notes_url: str
    download_url: str | None
    asset_name: str | None
    asset_size: int | None
    checksum_url: str | None
    checksum_asset_name: str | None
    update_available: bool


@dataclass(frozen=True)
class VerifiedUpdate:
    version: str
    asset_name: str
    path: Path
    sha256: str
    size: int
    reused_existing_file: bool = False


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


def select_asset(
    assets: Iterable[ReleaseAsset],
    platform_tag: str | None = None,
    *,
    version: str | None = None,
) -> ReleaseAsset | None:
    tag = (platform_tag or current_platform_tag()).lower()
    candidates = list(assets)
    if version is not None:
        normalized_version = str(parse_semver(version))
        suffixes = {
            'windows': ('-setup.exe',),
            'macos': ('.dmg',),
            'linux': ('.deb',),
        }
        os_key = tag.split('-', 1)[0]
        platform_suffixes = suffixes.get(os_key, ())
        base = f'chaos-toolbox-v{normalized_version}-{tag}'
        expected_names = {
            f'{base}{suffix}'.lower() for suffix in platform_suffixes
        }
        matches = [
            asset for asset in candidates
            if asset.name.lower() in expected_names
        ]
        product_pattern = re.compile(
            rf'^chaos-toolbox-v.+-{re.escape(tag)}'
            rf'(?:{"|".join(re.escape(suffix) for suffix in platform_suffixes)})$',
            re.IGNORECASE,
        )
        mismatched = [
            asset.name for asset in candidates
            if product_pattern.fullmatch(asset.name)
            and asset.name.lower() not in expected_names
        ]
        if mismatched:
            raise UpdateCheckError(
                'El release contiene instaladores de otra versión para esta '
                f'plataforma: {sorted(mismatched)}.'
            )
        if len(matches) > 1:
            raise UpdateCheckError(
                'El release contiene varios instaladores candidatos para esta '
                f'plataforma: {sorted(asset.name for asset in matches)}.'
            )
        return matches[0] if matches else None

    os_key = tag.split('-', 1)[0]
    suffixes = {
        'windows': ('-setup.exe',),
        'macos': ('.dmg',),
        'linux': ('.deb',),
    }.get(os_key, ())
    if not suffixes:
        return None
    product_pattern = re.compile(
        rf'^chaos-toolbox-v[^/\\]+-{re.escape(tag)}'
        rf'(?:{"|".join(re.escape(suffix) for suffix in suffixes)})$',
        re.IGNORECASE,
    )
    matches = [
        asset for asset in candidates
        if product_pattern.fullmatch(asset.name)
    ]
    if len(matches) > 1:
        raise UpdateCheckError(
            'El release contiene varios instaladores candidatos para esta '
            f'plataforma: {sorted(asset.name for asset in matches)}.'
        )
    return matches[0] if matches else None


def select_checksum_asset(
    assets: Iterable[ReleaseAsset], selected_asset: ReleaseAsset | None
) -> ReleaseAsset | None:
    candidates = list(assets)
    by_lower_name = {asset.name.lower(): asset for asset in candidates}
    if selected_asset is not None:
        sidecar = by_lower_name.get(f'{selected_asset.name}.sha256'.lower())
        if sidecar is not None:
            return sidecar
    for name in CHECKSUM_ASSET_NAMES:
        candidate = by_lower_name.get(name.lower())
        if candidate is not None:
            return candidate
    return None


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


def validate_release_download_url(url: str) -> str:
    return _validated_https_url(
        url, ALLOWED_RELEASE_LINK_HOSTS, 'La URL de descarga'
    )


def _safe_asset_name(name: str) -> str:
    clean = str(name).strip()
    if (
        not clean
        or len(clean) > 512
        or clean in {'.', '..'}
        or '/' in clean
        or '\\' in clean
        or Path(clean).name != clean
    ):
        raise UpdateCheckError('El release contiene un nombre de artefacto no seguro.')
    return clean


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


def parse_sha256_manifest(
    manifest: str, asset_name: str, *, allow_bare_digest: bool = False
) -> str:
    text = str(manifest).lstrip('\ufeff').strip()
    if allow_bare_digest and re.fullmatch(r'[0-9a-fA-F]{64}', text):
        return text.lower()

    matches: list[str] = []
    gnu_pattern = re.compile(r'^([0-9a-fA-F]{64})[ \t]+[* ]?(.+?)\s*$')
    bsd_pattern = re.compile(r'^SHA256\s*\((.+)\)\s*=\s*([0-9a-fA-F]{64})$', re.I)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        digest = ''
        filename = ''
        gnu_match = gnu_pattern.match(line)
        if gnu_match:
            digest, filename = gnu_match.groups()
        else:
            bsd_match = bsd_pattern.match(line)
            if bsd_match:
                filename, digest = bsd_match.groups()
        filename = filename.strip()
        if filename.startswith('./'):
            filename = filename[2:]
        if filename == asset_name:
            matches.append(digest.lower())

    if not matches:
        raise UpdateDownloadError(
            f'El manifiesto SHA-256 no contiene una entrada para {asset_name}.'
        )
    if len(set(matches)) != 1:
        raise UpdateDownloadError(
            f'El manifiesto SHA-256 contiene entradas contradictorias para {asset_name}.'
        )
    return matches[0]


def file_sha256(path: Path) -> str:
    digest = sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_update_before_launch(verified: VerifiedUpdate) -> Path:
    installer = Path(verified.path).resolve()
    if not installer.is_file():
        raise UpdateDownloadError('El instalador verificado ya no existe.')
    try:
        size = installer.stat().st_size
        digest = file_sha256(installer)
    except OSError as exc:
        raise UpdateDownloadError(
            f'No se pudo volver a verificar el instalador antes de ejecutarlo: {exc}'
        ) from exc
    if size != verified.size or digest != verified.sha256:
        raise UpdateDownloadError(
            'El instalador cambió después de la descarga y no será ejecutado.'
        )
    return installer


def _response_content_length(response, *, maximum: int, label: str) -> int | None:
    raw_length = response.headers.get('Content-Length')
    if not raw_length:
        return None
    try:
        content_length = int(raw_length)
    except ValueError as exc:
        raise UpdateDownloadError(f'Content-Length de {label} no es válido.') from exc
    if content_length < 0 or content_length > maximum:
        raise UpdateDownloadError(f'{label} excede el límite permitido.')
    return content_length


def _default_manifest_fetcher(url: str) -> bytes:
    validated_url = validate_release_download_url(url)
    request = Request(
        validated_url,
        headers={
            'Accept': 'application/octet-stream',
            'User-Agent': 'ChaosToolboxUpdater',
        },
    )
    opener = build_validating_opener(validate_release_download_url)
    with opener.open(request, timeout=15) as response:
        validate_release_download_url(response.geturl())
        _response_content_length(
            response,
            maximum=MAX_CHECKSUM_MANIFEST_BYTES,
            label='el manifiesto SHA-256',
        )
        payload = response.read(MAX_CHECKSUM_MANIFEST_BYTES + 1)
        if len(payload) > MAX_CHECKSUM_MANIFEST_BYTES:
            raise UpdateDownloadError('El manifiesto SHA-256 excede 1 MiB.')
        return payload


def _ensure_download_active(
    cancel_event: Event | None, deadline: float
) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise UpdateDownloadError('La descarga fue cancelada.')
    if monotonic() >= deadline:
        raise UpdateDownloadError(
            'La descarga excedió el tiempo total permitido.'
        )


def _default_asset_downloader(
    url: str,
    destination: Path,
    maximum: int,
    cancel_event: Event | None,
    deadline: float,
) -> int:
    _ensure_download_active(cancel_event, deadline)
    validated_url = validate_release_download_url(url)
    request = Request(
        validated_url,
        headers={
            'Accept': 'application/octet-stream',
            'User-Agent': 'ChaosToolboxUpdater',
        },
    )
    opener = build_validating_opener(validate_release_download_url)
    total = 0
    with opener.open(request, timeout=30) as response, Path(destination).open('wb') as handle:
        validate_release_download_url(response.geturl())
        _response_content_length(
            response, maximum=maximum, label='el instalador'
        )
        while True:
            _ensure_download_active(cancel_event, deadline)
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise UpdateDownloadError('El instalador excede el límite permitido.')
            handle.write(chunk)
        handle.flush()
        os.fsync(handle.fileno())
    _ensure_download_active(cancel_event, deadline)
    return total


def download_verified_update(
    *,
    info: UpdateInfo,
    destination_dir: Path,
    manifest_fetcher: Callable[[str], bytes] | None = None,
    asset_downloader: Callable[[str, Path, int, Event | None, float], int] | None = None,
    cancel_event: Event | None = None,
    deadline_seconds: float = UPDATE_DOWNLOAD_DEADLINE_SECONDS,
) -> VerifiedUpdate:
    if not info.update_available:
        raise UpdateDownloadError('No hay una versión nueva para descargar.')
    if not info.download_url or not info.asset_name:
        raise UpdateDownloadError(
            'El release no contiene un instalador para esta plataforma.'
        )
    if not info.checksum_url or not info.checksum_asset_name:
        raise UpdateDownloadError(
            'El release no contiene SHA256SUMS ni un checksum lateral del instalador.'
        )
    if info.asset_size is not None and (
        info.asset_size <= 0 or info.asset_size > MAX_UPDATE_ASSET_BYTES
    ):
        raise UpdateDownloadError('El tamaño publicado del instalador no es válido.')
    if deadline_seconds <= 0:
        raise UpdateDownloadError('El tiempo total permitido para la descarga no es válido.')

    deadline = monotonic() + float(deadline_seconds)
    _ensure_download_active(cancel_event, deadline)
    try:
        validate_release_download_url(info.download_url)
        validate_release_download_url(info.checksum_url)
    except UpdateCheckError as exc:
        raise UpdateDownloadError(str(exc)) from exc

    allow_bare = info.checksum_asset_name.lower() == f'{info.asset_name}.sha256'.lower()
    try:
        raw_manifest = (manifest_fetcher or _default_manifest_fetcher)(info.checksum_url)
        manifest = raw_manifest.decode('utf-8-sig')
    except UpdateDownloadError:
        raise
    except (OSError, URLError, TimeoutError, UnicodeError) as exc:
        raise UpdateDownloadError(
            f'No se pudo descargar el manifiesto SHA-256: {exc}'
        ) from exc
    expected_digest = parse_sha256_manifest(
        manifest, info.asset_name, allow_bare_digest=allow_bare
    )
    try:
        destination = Path(destination_dir).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        target = (destination / info.asset_name).resolve()
        if target.parent != destination:
            raise UpdateDownloadError('La ruta local del instalador no es segura.')
        if target.is_file():
            existing_digest = file_sha256(target)
            if existing_digest == expected_digest:
                size = target.stat().st_size
                if info.asset_size is None or size == info.asset_size:
                    return VerifiedUpdate(
                        version=info.latest_version,
                        asset_name=info.asset_name,
                        path=target,
                        sha256=existing_digest,
                        size=size,
                        reused_existing_file=True,
                    )

        _ensure_download_active(cancel_event, deadline)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f'.{info.asset_name}.', suffix='.part', dir=destination
        )
        os.close(file_descriptor)
        temporary = Path(temporary_name)
        try:
            try:
                downloaded_size = (asset_downloader or _default_asset_downloader)(
                    info.download_url,
                    temporary,
                    MAX_UPDATE_ASSET_BYTES,
                    cancel_event,
                    deadline,
                )
            except UpdateDownloadError:
                raise
            except (OSError, URLError, TimeoutError) as exc:
                raise UpdateDownloadError(
                    f'No se pudo descargar el instalador: {exc}'
                ) from exc
            _ensure_download_active(cancel_event, deadline)
            if not temporary.is_file():
                raise UpdateDownloadError('La descarga no produjo un archivo local.')
            actual_size = temporary.stat().st_size
            if downloaded_size != actual_size:
                raise UpdateDownloadError(
                    'El tamaño escrito del instalador es inconsistente.'
                )
            if info.asset_size is not None and actual_size != info.asset_size:
                raise UpdateDownloadError(
                    'El tamaño descargado no coincide con el tamaño publicado en GitHub.'
                )
            actual_digest = file_sha256(temporary)
            if actual_digest != expected_digest:
                raise UpdateDownloadError(
                    'La verificación SHA-256 falló; el instalador descargado fue descartado.'
                )
            _ensure_download_active(cancel_event, deadline)
            os.replace(temporary, target)
            return VerifiedUpdate(
                version=info.latest_version,
                asset_name=info.asset_name,
                path=target,
                sha256=actual_digest,
                size=actual_size,
            )
        finally:
            temporary.unlink(missing_ok=True)
    except UpdateDownloadError:
        raise
    except OSError as exc:
        raise UpdateDownloadError(
            f'No se pudo preparar o guardar el instalador: {exc}'
        ) from exc


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

    if payload.get('draft'):
        raise UpdateCheckError('La fuente devolvió un release en borrador, no uno estable.')
    if payload.get('prerelease'):
        raise UpdateCheckError('La fuente devolvió un prerelease, no una versión estable.')

    latest = str(payload.get('tag_name') or payload.get('name') or '').strip()
    if not latest:
        raise UpdateCheckError('La respuesta de releases no contiene tag_name.')
    try:
        parsed_latest = parse_semver(latest)
        if parsed_latest.is_prerelease or parsed_latest.is_devrelease:
            raise UpdateCheckError(
                f'La fuente devolvió la versión preliminar {latest!r}, no una versión estable.'
            )
        update_available = parsed_latest > parse_semver(installed_version)
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
        asset_name = _safe_asset_name(str(item['name']))
        download_url = _validated_https_url(
            str(item['browser_download_url']),
            ALLOWED_RELEASE_LINK_HOSTS,
            'La URL de descarga',
        )
        raw_size = item.get('size')
        asset_size = None
        if raw_size is not None:
            try:
                asset_size = int(raw_size)
            except (TypeError, ValueError) as exc:
                raise UpdateCheckError(
                    f'El tamaño publicado de {asset_name} no es válido.'
                ) from exc
            if asset_size < 0:
                raise UpdateCheckError(
                    f'El tamaño publicado de {asset_name} no es válido.'
                )
        assets.append(ReleaseAsset(asset_name, download_url, asset_size))
    selected = select_asset(
        assets, platform_tag, version=latest.lstrip('v')
    )
    checksum_asset = select_checksum_asset(assets, selected)
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
        asset_size=selected.size if selected else None,
        checksum_url=(
            checksum_asset.browser_download_url if checksum_asset else None
        ),
        checksum_asset_name=checksum_asset.name if checksum_asset else None,
        update_available=update_available,
    )
