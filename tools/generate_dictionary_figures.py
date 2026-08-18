"""Generate deterministic figures embedded in the Toolbox Chaos dictionary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.diagnostics import normalized_fft
from core.lorenz import (
    SYSTEM_REGISTRY,
    compute_basin_plane_z_lorenz_xiong,
    simulate_system,
)


LINE_COLOR = "#d000d8"
FFT_COLORS = ("#2563eb", "#dc2626", "#16a34a")
BASIN_RESIDUAL_LABEL = "Acotado residual / no clasificado"
DOC_FIGURE_DIR = ROOT / "assets" / "doc_figures"
OUT_DIR = ROOT / "assets" / "doc_figures" / "systems"

LORENZ_BASIN_CASE = {
    "params": (10.0, 24.4, 8.0 / 3.0),
    "z0": 1.0,
    "extent": (-60.0, 60.0, -60.0, 60.0),
    "resolution": (300, 300),
    "dt": 0.02,
    "T": 18.0,
    "hit_radius": 2.0,
    "escape_radius": 1.0e3,
}

LORENZ_BASIN_TRAJECTORIES = (
    {
        "initial": (-17.81, -12.88, 1.0),
        "expected_class": 2,
        "label": "Converge a E+",
        "color": "#d62728",
    },
    {
        "initial": (17.81, -12.88, 1.0),
        "expected_class": 3,
        "label": "Converge a E-",
        "color": "#2ca02c",
    },
    {
        "initial": (-0.27, 45.21, 1.0),
        "expected_class": 1,
        "label": BASIN_RESIDUAL_LABEL,
        "color": "#87ceeb",
    },
)

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
    "unified_lorenz_chen": {"dt": 0.01, "T": 40.0},
    "sprott_b": {"dt": 0.01, "T": 80.0},
    "sprott_c": {"dt": 0.01, "T": 80.0},
    "sprott_d": {"dt": 0.01, "T": 80.0},
    "sprott_e": {"dt": 0.01, "T": 80.0},
    "sprott_f": {"dt": 0.01, "T": 80.0},
    "sprott_g": {"dt": 0.01, "T": 80.0},
    "sprott_h": {"dt": 0.01, "T": 80.0},
    "sprott_i": {"dt": 0.01, "T": 80.0},
    "sprott_j": {"dt": 0.01, "T": 80.0},
    "sprott_k": {"dt": 0.01, "T": 80.0},
    "sprott_l": {"dt": 0.01, "T": 80.0},
    "sprott_m": {"dt": 0.01, "T": 80.0},
    "sprott_n": {"dt": 0.01, "T": 80.0},
    "sprott_o": {"dt": 0.01, "T": 80.0},
    "sprott_p": {"dt": 0.01, "T": 80.0},
    "sprott_q": {"dt": 0.01, "T": 80.0},
    "sprott_r": {"dt": 0.01, "T": 80.0},
    "sprott_s": {"dt": 0.01, "T": 80.0},
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


def compute_lorenz_basin_example() -> np.ndarray:
    sigma, rho, beta = LORENZ_BASIN_CASE["params"]
    x_min, x_max, y_min, y_max = LORENZ_BASIN_CASE["extent"]
    nx, ny = LORENZ_BASIN_CASE["resolution"]
    basin = compute_basin_plane_z_lorenz_xiong(
        sigma,
        rho,
        beta,
        LORENZ_BASIN_CASE["z0"],
        x_min,
        x_max,
        y_min,
        y_max,
        nx,
        ny,
        LORENZ_BASIN_CASE["dt"],
        LORENZ_BASIN_CASE["T"],
        LORENZ_BASIN_CASE["hit_radius"],
        LORENZ_BASIN_CASE["escape_radius"],
        method_key="rk4",
    )
    present = set(int(value) for value in np.unique(basin))
    expected = {1, 2, 3}
    if present != expected:
        raise RuntimeError(
            "The documented Lorenz basin classes changed: "
            f"expected {sorted(expected)}, obtained {sorted(present)}."
        )
    return basin


def classify_lorenz_initial(initial: tuple[float, float, float]) -> int:
    sigma, rho, beta = LORENZ_BASIN_CASE["params"]
    x0, y0, z0 = initial
    epsilon = 1.0e-6
    basin = compute_basin_plane_z_lorenz_xiong(
        sigma,
        rho,
        beta,
        z0,
        x0 - epsilon,
        x0 + epsilon,
        y0 - epsilon,
        y0 + epsilon,
        2,
        2,
        LORENZ_BASIN_CASE["dt"],
        LORENZ_BASIN_CASE["T"],
        LORENZ_BASIN_CASE["hit_radius"],
        LORENZ_BASIN_CASE["escape_radius"],
        method_key="rk4",
    )
    return int(basin[0, 0])


def plot_lorenz_basin_example(basin: np.ndarray) -> None:
    class_colors = (
        "#000000",
        "#87ceeb",
        "#d62728",
        "#2ca02c",
        "#1f77b4",
        "#9467bd",
    )
    class_labels = {
        1: BASIN_RESIDUAL_LABEL,
        2: "Converge a E+",
        3: "Converge a E-",
    }
    present = sorted(int(value) for value in np.unique(basin))

    fig, ax = plt.subplots(figsize=(5.25, 5.2), dpi=170)
    ax.imshow(
        basin,
        origin="lower",
        extent=LORENZ_BASIN_CASE["extent"],
        interpolation="nearest",
        aspect="auto",
        cmap=ListedColormap(class_colors),
        vmin=-0.5,
        vmax=len(class_colors) - 0.5,
    )
    ax.set_title(
        "Lorenz: clasificación rápida en "
        rf"$z_0={LORENZ_BASIN_CASE['z0']:.0f}$, "
        rf"$\rho={LORENZ_BASIN_CASE['params'][1]:.1f}$"
    )
    ax.set_xlabel(r"$x_0$")
    ax.set_ylabel(r"$y_0$")
    handles = [
        Patch(
            facecolor=class_colors[value],
            edgecolor="black",
            linewidth=0.4,
            label=class_labels[value],
        )
        for value in present
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        fontsize=8,
        framealpha=0.90,
        title="Clasificación",
        title_fontsize=9,
    )
    ax.text(
        0.01,
        0.01,
        f"Horizonte finito T={LORENZ_BASIN_CASE['T']:.0f}; la clase residual no certifica caos.",
        transform=ax.transAxes,
        fontsize=6.5,
        ha="left",
        va="bottom",
        color="#111827",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "white",
            "alpha": 0.82,
            "edgecolor": "0.55",
        },
    )
    fig.tight_layout()
    fig.savefig(DOC_FIGURE_DIR / "lorenz_basin.png", dpi=170)
    plt.close(fig)


def plot_lorenz_basin_trajectories() -> None:
    params = LORENZ_BASIN_CASE["params"]
    fig = plt.figure(figsize=(12.0, 4.25), dpi=170)
    axes = [fig.add_subplot(1, 3, index + 1, projection="3d") for index in range(3)]

    for ax, case in zip(axes, LORENZ_BASIN_TRAJECTORIES):
        actual_class = classify_lorenz_initial(case["initial"])
        if actual_class != case["expected_class"]:
            raise RuntimeError(
                f"Initial condition {case['initial']} changed basin class: "
                f"expected {case['expected_class']}, obtained {actual_class}."
            )
        _, trajectory = simulate_system(
            "lorenz",
            case["initial"],
            params,
            LORENZ_BASIN_CASE["dt"],
            LORENZ_BASIN_CASE["T"],
            method_key="rk4",
        )
        ax.plot(
            trajectory[:, 0],
            trajectory[:, 1],
            trajectory[:, 2],
            color=case["color"],
            linewidth=0.75,
        )
        ax.scatter(
            [case["initial"][0]],
            [case["initial"][1]],
            [case["initial"][2]],
            color="black",
            s=28,
            depthshade=False,
            zorder=4,
        )
        x0, y0, z0 = case["initial"]
        label = case["label"]
        if actual_class == 1:
            label = BASIN_RESIDUAL_LABEL.replace(" / ", " /\n")
        ax.set_title(
            f"{label}\nIC=({x0:.2f}, {y0:.2f}, {z0:.2f})",
            fontsize=10,
            pad=10,
        )
        ax.set_xlabel("x", labelpad=3)
        ax.set_ylabel("y", labelpad=3)
        ax.set_zlabel("z", labelpad=3)
        ax.tick_params(labelsize=8, pad=1)
        ax.view_init(elev=24, azim=-58)

    fig.suptitle(
        "Lorenz: trayectorias desde clases distintas de la cuenca "
        rf"($\rho={params[1]:.1f}$, $T={LORENZ_BASIN_CASE['T']:.0f}$)",
        fontsize=13,
    )
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.04, top=0.80, wspace=0.10)
    fig.savefig(DOC_FIGURE_DIR / "lorenz_basin_trajectories.png", dpi=170)
    plt.close(fig)


def generate_lorenz_basin_figures() -> None:
    DOC_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    basin = compute_lorenz_basin_example()
    plot_lorenz_basin_example(basin)
    plot_lorenz_basin_trajectories()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lorenz-basin-only",
        action="store_true",
        help="Regenerate only the two documented Lorenz basin figures.",
    )
    args = parser.parse_args(argv)

    if args.lorenz_basin_only:
        generate_lorenz_basin_figures()
        print("generated lorenz_basin and lorenz_basin_trajectories")
        return 0

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
    generate_lorenz_basin_figures()
    print("generated lorenz_basin and lorenz_basin_trajectories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
