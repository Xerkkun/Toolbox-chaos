from __future__ import annotations

from dataclasses import dataclass, field
from math import comb
from typing import Literal


Kind = Literal['map', 'flow', 'special', 'unknown']


@dataclass(frozen=True)
class SprottCode:
    raw: str
    family_letter: str
    family_name: str
    dimension: int
    order: int
    kind: Kind
    coefficients: list[float] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _family_table() -> dict[str, dict]:
    table: dict[str, dict] = {}
    groups = [
        ('ABCD', 'map', 1, 'Polynomial map 1D'),
        ('EFGH', 'map', 2, 'Polynomial map 2D'),
        ('IJKL', 'map', 3, 'Polynomial map 3D'),
        ('MNOP', 'map', 4, 'Polynomial map 4D'),
        ('QRST', 'flow', 3, 'Polynomial flow 3D'),
        ('UVWX', 'flow', 4, 'Polynomial flow 4D'),
    ]
    for letters, kind, dimension, family_name in groups:
        for offset, letter in enumerate(letters):
            table[letter] = {
                'letter': letter,
                'kind': kind,
                'dimension': dimension,
                'order': offset + 2,
                'family_name': f'{family_name}, order {offset + 2}',
            }
    for letter in 'YZ':
        table[letter] = {
            'letter': letter,
            'kind': 'special',
            'dimension': 0,
            'order': 0,
            'family_name': 'Special-function family pending implementation',
        }
    return table


FAMILY_TABLE = _family_table()


def describe_family(letter: str) -> dict:
    if not letter:
        return {
            'letter': '',
            'kind': 'unknown',
            'dimension': 0,
            'order': 0,
            'family_name': 'Unknown family',
            'coefficient_count': 0,
        }
    key = letter.strip().upper()[:1]
    data = dict(FAMILY_TABLE.get(key, {
        'letter': key,
        'kind': 'unknown',
        'dimension': 0,
        'order': 0,
        'family_name': 'Unknown family',
    }))
    data['coefficient_count'] = coefficient_count(data['dimension'], data['order'], data['kind'])
    return data


def coefficient_count(dimension: int, order: int, kind: str = 'map') -> int:
    if kind not in {'map', 'flow'} or dimension <= 0 or order < 0:
        return 0
    return int(dimension) * comb(int(dimension) + int(order), int(order))


def decode_coefficient_char(ch: str) -> float:
    """Decode Sprott-style coefficient characters as (ord(ch)-77)/10.

    The initial convention maps M to 0.0, A to -1.2, and Y to 1.2.
    This module uses it only for independent educational reimplementation.
    """

    if len(ch) != 1 or not (33 <= ord(ch) <= 126):
        raise ValueError(f'invalid coefficient character: {ch!r}')
    return (ord(ch.upper()) - 77) / 10.0


def encode_coefficients(coefficients: list[float]) -> str:
    chars = []
    for value in coefficients:
        ordinal = int(round(float(value) * 10.0 + 77))
        ordinal = max(ord('A'), min(ord('Z'), ordinal))
        chars.append(chr(ordinal))
    return ''.join(chars)


def _clean_code(raw: str) -> str:
    return ''.join(ch for ch in str(raw).strip().upper() if not ch.isspace() and ch not in {'-', '_'})


def decode_code(raw: str) -> SprottCode:
    text = _clean_code(raw)
    warnings: list[str] = []
    if not text:
        return SprottCode(str(raw), '', 'Unknown family', 0, 0, 'unknown', [], ['empty code'])
    family = text[0]
    meta = describe_family(family)
    coeff_chars = text[1:]
    coefficients = []
    for ch in coeff_chars:
        try:
            coefficients.append(decode_coefficient_char(ch))
        except ValueError as exc:
            warnings.append(str(exc))
    expected = meta['coefficient_count']
    if meta['kind'] in {'map', 'flow'}:
        if len(coefficients) < expected:
            warnings.append(f'expected {expected} coefficients, got {len(coefficients)}; missing values are treated as zero')
        elif len(coefficients) > expected:
            warnings.append(f'expected {expected} coefficients, got {len(coefficients)}; extra values are ignored by simulators')
    elif meta['kind'] == 'special':
        warnings.append('special-function Sprott families are documented but not implemented yet')
    else:
        warnings.append('unknown Sprott family letter')
    return SprottCode(
        raw=str(raw),
        family_letter=family,
        family_name=meta['family_name'],
        dimension=int(meta['dimension']),
        order=int(meta['order']),
        kind=meta['kind'],
        coefficients=coefficients,
        warnings=warnings,
    )
