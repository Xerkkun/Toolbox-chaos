from __future__ import annotations

from pathlib import Path
import shutil

import numpy as np

from core.sprott.catalog import load_synthetic_examples
from core.sprott.references import index_local_reference_folder
from core.sprott.search import simulate_candidate


def test_synthetic_map_short_simulation_does_not_fail():
    result = simulate_candidate('AWMA', n_iter=32, transient=4)
    trajectory = result['trajectory']
    assert trajectory.shape == (33, 1)
    assert np.isfinite(trajectory[:8]).all()


def test_synthetic_examples_load():
    examples = load_synthetic_examples()
    assert examples
    assert all(item.get('source') == 'synthetic educational example' for item in examples)


def test_importer_indexes_without_copying():
    base = Path.cwd() / '.pytest_tmp' / 'sprott_importer_test'
    if base.exists():
        shutil.rmtree(base)
    source = base / 'local_refs'
    try:
        source.mkdir(parents=True)
        dic = source / 'LOCAL.DIC'
        dic.write_text('AWMA\n', encoding='utf-8')
        ignored = source / 'note.txt'
        ignored.write_text('ignored', encoding='utf-8')

        inventory = index_local_reference_folder(source)
        assert len(inventory) == 1
        assert inventory[0]['name'] == 'LOCAL.DIC'
        assert inventory[0]['category'] == 'dictionary'
        assert Path(inventory[0]['path']).read_text(encoding='utf-8') == 'AWMA\n'
    finally:
        if base.exists():
            shutil.rmtree(base)
