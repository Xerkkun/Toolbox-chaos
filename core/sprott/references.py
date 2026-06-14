from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .codes import decode_code


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
            entry.update(classify_dic_entry(entry['code'], parts[1:]))
            entries.append(entry)
            if limit is not None and len(entries) >= int(limit):
                break
    return entries


def classify_dic_entry(code_text: str, metric_tokens: list[str] | None = None) -> dict:
    code = decode_code(code_text)
    metrics = parse_dic_metrics(metric_tokens or [])
    if code.kind in {'map', 'flow'}:
        support = 'simulable'
    elif code.kind == 'special':
        support = 'familia especial pendiente'
    else:
        support = 'error'
    return {
        'family': code.family_letter,
        'kind': code.kind,
        'dimension': code.dimension,
        'order': code.order,
        'support': support,
        'f_metric': metrics.get('F'),
        'l_metric': metrics.get('L'),
        'parsed_metrics': metrics,
    }


def parse_dic_metrics(tokens: list[str]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    pending_key = ''
    numeric_seen = []
    for token in tokens:
        clean = token.strip().strip(',;')
        if not clean:
            continue
        upper = clean.upper()
        if upper in {'F', 'L'}:
            pending_key = upper
            continue
        match = re.match(r'^([FL])\s*[:=]\s*(-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)$', upper)
        if match:
            metrics[match.group(1)] = float(match.group(2))
            pending_key = ''
            continue
        try:
            value = float(clean)
        except ValueError:
            pending_key = ''
            continue
        if pending_key:
            metrics[pending_key] = value
            pending_key = ''
        else:
            numeric_seen.append(value)
    if 'F' not in metrics and numeric_seen:
        metrics['F'] = numeric_seen[0]
    if 'L' not in metrics and len(numeric_seen) > 1:
        metrics['L'] = numeric_seen[1]
    return metrics
