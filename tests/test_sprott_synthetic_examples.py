from __future__ import annotations

import json
from pathlib import Path

from core.sprott import decode_code
from core.sprott.catalog import examples_path, load_synthetic_examples
from core.sprott.search import classify_candidate, simulate_candidate


REQUIRED_STARTERS = {
    'Primera imagen bonita',
    'Color por profundidad',
    'Bandas tipo libro',
    'Mapa 4D',
    'Flujo 3D',
    'Cuando algo sale mal',
    'Mejorar imagen pobre',
}


def test_synthetic_examples_are_curated_lessons():
    with examples_path().open('r', encoding='utf-8') as handle:
        document = json.load(handle)
    examples = document['examples']
    assert document['schema'] >= 2
    assert 10 <= len(examples) <= 14
    ids = [item['id'] for item in examples]
    assert len(ids) == len(set(ids))
    starters = {item.get('starter_label') for item in examples if item.get('starter_label')}
    assert REQUIRED_STARTERS <= starters

    for item in examples:
        assert item['source'] == 'synthetic educational example'
        assert item.get('category')
        assert len(item.get('learning_goal', '')) >= 24
        assert len(item.get('visual_intent', '')) >= 24
        assert item['learning_goal'] != item['visual_intent']
        assert item.get('expected_status')
        assert item.get('thumbnail', '').startswith('examples/thumbnails/')
        decoded = decode_code(item['code'])
        params = item['parameters']
        assert decoded.kind == params['kind']
        assert decoded.dimension == params['dimension']
        assert decoded.order == params['order']
        assert item.get('visual', {}).get('projection')


def test_public_examples_do_not_embed_historical_dictionary_assets():
    text = examples_path().read_text(encoding='utf-8')
    forbidden_names = ['BOOKFIGS.DIC', 'SELECTED.DIC', 'SPECIAL.DIC', 'SADISK.ZIP', 'SA.EXE', 'PROG28']
    for name in forbidden_names:
        assert name not in text


def _example_by_id(example_id: str) -> dict:
    for item in load_synthetic_examples():
        if item['id'] == example_id:
            return item
    raise AssertionError(f'Missing example: {example_id}')


def _classify_example(example_id: str, *, iterations: int, transient: int) -> str:
    item = _example_by_id(example_id)
    params = item['parameters']
    result = simulate_candidate(
        item['code'],
        n_iter=iterations,
        transient=transient,
        h=float(params.get('h', 0.01)),
        method=str(params.get('method', 'rk4')),
        divergence_threshold=float(params.get('divergence_threshold', 1e9)),
        backend='c',
    )
    classification = classify_candidate(
        result['post_transient'],
        divergence_threshold=float(params.get('divergence_threshold', 1e9)),
    )
    return classification['state']


def test_selected_examples_match_their_teaching_role():
    assert _classify_example('synthetic_e_henon_first_beauty', iterations=1600, transient=200) == 'candidate_chaotic'
    assert _classify_example('synthetic_a_fixed_point_poor', iterations=120, transient=1) == 'fixed_point'
    assert _classify_example('synthetic_a_divergent_warning', iterations=420, transient=0) == 'divergent'


def test_referenced_public_thumbnails_exist():
    asset_root = Path(__file__).resolve().parents[1] / 'assets' / 'sprott'
    for item in load_synthetic_examples():
        path = asset_root / item['thumbnail']
        assert path.exists(), item['thumbnail']
        assert path.stat().st_size > 1000, item['thumbnail']
