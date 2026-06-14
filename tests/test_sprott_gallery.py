from __future__ import annotations

from pathlib import Path
import shutil

from core.sprott.gallery import ATTRIBUTION_WARNING, build_metadata, list_gallery_entries, save_gallery_entry


def test_gallery_metadata_and_local_save():
    base = Path.cwd() / '.pytest_tmp' / 'sprott_gallery'
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    try:
        render = base / 'render_source.png'
        thumb = base / 'thumb_source.png'
        render.write_bytes(b'png-render')
        thumb.write_bytes(b'png-thumb')
        metadata = build_metadata(
            code='AWMA',
            source='synthetic',
            simulation={'iterations': 10, 'transient': 1},
            style={'projection': 'x-y'},
            classification={'state': 'candidate_chaotic'},
            notes='test',
        )
        assert metadata['attribution_warning'] == ATTRIBUTION_WARNING
        entry_dir = save_gallery_entry(render_path=render, thumbnail_path=thumb, metadata=metadata, base=base / 'gallery')
        assert (entry_dir / 'render.png').exists()
        assert (entry_dir / 'thumbnail.png').exists()
        assert (entry_dir / 'metadata.json').exists()
        entries = list_gallery_entries(base / 'gallery')
        assert len(entries) == 1
        assert entries[0]['code'] == 'AWMA'
        assert Path(entries[0]['_render_path']).name == 'render.png'
    finally:
        if base.exists():
            shutil.rmtree(base)
