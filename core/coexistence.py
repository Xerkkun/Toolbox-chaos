from __future__ import annotations

from pathlib import Path
import yaml
from core.paths import resource_path


def coexisting_attractors_path() -> Path:
    # First search in resources/bundled/data/
    candidate = resource_path('resources', 'bundled', 'data', 'coexisting_attractors.yaml')
    if candidate.exists():
        return candidate
    # Fallback to data/coexisting_attractors.yaml
    return resource_path('data', 'coexisting_attractors.yaml')


def load_coexisting_attractors() -> list[dict]:
    path = coexisting_attractors_path()
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or []

