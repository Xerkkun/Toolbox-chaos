from __future__ import annotations

from pathlib import Path

from PIL import Image

from ui.sprott_explorer_tab import _markdown_to_clean_html


def test_markdown_images_are_local_confined_decodable_png(tmp_path: Path):
    image = tmp_path / 'figure.png'
    Image.new('RGB', (3, 2), (10, 30, 50)).save(image, format='PNG')

    rendered = _markdown_to_clean_html(
        '![Figura local](figure.png)', asset_root=tmp_path
    )
    assert image.resolve().as_uri() in rendered
    assert 'Imagen bloqueada' not in rendered


def test_markdown_blocks_remote_svg_and_traversal(tmp_path: Path):
    outside = tmp_path.parent / 'outside.png'
    Image.new('RGB', (1, 1), (0, 0, 0)).save(outside, format='PNG')
    markdown = '\n'.join(
        (
            '![Remota](https://example.test/attack.svg)',
            '![Traversal](../outside.png)',
            '![SVG local](attack.svg)',
        )
    )
    (tmp_path / 'attack.svg').write_text('<svg/>', encoding='utf-8')

    rendered = _markdown_to_clean_html(markdown, asset_root=tmp_path)
    assert rendered.count('Imagen bloqueada') == 3
    assert 'https://example.test' not in rendered
    assert outside.resolve().as_uri() not in rendered
