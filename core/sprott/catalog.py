from __future__ import annotations

import json
import os
from pathlib import Path

from core.paths import sprott_asset_path
from core.time_policy import utc_now_iso


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def examples_path() -> Path:
    return sprott_asset_path('examples', 'synthetic_examples.json')


def load_synthetic_examples(path: str | Path | None = None) -> list[dict]:
    source = Path(path) if path else examples_path()
    with source.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    examples = data.get('examples', data if isinstance(data, list) else [])
    for item in examples:
        item.setdefault('source', 'synthetic educational example')
    return examples


def favorites_path() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
        return base / 'Chaos Toolbox' / 'sprott_favorites.json'
    return Path.home() / '.chaos_toolbox' / 'sprott_favorites.json'


def load_favorites(path: str | Path | None = None) -> list[dict]:
    target = Path(path) if path else favorites_path()
    if not target.exists():
        return []
    with target.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else data.get('favorites', [])


def save_favorite(entry: dict, path: str | Path | None = None) -> Path:
    target = Path(path) if path else favorites_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    favorites = load_favorites(target)
    record = dict(entry)
    record.setdefault('date', utc_now_iso())
    record.setdefault('source', 'user favorite')
    favorites.append(record)
    with target.open('w', encoding='utf-8') as handle:
        json.dump(favorites, handle, indent=2, ensure_ascii=False)
    return target
