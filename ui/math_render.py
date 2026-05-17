from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image

_CACHE_DIR = Path(tempfile.gettempdir()) / 'lorenz_app_math_cache'
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def render_math_to_path(expression: str, *, size: int = 14, color: str = 'black') -> str:
    """Render a TeX-like math expression to a cached PNG file and return its path.

    Falls back to plain text rendering if MathText parsing fails, so the GUI does
    not crash because of a malformed or unsupported expression.
    """
    key = hashlib.sha256(f'{expression}|{size}|{color}'.encode('utf-8')).hexdigest()
    out_path = _CACHE_DIR / f'{key}.png'
    if not out_path.exists():
        prop = FontProperties(size=size)
        try:
            math_to_image(expression, str(out_path), prop=prop, dpi=180, format='png', color=color)
        except Exception:
            fig = Figure(figsize=(8, 0.55), dpi=180)
            FigureCanvasAgg(fig)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            plain = expression.strip()
            if plain.startswith('$') and plain.endswith('$') and len(plain) >= 2:
                plain = plain[1:-1]
            plain = plain.replace('\\', '\\').replace('\n', ' ').replace('\t', ' ')
            ax.text(0.01, 0.5, plain, fontsize=size, color=color, va='center', ha='left')
            fig.savefig(
                out_path,
                format='png',
                dpi=180,
                bbox_inches='tight',
                pad_inches=0.02,
                facecolor='white',
            )
    return out_path.as_uri() if os.name != 'nt' else out_path.resolve().as_uri()
