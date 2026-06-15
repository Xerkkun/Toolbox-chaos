from __future__ import annotations

from pathlib import Path
import os
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import matplotlib
import numpy as np
import pyqtgraph
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication

from core.native import library
from core.lorenz import simulate_system, system_defaults
from core.sprott import decode_code, multi_indices
from core.sprott.catalog import load_synthetic_examples
from tools.generate_sprott_example_thumbnails import render_example_thumbnail
from ui.sprott_explorer_tab import SprottExplorerTab


def main() -> int:
    _ = (matplotlib, np, pyqtgraph, QtCore)

    library()

    params, initial = system_defaults('lorenz')
    t, states = simulate_system('lorenz', initial, params, dt=0.01, T=0.1, method_key='rk4')
    if t.shape[0] < 2 or states.shape != (t.shape[0], 3):
        raise RuntimeError(f'Unexpected Lorenz output shapes: t={t.shape}, states={states.shape}')
    if not np.all(np.isfinite(states)):
        raise RuntimeError('Lorenz smoke simulation returned non-finite values.')

    dictionary = REPO_ROOT / 'assets' / 'chaos_dictionary.pdf'
    if not dictionary.exists():
        raise FileNotFoundError(f'Required educational asset is missing: {dictionary}')

    code = decode_code('AWMA')
    if code.family_letter != 'A' or code.dimension != 1 or code.order != 2:
        raise RuntimeError(f'Unexpected Sprott decode result: {code}')
    if len(multi_indices(2, 2)) != 6:
        raise RuntimeError('Unexpected Sprott monomial count for D=2, O=2.')
    examples = load_synthetic_examples()
    if len(examples) < 10:
        raise RuntimeError('Sprott synthetic examples did not load.')
    if not all(item.get('learning_goal') and item.get('visual_intent') for item in examples):
        raise RuntimeError('Sprott synthetic examples must include learning_goal and visual_intent.')

    app = QApplication.instance() or QApplication([])
    first_visual = next((item for item in examples if item.get('starter_label') == 'Primera imagen bonita'), examples[0])
    thumb_dir = REPO_ROOT / '.pytest_tmp' / 'smoke_sprott'
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb = render_example_thumbnail(first_visual, thumb_dir / 'smoke_thumb.png', app=app)
    if not thumb.exists() or thumb.stat().st_size < 1000:
        raise RuntimeError('Sprott example thumbnail smoke render failed.')

    tab = SprottExplorerTab()
    if tab.sections.count() != 8:
        raise RuntimeError(f'Unexpected Sprott tab section count: {tab.sections.count()}')
    tab.deleteLater()
    app.processEvents()

    print('Smoke test OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
