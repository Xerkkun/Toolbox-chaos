from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


PROJECTIONS = ['x-y', 'x-z', 'y-z', 'x-w', 'y-w', 'z-w', 'n-x', 'n-y', 'n-z', '3D x-y-z']
COLOR_MODES = ['constante', 'tiempo', 'x', 'y', 'z', 'w', 'radio', 'velocidad']
PALETTES = ['Sprott clasica', 'Viridis', 'Plasma', 'Inferno', 'Magma', 'Turbo', 'Gray', 'Cyclic']
BACKGROUNDS = ['blanco', 'negro', 'azul oscuro', 'transparente']
DRAW_MODES = ['puntos', 'linea', 'linea + puntos', 'densidad']


@dataclass
class SprottVisualConfig:
    projection: str = 'x-y'
    color_by: str = 'constante'
    palette: str = 'Sprott clasica'
    background: str = 'blanco'
    point_size: float = 0.7
    alpha: float = 0.75
    max_points: int = 20000
    show_axes: bool = False
    show_grid: bool = False
    equal_aspect: bool = True
    draw_mode: str = 'puntos'
    export_dpi: int = 220
    band_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        if not data:
            return cls()
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        clean = {key: value for key, value in dict(data).items() if key in allowed}
        return cls(**clean)


VISUAL_PRESETS: dict[str, SprottVisualConfig] = {
    'Sprott libro blanco': SprottVisualConfig(
        projection='x-y',
        color_by='constante',
        palette='Gray',
        background='blanco',
        point_size=0.6,
        alpha=0.65,
        max_points=24000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
    ),
    'Color por profundidad': SprottVisualConfig(
        projection='x-y',
        color_by='z',
        palette='Turbo',
        background='negro',
        point_size=0.7,
        alpha=0.75,
        max_points=26000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
    ),
    'Bandas': SprottVisualConfig(
        projection='x-y',
        color_by='z',
        palette='Cyclic',
        background='negro',
        point_size=0.7,
        alpha=0.82,
        max_points=26000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
        band_count=14,
    ),
    'Sombra/profundidad': SprottVisualConfig(
        projection='x-y',
        color_by='radio',
        palette='Inferno',
        background='negro',
        point_size=0.5,
        alpha=0.62,
        max_points=32000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
    ),
    'Mapa 4D': SprottVisualConfig(
        projection='x-y',
        color_by='w',
        palette='Plasma',
        background='negro',
        point_size=0.55,
        alpha=0.72,
        max_points=28000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
        band_count=12,
    ),
    'Alta densidad': SprottVisualConfig(
        projection='x-y',
        color_by='tiempo',
        palette='Viridis',
        background='azul oscuro',
        point_size=0.22,
        alpha=0.34,
        max_points=70000,
        show_axes=False,
        show_grid=False,
        equal_aspect=True,
        draw_mode='puntos',
    ),
    'Didactico': SprottVisualConfig(
        projection='x-y',
        color_by='tiempo',
        palette='Viridis',
        background='blanco',
        point_size=1.6,
        alpha=0.9,
        max_points=8000,
        show_axes=True,
        show_grid=True,
        equal_aspect=False,
        draw_mode='linea + puntos',
    ),
}


def default_visual_config() -> SprottVisualConfig:
    return SprottVisualConfig()


def visual_preset(name: str) -> SprottVisualConfig:
    preset = VISUAL_PRESETS.get(name)
    return SprottVisualConfig.from_dict(preset.to_dict()) if preset else default_visual_config()


def sanitize_visual_config(config: SprottVisualConfig | dict[str, Any] | None) -> SprottVisualConfig:
    cfg = SprottVisualConfig.from_dict(config) if isinstance(config, dict) else (config or default_visual_config())
    if cfg.projection not in PROJECTIONS:
        cfg.projection = 'x-y'
    if cfg.color_by not in COLOR_MODES:
        cfg.color_by = 'constante'
    if cfg.palette not in PALETTES:
        cfg.palette = 'Sprott clasica'
    if cfg.background not in BACKGROUNDS:
        cfg.background = 'blanco'
    if cfg.draw_mode not in DRAW_MODES:
        cfg.draw_mode = 'puntos'
    cfg.point_size = max(0.05, float(cfg.point_size))
    cfg.alpha = min(1.0, max(0.02, float(cfg.alpha)))
    cfg.max_points = max(64, int(cfg.max_points))
    cfg.export_dpi = min(600, max(72, int(cfg.export_dpi)))
    cfg.band_count = max(0, int(cfg.band_count))
    return cfg


def background_color(name: str) -> str:
    return {
        'blanco': '#ffffff',
        'negro': '#000000',
        'azul oscuro': '#08111f',
        'transparente': 'none',
    }.get(name, '#ffffff')


def foreground_color(background: str) -> str:
    return '#f8fafc' if background in {'negro', 'azul oscuro'} else '#111827'


def mpl_colormap_name(palette: str) -> str:
    return {
        'Sprott clasica': 'copper',
        'Viridis': 'viridis',
        'Plasma': 'plasma',
        'Inferno': 'inferno',
        'Magma': 'magma',
        'Turbo': 'turbo',
        'Gray': 'gray',
        'Cyclic': 'twilight',
    }.get(palette, 'viridis')


def finite_post_transient(trajectory) -> np.ndarray:
    values = np.asarray(trajectory, dtype=float)
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.size == 0:
        return np.empty((0, 1), dtype=float)
    return values[np.all(np.isfinite(values), axis=1)]


def downsample(values: np.ndarray, max_points: int) -> np.ndarray:
    if len(values) <= max_points:
        return values
    idx = np.linspace(0, len(values) - 1, int(max_points)).astype(int)
    return values[idx]


def projection_axes(values: np.ndarray, projection: str) -> tuple[np.ndarray, np.ndarray, str, str]:
    if values.size == 0:
        return np.array([]), np.array([]), 'x', 'y'
    dim = values.shape[1]
    names = ['x', 'y', 'z', 'w']
    if projection.startswith('n-'):
        component = projection.split('-', 1)[1]
        idx = names.index(component) if component in names else 0
        idx = min(idx, dim - 1)
        return np.arange(len(values)), values[:, idx], 'n', names[idx]
    left, right = projection.split('-') if '-' in projection else ('x', 'y')
    ix = names.index(left) if left in names else 0
    iy = names.index(right) if right in names else min(1, dim - 1)
    ix = min(ix, dim - 1)
    iy = min(iy, dim - 1)
    return values[:, ix], values[:, iy], names[ix], names[iy]


def color_values(values: np.ndarray, color_by: str) -> np.ndarray | None:
    if values.size == 0 or color_by == 'constante':
        return None
    dim = values.shape[1]
    names = ['x', 'y', 'z', 'w']
    if color_by == 'tiempo':
        return np.linspace(0.0, 1.0, len(values))
    if color_by in names:
        idx = min(names.index(color_by), dim - 1)
        return values[:, idx]
    if color_by == 'radio':
        return np.linalg.norm(values, axis=1)
    if color_by == 'velocidad':
        if len(values) < 2:
            return np.zeros(len(values))
        diffs = np.diff(values, axis=0, prepend=values[:1])
        return np.linalg.norm(diffs, axis=1)
    return None


def quantize(values: np.ndarray | None, bands: int) -> np.ndarray | None:
    if values is None or bands <= 1:
        return values
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return values
    lo = float(np.min(finite))
    hi = float(np.max(finite))
    if hi <= lo:
        return np.zeros_like(values)
    scaled = (values - lo) / (hi - lo)
    return np.floor(np.clip(scaled, 0.0, 0.999999) * bands)


def trajectory_stats(trajectory) -> dict[str, Any]:
    values = finite_post_transient(trajectory)
    if values.size == 0:
        return {'finite_count': 0, 'dimension': 0, 'ranges': [], 'means': [], 'stds': []}
    return {
        'finite_count': int(len(values)),
        'dimension': int(values.shape[1]),
        'ranges': [(float(np.min(values[:, i])), float(np.max(values[:, i]))) for i in range(values.shape[1])],
        'means': [float(np.mean(values[:, i])) for i in range(values.shape[1])],
        'stds': [float(np.std(values[:, i])) for i in range(values.shape[1])],
    }


def visual_recommendation(trajectory, classification: dict[str, Any] | None = None) -> str:
    state = (classification or {}).get('state', '')
    stats = trajectory_stats(trajectory)
    dim = stats.get('dimension', 0)
    count = stats.get('finite_count', 0)
    if state == 'fixed_point':
        return 'Este codigo parece fijo; prueba otro codigo o aumenta transitorio solo para confirmarlo.'
    if state == 'divergent':
        return 'La trayectoria diverge; en flujos reduce h o usa RK4 antes de subir el umbral.'
    if count < 1000:
        return 'Hay pocos puntos utiles; aumenta iteraciones y transitorio para revelar estructura.'
    if dim >= 4:
        return 'Sistema 4D: usa proyeccion x-y con color por z o w, o bandas.'
    if dim == 3:
        return 'Prueba color por z, radio o tiempo; cambia entre x-y, x-z e y-z.'
    if state == 'periodic_or_low_complexity':
        return 'La cola parece simple; prueba otra proyeccion, mas iteraciones o un codigo distinto.'
    return 'Buena base visual: ajusta paleta, alpha y maximo de puntos antes de exportar.'
