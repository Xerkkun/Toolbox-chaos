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


# List of groups for polynomial families A-X
POLYNOMIAL_GROUPS = [
    ('ABCD', 'map', 1, 'Polynomial map 1D'),
    ('EFGH', 'map', 2, 'Polynomial map 2D'),
    ('IJKL', 'map', 3, 'Polynomial map 3D'),
    ('MNOP', 'map', 4, 'Polynomial map 4D'),
    ('QRST', 'flow', 3, 'Polynomial flow 3D'),
    ('UVWX', 'flow', 4, 'Polynomial flow 4D'),
]

# Construct POLYNOMIAL_FAMILIES dictionary
POLYNOMIAL_FAMILIES = {}
for letters, kind, dimension, family_name in POLYNOMIAL_GROUPS:
    for offset, letter in enumerate(letters):
        POLYNOMIAL_FAMILIES[letter] = {
            'letter': letter,
            'kind': kind,
            'dimension': dimension,
            'order': offset + 2,
            'family_name': f'{family_name}, order {offset + 2}',
        }

# Special families Y and Z, plus any registered symbols or characters
SPECIAL_FAMILIES = {
    'Y': {
        'letter': 'Y',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 10,
        'family_name': 'Special-function family Y (Absolute Values)',
        'status': 'implemented',
    },
    'Z': {
        'letter': 'Z',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 10,
        'family_name': 'Special-function family Z (AND/OR)',
        'status': 'pending_semantics_validation',
    },
    '[': {
        'letter': '[',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 14,
        'family_name': 'Special-function family [ (Power Absolute)',
        'status': 'implemented',
    },
    '\\': {
        'letter': '\\',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 18,
        'family_name': 'Special-function family \\ (Sines)',
        'status': 'implemented',
    },
    ']': {
        'letter': ']',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 6,
        'family_name': 'Special-function family ] (Rotational Sine)',
        'status': 'implemented',
    },
    '^': {
        'letter': '^',
        'kind': 'special',
        'dimension': 4,
        'order': 0,
        'coefficient_count': 9,
        'family_name': 'Special-function family ^ (Forced Oscillator)',
        'status': 'implemented',
    },
}


def _family_table() -> dict[str, dict]:
    table = {}
    table.update(POLYNOMIAL_FAMILIES)
    table.update(SPECIAL_FAMILIES)
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
    key = letter.strip()[:1]
    key = key.upper()
    data = dict(FAMILY_TABLE.get(key, {
        'letter': key,
        'kind': 'unknown',
        'dimension': 0,
        'order': 0,
        'family_name': 'Special-function family pending identification',
    }))
    if 'coefficient_count' not in data:
        data['coefficient_count'] = coefficient_count(data['dimension'], data['order'], data['kind'])
    return data


def explain_support_status(code_text: str) -> dict:
    from core.sprott.dic_parser import select_best_code_candidate
    
    raw = str(code_text).strip()
    best = select_best_code_candidate(raw)
    
    if not best:
        return {
            "normalized_code": "",
            "family": "",
            "kind": "unknown",
            "support": "unknown",
            "reason": "No se encontró ningún candidato de código Sprott en la línea.",
            "recommended_action": "Verifica que la línea contenga un código Sprott válido de al menos 3 caracteres."
        }
        
    norm = best.normalized_code
    family = norm[0]
    meta = describe_family(family)
    
    tokens = raw.split()
    is_first_token = bool(tokens and tokens[0] == best.raw_token)
    
    if best.prefix_removed or best.suffix_removed or not is_first_token:
        return {
            "normalized_code": norm,
            "family": family,
            "kind": meta['kind'],
            "support": "parse_error",
            "reason": "La línea parece tener prefijo antes del código; se propone un candidato normalizado.",
            "recommended_action": f"Usa el candidato propuesto '{norm}' para la simulación."
        }
        
    if meta['kind'] in ('map', 'flow'):
        return {
            "normalized_code": norm,
            "family": family,
            "kind": meta['kind'],
            "support": "simulable",
            "reason": "Familia A-X implementada como mapa/flujo polinomial.",
            "recommended_action": "Puedes simular y graficar este código directamente."
        }
    elif meta['kind'] == 'special':
        status = meta.get('status')
        if status == 'implemented':
            return {
                "normalized_code": norm,
                "family": family,
                "kind": meta['kind'],
                "support": "simulable_special",
                "reason": f"Familia especial {family} ({meta['family_name']}) implementada mediante simulación de funciones especiales. Este símbolo no es basura: identifica una familia especial de Sprott.",
                "recommended_action": "Puedes simular y graficar este código directamente."
            }
        elif family == 'Z':
            return {
                "normalized_code": norm,
                "family": family,
                "kind": meta['kind'],
                "support": "special_pending",
                "reason": "La familia especial Z (AND/OR) está pendiente de validar su semántica exacta. Este símbolo no es basura: identifica una familia especial de Sprott.",
                "recommended_action": "No simulable por el momento: requiere validar la lógica lógica de Sprott."
            }
        else:
            return {
                "normalized_code": norm,
                "family": family,
                "kind": meta['kind'],
                "support": "special_pending",
                "reason": "La familia pertenece a funciones especiales; está reconocida pero aún no implementada.",
                "recommended_action": "Puedes marcarla como pendiente de familia especial o revisar la referencia local."
            }
    else:
        return {
            "normalized_code": norm,
            "family": family,
            "kind": "unknown",
            "support": "unknown",
            "reason": "El primer carácter no coincide con una familia registrada.",
            "recommended_action": "Verifica si el código es correcto o si corresponde a una familia personalizada."
        }


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
        status = meta.get('status')
        if status == 'implemented':
            if len(coefficients) < expected:
                warnings.append(f'expected {expected} coefficients, got {len(coefficients)}; missing values are treated as zero')
            elif len(coefficients) > expected:
                warnings.append(f'expected {expected} coefficients, got {len(coefficients)}; extra values are ignored by simulators')
        else:
            warnings.append(f"special-function Sprott family '{family}' ({meta['family_name']}) is recognized but not implemented yet: {status}")
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
