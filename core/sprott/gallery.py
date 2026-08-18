from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from uuid import uuid4

from core.image_security import confined_png, validate_png_file
from core.time_policy import utc_now_iso


LOGGER = logging.getLogger(__name__)


ATTRIBUTION_WARNING = (
    'Imagen generada por Chaos Toolbox a partir de un codigo cargado localmente '
    'por el usuario. No se redistribuye la imagen original de Sprott.'
)


class GallerySecurityError(ValueError):
    """Raised when a gallery path escapes its configured storage root."""


def _is_link_like(path: Path) -> bool:
    is_junction = getattr(path, 'is_junction', lambda: False)
    return path.is_symlink() or bool(is_junction())


def _confined_entry(
    path: str | Path,
    *,
    base: str | Path | None = None,
    must_exist: bool = True,
) -> Path:
    root = gallery_root(base).expanduser().resolve()
    candidate = Path(path).expanduser()
    if must_exist and not candidate.exists():
        raise GallerySecurityError(f'La entrada de galeria no existe: {candidate}')
    if candidate.exists() and _is_link_like(candidate):
        raise GallerySecurityError('Las entradas enlazadas no se admiten en la galeria.')
    resolved = candidate.resolve(strict=must_exist)
    if resolved == root or resolved.parent != root:
        raise GallerySecurityError('La entrada debe ser un subdirectorio directo de la galeria.')
    return resolved


def _confined_entry_file(entry_dir: Path, relative_name: object) -> Path:
    if not isinstance(relative_name, str) or not relative_name.strip():
        raise GallerySecurityError('La metadata de galeria contiene una ruta vacia.')
    candidate = entry_dir / relative_name
    if not candidate.exists() or _is_link_like(candidate):
        raise GallerySecurityError('El archivo de galeria no existe o es un enlace.')
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(entry_dir)
    except ValueError as exc:
        raise GallerySecurityError('La metadata intenta leer fuera de la entrada.') from exc
    if not resolved.is_file():
        raise GallerySecurityError('La ruta de galeria no identifica un archivo regular.')
    return resolved


def gallery_root(base: str | Path | None = None) -> Path:
    if base is not None:
        return Path(base)
    if os.name == 'nt':
        appdata = Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
        return appdata / 'Chaos Toolbox' / 'sprott_gallery'
    return Path.home() / '.chaos_toolbox' / 'sprott_gallery'


def new_entry_dir(base: str | Path | None = None) -> Path:
    root = gallery_root(base).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = utc_now_iso().replace('-', '').replace(':', '')[:15] + 'Z'
    path = root / f'{stamp}_{uuid4().hex[:8]}'
    path.mkdir(parents=True, exist_ok=False)
    return path


def build_metadata(
    *,
    code: str,
    source: str,
    simulation: dict,
    style: dict,
    classification: dict | None = None,
    notes: str = '',
    source_file: str = '',
    source_line: int | None = None,
) -> dict:
    metadata = {
        'schema': 1,
        'date': utc_now_iso(),
        'code': code,
        'source': source,
        'source_file': source_file,
        'source_line': source_line,
        'simulation': simulation,
        'style': style,
        'classification': classification or {},
        'notes': notes,
        'attribution_warning': ATTRIBUTION_WARNING,
    }
    if source == 'local_dic':
        metadata['generated_by'] = 'Chaos Toolbox'
        metadata['attribution'] = 'Julien C. Sprott, Strange Attractors: Creating Patterns in Chaos'
        metadata['note'] = 'imagen generada localmente desde código proporcionado por el usuario; no es imagen original redistribuida.'
    return metadata


def save_gallery_entry(
    *,
    render_path: str | Path,
    thumbnail_path: str | Path | None,
    metadata: dict,
    base: str | Path | None = None,
) -> Path:
    render_source = validate_png_file(render_path)
    thumbnail_source = (
        validate_png_file(thumbnail_path) if thumbnail_path else render_source
    )
    entry_dir = new_entry_dir(base)
    render_target = entry_dir / 'render.png'
    shutil.copyfile(render_source, render_target)
    thumb_target = entry_dir / 'thumbnail.png'
    shutil.copyfile(thumbnail_source, thumb_target)
    enriched = dict(metadata)
    enriched['render'] = 'render.png'
    enriched['thumbnail'] = 'thumbnail.png'
    with (entry_dir / 'metadata.json').open('w', encoding='utf-8') as handle:
        json.dump(enriched, handle, indent=2, ensure_ascii=False)
    return entry_dir


def load_gallery_entry(
    path: str | Path, *, base: str | Path | None = None
) -> dict:
    entry_dir = _confined_entry(path, base=base)
    metadata_path = _confined_entry_file(entry_dir, 'metadata.json')
    if metadata_path.stat().st_size > 1_048_576:
        raise GallerySecurityError('metadata.json excede el limite de 1 MiB.')
    with metadata_path.open('r', encoding='utf-8') as handle:
        metadata = json.load(handle)
    if not isinstance(metadata, dict):
        raise GallerySecurityError('metadata.json debe contener un objeto JSON.')
    render_path = confined_png(entry_dir, metadata.get('render', 'render.png'))
    thumbnail_path = confined_png(
        entry_dir, metadata.get('thumbnail', 'thumbnail.png')
    )
    metadata['_entry_dir'] = str(entry_dir)
    metadata['_render_path'] = str(render_path)
    metadata['_thumbnail_path'] = str(thumbnail_path)
    return metadata


def list_gallery_entries(base: str | Path | None = None) -> list[dict]:
    root = gallery_root(base)
    if not root.exists():
        return []
    entries = []
    for path in sorted(root.iterdir(), reverse=True):
        if not path.is_dir() or not (path / 'metadata.json').exists():
            continue
        try:
            entries.append(load_gallery_entry(path, base=root))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning('Se omitió una entrada inválida de la galería %s: %s', path, exc)
            continue
    return entries


def delete_gallery_entry(
    path: str | Path, *, base: str | Path | None = None
) -> bool:
    entry_dir = _confined_entry(path, base=base)
    if not entry_dir.is_dir():
        raise GallerySecurityError('La entrada de galeria no es un directorio.')
    shutil.rmtree(entry_dir)
    return True
