from __future__ import annotations

import os

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from core.sprott.visual import (
    PROJECTIONS,
    SprottVisualConfig,
    color_values,
    projection_axes,
    unit_sphere_projection,
    visual_preset,
)
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


def test_unit_sphere_projection_is_stable_and_reports_retained_rows():
    values = np.array([
        [3.0, 4.0, 0.0, 11.0],
        [0.0, 0.0, 0.0, 12.0],
        [-1.0e308, 0.0, 0.0, 13.0],
    ])
    projected, retained = unit_sphere_projection(values)
    assert 'esfera unitaria' in PROJECTIONS
    assert retained.tolist() == [True, False, True]
    assert np.all(np.isfinite(projected))
    assert np.allclose(np.linalg.norm(projected, axis=1), 1.0)
    assert np.allclose(projected[0], [0.6, 0.8, 0.0])
    assert np.allclose(projected[1], [-1.0, 0.0, 0.0])
    with pytest.raises(ValueError, match='dimensión 3'):
        unit_sphere_projection(np.ones((3, 2)))


def test_sprott_canvas_headless_export(tmp_path):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    app = QApplication.instance() or QApplication([])
    trajectory = np.column_stack([
        np.sin(np.linspace(0, 20, 600)),
        np.cos(np.linspace(0, 20, 600)),
        np.linspace(-1, 1, 600),
    ])
    canvas = Sprott2DCanvas()
    config = visual_preset('Color por profundidad')
    canvas.plot_trajectory(trajectory, config)
    out = canvas.export_image(tmp_path / 'sprott.png')
    assert out.exists()
    assert out.stat().st_size > 1000
    sphere = SprottVisualConfig(
        projection='esfera unitaria', color_by='radio', show_axes=True
    )
    canvas.plot_trajectory(trajectory, sphere)
    assert canvas.ax.name == '3d'
    sphere_out = canvas.export_image(tmp_path / 'sprott-sphere.png')
    assert sphere_out.exists()
    assert sphere_out.stat().st_size > 1000
    with pytest.raises(ValueError, match='dimensión 3'):
        canvas.plot_trajectory(np.ones((10, 2)), sphere)
    canvas.deleteLater()
    app.processEvents()
