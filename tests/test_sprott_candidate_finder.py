from __future__ import annotations

from tools.find_sprott_synthetic_examples import (
    candidate_passes,
    candidate_record,
    recommended_visual_for_code,
)
from tools.promote_sprott_synthetic_examples import promote_candidate_record


def test_candidate_record_and_pass_filter_for_known_map():
    record = candidate_record('EWMWAMMMPMMMM', iterations=1400, transient=160)
    assert record['classification']['state'] == 'candidate_chaotic'
    assert candidate_passes(record, min_finite=200)
    assert record['parameters']['dimension'] == 2


def test_candidate_pass_filter_rejects_fixed_point():
    record = candidate_record('AMMM', iterations=140, transient=5)
    assert record['classification']['state'] == 'fixed_point'
    assert not candidate_passes(record)


def test_recommended_visuals_follow_dimension():
    visual = recommended_visual_for_code('MSLMFPHPIEFTPJJLOJNNTQQIINJUKJUUPPRMFIRIMELNKERJJIGJSGFLLOMSU')
    assert visual['color_by'] == 'w'
    assert visual['projection'] == 'x-y'


def test_promote_candidate_requires_pedagogical_fields():
    record = candidate_record('EWMWAMMMPMMMM', iterations=900, transient=100)
    record['id'] = 'candidate_demo'
    record['learning_goal'] = 'Teach how a reviewed generated candidate becomes a curated lesson.'
    record['visual_intent'] = 'Show a compact folded projection with a reviewed visual style.'
    promoted = promote_candidate_record(record)
    assert promoted['id'] == 'synthetic_candidate_demo'
    assert promoted['source'] == 'synthetic educational example'
    assert promoted['thumbnail'] == 'examples/thumbnails/synthetic_candidate_demo.png'
