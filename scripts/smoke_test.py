from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib
import numpy as np
import pyqtgraph
from PyQt6 import QtCore

from core.native import library
from core.lorenz import simulate_system, system_defaults


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

    print('Smoke test OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
