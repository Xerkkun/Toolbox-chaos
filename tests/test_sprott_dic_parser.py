from __future__ import annotations

from core.sprott.dic_parser import extract_code_candidates, select_best_code_candidate


def test_parse_clean_line():
    line = "EWMWAMMMPMMMM F=2.4 L=0.1"
    cand = select_best_code_candidate(line)
    assert cand is not None
    assert cand.normalized_code == "EWMWAMMMPMMMM"
    assert cand.strategy == "direct_token"
    assert cand.confidence == "high"


def test_parse_line_with_prefixes():
    # Numbering prefix "12:"
    line1 = "12: EWMWAMMMPMMMM F=2.4 L=0.1"
    cand1 = select_best_code_candidate(line1)
    assert cand1 is not None
    assert cand1.normalized_code == "EWMWAMMMPMMMM"
    assert cand1.strategy == "direct_token"  # "EWMWAMMMPMMMM" is a separate direct token

    # Prefix attached to token, e.g. "12:EWMWAMMMPMMMM"
    line2 = "12:EWMWAMMMPMMMM"
    cand2 = select_best_code_candidate(line2)
    assert cand2 is not None
    assert cand2.normalized_code == "EWMWAMMMPMMMM"
    assert cand2.strategy == "soft_cleaning"
    assert cand2.prefix_removed == "12:"


def test_parse_quoted_lines():
    line = '"EWMWAMMMPMMMM"'
    cand = select_best_code_candidate(line)
    assert cand is not None
    assert cand.normalized_code == "EWMWAMMMPMMMM"
    assert cand.strategy == "direct_token"


def test_special_family_line():
    line = "YABC"
    cand = select_best_code_candidate(line)
    assert cand is not None
    assert cand.normalized_code == "YABC"
    assert cand.confidence == "medium"
    assert "Y" in cand.reason


def test_line_without_candidate():
    assert select_best_code_candidate("Chapter 3") is None
    assert select_best_code_candidate("12: NoCodeHere") is None
    assert select_best_code_candidate("") is None


def test_preserving_registered_symbols():
    # '[' is registered in SPECIAL_FAMILIES in codes.py
    line = "[ABC"
    cand = select_best_code_candidate(line)
    assert cand is not None
    assert cand.normalized_code == "[ABC"
    assert cand.confidence == "medium"
    assert "[" in cand.reason
