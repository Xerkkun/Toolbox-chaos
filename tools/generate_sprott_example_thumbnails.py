from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtWidgets import QApplication

from core.sprott.catalog import examples_path, load_synthetic_examples
from core.sprott.search import simulate_candidate
from core.sprott.visual import SprottVisualConfig
from ui.sprott_canvases import Sprott2DCanvas


SYNTHETIC_SOURCE = 'synthetic educational example'


def default_thumbnail_dir() -> Path:
    return REPO_ROOT / 'assets' / 'sprott' / 'examples' / 'thumbnails'


def thumbnail_relative_path(example_id: str) -> str:
    return f'examples/thumbnails/{example_id}.png'


def thumbnail_path(example: dict, output_dir: str | Path | None = None) -> Path:
    base = Path(output_dir) if output_dir else default_thumbnail_dir()
    return base / f"{example['id']}.png"


def simulation_kwargs(example: dict) -> dict:
    params = example.get('parameters', {})
    return {
        'n_iter': int(params.get('iterations', 2400)),
        'transient': int(params.get('transient', 200)),
        'h': float(params.get('h', 0.01)),
        'method': str(params.get('method', 'rk4')),
        'divergence_threshold': float(params.get('divergence_threshold', 1e9)),
        'backend': str(params.get('backend', 'c')),
    }


def render_example_thumbnail(example: dict, output_path: str | Path, *, app: QApplication | None = None) -> Path:
    if example.get('source', SYNTHETIC_SOURCE) != SYNTHETIC_SOURCE:
        raise ValueError(f"Refusing to render non-synthetic public example: {example.get('id', '<missing id>')}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    app = app or QApplication.instance() or QApplication([])
    result = simulate_candidate(example['code'], **simulation_kwargs(example))
    trajectory = result['post_transient']
    if len(trajectory) == 0:
        trajectory = result['trajectory']
    config = SprottVisualConfig.from_dict(example.get('visual', {}))
    canvas = Sprott2DCanvas()
    # The surrounding manual or web card supplies the explanatory caption.
    # Keeping the raster titleless prevents duplicated headings and gives the
    # trajectory the full plotting area.
    canvas.plot_trajectory(trajectory, config, title='')
    canvas.export_thumbnail(target)
    canvas.deleteLater()
    app.processEvents()
    return target


def _read_examples_document(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {'schema': 2, 'examples': data}
    return data


def update_thumbnail_fields(data: dict, rendered_ids: Iterable[str]) -> bool:
    rendered = set(rendered_ids)
    changed = False
    for example in data.get('examples', []):
        example_id = example.get('id')
        if example_id in rendered:
            relative = thumbnail_relative_path(example_id)
            if example.get('thumbnail') != relative:
                example['thumbnail'] = relative
                changed = True
    return changed


def generate_thumbnails(
    *,
    examples_file: str | Path | None = None,
    output_dir: str | Path | None = None,
    update_json: bool = True,
    ids: Iterable[str] | None = None,
    limit: int | None = None,
) -> list[Path]:
    source = Path(examples_file) if examples_file else examples_path()
    output = Path(output_dir) if output_dir else default_thumbnail_dir()
    data = _read_examples_document(source)
    examples = list(data.get('examples', []))
    requested_ids = set(ids or [])
    if requested_ids:
        examples = [example for example in examples if example.get('id') in requested_ids]
        found_ids = {example.get('id') for example in examples}
        missing_ids = sorted(requested_ids - found_ids)
        if missing_ids:
            raise ValueError(f"Example ids not found: {', '.join(missing_ids)}")
    if limit is not None:
        examples = examples[: int(limit)]
    app = QApplication.instance() or QApplication([])
    rendered: list[Path] = []
    rendered_ids: list[str] = []
    for example in examples:
        if not example.get('id'):
            raise ValueError('Every example needs an id before rendering thumbnails.')
        path = thumbnail_path(example, output)
        rendered.append(render_example_thumbnail(example, path, app=app))
        rendered_ids.append(example['id'])
    if update_json and output.resolve() == default_thumbnail_dir().resolve():
        if update_thumbnail_fields(data, rendered_ids):
            with source.open('w', encoding='utf-8') as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write('\n')
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Generate public thumbnails for synthetic Sprott examples.')
    parser.add_argument('--examples', default=str(examples_path()), help='Path to synthetic_examples.json.')
    parser.add_argument('--output-dir', default=str(default_thumbnail_dir()), help='Directory for PNG thumbnails.')
    parser.add_argument('--no-update-json', action='store_true', help='Do not update thumbnail fields in the JSON.')
    parser.add_argument('--ids', nargs='*', default=[], help='Render only these example ids.')
    parser.add_argument('--limit', type=int, default=None, help='Render only the first N examples.')
    args = parser.parse_args(argv)
    paths = generate_thumbnails(
        examples_file=args.examples,
        output_dir=args.output_dir,
        update_json=not args.no_update_json,
        ids=args.ids,
        limit=args.limit,
    )
    for path in paths:
        print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
