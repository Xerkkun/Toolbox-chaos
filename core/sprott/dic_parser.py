from __future__ import annotations

import re
from dataclasses import dataclass
from math import comb
from pathlib import Path

@dataclass
class DicCodeCandidate:
    raw_line: str
    raw_token: str
    normalized_code: str
    strategy: str
    prefix_removed: str
    suffix_removed: str
    confidence: str
    reason: str


def extract_code_candidates(line: str) -> list[DicCodeCandidate]:
    line = line.strip()
    if not line:
        return []
    
    tokens = line.split()
    candidates = []
    
    from core.sprott.codes import FAMILY_TABLE
    
    for token in tokens:
        raw_token = token
        clean_token = raw_token.strip().strip('"\'')
        
        # Soft cleaning for suffix punctuation
        suffix_removed = ""
        while clean_token and clean_token[-1] in (',', ';', '.', ':', ')'):
            suffix_removed = clean_token[-1] + suffix_removed
            clean_token = clean_token[:-1]
            
        # Soft cleaning for prefix (numbering, labels, comments)
        prefix_removed = ""
        prefix_pattern = r'^(\d+[:)]|\[\d+\]|[Ff]ig(?:\.?(?:ure)?)?\.?|[#;*]+)\s*'
        match = re.match(prefix_pattern, clean_token)
        if match:
            prefix_removed = match.group(1)
            clean_token = clean_token[match.end():]
            
        # Re-strip quotes after prefix/suffix removal
        clean_token = clean_token.strip('"\'')
        
        # Require that the token is mostly uppercase to avoid matching normal English words (e.g. "Chapter")
        letters_in_token = [c for c in clean_token if c.isalpha()]
        if letters_in_token:
            upper_ratio = sum(1 for c in letters_in_token if c.isupper()) / len(letters_in_token)
            if upper_ratio < 0.6:
                continue
                
        norm_code = clean_token.upper()
        
        if len(norm_code) >= 3:
            first_char = norm_code[0]
            if first_char in FAMILY_TABLE:
                # Sprott codes contain mostly letters/monomial representations.
                # Allow standard characters but exclude numbers in coefficients
                if re.match(r'^[A-Z]+$', norm_code[1:]):
                    is_direct = (raw_token.strip().strip('"\'') == clean_token)
                    strategy = "direct_token" if is_direct else "soft_cleaning"
                    
                    meta = FAMILY_TABLE[first_char]
                    family_kind = meta['kind']
                    
                    if family_kind in ('map', 'flow'):
                        confidence = 'high' if is_direct else 'medium'
                        reason = "Familia A-X válida y simulable."
                    elif family_kind == 'special':
                        confidence = 'medium'
                        reason = "Familia especial Y/Z reconocida pero pendiente de implementación."
                    else:
                        confidence = 'low'
                        reason = "Familia desconocida."
                        
                    candidates.append(DicCodeCandidate(
                        raw_line=line,
                        raw_token=raw_token,
                        normalized_code=norm_code,
                        strategy=strategy,
                        prefix_removed=prefix_removed,
                        suffix_removed=suffix_removed,
                        confidence=confidence,
                        reason=reason
                    ))
                    
    # Refine confidence based on expected coefficient count
    for cand in candidates:
        code_str = cand.normalized_code
        first_char = code_str[0]
        meta = FAMILY_TABLE[first_char]
        
        if meta['kind'] in ('map', 'flow'):
            expected_len = 1 + meta['dimension'] * comb(meta['dimension'] + meta['order'], meta['order'])
            if len(code_str) == expected_len:
                cand.confidence = 'high'
                cand.reason = f"Familia {first_char} simulable con longitud de coeficientes exacta ({len(code_str)})."
            elif abs(len(code_str) - expected_len) <= 2:
                cand.reason = f"Familia {first_char} simulable con longitud de coeficientes cercana ({len(code_str)} vs esp. {expected_len})."
            else:
                cand.confidence = 'medium' if cand.confidence == 'high' else 'low'
                cand.reason = f"Familia {first_char} simulable pero con discrepancia de longitud ({len(code_str)} vs esp. {expected_len})."
        elif meta['kind'] == 'special':
            cand.confidence = 'medium'
            cand.reason = f"Familia especial {first_char} reconocida pero pendiente de simulación."
            
    return candidates


def select_best_code_candidate(line: str) -> DicCodeCandidate | None:
    candidates = extract_code_candidates(line)
    if not candidates:
        return None
        
    def sort_key(c: DicCodeCandidate):
        # Confidence score
        conf_score = {'high': 3, 'medium': 2, 'low': 1}.get(c.confidence, 0)
        
        # Support priority
        from core.sprott.codes import FAMILY_TABLE
        first_char = c.normalized_code[0]
        meta = FAMILY_TABLE[first_char]
        kind_score = {'map': 3, 'flow': 3, 'special': 2, 'unknown': 1}.get(meta['kind'], 0)
        
        # Length score
        len_score = len(c.normalized_code)
        
        return (conf_score, kind_score, len_score)
        
    sorted_candidates = sorted(candidates, key=sort_key, reverse=True)
    return sorted_candidates[0]
