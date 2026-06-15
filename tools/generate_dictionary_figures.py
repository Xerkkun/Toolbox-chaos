from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.diagnostics import normalized_fft
from core.lorenz import SYSTEM_REGISTRY, simulate_system


LINE_COLOR = "#d000d8"
FFT_COLORS = ("#2563eb", "#dc2626", "#16a34a")
OUT_DIR = ROOT / "assets" / "doc_figures" / "systems"

CASES = {
    "lorenz": {"dt": 0.01, "T": 40.0},
    "rossler": {"dt": 0.02, "T": 160.0},
    "chua": {"dt": 0.01, "T": 80.0},
    "chen": {"dt": 0.005, "T": 40.0},
    "lu": {"dt": 0.005, "T": 40.0},
    "henon": {"dt": 1.0, "T": 1800.0},
    "logistic": {"dt": 1.0, "T": 1200.0},
    "ikeda": {"dt": 1.0, "T": 1200.0},
    "mackey_glass": {"dt": 0.1, "T": 600.0},
    "duffing_ueda": {"dt": 0.01, "T": 120.0},
    "rabinovich_fabrikant": {"dt": 0.005, "T": 40.0},
    "rikitake": {"dt": 0.01, "T": 100.0},
    "sprott_a": {"dt": 0.01, "T": 80.0},
    "thomas": {"dt": 0.02, "T": 140.0},
    "hindmarsh_rose": {"dt": 0.02, "T": 500.0},
    "lorenz96": {"dt": 0.01, "T": 40.0},
}


def finite_tail(t: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mask = np.isfinite(t) & np.all(np.isfinite(x), axis=1)
    t = t[mask]
    x = x[mask]
    if len(t) < 4:
        return t, x
    start = max(0, int(0.08 * len(t)))
    return t[start:] - t[start], x[start:]


def thin(t: np.ndarray, x: np.ndarray, max_points: int = 6500) -> tuple[np.ndarray, np.ndarray]:
    if len(t) <= max_points:
        return t, x
    idx = np.linspace(0, len(t) - 1, max_points).astype(int)
    return t[idx], x[idx]


def style_2d(ax, xlabel: str, ylabel: str) -> None:
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=7, width=0.6, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)


def style_3d(ax) -> None:
    ax.set_xlabel("x", fontsize=8, labelpad=2)
    ax.set_ylabel("y", fontsize=8, labelpad=2)
    ax.set_zlabel("z", fontsize=8, labelpad=2)
    ax.tick_params(labelsize=7, pad=0)
    ax.view_init(elev=26, azim=-58)


def plot_phase_timeseries(key: str, label: str, t: np.ndarray, x: np.ndarray) -> None:
    t_plot, x_plot = thin(t, x)
    fig = plt.figure(figsize=(10.0, 4.2), dpi=180)
    grid = fig.add_gridspec(
        3,
        2,
        width_ratios=[1.05, 1.65],
        left=0.055,
        right=0.985,
        bottom=0.17,
        top=0.95,
        wspace=0.22,
        hspace=0.22,
    )

    ax3d = fig.add_subplot(grid[:, 0], projection="3d")
    ax3d.plot(x_plot[:, 0], x_plot[:, 1], x_plot[:, 2], color=LINE_COLOR, lw=0.65)
    style_3d(ax3d)

    labels = ("x", "y", "z")
    for row in range(3):
        ax = fig.add_subplot(grid[row, 1])
        ax.plot(t_plot, x_plot[:, row], color=LINE_COLOR, lw=0.6)
        style_2d(ax, "Tiempo" if row == 2 else "", labels[row])
        if row < 2:
            ax.tick_params(labelbottom=False)

    fig.text(0.23, 0.055, "(a)", ha="center", va="center", fontsize=11, fontweight="bold")
    fig.text(0.72, 0.055, "(b)", ha="center", va="center", fontsize=11, fontweight="bold")
    fig.savefig(OUT_DIR / f"{key}_phase_timeseries.png")
    plt.close(fig)


def plot_projections(key: str, label: str, t: np.ndarray, x: np.ndarray) -> None:
    _, x_plot = thin(t, x)
    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.4), dpi=180)
    pairs = ((0, 1, "x", "y"), (0, 2, "x", "z"), (1, 2, "y", "z"))
    panel_labels = ("(a)", "(b)", "(c)")
    for ax, pair, panel in zip(axes, pairs, panel_labels):
        i, j, xlabel, ylabel = pair
        ax.plot(x_plot[:, i], x_plot[:, j], color=LINE_COLOR, lw=0.65)
        style_2d(ax, xlabel, ylabel)
        ax.text(0.5, -0.22, panel, transform=ax.transAxes, ha="center", va="top", fontsize=11, fontweight="bold")

    fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.24, wspace=0.26)
    fig.savefig(OUT_DIR / f"{key}_projections.png")
    plt.close(fig)


def dominant_frequency_xlim(freqs: np.ndarray, spectra: np.ndarray) -> tuple[float, float] | None:
    freqs = np.asarray(freqs, dtype=float)
    spectra = np.asarray(spectra, dtype=float)
    if freqs.size < 3 or spectra.size == 0:
        return None
    finite = np.isfinite(freqs) & np.all(np.isfinite(spectra), axis=1)
    freqs = freqs[finite]
    spectra = spectra[finite]
    if freqs.size < 3:
        return None
    energy = np.nanmax(np.abs(spectra), axis=1) ** 2
    total = float(np.sum(energy))
    if not np.isfinite(total) or total <= 1.0e-300:
        return None
    order = np.argsort(freqs)
    f = freqs[order]
    e = energy[order]
    cumulative = np.cumsum(e) / total
    lo_idx = int(np.searchsorted(cumulative, 0.01, side="left"))
    hi_idx = int(np.searchsorted(cumulative, 0.99, side="left"))
    lo = float(f[max(0, min(lo_idx, len(f) - 1))])
    hi = float(f[max(0, min(hi_idx, len(f) - 1))])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return None
    pad = max(0.1 * (hi - lo), float(np.median(np.diff(f))) if len(f) > 1 else 0.0)
    lo -= pad
    hi += pad
    if lo < 0.0 < hi:
        span = max(abs(lo), abs(hi))
        lo, hi = -span, span
    return max(float(np.min(freqs)), lo), min(float(np.max(freqs)), hi)


def plot_fft_example() -> None:
    meta = SYSTEM_REGISTRY["lorenz"]
    t, x = simulate_system("lorenz", meta["initial"], meta["defaults"], 0.01, 80.0, method_key="rk4")
    tail = max(4, int(0.25 * len(t)))
    freqs, spectra = normalized_fft(t[tail:], x[tail:, :3])
    xlim = dominant_frequency_xlim(freqs, spectra)

    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(7.4, 6.0), dpi=180)
    labels = ("x", "y", "z")
    for idx, ax in enumerate(axes):
        ax.vlines(freqs, 0.0, spectra[:, idx], color=FFT_COLORS[idx], linewidth=0.65)
        ax.axhline(0.0, color="0.25", linewidth=0.6)
        ax.set_ylabel(labels[idx], fontsize=11)
        ax.tick_params(labelsize=10)
        if xlim is not None:
            ax.set_xlim(*xlim)
        ax.set_ylim(0.0, max(1.05, float(np.nanmax(spectra[:, idx])) * 1.08))
    axes[0].set_title("Lorenz: FFT normalizada", fontsize=13)
    axes[-1].set_xlabel("Frequency (Hz)", fontsize=11)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.10, hspace=0.12)
    fig.savefig(ROOT / "assets" / "doc_figures" / "lorenz_fft.png")
    plt.close(fig)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, case in CASES.items():
        meta = SYSTEM_REGISTRY[key]
        params = meta.get("defaults", ())
        initial = meta.get("initial", (0.1, 0.1, 0.1))
        t, x = simulate_system(key, initial, params, case["dt"], case["T"], method_key="rk4")
        t_tail, x_tail = finite_tail(t, x)
        plot_phase_timeseries(key, meta["label"], t_tail, x_tail)
        plot_projections(key, meta["label"], t_tail, x_tail)
        print(f"generated {key}")
    plot_fft_example()
    print("generated lorenz_fft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
