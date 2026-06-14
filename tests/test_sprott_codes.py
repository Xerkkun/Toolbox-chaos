from __future__ import annotations

from core.sprott.codes import coefficient_count, decode_code, decode_coefficient_char


def test_decode_coefficient_char_reference_values():
    assert decode_coefficient_char('M') == 0.0
    assert decode_coefficient_char('A') == -1.2
    assert decode_coefficient_char('Y') == 1.2


def test_family_mapping():
    assert decode_code('A').kind == 'map'
    assert decode_code('A').dimension == 1
    assert decode_code('A').order == 2
    assert decode_code('E').kind == 'map'
    assert decode_code('E').dimension == 2
    assert decode_code('E').order == 2
    assert decode_code('I').kind == 'map'
    assert decode_code('I').dimension == 3
    assert decode_code('I').order == 2
    assert decode_code('Q').kind == 'flow'
    assert decode_code('Q').dimension == 3
    assert decode_code('Q').order == 2


def test_coefficient_counts_for_quadratic_families():
    assert coefficient_count(1, 2) == 3
    assert coefficient_count(2, 2) == 12
    assert coefficient_count(3, 2) == 30
    assert coefficient_count(4, 2) == 60
