from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = Path(__file__).resolve().parent / 'images'
GENERATED_DIR = OUT_DIR / 'generated'


def _style_axes(ax, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, fontsize=12, pad=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, color='#d8dee9', linewidth=0.6, alpha=0.55)
    ax.set_facecolor('#ffffff')
    for spine in ax.spines.values():
        spine.set_color('#94a3b8')


def _henon_points(n_iter=26000, transient=1000):
    points = []
    x, y = 0.1, 0.1
    for n in range(n_iter):
        x, y = 1.0 - 1.4 * x * x + y, 0.3 * x
        if n >= transient:
            points.append((x, y))
    return np.asarray(points, dtype=float)


def generate_logistic_bifurcation():
    r_values = np.linspace(2.6, 4.0, 1000)
    keep_r = []
    keep_x = []
    for r in r_values:
        x = 0.213
        for n in range(1200):
            x = r * x * (1.0 - x)
            if n >= 700:
                keep_r.append(r)
                keep_x.append(x)

    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=160)
    ax.plot(keep_r, keep_x, ',', color='#172033', alpha=0.58)
    _style_axes(ax, 'Bifurcacion logistica', 'R', 'x post-transitorio')
    ax.set_xlim(2.6, 4.0)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'logistic_bifurcation_sprott_theory.png')
    plt.close(fig)


def generate_henon_map():
    xy = _henon_points()

    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
    ax.scatter(xy[:, 0], xy[:, 1], s=0.16, color='#2563eb', alpha=0.42, linewidths=0)
    _style_axes(ax, 'Mapa de Henon', 'x', 'y')
    ax.set_aspect('equal', adjustable='datalim')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'henon_like_synthetic_sprott_theory.png')
    plt.close(fig)


def generate_visual_language_examples():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    xy = _henon_points(32000, 1200)
    n = np.linspace(0.0, 1.0, len(xy))
    z = np.sin(7.0 * xy[:, 0]) + np.cos(9.0 * xy[:, 1])
    w = np.sin(16.0 * n) + 0.4 * xy[:, 0] * xy[:, 1]

    examples = [
        ('map3d_color_z.png', z, 'Mapa sintetico 3D: color por z', 'turbo', '#020617'),
        ('map3d_bands_z.png', np.floor((z - z.min()) / (z.max() - z.min()) * 14), 'Mapa sintetico 3D: bandas por z', 'twilight', '#020617'),
        ('map4d_projection_w.png', w, 'Ejemplo sintetico 4D: proyeccion x-y, color por w', 'plasma', '#000000'),
        ('comparison_color_time.png', n, 'Comparacion: color por tiempo', 'viridis', '#ffffff'),
        ('comparison_color_z_black.png', z, 'Comparacion: color por z en fondo negro', 'magma', '#000000'),
    ]
    for filename, colors, title, cmap, face in examples:
        fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
        fig.patch.set_facecolor(face)
        ax.set_facecolor(face)
        ax.scatter(xy[:, 0], xy[:, 1], s=0.22, c=colors, cmap=cmap, alpha=0.72, linewidths=0)
        fg = '#f8fafc' if face != '#ffffff' else '#172033'
        ax.set_title(title, color=fg, fontsize=12, pad=8)
        ax.tick_params(colors=fg)
        for spine in ax.spines.values():
            spine.set_color(fg)
        ax.set_axis_off()
        ax.set_aspect('equal', adjustable='datalim')
        fig.tight_layout()
        fig.savefig(GENERATED_DIR / filename, facecolor=face)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
    ax.scatter(xy[:1200, 0], xy[:1200, 1], s=1.6, color='#111827', alpha=0.9, linewidths=0)
    _style_axes(ax, 'Imagen pobre: muy pocas iteraciones', 'x', 'y')
    fig.tight_layout()
    fig.savefig(GENERATED_DIR / 'bad_too_few_iterations.png')
    plt.close(fig)

    fixed = np.column_stack([np.linspace(0.8, 1.0, 800), np.linspace(-0.3, 0.0, 800)])
    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
    ax.plot(fixed[:, 0], fixed[:, 1], color='#991b1b', linewidth=1.0)
    _style_axes(ax, 'Imagen pobre: colapso a punto fijo', 'x', 'y')
    fig.tight_layout()
    fig.savefig(GENERATED_DIR / 'bad_fixed_point.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
    ax.scatter(xy[:, 0], xy[:, 1], s=0.18, c=z, cmap='turbo', alpha=0.5, linewidths=0)
    ax.set_facecolor('#020617')
    fig.patch.set_facecolor('#020617')
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim')
    ax.set_title('Imagen mejorada: mas puntos, color por z, fondo oscuro', color='#f8fafc', fontsize=12)
    fig.tight_layout()
    fig.savefig(GENERATED_DIR / 'improved_dense_color_z.png', facecolor='#020617')
    plt.close(fig)


def _sprott_five_term_rhs(state: np.ndarray) -> np.ndarray:
    x, y, z = state
    return np.array([y * z, x - y, 1.0 - x * y], dtype=float)


def _rk4_step(state: np.ndarray, h: float) -> np.ndarray:
    k1 = _sprott_five_term_rhs(state)
    k2 = _sprott_five_term_rhs(state + 0.5 * h * k1)
    k3 = _sprott_five_term_rhs(state + 0.5 * h * k2)
    k4 = _sprott_five_term_rhs(state + h * k3)
    return state + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def generate_sprott_five_term_flow():
    h = 0.01
    steps = 60000
    transient = 10000
    state = np.array([0.1, 0.1, 0.1], dtype=float)
    kept = []
    for step in range(steps):
        state = _rk4_step(state, h)
        if step >= transient:
            kept.append(state.copy())
    xyz = np.asarray(kept)
    stride = max(1, len(xyz) // 18000)
    xyz = xyz[::stride]

    fig = plt.figure(figsize=(7.6, 6.4), dpi=160)
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2], color='#0f766e', linewidth=0.28, alpha=0.88)
    ax.set_title('Flujo Sprott 3D de cinco terminos', fontsize=12, pad=10)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.view_init(elev=22, azim=-56)
    ax.set_facecolor('#ffffff')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'sprott_five_term_flow_theory.png')
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_logistic_bifurcation()
    generate_henon_map()
    generate_sprott_five_term_flow()
    generate_visual_language_examples()
    print(f'Generated theory figures in {OUT_DIR}')


if __name__ == '__main__':
    main()
