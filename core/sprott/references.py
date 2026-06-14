from __future__ import annotations

import hashlib
from pathlib import Path


EXTENSION_CATEGORIES = {
    '.dic': 'dictionary',
    '.bas': 'source_basic',
    '.c': 'source_c',
    '.cpp': 'source_cpp',
    '.zip': 'archive',
    '.exe': 'binary_not_executed',
    '.pdf': 'document',
    '.htm': 'html',
    '.html': 'html',
}


def file_hash(path: str | Path, algorithm='sha256', chunk_size=1024 * 1024) -> str:
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def index_local_reference_folder(folder: str | Path, *, include_hash=False) -> list[dict]:
    root = Path(folder).expanduser()
    if not root.exists() or not root.is_dir():
        raise ValueError(f'not a directory: {root}')
    inventory = []
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in EXTENSION_CATEGORIES:
            continue
        item = {
            'name': path.name,
            'path': str(path),
            'type': suffix.lstrip('.').upper(),
            'size': path.stat().st_size,
            'hash': file_hash(path) if include_hash else '',
            'category': EXTENSION_CATEGORIES[suffix],
        }
        inventory.append(item)
    return inventory


def read_dic_codes(path: str | Path) -> list[str]:
    source = Path(path)
    if source.suffix.lower() != '.dic':
        raise ValueError('only .DIC files are supported by this light importer')
    codes = []
    with source.open('r', encoding='latin-1', errors='ignore') as handle:
        for line in handle:
            token = line.strip().split()
            if token:
                codes.append(token[0])
    return codes


def read_dic_entries(path: str | Path, *, limit: int | None = None) -> list[dict]:
    source = Path(path)
    if source.suffix.lower() != '.dic':
        raise ValueError('only .DIC files are supported by this light importer')
    entries = []
    with source.open('r', encoding='latin-1', errors='ignore') as handle:
        for line_no, line in enumerate(handle, start=1):
            parts = line.strip().split()
            if not parts:
                continue
            entry = {
                'code': parts[0],
                'metrics': parts[1:],
                'line': line_no,
                'source_file': str(source),
                'source_name': source.name,
                'source': 'local external reference',
            }
            entries.append(entry)
            if limit is not None and len(entries) >= int(limit):
                break
    return entries
