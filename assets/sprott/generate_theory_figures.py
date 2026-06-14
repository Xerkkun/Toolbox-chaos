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


def _style_axes(ax, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, fontsize=12, pad=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, color='#d8dee9', linewidth=0.6, alpha=0.55)
    ax.set_facecolor('#ffffff')
    for spine in ax.spines.values():
        spine.set_color('#94a3b8')


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
    points = []
    x, y = 0.1, 0.1
    for n in range(26000):
        x, y = 1.0 - 1.4 * x * x + y, 0.3 * x
        if n >= 1000:
            points.append((x, y))
    xy = np.asarray(points, dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=160)
    ax.scatter(xy[:, 0], xy[:, 1], s=0.16, color='#2563eb', alpha=0.42, linewidths=0)
    _style_axes(ax, 'Mapa de Henon', 'x', 'y')
    ax.set_aspect('equal', adjustable='datalim')
    fig.tight_layout()
    fig.savefig(OUT_DIR / 'henon_like_synthetic_sprott_theory.png')
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
    print(f'Generated theory figures in {OUT_DIR}')


if __name__ == '__main__':
    main()
