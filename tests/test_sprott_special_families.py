from __future__ import annotations

import math
from core.sprott.codes import decode_code, explain_support_status
from core.sprott.references import classify_dic_entry
from core.sprott.search import simulate_candidate


def test_decode_code_ypsrtgnd():
    code = decode_code("YPSRTGND")
    assert code.kind == "special"
    assert code.dimension == 4
    
    meta = classify_dic_entry("YPSRTGND")
    assert meta["support"] == "simulable especial"


def test_simulate_family_y():
    # Y requires 10 coefficients.
    res = simulate_candidate("YMMMMMMMMMM", n_iter=100, transient=0)
    assert res["trajectory"].shape == (100, 4)
    assert "equations" in res
    assert "X'" in res["equations"]
    assert "Z'" in res["equations"]


def test_simulate_family_bracket():
    # Family [ has 14 coefficients. Code length 15: "[MMMMMMMMMMMMMM"
    res = simulate_candidate("[MMMMMMMMMMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "|X|^" in res["equations"]


def test_simulate_family_backslash():
    # Family \ has 18 coefficients. Code length 19: "\MMMMMMMMMMMMMMMMMM"
    res = simulate_candidate("\\MMMMMMMMMMMMMMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "sin" in res["equations"]


def test_simulate_family_bracket_right():
    # Family ] has 6 coefficients. Code length 7: "]MMMMMM"
    res = simulate_candidate("]MMMMMM", n_iter=50, transient=0)
    assert res["trajectory"].shape == (50, 4)
    assert "equations" in res
    assert "theta" in res["equations"]


def test_simulate_family_caret():
    # Family ^ has 9 coefficients. Code length 10: "^MMMMMMMMM"
    res = simulate_candidate("^MMMMMMMMM", n_iter=100, transient=0)
    assert res["trajectory"].shape == (100, 4)
    # verify Z (index 2) stays in [0, 2*pi)
    z_vals = res["trajectory"][:, 2]
    for z in z_vals:
        assert 0.0 <= z < 2.0 * math.pi
    assert "equations" in res
    assert "mod 2*pi" in res["equations"]


def test_family_z_pending():
    # Z has 10 coefficients.
    res = explain_support_status("ZMMMMMMMMMM")
    assert res["support"] == "special_pending"
    assert "Z (AND/OR)" in res["reason"] or "Z" in res["reason"]
    
    entry = classify_dic_entry("ZMMMMMMMMMM")
    assert entry["support"] == "especial pendiente: validar AND/OR"
    assert entry["kind"] == "special"
