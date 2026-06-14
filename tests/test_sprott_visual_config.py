from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import QApplication

from core.sprott.visual import SprottVisualConfig, color_values, projection_axes, visual_preset
from ui.sprott_canvases import Sprott2DCanvas


def test_visual_config_round_trip():
    config = visual_preset('Color por profundidad')
    data = config.to_dict()
    restored = SprottVisualConfig.from_dict(data)
    assert restored.projection == config.projection
    assert restored.color_by == 'z'
    assert restored.palette == config.palette


def test_projection_and_color_values():
    values = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 8.0]])
    x, y, xlabel, ylabel = projection_axes(values, 'x-z')
    assert xlabel == 'x'
    assert ylabel == 'z'
    assert np.allclose(x, [1.0, 2.0])
    assert np.allclose(y, [3.0, 8.0])
    assert np.allclose(color_values(values, 'radio'), np.linalg.norm(values, axis=1))


def test_sprott_canvas_headless_export():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    base = Path.cwd() / '.pytest_tmp' / 'sprott_canvas_export'
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    app = QApplication.instance() or QApplication([])
    try:
        trajectory = np.column_stack([
            np.sin(np.linspace(0, 20, 600)),
            np.cos(np.linspace(0, 20, 600)),
            np.linspace(-1, 1, 600),
        ])
        canvas = Sprott2DCanvas()
        config = visual_preset('Color por profundidad')
        canvas.plot_trajectory(trajectory, config)
        out = canvas.export_image(base / 'sprott.png')
        assert out.exists()
        assert out.stat().st_size > 1000
        canvas.deleteLater()
        app.processEvents()
    finally:
        if base.exists():
            shutil.rmtree(base)
