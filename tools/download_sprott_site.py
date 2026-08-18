#!/usr/bin/env python3
"""
Download and organize downloadable material from Sprott's website.

Purpose:
    Local research archive for studying J. C. Sprott's publicly linked material.

Default behavior:
    - Starts at https://sprott.physics.wisc.edu/
    - Crawls same-domain HTML pages.
    - Downloads linked non-HTML files.
    - Preserves remote path structure locally.
    - Writes manifest CSV and JSONL.
    - Respects robots.txt when available.
    - Uses a delay between requests.

Important:
    Do not commit downloaded files to this repository unless you have permission
    and the licensing terms are compatible with your project.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any


DEFAULT_START_URL = "https://sprott.physics.wisc.edu/"
ALLOWED_SITE_HOSTS = frozenset({'sprott.physics.wisc.edu'})
DEFAULT_MAX_PAGE_BYTES = 4 * 1024 * 1024
DEFAULT_MAX_FILE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 8 * 1024 * 1024 * 1024
DEFAULT_MANIFEST_CHECKPOINT_EVERY = 50
HARD_MAX_RESPONSE_BYTES = 1024 * 1024 * 1024
HARD_MAX_TOTAL_BYTES = 1024 * HARD_MAX_RESPONSE_BYTES
ROBOTS_MAX_RESPONSE_BYTES = 1024 * 1024
MANIFEST_MAX_BYTES = 16 * 1024 * 1024
MANIFEST_MAX_ROWS = 100_000
STREAM_CHUNK_BYTES = 1024 * 1024
ACCOUNTED_MANIFEST_STATUSES = frozenset(
    {'downloaded', 'skipped_exists', 'page_saved', 'page_asset_parse_error'}
)


class DownloadBudgetExceeded(RuntimeError):
    """The configured aggregate archive budget has been exhausted."""


class RobotsPolicyError(RuntimeError):
    """robots.txt could not be verified, so crawling must stop fail-closed."""


class ValidatingSiteRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Validate a redirect target before urllib sends the next request."""

    def __init__(self, allowed_netloc: str):
        super().__init__()
        self.allowed_netloc = allowed_netloc

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = validate_site_url(urllib.parse.urljoin(req.full_url, newurl))
        if not same_site(target, self.allowed_netloc):
            raise ValueError(f'La redirección salió del sitio autorizado: {target}')
        return super().redirect_request(req, fp, code, msg, headers, target)

HTML_EXTENSIONS = {
    "",
    ".html",
    ".htm",
    ".shtml",
    ".asp",
    ".aspx",
    ".php",
    ".cgi",
}

DOWNLOAD_EXTENSIONS = {
    ".zip",
    ".gz",
    ".tgz",
    ".tar",
    ".rar",
    ".7z",
    ".bz2",
    ".exe",
    ".dll",
    ".com",
    ".bat",
    ".sys",
    ".msi",
    ".bas",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".f",
    ".for",
    ".f90",
    ".py",
    ".m",
    ".java",
    ".js",
    ".vb",
    ".vbs",
    ".pl",
    ".sh",
    ".dic",
    ".mrg",
    ".mac",
    ".dat",
    ".txt",
    ".csv",
    ".tsv",
    ".ini",
    ".cfg",
    ".json",
    ".xml",
    ".pdf",
    ".doc",
    ".docx",
    ".rtf",
    ".ps",
    ".eps",
    ".tex",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
    ".svg",
    ".webp",
    ".mid",
    ".midi",
    ".mp3",
    ".wav",
    ".au",
    ".aif",
    ".aiff",
    ".ogg",
    ".flac",
    ".mp4",
    ".mpg",
    ".mpeg",
    ".avi",
    ".mov",
    ".wmv",
    ".webm",
    ".m4v",
}

IMAGE_EXTENSIONS = {
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".ico",
    ".svg",
    ".webp",
}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value for key, value in attrs if value}
        for key in ("href", "src"):
            value = attrs_dict.get(key)
            if value:
                self.links.append(value)


@dataclass
class DownloadRecord:
    url: str
    local_path: str
    status: str
    http_status: int | None
    content_type: str | None
    size_bytes: int
    sha256: str | None
    error: str | None


def normalize_url(base_url: str, link: str) -> str | None:
    link = link.strip()
    if not link:
        return None

    lowered = link.lower()
    if lowered.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    absolute = urllib.parse.urljoin(base_url, link)
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None

    parsed = parsed._replace(fragment="")
    return urllib.parse.urlunparse(parsed)


def same_site(url: str, allowed_netloc: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower() == allowed_netloc.lower()


def validate_site_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url).strip())
    hostname = (parsed.hostname or '').lower()
    if parsed.scheme.lower() != 'https' or hostname not in ALLOWED_SITE_HOSTS:
        raise ValueError(
            f'La URL sólo puede usar HTTPS en {sorted(ALLOWED_SITE_HOSTS)}: {url}'
        )
    if parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise ValueError('La URL contiene credenciales o un puerto no autorizado.')
    return urllib.parse.urlunparse(parsed)


def under_path_prefix(url: str, path_prefix: str) -> bool:
    path = urllib.parse.urlparse(url).path
    return path.startswith(path_prefix)


def extension_from_url(url: str) -> str:
    return Path(urllib.parse.urlparse(url).path).suffix.lower()


def looks_like_html(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return extension_from_url(url) in HTML_EXTENSIONS or parsed.path.endswith("/")


def looks_downloadable(
    url: str,
    download_unknown: bool = False,
    include_extensions: set[str] | None = None,
    exclude_extensions: set[str] | None = None,
) -> bool:
    ext = extension_from_url(url)
    if include_extensions is not None:
        return ext in include_extensions
    if exclude_extensions is not None and ext in exclude_extensions:
        return False
    if ext in DOWNLOAD_EXTENSIONS:
        return True
    if ext in HTML_EXTENSIONS:
        return False
    return download_unknown


def parse_extension_list(value: str | None) -> set[str] | None:
    if value is None:
        return None

    out: set[str] = set()
    for item in value.split(","):
        ext = item.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        out.add(ext)
    return out


def safe_local_path(output_dir: Path, url: str, subdir: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path).replace('\\', '/')
    if not path or path.endswith("/"):
        path = path + "index.html"
    raw_parts = PurePosixPath(path).parts
    if any(part in {'..', '.'} for part in raw_parts):
        raise ValueError(f'La URL contiene segmentos de ruta no permitidos: {url}')
    clean_parts = []
    for part in raw_parts:
        if part in {'', '/'}:
            continue
        clean = re.sub(r'[<>:"|?*\x00-\x1f]', "_", part).rstrip(' .')
        if not clean:
            clean = '_'
        clean_parts.append(clean)
    if not clean_parts:
        clean_parts = ['index.html']
    relative = Path(*clean_parts)

    if parsed.query:
        query_hash = hashlib.sha256(parsed.query.encode("utf-8")).hexdigest()[:12]
        relative = relative.with_name(
            f"{relative.stem}_{query_hash}{relative.suffix}"
        )

    root = output_dir.expanduser().resolve()
    local_path = (root / subdir / relative).resolve()
    try:
        local_path.relative_to(root / subdir)
    except ValueError as exc:
        raise ValueError('La ruta de descarga escapa del directorio configurado.') from exc
    local_path.parent.mkdir(parents=True, exist_ok=True)
    return local_path


def _positive_integer(
    value: object,
    name: str,
    *,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > maximum
    ):
        raise ValueError(f'{name} debe ser un entero entre 1 y {maximum}.')
    return value


def _nonnegative_integer(
    value: object,
    name: str,
    *,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > maximum
    ):
        raise ValueError(f'{name} debe ser un entero entre 0 y {maximum}.')
    return value


@contextmanager
def _validated_response(
    url: str,
    user_agent: str,
    timeout: float,
    *,
    allowed_netloc: str,
    max_bytes: int,
    remaining_total_bytes: int | None = None,
) -> Iterator[tuple[int | None, str | None, Any, int | None]]:
    url = validate_site_url(url)
    max_bytes = _positive_integer(
        max_bytes, 'max_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    if remaining_total_bytes is not None:
        remaining_total_bytes = _nonnegative_integer(
            remaining_total_bytes,
            'remaining_total_bytes',
            maximum=HARD_MAX_TOTAL_BYTES,
        )
        if remaining_total_bytes == 0:
            raise DownloadBudgetExceeded(
                'El presupuesto agregado de descarga está agotado.'
            )

    request = urllib.request.Request(
        url, headers={'User-Agent': user_agent}, method='GET'
    )
    opener = urllib.request.build_opener(
        ValidatingSiteRedirectHandler(allowed_netloc)
    )
    with opener.open(request, timeout=timeout) as response:
        final_url = validate_site_url(response.geturl())
        if not same_site(final_url, allowed_netloc):
            raise ValueError(f'La redirección salió del sitio autorizado: {final_url}')
        status = getattr(response, 'status', None)
        content_type = response.headers.get('Content-Type')
        raw_length = response.headers.get('Content-Length')
        content_length: int | None = None
        if raw_length is not None:
            try:
                content_length = int(str(raw_length).strip())
            except (TypeError, ValueError) as exc:
                raise ValueError('Content-Length no es un entero válido.') from exc
            if content_length < 0:
                raise ValueError('Content-Length no puede ser negativo.')
            if (
                remaining_total_bytes is not None
                and content_length > remaining_total_bytes
            ):
                raise DownloadBudgetExceeded(
                    'Content-Length excede el presupuesto agregado restante '
                    f'de {remaining_total_bytes} bytes.'
                )
            if content_length > max_bytes:
                raise ValueError(
                    f'La respuesta excede el límite de {max_bytes} bytes.'
                )
        yield status, content_type, response, content_length


def _iter_response_chunks(
    response: Any,
    *,
    max_bytes: int,
    remaining_total_bytes: int | None,
    content_length: int | None,
) -> Iterator[bytes]:
    total = 0
    while True:
        read_size = min(STREAM_CHUNK_BYTES, max_bytes - total + 1)
        if remaining_total_bytes is not None:
            read_size = min(
                read_size,
                remaining_total_bytes - total + 1,
            )
        chunk = response.read(max(1, read_size))
        if not chunk:
            break
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise TypeError('La respuesta HTTP no devolvió bytes.')
        chunk = bytes(chunk)
        total += len(chunk)
        if (
            remaining_total_bytes is not None
            and total > remaining_total_bytes
        ):
            raise DownloadBudgetExceeded(
                'La respuesta excede el presupuesto agregado restante '
                f'de {remaining_total_bytes} bytes.'
            )
        if total > max_bytes:
            raise ValueError(
                f'La respuesta excede el límite de {max_bytes} bytes.'
            )
        yield chunk

    if content_length is not None and total != content_length:
        raise OSError(
            'La longitud real de la respuesta no coincide con Content-Length: '
            f'{total} != {content_length}.'
        )


def open_request(
    url: str,
    user_agent: str,
    timeout: float,
    *,
    allowed_netloc: str,
    max_bytes: int,
    remaining_total_bytes: int | None = None,
) -> tuple[int | None, str | None, bytes]:
    data = bytearray()
    with _validated_response(
        url,
        user_agent,
        timeout,
        allowed_netloc=allowed_netloc,
        max_bytes=max_bytes,
        remaining_total_bytes=remaining_total_bytes,
    ) as (status, content_type, response, content_length):
        for chunk in _iter_response_chunks(
            response,
            max_bytes=max_bytes,
            remaining_total_bytes=remaining_total_bytes,
            content_length=content_length,
        ):
            data.extend(chunk)
    return status, content_type, bytes(data)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(
    url: str,
    output_dir: Path,
    user_agent: str,
    timeout: float,
    overwrite: bool,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
    *,
    remaining_total_bytes: int | None = None,
) -> DownloadRecord:
    url = validate_site_url(url)
    max_bytes = _positive_integer(
        max_bytes, 'max_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    if remaining_total_bytes is not None:
        remaining_total_bytes = _nonnegative_integer(
            remaining_total_bytes,
            'remaining_total_bytes',
            maximum=HARD_MAX_TOTAL_BYTES,
        )
    local_path = safe_local_path(output_dir, url, subdir='files')

    if local_path.exists() and not overwrite:
        size_bytes = local_path.stat().st_size
        if (
            remaining_total_bytes is not None
            and size_bytes > remaining_total_bytes
        ):
            raise DownloadBudgetExceeded(
                'El archivo existente excede el presupuesto agregado restante '
                f'de {remaining_total_bytes} bytes.'
            )
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status='skipped_exists',
            http_status=None,
            content_type=None,
            size_bytes=size_bytes,
            sha256=sha256_file(local_path),
            error=None,
        )

    try:
        allowed_netloc = urllib.parse.urlparse(url).netloc
        with _validated_response(
            url,
            user_agent,
            timeout,
            allowed_netloc=allowed_netloc,
            max_bytes=max_bytes,
            remaining_total_bytes=remaining_total_bytes,
        ) as (http_status, content_type, response, content_length):
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f'.{local_path.name}.',
                suffix='.tmp',
                dir=local_path.parent,
            )
            temporary_path = Path(temporary_name)
            try:
                digest = hashlib.sha256()
                size_bytes = 0
                with os.fdopen(descriptor, 'wb') as handle:
                    for chunk in _iter_response_chunks(
                        response,
                        max_bytes=max_bytes,
                        remaining_total_bytes=remaining_total_bytes,
                        content_length=content_length,
                    ):
                        handle.write(chunk)
                        digest.update(chunk)
                        size_bytes += len(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, local_path)
            finally:
                temporary_path.unlink(missing_ok=True)
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status='downloaded',
            http_status=http_status,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            error=None,
        )
    except DownloadBudgetExceeded:
        raise
    except Exception as exc:
        return DownloadRecord(
            url=url,
            local_path=str(local_path),
            status='error',
            http_status=None,
            content_type=None,
            size_bytes=0,
            sha256=None,
            error=repr(exc),
        )


def save_html_page(url: str, html: bytes, output_dir: Path) -> Path:
    local_path = safe_local_path(output_dir, url, subdir='pages')
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f'.{local_path.name}.', suffix='.tmp', dir=local_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(html)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, local_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return local_path


def load_robots(
    start_url: str,
    *,
    user_agent: str,
    timeout: float,
    allowed_netloc: str,
) -> urllib.robotparser.RobotFileParser:
    parsed = urllib.parse.urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    robots = urllib.robotparser.RobotFileParser()
    robots.set_url(robots_url)
    try:
        _status, _content_type, data = open_request(
            robots_url,
            user_agent,
            timeout,
            allowed_netloc=allowed_netloc,
            max_bytes=ROBOTS_MAX_RESPONSE_BYTES,
        )
        robots.parse(data.decode('utf-8', errors='replace').splitlines())
    except Exception as exc:
        raise RobotsPolicyError(
            'No se pudo verificar robots.txt; el rastreo se abortó '
            'con política fail-closed.'
        ) from exc
    return robots


def write_manifest(output_dir: Path, records: list[DownloadRecord]) -> None:
    """Replace both manifests atomically; CSV is the authoritative resume file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / 'manifest.csv'
    jsonl_path = output_dir / 'manifest.jsonl'
    fieldnames = [
        'url',
        'local_path',
        'status',
        'http_status',
        'content_type',
        'size_bytes',
        'sha256',
        'error',
    ]

    csv_temporary: Path | None = None
    jsonl_temporary: Path | None = None
    try:
        csv_descriptor, csv_name = tempfile.mkstemp(
            prefix='.manifest.csv.', suffix='.tmp', dir=output_dir
        )
        csv_temporary = Path(csv_name)
        with os.fdopen(csv_descriptor, 'w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(asdict(record))
            handle.flush()
            os.fsync(handle.fileno())

        jsonl_descriptor, jsonl_name = tempfile.mkstemp(
            prefix='.manifest.jsonl.', suffix='.tmp', dir=output_dir
        )
        jsonl_temporary = Path(jsonl_name)
        with os.fdopen(jsonl_descriptor, 'w', encoding='utf-8') as handle:
            for record in records:
                handle.write(
                    json.dumps(asdict(record), ensure_ascii=False) + '\n'
                )
            handle.flush()
            os.fsync(handle.fileno())

        # Publish JSONL first and the authoritative CSV last. A failure can
        # therefore never expose a partially written CSV to load_manifest().
        os.replace(jsonl_temporary, jsonl_path)
        jsonl_temporary = None
        os.replace(csv_temporary, csv_path)
        csv_temporary = None
    finally:
        if csv_temporary is not None:
            csv_temporary.unlink(missing_ok=True)
        if jsonl_temporary is not None:
            jsonl_temporary.unlink(missing_ok=True)


class ManifestCheckpoint:
    """Batch manifest writes so a crawl does not rewrite O(N) rows per asset."""

    def __init__(
        self,
        output_dir: Path,
        records_supplier: Callable[[], list[DownloadRecord]],
        *,
        every: int,
    ) -> None:
        self.output_dir = output_dir
        self.records_supplier = records_supplier
        self.every = _positive_integer(
            every, 'manifest_checkpoint_every', maximum=MANIFEST_MAX_ROWS
        )
        self.pending = 0

    def changed(self) -> None:
        self.pending += 1
        if self.pending >= self.every:
            self.flush()

    def flush(self, *, force: bool = False) -> None:
        manifests_exist = (
            (self.output_dir / 'manifest.csv').is_file()
            and (self.output_dir / 'manifest.jsonl').is_file()
        )
        if self.pending == 0 and (not force or manifests_exist):
            return
        write_manifest(self.output_dir, self.records_supplier())
        self.pending = 0


def load_manifest(output_dir: Path) -> list[DownloadRecord]:
    csv_path = output_dir / "manifest.csv"
    if not csv_path.exists():
        return []
    manifest_size = csv_path.stat().st_size
    if manifest_size > MANIFEST_MAX_BYTES:
        raise ValueError(
            f'El manifiesto excede el límite de {MANIFEST_MAX_BYTES} bytes.'
        )

    records: list[DownloadRecord] = []
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        for row_number, row in enumerate(csv.DictReader(fh), start=1):
            if row_number > MANIFEST_MAX_ROWS:
                raise ValueError(
                    f'El manifiesto excede el límite de {MANIFEST_MAX_ROWS} filas.'
                )
            records.append(
                DownloadRecord(
                    url=row.get("url", ""),
                    local_path=row.get("local_path", ""),
                    status=row.get("status", ""),
                    http_status=int(row["http_status"]) if row.get("http_status") else None,
                    content_type=row.get("content_type") or None,
                    size_bytes=int(row["size_bytes"]) if row.get("size_bytes") else 0,
                    sha256=row.get("sha256") or None,
                    error=row.get("error") or None,
                )
            )
    return records


def _confined_existing_path(
    output_dir: Path,
    local_path: str,
) -> Path | None:
    if not local_path:
        return None
    output_root = output_dir.expanduser().resolve()
    candidate = Path(local_path).expanduser()
    if not candidate.is_absolute():
        candidate = output_root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(output_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _record_size_for_budget(output_dir: Path, record: DownloadRecord) -> int:
    declared = _nonnegative_integer(
        record.size_bytes,
        f'size_bytes del manifiesto para {record.url!r}',
        maximum=HARD_MAX_TOTAL_BYTES,
    )
    existing = _confined_existing_path(output_dir, record.local_path)
    if existing is not None:
        return max(declared, existing.stat().st_size)
    return declared


def _initial_budget_state(
    output_dir: Path,
    records: list[DownloadRecord],
    max_total_bytes: int,
) -> tuple[int, set[str]]:
    max_total_bytes = _positive_integer(
        max_total_bytes,
        'max_total_bytes',
        maximum=HARD_MAX_TOTAL_BYTES,
    )
    used = 0
    accounted_urls: set[str] = set()
    accounted_paths: set[Path] = set()
    for record in records:
        if (
            record.status not in ACCOUNTED_MANIFEST_STATUSES
            or not record.url
            or record.url in accounted_urls
        ):
            continue
        used += _record_size_for_budget(output_dir, record)
        existing = _confined_existing_path(output_dir, record.local_path)
        if existing is not None:
            accounted_paths.add(existing)
        accounted_urls.add(record.url)
        if used > max_total_bytes:
            raise DownloadBudgetExceeded(
                'Los archivos existentes y el manifiesto exceden el presupuesto '
                f'agregado de {max_total_bytes} bytes.'
            )

    output_root = output_dir.expanduser().resolve()
    for subdirectory in ('files', 'pages'):
        archive_root = (output_root / subdirectory).resolve()
        if not archive_root.is_dir():
            continue
        for path in archive_root.rglob('*'):
            resolved = path.resolve()
            try:
                resolved.relative_to(archive_root)
            except ValueError:
                continue
            if not resolved.is_file() or resolved in accounted_paths:
                continue
            used += resolved.stat().st_size
            accounted_paths.add(resolved)
            if used > max_total_bytes:
                raise DownloadBudgetExceeded(
                    'Los archivos existentes y el manifiesto exceden el presupuesto '
                    f'agregado de {max_total_bytes} bytes.'
                )
    return used, accounted_urls


def _remaining_budget(max_total_bytes: int, used_bytes: int) -> int:
    remaining = max_total_bytes - used_bytes
    if remaining <= 0:
        raise DownloadBudgetExceeded(
            f'El presupuesto agregado de {max_total_bytes} bytes está agotado.'
        )
    return remaining


def _consume_bytes(
    used_bytes: int,
    size_bytes: int,
    max_total_bytes: int,
) -> int:
    updated = used_bytes + _nonnegative_integer(
        size_bytes, 'size_bytes', maximum=HARD_MAX_TOTAL_BYTES
    )
    if updated > max_total_bytes:
        raise DownloadBudgetExceeded(
            f'Se excedió el presupuesto agregado de {max_total_bytes} bytes.'
        )
    return updated


def _account_record(
    output_dir: Path,
    record: DownloadRecord,
    accounted_urls: set[str],
    used_bytes: int,
    max_total_bytes: int,
) -> int:
    if (
        record.status not in ACCOUNTED_MANIFEST_STATUSES
        or not record.url
        or record.url in accounted_urls
    ):
        return used_bytes
    updated = _consume_bytes(
        used_bytes,
        _record_size_for_budget(output_dir, record),
        max_total_bytes,
    )
    accounted_urls.add(record.url)
    return updated


def upsert_record(records_by_url: dict[str, DownloadRecord], record: DownloadRecord) -> None:
    records_by_url[record.url] = record


def download_assets_from_manifest(
    output_dir: Path,
    *,
    max_files: int,
    delay: float,
    timeout: float,
    user_agent: str,
    overwrite: bool,
    include_extensions: set[str] | None,
    exclude_extensions: set[str] | None,
    download_unknown: bool,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_page_bytes: int = DEFAULT_MAX_PAGE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    manifest_checkpoint_every: int = DEFAULT_MANIFEST_CHECKPOINT_EVERY,
) -> list[DownloadRecord]:
    _positive_integer(
        max_page_bytes, 'max_page_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    _positive_integer(
        max_file_bytes, 'max_file_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    max_total_bytes = _positive_integer(
        max_total_bytes, 'max_total_bytes', maximum=HARD_MAX_TOTAL_BYTES
    )
    _positive_integer(
        manifest_checkpoint_every,
        'manifest_checkpoint_every',
        maximum=MANIFEST_MAX_ROWS,
    )
    existing_records = load_manifest(output_dir)
    records_by_url = {record.url: record for record in existing_records if record.url}
    seen_files: set[str] = {
        record.url
        for record in existing_records
        if record.url and record.status in {"downloaded", "skipped_exists", "dry_run"}
    }
    page_records = [
        record
        for record in existing_records
        if record.status == "page_saved" and record.local_path
    ]

    downloaded_this_run = 0
    asset_extensions = include_extensions if include_extensions is not None else IMAGE_EXTENSIONS

    def current_records() -> list[DownloadRecord]:
        return list(records_by_url.values())

    total_bytes_used, accounted_urls = _initial_budget_state(
        output_dir, current_records(), max_total_bytes
    )
    checkpoint = ManifestCheckpoint(
        output_dir,
        current_records,
        every=manifest_checkpoint_every,
    )

    try:
        for page_record in page_records:
            if downloaded_this_run >= max_files:
                break

            page_url = validate_site_url(page_record.url)
            allowed_netloc = urllib.parse.urlparse(page_url).netloc
            page_path = Path(page_record.local_path).expanduser().resolve()
            pages_root = (output_dir.expanduser().resolve() / 'pages').resolve()
            try:
                page_path.relative_to(pages_root)
            except ValueError:
                continue
            if not page_path.is_file():
                continue
            try:
                with page_path.open('rb') as handle:
                    page_data = handle.read(max_page_bytes + 1)
                if len(page_data) > max_page_bytes:
                    raise ValueError(
                        f'La página local excede el límite de {max_page_bytes} bytes.'
                    )
                html = page_data.decode("utf-8", errors="ignore")
            except Exception as exc:
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_record.url,
                        local_path=page_record.local_path,
                        status="page_asset_parse_error",
                        http_status=page_record.http_status,
                        content_type=page_record.content_type,
                        size_bytes=page_record.size_bytes,
                        sha256=page_record.sha256,
                        error=repr(exc),
                    ),
                )
                checkpoint.changed()
                continue

            parser = LinkExtractor()
            try:
                parser.feed(html)
            except Exception:
                continue

            for raw_link in parser.links:
                if downloaded_this_run >= max_files:
                    break

                url = normalize_url(page_record.url, raw_link)
                if not url or not same_site(url, allowed_netloc):
                    continue
                if url in seen_files:
                    continue
                if not looks_downloadable(
                    url,
                    download_unknown=download_unknown,
                    include_extensions=asset_extensions,
                    exclude_extensions=exclude_extensions,
                ):
                    continue

                seen_files.add(url)
                downloaded_this_run += 1
                print(f"[asset {downloaded_this_run}] {url}")
                record = download_file(
                    url,
                    output_dir,
                    user_agent=user_agent,
                    timeout=timeout,
                    overwrite=overwrite,
                    max_bytes=max_file_bytes,
                    remaining_total_bytes=_remaining_budget(
                        max_total_bytes, total_bytes_used
                    ),
                )
                upsert_record(records_by_url, record)
                total_bytes_used = _account_record(
                    output_dir,
                    record,
                    accounted_urls,
                    total_bytes_used,
                    max_total_bytes,
                )
                checkpoint.changed()
                time.sleep(delay)
    finally:
        checkpoint.flush(force=True)

    return current_records()


def crawl(
    start_url: str,
    output_dir: Path,
    *,
    max_pages: int,
    max_files: int,
    delay: float,
    timeout: float,
    user_agent: str,
    save_pages: bool,
    overwrite: bool,
    download_unknown: bool,
    include_extensions: set[str] | None,
    exclude_extensions: set[str] | None,
    stay_under_start_path: bool,
    dry_run: bool,
    max_page_bytes: int = DEFAULT_MAX_PAGE_BYTES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    manifest_checkpoint_every: int = DEFAULT_MANIFEST_CHECKPOINT_EVERY,
) -> list[DownloadRecord]:
    _positive_integer(
        max_page_bytes, 'max_page_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    _positive_integer(
        max_file_bytes, 'max_file_bytes', maximum=HARD_MAX_RESPONSE_BYTES
    )
    max_total_bytes = _positive_integer(
        max_total_bytes, 'max_total_bytes', maximum=HARD_MAX_TOTAL_BYTES
    )
    _positive_integer(
        manifest_checkpoint_every,
        'manifest_checkpoint_every',
        maximum=MANIFEST_MAX_ROWS,
    )
    parsed_start = urllib.parse.urlparse(start_url)
    allowed_netloc = parsed_start.netloc.lower()
    if parsed_start.scheme != 'https' or (parsed_start.hostname or '').lower() not in ALLOWED_SITE_HOSTS:
        raise ValueError(
            f'El rastreo sólo admite HTTPS en {sorted(ALLOWED_SITE_HOSTS)}.'
        )
    path_prefix = parsed_start.path
    if not path_prefix.endswith("/"):
        path_prefix = str(Path(path_prefix).parent).replace("\\", "/")
        if not path_prefix.endswith("/"):
            path_prefix += "/"
    robots = load_robots(
        start_url,
        user_agent=user_agent,
        timeout=timeout,
        allowed_netloc=allowed_netloc,
    )

    queue: list[str] = [start_url]
    seen_pages: set[str] = set()
    existing_records = load_manifest(output_dir)
    records_by_url = {record.url: record for record in existing_records if record.url}
    seen_files: set[str] = {
        record.url
        for record in existing_records
        if record.url and record.status in {"downloaded", "skipped_exists", "dry_run"}
    }
    files_seen_this_run = 0

    def current_records() -> list[DownloadRecord]:
        return list(records_by_url.values())

    total_bytes_used, accounted_urls = _initial_budget_state(
        output_dir, current_records(), max_total_bytes
    )
    checkpoint = ManifestCheckpoint(
        output_dir,
        current_records,
        every=manifest_checkpoint_every,
    )

    try:
        while queue and len(seen_pages) < max_pages and files_seen_this_run < max_files:
            page_url = queue.pop(0)
            if page_url in seen_pages:
                continue
            if not same_site(page_url, allowed_netloc):
                continue
            if stay_under_start_path and not under_path_prefix(page_url, path_prefix):
                continue
            if not robots.can_fetch(user_agent, page_url):
                print(f"[robots] skip page: {page_url}")
                continue

            seen_pages.add(page_url)
            print(f"[page {len(seen_pages)}] {page_url}")

            try:
                status, content_type, data = open_request(
                    page_url,
                    user_agent,
                    timeout,
                    allowed_netloc=allowed_netloc,
                    max_bytes=max_page_bytes,
                    remaining_total_bytes=_remaining_budget(
                        max_total_bytes, total_bytes_used
                    ),
                )
                total_bytes_used = _consume_bytes(
                    total_bytes_used, len(data), max_total_bytes
                )
            except DownloadBudgetExceeded:
                raise
            except Exception as exc:
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_url,
                        local_path="",
                        status="page_error",
                        http_status=None,
                        content_type=None,
                        size_bytes=0,
                        sha256=None,
                        error=repr(exc),
                    ),
                )
                checkpoint.changed()
                time.sleep(delay)
                continue

            if save_pages:
                local_page = save_html_page(page_url, data, output_dir)
                upsert_record(
                    records_by_url,
                    DownloadRecord(
                        url=page_url,
                        local_path=str(local_page),
                        status="page_saved",
                        http_status=status,
                        content_type=content_type,
                        size_bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(),
                        error=None,
                    ),
                )
                checkpoint.changed()

            content_type = (content_type or "").lower()
            if "html" not in content_type and not looks_like_html(page_url):
                time.sleep(delay)
                continue

            parser = LinkExtractor()
            try:
                parser.feed(data.decode("utf-8", errors="ignore"))
            except Exception:
                time.sleep(delay)
                continue

            for raw_link in parser.links:
                url = normalize_url(page_url, raw_link)
                if not url or not same_site(url, allowed_netloc):
                    continue
                if stay_under_start_path and not under_path_prefix(url, path_prefix):
                    continue

                if looks_like_html(url):
                    if url not in seen_pages and len(seen_pages) + len(queue) < max_pages:
                        queue.append(url)
                    continue

                if not looks_downloadable(
                    url,
                    download_unknown=download_unknown,
                    include_extensions=include_extensions,
                    exclude_extensions=exclude_extensions,
                ):
                    continue
                if url in seen_files:
                    continue
                if files_seen_this_run >= max_files:
                    break
                if not robots.can_fetch(user_agent, url):
                    print(f"[robots] skip file: {url}")
                    continue

                seen_files.add(url)
                files_seen_this_run += 1
                print(f"  [file {files_seen_this_run}] {url}")

                if dry_run:
                    record = DownloadRecord(
                        url=url,
                        local_path=str(safe_local_path(output_dir, url, subdir="files")),
                        status="dry_run",
                        http_status=None,
                        content_type=None,
                        size_bytes=0,
                        sha256=None,
                        error=None,
                    )
                else:
                    record = download_file(
                        url,
                        output_dir,
                        user_agent=user_agent,
                        timeout=timeout,
                        overwrite=overwrite,
                        max_bytes=max_file_bytes,
                        remaining_total_bytes=_remaining_budget(
                            max_total_bytes, total_bytes_used
                        ),
                    )
                upsert_record(records_by_url, record)
                total_bytes_used = _account_record(
                    output_dir,
                    record,
                    accounted_urls,
                    total_bytes_used,
                    max_total_bytes,
                )
                checkpoint.changed()
                time.sleep(delay)

            time.sleep(delay)
    finally:
        checkpoint.flush(force=True)

    return current_records()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download linked downloadable files from Sprott's website."
    )
    parser.add_argument("--start", default=DEFAULT_START_URL, help=f"Start URL. Default: {DEFAULT_START_URL}")
    parser.add_argument("--output", default="external/sprott_site", help="Output directory.")
    parser.add_argument("--max-pages", type=int, default=3000, help="Maximum HTML pages to crawl.")
    parser.add_argument("--max-files", type=int, default=20000, help="Maximum files to download.")
    parser.add_argument("--max-page-bytes", type=int, default=DEFAULT_MAX_PAGE_BYTES, help="Maximum bytes accepted for one HTML page.")
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES, help="Maximum bytes accepted for one downloaded file.")
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES, help="Aggregate byte budget, including resumed manifest entries and existing confined files.")
    parser.add_argument("--manifest-checkpoint-every", type=int, default=DEFAULT_MANIFEST_CHECKPOINT_EVERY, help="Atomically checkpoint manifests after this many record changes.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument("--save-pages", action="store_true", help="Save crawled HTML pages under output/pages.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite files already downloaded.")
    parser.add_argument(
        "--download-assets-from-manifest",
        action="store_true",
        help="Read saved HTML pages from manifest.csv and download their linked image assets.",
    )
    parser.add_argument(
        "--download-unknown",
        action="store_true",
        help="Download same-domain links with unknown or nonstandard extensions.",
    )
    parser.add_argument(
        "--include-ext",
        help="Comma-separated extension allowlist for file downloads, for example: .pdf,.doc,.txt",
    )
    parser.add_argument(
        "--exclude-ext",
        help="Comma-separated extension denylist for file downloads, for example: .gif,.jpg,.exe",
    )
    parser.add_argument(
        "--stay-under-start-path",
        action="store_true",
        help="Only crawl and download URLs whose path stays under the start URL path.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List downloads without writing downloaded files.")
    parser.add_argument(
        "--user-agent",
        default="ChaosToolboxResearchDownloader/0.1 (+local academic archive; respectful crawl)",
        help="User-Agent string.",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    include_extensions = parse_extension_list(args.include_ext)
    exclude_extensions = parse_extension_list(args.exclude_ext)

    try:
        if args.download_assets_from_manifest:
            if args.dry_run:
                raise ValueError(
                    '--dry-run is not supported with '
                    '--download-assets-from-manifest'
                )
            records = download_assets_from_manifest(
                output_dir,
                max_files=args.max_files,
                delay=args.delay,
                timeout=args.timeout,
                user_agent=args.user_agent,
                overwrite=args.overwrite,
                include_extensions=include_extensions,
                exclude_extensions=exclude_extensions,
                download_unknown=args.download_unknown,
                max_file_bytes=args.max_file_bytes,
                max_page_bytes=args.max_page_bytes,
                max_total_bytes=args.max_total_bytes,
                manifest_checkpoint_every=args.manifest_checkpoint_every,
            )
        else:
            records = crawl(
                args.start,
                output_dir,
                max_pages=args.max_pages,
                max_files=args.max_files,
                delay=args.delay,
                timeout=args.timeout,
                user_agent=args.user_agent,
                save_pages=args.save_pages,
                overwrite=args.overwrite,
                download_unknown=args.download_unknown,
                include_extensions=include_extensions,
                exclude_extensions=exclude_extensions,
                stay_under_start_path=args.stay_under_start_path,
                dry_run=args.dry_run,
                max_page_bytes=args.max_page_bytes,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
                manifest_checkpoint_every=args.manifest_checkpoint_every,
            )
    except (DownloadBudgetExceeded, RobotsPolicyError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2

    downloaded = sum(1 for record in records if record.status == "downloaded")
    page_saved = sum(1 for record in records if record.status == "page_saved")
    skipped = sum(1 for record in records if record.status == "skipped_exists")
    errors = sum(1 for record in records if "error" in record.status)

    print()
    print("Done.")
    print(f"Downloaded: {downloaded}")
    print(f"Pages saved: {page_saved}")
    print(f"Skipped existing: {skipped}")
    print(f"Errors: {errors}")
    print(f"Manifest: {output_dir / 'manifest.csv'}")
    print(f"Manifest JSONL: {output_dir / 'manifest.jsonl'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
