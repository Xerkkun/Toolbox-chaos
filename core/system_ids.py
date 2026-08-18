"""Canonical system identifiers shared by the Python and C backends."""
from __future__ import annotations

from pathlib import Path
import re


_DEFINITION_PATTERN = re.compile(
    r'^CHAOS_SYSTEM\("(?P<key>[a-z0-9_]+)",\s*'
    r'(?P<symbol>SYS_[A-Z0-9_]+),\s*(?P<code>[0-9]+)\)$'
)


def _load_native_system_definitions() -> tuple[tuple[str, str, int], ...]:
    source = Path(__file__).resolve().parent / 'csrc' / 'system_ids.def'
    try:
        lines = source.read_text(encoding='utf-8').splitlines()
    except OSError as exc:
        raise RuntimeError(f'No se encontró la tabla canónica de sistemas: {source}') from exc
    definitions: list[tuple[str, str, int]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith('/*'):
            continue
        match = _DEFINITION_PATTERN.fullmatch(line)
        if match is None:
            raise RuntimeError(
                f'Entrada inválida en {source.name}:{line_number}: {raw_line!r}'
            )
        definitions.append(
            (match.group('key'), match.group('symbol'), int(match.group('code')))
        )
    keys = [item[0] for item in definitions]
    symbols = [item[1] for item in definitions]
    codes = [item[2] for item in definitions]
    if len(set(keys)) != len(keys) or len(set(symbols)) != len(symbols):
        raise RuntimeError('La tabla canónica contiene claves o símbolos duplicados.')
    if codes != list(range(len(definitions))):
        raise RuntimeError('Los IDs nativos deben ser contiguos y comenzar en cero.')
    return tuple(definitions)


NATIVE_SYSTEM_DEFINITIONS = _load_native_system_definitions()
NATIVE_SYSTEM_IDS = tuple(item[0] for item in NATIVE_SYSTEM_DEFINITIONS)
NATIVE_SYSTEM_CODES = {key: code for key, _symbol, code in NATIVE_SYSTEM_DEFINITIONS}
PYTHON_ONLY_SYSTEM_IDS = frozenset({'hyper_lorenz'})


__all__ = [
    'NATIVE_SYSTEM_CODES',
    'NATIVE_SYSTEM_DEFINITIONS',
    'NATIVE_SYSTEM_IDS',
    'PYTHON_ONLY_SYSTEM_IDS',
]
