from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import colormaps
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap

from core.sprott.visual import (
    SprottVisualConfig,
    background_color,
    color_values,
    downsample,
    finite_post_transient,
    foreground_color,
    mpl_colormap_name,
    projection_axes,
    quantize,
    sanitize_visual_config,
    unit_sphere_projection,
)


LOGGER = logging.getLogger(__name__)


class Sprott2DCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(7.2, 5.4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.last_values = np.empty((0, 1))
        self.last_config = SprottVisualConfig()
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
        self.reset_plot()

    def reset_plot(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('Trayectoria Sprott')
        self.ax.grid(alpha=0.2)
        self.fig.subplots_adjust(left=0.08, right=0.98, bottom=0.10, top=0.92)
        self.draw_idle()

    def plot_trajectory(self, trajectory, config: SprottVisualConfig | dict | None = None, title: str = 'Trayectoria Sprott'):
        cfg = sanitize_visual_config(config)
        values = downsample(finite_post_transient(trajectory), cfg.max_points)
        self.last_values = values
        self.last_config = cfg
        self.fig.clear()
        if cfg.projection == 'esfera unitaria':
            if values.shape[1] < 3:
                raise ValueError(
                    'La proyección esférica requiere una trayectoria de dimensión 3 o mayor.'
                )
            self._plot_unit_sphere(values, cfg, title)
        elif cfg.projection == '3D x-y-z' and values.shape[1] >= 3:
            self._plot_3d(values, cfg, title)
        else:
            self.ax = self.fig.add_subplot(111)
            self._plot_2d(values, cfg, title)
        self.draw_idle()

    def _plot_2d(self, values: np.ndarray, cfg: SprottVisualConfig, title: str):
        bg = background_color(cfg.background)
        fg = foreground_color(cfg.background)
        transparent = cfg.background == 'transparente'
        self.fig.patch.set_facecolor('none' if transparent else bg)
        self.fig.patch.set_alpha(0.0 if transparent else 1.0)
        self.ax.set_facecolor('none' if transparent else bg)
        self.ax.tick_params(colors=fg)
        for spine in self.ax.spines.values():
            spine.set_color(fg)

        if values.size == 0:
            self.ax.text(0.5, 0.5, 'Sin muestras finitas', color=fg, ha='center', va='center', transform=self.ax.transAxes)
            self._finish_axes(cfg, title, fg, 'x', 'y')
            return

        if values.shape[1] == 1 and not cfg.projection.startswith('n-'):
            projection = 'n-x'
        else:
            projection = cfg.projection if cfg.projection != '3D x-y-z' else 'x-y'
        x, y, xlabel, ylabel = projection_axes(values, projection)
        cvals = quantize(color_values(values, cfg.color_by), cfg.band_count)
        cmap = self._colormap(cfg)
        constant_color = '#f8fafc' if cfg.background in {'negro', 'azul oscuro'} else '#111827'

        if cfg.draw_mode == 'densidad' and len(x) > 2:
            self.ax.hexbin(x, y, gridsize=170, cmap=cmap, mincnt=1, linewidths=0, alpha=cfg.alpha)
        else:
            if cfg.draw_mode in {'linea', 'linea + puntos'}:
                if cvals is None:
                    line_color = constant_color
                elif cfg.background in {'negro', 'azul oscuro'}:
                    line_color = '#e2e8f0'
                else:
                    line_color = '#475569'
                self.ax.plot(
                    x,
                    y,
                    color=line_color,
                    linewidth=max(0.65, cfg.point_size * 0.7),
                    alpha=min(1.0, cfg.alpha),
                )
            if cfg.draw_mode in {'puntos', 'linea + puntos'}:
                if cvals is None:
                    self.ax.scatter(x, y, s=cfg.point_size, color=constant_color, alpha=cfg.alpha, linewidths=0, rasterized=True)
                else:
                    self.ax.scatter(x, y, s=cfg.point_size, c=cvals, cmap=cmap, alpha=cfg.alpha, linewidths=0, rasterized=True)

        self._finish_axes(cfg, title, fg, xlabel, ylabel)

    def _plot_3d(self, values: np.ndarray, cfg: SprottVisualConfig, title: str):
        self.ax = self.fig.add_subplot(111, projection='3d')
        bg = background_color(cfg.background)
        fg = foreground_color(cfg.background)
        transparent = cfg.background == 'transparente'
        self.fig.patch.set_facecolor('none' if transparent else bg)
        self.fig.patch.set_alpha(0.0 if transparent else 1.0)
        self.ax.set_facecolor('none' if transparent else bg)
        cvals = quantize(color_values(values, cfg.color_by), cfg.band_count)
        cmap = self._colormap(cfg)
        constant_color = '#f8fafc' if cfg.background in {'negro', 'azul oscuro'} else '#111827'
        x, y, z = values[:, 0], values[:, 1], values[:, 2]
        if cfg.draw_mode in {'linea', 'linea + puntos'}:
            self.ax.plot(x, y, z, color=constant_color, linewidth=max(0.25, cfg.point_size * 0.55), alpha=cfg.alpha)
        if cfg.draw_mode in {'puntos', 'linea + puntos', 'densidad'}:
            if cvals is None:
                self.ax.scatter(x, y, z, s=cfg.point_size, color=constant_color, alpha=cfg.alpha, linewidths=0)
            else:
                self.ax.scatter(x, y, z, s=cfg.point_size, c=cvals, cmap=cmap, alpha=cfg.alpha, linewidths=0)
        self.ax.set_title(title, color=fg)
        self.ax.set_xlabel('x', color=fg)
        self.ax.set_ylabel('y', color=fg)
        self.ax.set_zlabel('z', color=fg)
        self.ax.tick_params(colors=fg)
        if not cfg.show_axes:
            self.ax.set_axis_off()
        self.fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.92)

    def _plot_unit_sphere(
        self, values: np.ndarray, cfg: SprottVisualConfig, title: str
    ):
        self.ax = self.fig.add_subplot(111, projection='3d')
        bg = background_color(cfg.background)
        fg = foreground_color(cfg.background)
        transparent = cfg.background == 'transparente'
        self.fig.patch.set_facecolor('none' if transparent else bg)
        self.fig.patch.set_alpha(0.0 if transparent else 1.0)
        self.ax.set_facecolor('none' if transparent else bg)

        projected, retained = unit_sphere_projection(values)
        source_values = values[retained]
        cvals = quantize(color_values(source_values, cfg.color_by), cfg.band_count)
        cmap = self._colormap(cfg)
        constant_color = (
            '#f8fafc' if cfg.background in {'negro', 'azul oscuro'} else '#111827'
        )
        if projected.size == 0:
            self.ax.text2D(
                0.5, 0.5, 'Sin direcciones no nulas', color=fg,
                ha='center', va='center', transform=self.ax.transAxes,
            )
        else:
            x, y, z = projected.T
            if cfg.draw_mode in {'linea', 'linea + puntos'}:
                self.ax.plot(
                    x, y, z, color=constant_color,
                    linewidth=max(0.25, cfg.point_size * 0.55), alpha=cfg.alpha,
                )
            if cfg.draw_mode in {'puntos', 'linea + puntos', 'densidad'}:
                scatter_kwargs = {
                    's': cfg.point_size, 'alpha': cfg.alpha, 'linewidths': 0,
                }
                if cvals is None:
                    scatter_kwargs['color'] = constant_color
                else:
                    scatter_kwargs.update({'c': cvals, 'cmap': cmap})
                self.ax.scatter(x, y, z, **scatter_kwargs)

        azimuth = np.linspace(0.0, 2.0 * np.pi, 32)
        polar = np.linspace(0.0, np.pi, 17)
        sphere_x = np.outer(np.cos(azimuth), np.sin(polar))
        sphere_y = np.outer(np.sin(azimuth), np.sin(polar))
        sphere_z = np.outer(np.ones_like(azimuth), np.cos(polar))
        self.ax.plot_wireframe(
            sphere_x, sphere_y, sphere_z,
            rstride=2, cstride=2, color=fg, alpha=0.12, linewidth=0.35,
        )
        self.ax.set_title(title, color=fg)
        self.ax.set_xlabel('x / ||(x,y,z)||', color=fg)
        self.ax.set_ylabel('y / ||(x,y,z)||', color=fg)
        self.ax.set_zlabel('z / ||(x,y,z)||', color=fg)
        self.ax.set_xlim(-1.05, 1.05)
        self.ax.set_ylim(-1.05, 1.05)
        self.ax.set_zlim(-1.05, 1.05)
        self.ax.set_box_aspect((1.0, 1.0, 1.0))
        self.ax.tick_params(colors=fg)
        self.ax.grid(cfg.show_grid, alpha=0.18)
        if not cfg.show_axes:
            self.ax.set_axis_off()
        self.fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.92)

    def _finish_axes(self, cfg: SprottVisualConfig, title: str, fg: str, xlabel: str, ylabel: str):
        self.ax.set_title(title, color=fg)
        self.ax.set_xlabel(xlabel, color=fg)
        self.ax.set_ylabel(ylabel, color=fg)
        if cfg.show_grid:
            self.ax.grid(True, alpha=0.18)
        else:
            self.ax.grid(False)
        if cfg.equal_aspect:
            try:
                self.ax.set_aspect('equal', adjustable='datalim')
            except Exception as exc:
                LOGGER.debug(
                    'Matplotlib no pudo aplicar el aspecto igual; se conserva el aspecto automático.',
                    exc_info=exc,
                )
        if not cfg.show_axes:
            self.ax.set_axis_off()
        self.fig.subplots_adjust(left=0.06, right=0.985, bottom=0.08, top=0.92)

    def _colormap(self, cfg: SprottVisualConfig):
        if cfg.palette == 'Sprott clasica':
            return ListedColormap(['#111827', '#1d4ed8', '#f59e0b', '#f8fafc'])
        cmap = colormaps[mpl_colormap_name(cfg.palette)]
        if cfg.background in {'negro', 'azul oscuro'}:
            # Sequential maps often start almost black.  On a dark canvas that
            # erases a sizeable part of the orbit, so keep the informative,
            # luminous portion of the same palette.
            return ListedColormap(cmap(np.linspace(0.38, 1.0, 256)))
        return cmap

    def export_image(self, path: str | Path, *, dpi: int | None = None):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        transparent = self.last_config.background == 'transparente'
        self.fig.savefig(target, dpi=int(dpi or self.last_config.export_dpi), bbox_inches='tight', facecolor='none' if transparent else self.fig.get_facecolor(), transparent=transparent)
        return target

    def export_thumbnail(self, path: str | Path):
        return self.export_image(path, dpi=96)


class Sprott3DCanvas(Sprott2DCanvas):
    def plot_trajectory(self, trajectory, config: SprottVisualConfig | dict | None = None, title: str = 'Trayectoria Sprott 3D'):
        cfg = sanitize_visual_config(config)
        cfg.projection = '3D x-y-z'
        super().plot_trajectory(trajectory, cfg, title)


class SprottGalleryThumbnail(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 100)
        self.setScaledContents(True)

    def set_image(self, path: str | Path):
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            self.setPixmap(pixmap)
