from __future__ import annotations

from pathlib import Path
import yaml


def coexisting_attractors_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'data' / 'coexisting_attractors.yaml'


def load_coexisting_attractors() -> list[dict]:
    path = coexisting_attractors_path()
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or []
