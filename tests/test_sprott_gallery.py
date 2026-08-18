from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from core.image_security import ImageSecurityError, confined_png, validate_png_file
from core.sprott.gallery import (
    ATTRIBUTION_WARNING,
    build_metadata,
    list_gallery_entries,
    load_gallery_entry,
    save_gallery_entry,
)


def _write_png(path: Path, color: tuple[int, int, int] = (20, 40, 60)) -> None:
    Image.new('RGB', (4, 3), color).save(path, format='PNG')


def test_gallery_metadata_and_local_save(tmp_path):
    render = tmp_path / 'render_source.png'
    thumb = tmp_path / 'thumb_source.png'
    _write_png(render)
    _write_png(thumb, (80, 100, 120))
    metadata = build_metadata(
        code='AWMA',
        source='synthetic',
        simulation={'iterations': 10, 'transient': 1},
        style={'projection': 'x-y'},
        classification={'state': 'candidate_chaotic'},
        notes='test',
    )
    assert metadata['attribution_warning'] == ATTRIBUTION_WARNING
    entry_dir = save_gallery_entry(
        render_path=render, thumbnail_path=thumb, metadata=metadata,
        base=tmp_path / 'gallery',
    )
    assert (entry_dir / 'render.png').exists()
    assert (entry_dir / 'thumbnail.png').exists()
    assert (entry_dir / 'metadata.json').exists()
    entries = list_gallery_entries(tmp_path / 'gallery')
    assert len(entries) == 1
    assert entries[0]['code'] == 'AWMA'
    assert Path(entries[0]['_render_path']).name == 'render.png'


def test_gallery_rejects_svg_or_spoofed_png_inputs(tmp_path):
    gallery = tmp_path / 'gallery'
    entry = gallery / 'entry'
    entry.mkdir(parents=True)
    (entry / 'render.svg').write_text('<svg/>', encoding='utf-8')
    (entry / 'thumbnail.png').write_text('<svg/>', encoding='utf-8')
    (entry / 'metadata.json').write_text(
        '{"render": "render.svg", "thumbnail": "thumbnail.png"}',
        encoding='utf-8',
    )

    with pytest.raises(ImageSecurityError):
        load_gallery_entry(entry, base=gallery)
    assert list_gallery_entries(gallery) == []
    with pytest.raises(ImageSecurityError):
        validate_png_file(entry / 'thumbnail.png')


def test_confined_png_rejects_remote_absolute_and_traversal_paths(tmp_path):
    root = tmp_path / 'assets'
    root.mkdir()
    image = root / 'safe.png'
    _write_png(image)
    assert confined_png(root, 'safe.png') == image.resolve()

    for unsafe in ('https://example.test/image.png', '../safe.png', str(image.resolve())):
        with pytest.raises(ImageSecurityError):
            confined_png(root, unsafe)
