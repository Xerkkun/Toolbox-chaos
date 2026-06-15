from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ATTRIBUTION_WARNING = (
    'Imagen generada por Chaos Toolbox a partir de un codigo cargado localmente '
    'por el usuario. No se redistribuye la imagen original de Sprott.'
)


def gallery_root(base: str | Path | None = None) -> Path:
    if base is not None:
        return Path(base)
    if os.name == 'nt':
        appdata = Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
        return appdata / 'Chaos Toolbox' / 'sprott_gallery'
    return Path.home() / '.chaos_toolbox' / 'sprott_gallery'


def new_entry_dir(base: str | Path | None = None) -> Path:
    root = gallery_root(base)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
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
        'date': datetime.now(timezone.utc).isoformat(),
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
    entry_dir = new_entry_dir(base)
    render_target = entry_dir / 'render.png'
    shutil.copyfile(Path(render_path), render_target)
    thumb_target = entry_dir / 'thumbnail.png'
    if thumbnail_path:
        shutil.copyfile(Path(thumbnail_path), thumb_target)
    else:
        shutil.copyfile(render_target, thumb_target)
    enriched = dict(metadata)
    enriched['render'] = 'render.png'
    enriched['thumbnail'] = 'thumbnail.png'
    with (entry_dir / 'metadata.json').open('w', encoding='utf-8') as handle:
        json.dump(enriched, handle, indent=2, ensure_ascii=False)
    return entry_dir


def load_gallery_entry(path: str | Path) -> dict:
    entry_dir = Path(path)
    with (entry_dir / 'metadata.json').open('r', encoding='utf-8') as handle:
        metadata = json.load(handle)
    metadata['_entry_dir'] = str(entry_dir)
    metadata['_render_path'] = str(entry_dir / metadata.get('render', 'render.png'))
    metadata['_thumbnail_path'] = str(entry_dir / metadata.get('thumbnail', 'thumbnail.png'))
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
            entries.append(load_gallery_entry(path))
        except Exception:
            continue
    return entries


def delete_gallery_entry(path: str | Path):
    entry_dir = Path(path)
    root = gallery_root()
    try:
        entry_dir.relative_to(root)
    except ValueError:
        pass
    if entry_dir.exists() and entry_dir.is_dir():
        shutil.rmtree(entry_dir)
