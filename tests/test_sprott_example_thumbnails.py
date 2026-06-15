from __future__ import annotations

import shutil
from pathlib import Path

from core.sprott.catalog import load_synthetic_examples
from tools.generate_sprott_example_thumbnails import (
    render_example_thumbnail,
    thumbnail_relative_path,
    update_thumbnail_fields,
)


def test_thumbnail_relative_path_is_public_asset_relative():
    assert thumbnail_relative_path('synthetic_demo') == 'examples/thumbnails/synthetic_demo.png'


def test_update_thumbnail_fields_only_changes_rendered_examples():
    data = {
        'examples': [
            {'id': 'one'},
            {'id': 'two', 'thumbnail': 'old.png'},
        ]
    }
    assert update_thumbnail_fields(data, ['two'])
    assert 'thumbnail' not in data['examples'][0]
    assert data['examples'][1]['thumbnail'] == 'examples/thumbnails/two.png'


def test_render_example_thumbnail_to_pytest_tmp():
    base = Path.cwd() / '.pytest_tmp' / 'sprott_example_thumbnail'
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    try:
        example = next(item for item in load_synthetic_examples() if item['id'] == 'synthetic_e_henon_first_beauty')
        output = render_example_thumbnail(example, base / 'thumb.png')
        assert output.exists()
        assert output.stat().st_size > 1000
    finally:
        if base.exists():
            shutil.rmtree(base)
