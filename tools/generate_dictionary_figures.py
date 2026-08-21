"""Generate deterministic figures embedded in the Toolbox Chaos dictionary."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Patch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.diagnostics import integer_qr_benettin_lyapunov, normalized_fft
from core.lorenz import (
    SYSTEM_REGISTRY,
    bifurcation_poincare_lorenz,
    compute_basin_plane_z_lorenz_xiong,
    simulate_system,
)


WHITE = "#ffffff"
INK = "#111827"
GRID = "#d1d5db"
LINE_COLOR = "#004b9b"
FFT_COLORS = ("#2563eb", "#dc2626", "#16a34a")
BASIN_RESIDUAL_LABEL = "Acotado residual / no clasificado"
DOC_FIGURE_DIR = ROOT / "assets" / "doc_figures"
OUT_DIR = ROOT / "assets" / "doc_figures" / "systems"

MANUAL_SYSTEM_KEYS = (
    "henon",
    "lorenz",
    "rossler",
    "chua",
    "duffing_ueda",
    "mackey_glass",
    "lorenz96",
)

THEORY_FIGURE_NAMES = (
    "topology_neighborhood_boundary.png",
    "flow_invariance_trapping.png",
    "omega_limit_trapping_region.png",
    "conjugacy_orbital_equivalence.png",
    "variational_volume_manifolds.png",
    "poincare_floquet_geometry.png",
    "degree_fixed_point.png",
    "horseshoe_symbolic_dynamics.png",
    "fractional_memory_kernel_pece.png",
)

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
        "color": "#b91c1c",
    },
    {
        "initial": (17.81, -12.88, 1.0),
        "expected_class": 3,
        "label": "Converge a E-",
        "color": "#047857",
    },
    {
        "initial": (-0.27, 45.21, 1.0),
        "expected_class": 1,
        "label": BASIN_RESIDUAL_LABEL,
        "color": "#0369a1",
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


def prepare_figure(fig) -> None:
    """Apply the print-safe white background shared by all manual figures."""

    fig.patch.set_facecolor(WHITE)


def save_figure(fig, path: Path, *, dpi: int | None = None) -> None:
    """Save an opaque white PNG and close its Matplotlib figure."""

    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {
        "facecolor": WHITE,
        "edgecolor": WHITE,
        "transparent": False,
        "metadata": {
            "Software": "Toolbox Chaos canonical documentation generator",
            "PlotStyle": "white-background-title-free-v1",
        },
    }
    if dpi is not None:
        kwargs["dpi"] = dpi
    fig.savefig(path, **kwargs)
    plt.close(fig)


def panel_label(ax, label: str, *, x: float = 0.02, y: float = 0.98) -> None:
    text_method = ax.text2D if hasattr(ax, "text2D") else ax.text
    text_method(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        fontweight="bold",
        color=INK,
        bbox={"facecolor": WHITE, "edgecolor": "none", "alpha": 0.86, "pad": 1.5},
        zorder=20,
    )


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
    ax.set_facecolor(WHITE)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=7, width=0.7, length=3, colors=INK)
    ax.grid(True, color=GRID, linewidth=0.45, alpha=0.55)
    for spine in ax.spines.values():
        spine.set_color(INK)
        spine.set_linewidth(0.7)


def style_3d(ax) -> None:
    ax.set_facecolor(WHITE)
    ax.set_xlabel("x", fontsize=8, labelpad=2)
    ax.set_ylabel("y", fontsize=8, labelpad=2)
    ax.set_zlabel("z", fontsize=8, labelpad=2)
    ax.tick_params(labelsize=7, pad=0, colors=INK)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 1.0))
        axis.pane.set_edgecolor(GRID)
        axis._axinfo["grid"]["color"] = GRID
        axis._axinfo["grid"]["linewidth"] = 0.45
    ax.view_init(elev=26, azim=-58)


def plot_phase_timeseries(key: str, label: str, t: np.ndarray, x: np.ndarray) -> None:
    t_plot, x_plot = thin(t, x)
    fig = plt.figure(figsize=(10.0, 4.2), dpi=180)
    prepare_figure(fig)
    dimension = int(SYSTEM_REGISTRY[key].get("dimension", 3))
    rows = 2 if dimension == 2 else 3
    grid = fig.add_gridspec(
        rows,
        2,
        width_ratios=[1.05, 1.65],
        left=0.055,
        right=0.985,
        bottom=0.17,
        top=0.95,
        wspace=0.22,
        hspace=0.22,
    )

    if dimension == 2:
        ax_phase = fig.add_subplot(grid[:, 0])
        ax_phase.scatter(
            x_plot[:, 0],
            x_plot[:, 1],
            s=2.0,
            color=LINE_COLOR,
            alpha=0.72,
            linewidths=0.0,
            rasterized=True,
        )
        style_2d(ax_phase, "x", "y")
        ax_phase.set_aspect("equal", adjustable="box")
    else:
        ax3d = fig.add_subplot(grid[:, 0], projection="3d")
        ax3d.plot(x_plot[:, 0], x_plot[:, 1], x_plot[:, 2], color=LINE_COLOR, lw=1.05)
        style_3d(ax3d)

    labels = ("x", "y", "z")
    for row in range(rows):
        ax = fig.add_subplot(grid[row, 1])
        ax.plot(t_plot, x_plot[:, row], color=LINE_COLOR, lw=0.90)
        style_2d(ax, "Tiempo" if row == 2 else "", labels[row])
        if row < rows - 1:
            ax.tick_params(labelbottom=False)

    fig.text(0.23, 0.055, "(a)", ha="center", va="center", fontsize=11, fontweight="bold")
    fig.text(0.72, 0.055, "(b)", ha="center", va="center", fontsize=11, fontweight="bold")
    save_figure(fig, OUT_DIR / f"{key}_phase_timeseries.png")


def plot_projections(key: str, label: str, t: np.ndarray, x: np.ndarray) -> None:
    _, x_plot = thin(t, x)
    fig, axes = plt.subplots(1, 3, figsize=(10.0, 3.4), dpi=180)
    prepare_figure(fig)
    pairs = ((0, 1, "x", "y"), (0, 2, "x", "z"), (1, 2, "y", "z"))
    panel_labels = ("(a)", "(b)", "(c)")
    for ax, pair, panel in zip(axes, pairs, panel_labels):
        i, j, xlabel, ylabel = pair
        ax.plot(x_plot[:, i], x_plot[:, j], color=LINE_COLOR, lw=1.05)
        style_2d(ax, xlabel, ylabel)
        ax.text(0.5, -0.22, panel, transform=ax.transAxes, ha="center", va="top", fontsize=11, fontweight="bold")

    fig.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.24, wspace=0.26)
    save_figure(fig, OUT_DIR / f"{key}_projections.png")


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
    prepare_figure(fig)
    labels = ("x", "y", "z")
    for idx, ax in enumerate(axes):
        ax.set_facecolor(WHITE)
        ax.vlines(freqs, 0.0, spectra[:, idx], color=FFT_COLORS[idx], linewidth=0.85)
        ax.axhline(0.0, color="0.25", linewidth=0.6)
        ax.set_ylabel(labels[idx], fontsize=11)
        ax.tick_params(labelsize=10, colors=INK)
        ax.grid(True, color=GRID, linewidth=0.45, alpha=0.55)
        for spine in ax.spines.values():
            spine.set_color(INK)
        if xlim is not None:
            ax.set_xlim(*xlim)
        ax.set_ylim(0.0, max(1.05, float(np.nanmax(spectra[:, idx])) * 1.08))
    axes[-1].set_xlabel("Frecuencia (Hz)", fontsize=11)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.98, bottom=0.10, hspace=0.12)
    save_figure(fig, ROOT / "assets" / "doc_figures" / "lorenz_fft.png")


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
    prepare_figure(fig)
    ax.set_facecolor(WHITE)
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
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_basin.png", dpi=170)


def plot_lorenz_basin_trajectories() -> None:
    params = LORENZ_BASIN_CASE["params"]
    fig = plt.figure(figsize=(12.0, 4.25), dpi=170)
    prepare_figure(fig)
    axes = [fig.add_subplot(1, 3, index + 1, projection="3d") for index in range(3)]

    for index, (ax, case) in enumerate(zip(axes, LORENZ_BASIN_TRAJECTORIES)):
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
            linewidth=1.35,
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
        style_3d(ax)
        ax.view_init(elev=24, azim=-58)
        panel_label(ax, f"({chr(97 + index)})")

    handles = [
        Line2D([0], [0], color=case["color"], lw=2.0, label=case["label"])
        for case in LORENZ_BASIN_TRAJECTORIES
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=8,
        bbox_to_anchor=(0.5, 0.015),
    )
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.16, top=0.98, wspace=0.10)
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_basin_trajectories.png", dpi=170)


def lorenz_reference_trajectory() -> tuple[np.ndarray, np.ndarray]:
    meta = SYSTEM_REGISTRY["lorenz"]
    t, x = simulate_system(
        "lorenz",
        meta["initial"],
        meta["defaults"],
        0.01,
        60.0,
        method_key="rk4",
    )
    keep = t >= 10.0
    return t[keep] - t[keep][0], x[keep]


def plot_lorenz_attractor(t: np.ndarray, x: np.ndarray) -> None:
    _, x_plot = thin(t, x, max_points=9000)
    fig = plt.figure(figsize=(6.0, 5.2), dpi=170)
    prepare_figure(fig)
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(x_plot[:, 0], x_plot[:, 1], x_plot[:, 2], color=LINE_COLOR, lw=1.0)
    style_3d(ax)
    fig.subplots_adjust(left=0.01, right=0.94, bottom=0.03, top=0.98)
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_attractor.png", dpi=170)


def plot_lorenz_projection_grid(t: np.ndarray, x: np.ndarray) -> None:
    _, x_plot = thin(t, x, max_points=9000)
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.85), dpi=170)
    prepare_figure(fig)
    pairs = (
        (0, 1, "x", "y", "#005a9c"),
        (0, 2, "x", "z", "#a64b00"),
        (1, 2, "y", "z", "#6b21a8"),
    )
    for index, (ax, (i, j, xlabel, ylabel, color)) in enumerate(zip(axes, pairs)):
        ax.plot(x_plot[:, i], x_plot[:, j], color=color, lw=1.0)
        style_2d(ax, xlabel, ylabel)
        panel_label(ax, f"({chr(97 + index)})")
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.18, top=0.97, wspace=0.28)
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_phase_portraits_2d_grid.png", dpi=170)


def lorenz_jacobian(state: np.ndarray, params: tuple[float, float, float]) -> np.ndarray:
    x, y, z = np.asarray(state, dtype=float)
    sigma, rho, beta = params
    return np.array(
        [
            [-sigma, sigma, 0.0],
            [rho - z, -1.0, -x],
            [y, x, -beta],
        ],
        dtype=float,
    )


def plot_lorenz_spectrum() -> None:
    sigma, rho, beta = SYSTEM_REGISTRY["lorenz"]["defaults"]
    branch = math.sqrt(beta * (rho - 1.0))
    equilibria = (
        ("$O$", np.array((0.0, 0.0, 0.0)), "o", "#005a9c"),
        (r"$E_{\pm}$", np.array((branch, branch, rho - 1.0)), "D", "#047857"),
    )
    fig, ax = plt.subplots(figsize=(6.4, 5.1), dpi=170)
    prepare_figure(fig)
    style_2d(ax, r"$\operatorname{Re}(\lambda)$", r"$\operatorname{Im}(\lambda)$")
    for label, point, marker, color in equilibria:
        eigenvalues = np.linalg.eigvals(lorenz_jacobian(point, (sigma, rho, beta)))
        ax.scatter(
            eigenvalues.real,
            eigenvalues.imag,
            s=68,
            marker=marker,
            facecolor=color,
            edgecolor=INK,
            linewidth=0.55,
            label=label,
            zorder=5,
        )
    ax.axhline(0.0, color=INK, lw=0.8)
    ax.axvline(0.0, color=INK, lw=0.8)
    ax.legend(loc="best", frameon=True, facecolor=WHITE, edgecolor=GRID)
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_spectrum.png", dpi=170)


def plot_logistic_bifurcation() -> None:
    parameters = np.linspace(2.6, 4.0, 1900)
    state = np.full_like(parameters, 0.5)
    for _ in range(900):
        state = parameters * state * (1.0 - state)
    retained = []
    for _ in range(180):
        state = parameters * state * (1.0 - state)
        retained.append(state.copy())
    values = np.asarray(retained)

    fig, ax = plt.subplots(figsize=(10.2, 5.2), dpi=180)
    prepare_figure(fig)
    ax.plot(
        np.repeat(parameters, values.shape[0]),
        values.T.ravel(),
        linestyle="none",
        marker=".",
        markersize=0.42,
        color=INK,
        alpha=0.72,
        rasterized=True,
    )
    style_2d(ax, "$r$", "$x_n$")
    ax.set_xlim(2.6, 4.0)
    ax.set_ylim(0.0, 1.0)
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "logistic_bifurcation.png", dpi=180)


def plot_lorenz_bifurcation() -> None:
    rho_values, events = bifurcation_poincare_lorenz(
        0.1,
        0.1,
        0.1,
        10.0,
        8.0 / 3.0,
        0.0,
        160.0,
        900,
        0.01,
        35.0,
        45.0,
        70,
        True,
        method_key="rk4",
    )
    finite = np.isfinite(rho_values) & np.isfinite(events)
    fig, ax = plt.subplots(figsize=(10.2, 5.2), dpi=180)
    prepare_figure(fig)
    ax.scatter(
        rho_values[finite],
        events[finite],
        s=0.65,
        color=LINE_COLOR,
        alpha=0.75,
        linewidths=0.0,
        rasterized=True,
    )
    style_2d(ax, r"$\rho$", "$z$ en el cruce")
    ax.set_xlim(0.0, 160.0)
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_bifurcation_rho.png", dpi=180)


def plot_lorenz_basin_reading_zones(basin: np.ndarray) -> None:
    class_colors = ("#111827", "#7dd3fc", "#dc2626", "#16a34a", "#2563eb", "#7c3aed")
    labels = {
        1: BASIN_RESIDUAL_LABEL,
        2: "Converge a $E_+$",
        3: "Converge a $E_-$",
    }
    present = sorted(int(value) for value in np.unique(basin))
    fig, ax = plt.subplots(figsize=(6.6, 5.7), dpi=170)
    prepare_figure(fig)
    ax.imshow(
        basin,
        origin="lower",
        extent=LORENZ_BASIN_CASE["extent"],
        interpolation="nearest",
        aspect="equal",
        cmap=ListedColormap(class_colors),
        vmin=-0.5,
        vmax=len(class_colors) - 0.5,
    )
    marker_handles = []
    for case in LORENZ_BASIN_TRAJECTORIES:
        x0, y0, _ = case["initial"]
        ax.scatter(
            [x0],
            [y0],
            s=62,
            facecolor=WHITE,
            edgecolor=INK,
            marker="o",
            linewidth=1.2,
            zorder=6,
        )
    ax.set_xlabel(r"$x_0$")
    ax.set_ylabel(r"$y_0$")
    ax.tick_params(colors=INK)
    for spine in ax.spines.values():
        spine.set_color(INK)
    handles = [
        Patch(facecolor=class_colors[value], edgecolor=INK, linewidth=0.5, label=labels[value])
        for value in present
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=WHITE,
            markeredgecolor=INK,
            label="Condición auditada",
        )
    )
    ax.legend(
        handles=handles,
        loc="upper right",
        fontsize=8,
        frameon=True,
        facecolor=WHITE,
        edgecolor=GRID,
    )
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_basin_reading_zones.png", dpi=170)


def plot_lyapunov_perturbation_concept() -> None:
    semi_axes = ((1.0, 1.0), (2.2, 0.36), (3.55, 0.10))
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.8), dpi=170)
    prepare_figure(fig)
    for index, (ax, (width, height)) in enumerate(zip(axes, semi_axes)):
        style_2d(ax, "dirección expansiva", "dirección contractiva")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-4.0, 4.0)
        ax.set_ylim(-1.65, 1.65)
        ellipse = Ellipse(
            (0.0, 0.0),
            width=2.0 * width,
            height=2.0 * height,
            facecolor="#dbeafe",
            edgecolor="#0369a1",
            linewidth=2.2,
            alpha=0.95,
        )
        ax.add_patch(ellipse)
        ax.arrow(
            0.0,
            0.0,
            width * 0.92,
            0.0,
            color="#be123c",
            width=0.018,
            head_width=0.14,
            head_length=0.16,
            length_includes_head=True,
            zorder=5,
        )
        ax.arrow(
            0.0,
            0.0,
            0.0,
            height * 0.90,
            color="#1d4ed8",
            width=0.018,
            head_width=0.14,
            head_length=min(0.16, max(0.04, 0.3 * height)),
            length_includes_head=True,
            zorder=5,
        )
        ax.scatter([0.0], [0.0], s=26, color=INK, zorder=6)
        panel_label(ax, f"({chr(97 + index)})")
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.20, top=0.97, wspace=0.25)
    save_figure(fig, DOC_FIGURE_DIR / "lyapunov_perturbation_concept.png", dpi=170)


def plot_lorenz_lyapunov() -> None:
    meta = SYSTEM_REGISTRY["lorenz"]
    result = integer_qr_benettin_lyapunov(
        "lorenz",
        meta["initial"],
        meta["defaults"],
        0.01,
        30.0,
        t_burn=10.0,
        reorthonormalize_every=10,
    )
    if result.status != "ok" or result.convergence.size == 0:
        raise RuntimeError(f"Lyapunov reference calculation failed: {result.status}")
    fig, ax = plt.subplots(figsize=(7.4, 4.7), dpi=170)
    prepare_figure(fig)
    for index, color in enumerate(FFT_COLORS):
        ax.plot(
            result.times,
            result.convergence[:, index],
            color=color,
            lw=1.35,
            label=rf"$\lambda_{index + 1}(t)$",
        )
    style_2d(ax, "$t$", r"$\lambda_i(t)$")
    ax.axhline(0.0, color=INK, lw=0.75)
    ax.legend(loc="center right", facecolor=WHITE, edgecolor=GRID, framealpha=0.95)
    fig.tight_layout()
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_lyapunov.png", dpi=170)


def poincare_crossings_x_zero(x: np.ndarray) -> np.ndarray:
    left = x[:-1, 0]
    right = x[1:, 0]
    indices = np.flatnonzero((left < 0.0) & (right >= 0.0))
    crossings = []
    for index in indices:
        denominator = right[index] - left[index]
        if abs(denominator) <= 1.0e-15:
            continue
        fraction = -left[index] / denominator
        crossings.append(x[index] + fraction * (x[index + 1] - x[index]))
    return np.asarray(crossings, dtype=float)


def plot_lorenz_poincare_section() -> None:
    meta = SYSTEM_REGISTRY["lorenz"]
    t, x = simulate_system(
        "lorenz",
        meta["initial"],
        meta["defaults"],
        0.01,
        140.0,
        method_key="rk4",
    )
    orbit = x[t >= 20.0]
    crossings = poincare_crossings_x_zero(orbit)
    _, orbit_plot = thin(np.arange(len(orbit), dtype=float), orbit, max_points=10000)

    fig = plt.figure(figsize=(10.4, 5.6), dpi=160)
    prepare_figure(fig)
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    ax3d.plot(
        orbit_plot[:, 0],
        orbit_plot[:, 1],
        orbit_plot[:, 2],
        color=LINE_COLOR,
        lw=0.85,
        alpha=0.92,
    )
    y_grid = np.linspace(float(np.min(orbit[:, 1])), float(np.max(orbit[:, 1])), 2)
    z_grid = np.linspace(float(np.min(orbit[:, 2])), float(np.max(orbit[:, 2])), 2)
    yy, zz = np.meshgrid(y_grid, z_grid)
    ax3d.plot_surface(
        np.zeros_like(yy),
        yy,
        zz,
        color="#0ea5e9",
        alpha=0.18,
        shade=False,
    )
    if crossings.size:
        ax3d.scatter(
            crossings[:, 0],
            crossings[:, 1],
            crossings[:, 2],
            color="#b91c1c",
            s=18,
            depthshade=False,
            zorder=6,
        )
    style_3d(ax3d)
    panel_label(ax3d, "(a)")

    ax = fig.add_subplot(1, 2, 2)
    style_2d(ax, "$y$ en el cruce", "$z$ en el cruce")
    if crossings.size:
        ax.scatter(
            crossings[:, 1],
            crossings[:, 2],
            s=22,
            color="#b91c1c",
            edgecolor=INK,
            linewidth=0.25,
        )
    panel_label(ax, "(b)")
    fig.subplots_adjust(left=0.04, right=0.985, bottom=0.12, top=0.98, wspace=0.22)
    save_figure(fig, DOC_FIGURE_DIR / "lorenz_poincare_section.png", dpi=160)


def hopf_normal_form_trajectory(
    mu: float,
    initial: tuple[float, float],
    *,
    dt: float = 0.01,
    duration: float = 32.0,
) -> np.ndarray:
    steps = int(round(duration / dt))
    trajectory = np.empty((steps + 1, 2), dtype=float)
    trajectory[0] = initial

    def field(state: np.ndarray) -> np.ndarray:
        x, y = state
        radius_squared = x * x + y * y
        return np.array(
            (mu * x - y - radius_squared * x, x + mu * y - radius_squared * y),
            dtype=float,
        )

    for index in range(steps):
        state = trajectory[index]
        k1 = field(state)
        k2 = field(state + 0.5 * dt * k1)
        k3 = field(state + 0.5 * dt * k2)
        k4 = field(state + dt * k3)
        trajectory[index + 1] = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return trajectory


def plot_hopf_bifurcation_example() -> None:
    fig = plt.figure(figsize=(9.6, 6.0), dpi=160)
    prepare_figure(fig)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.0, 0.78), hspace=0.36, wspace=0.24)
    cases = ((-0.35, (1.2, 0.05)), (0.45, (0.12, 0.04)))
    for index, (mu, initial) in enumerate(cases):
        ax = fig.add_subplot(grid[0, index])
        trajectory = hopf_normal_form_trajectory(mu, initial)
        ax.plot(trajectory[:, 0], trajectory[:, 1], color="#be123c", lw=1.35)
        if mu > 0.0:
            theta = np.linspace(0.0, 2.0 * np.pi, 500)
            radius = math.sqrt(mu)
            ax.plot(radius * np.cos(theta), radius * np.sin(theta), color="#0369a1", lw=2.2)
        ax.scatter([0.0], [0.0], s=34, color=INK, zorder=5)
        style_2d(ax, "$x$", "$y$")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)
        panel_label(ax, f"({chr(97 + index)})")

    ax = fig.add_subplot(grid[1, :])
    negative = np.linspace(-0.8, 0.0, 240)
    positive = np.linspace(0.0, 1.2, 320)
    ax.plot(negative, np.zeros_like(negative), color=INK, lw=2.0, label="equilibrio estable")
    ax.plot(
        positive,
        np.zeros_like(positive),
        color=INK,
        lw=1.7,
        linestyle="--",
        label="equilibrio inestable",
    )
    radius = np.sqrt(positive)
    ax.plot(positive, radius, color="#0369a1", lw=2.2, label="ciclo estable")
    ax.plot(positive, -radius, color="#0369a1", lw=2.2)
    ax.axvline(0.0, color="#be123c", lw=1.2, linestyle=":")
    style_2d(ax, r"$\mu$", "amplitud radial")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        fontsize=8,
        frameon=False,
    )
    panel_label(ax, "(c)")
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.10, top=0.98)
    save_figure(fig, DOC_FIGURE_DIR / "hopf_bifurcation_example.png", dpi=160)


def plot_topology_neighborhood_boundary() -> None:
    theta = np.linspace(0.0, 2.0 * np.pi, 600)
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.4), dpi=170)
    prepare_figure(fig)

    ax = axes[0]
    ax.fill(1.15 * np.cos(theta), 0.75 * np.sin(theta), color="#dbeafe", alpha=0.95)
    ax.plot(1.15 * np.cos(theta), 0.75 * np.sin(theta), color="#0369a1", lw=1.8, linestyle="--")
    ax.scatter([0.20], [-0.05], s=35, color=INK, zorder=5)
    ax.add_patch(Circle((0.20, -0.05), 0.30, fill=False, edgecolor="#be123c", linewidth=1.8))
    ax.text(0.24, -0.01, "$p$", fontsize=10, color=INK)
    ax.text(0.50, 0.25, r"$B_{\varepsilon}(p)$", fontsize=10, color="#be123c")
    ax.text(-0.95, 0.52, "$U$", fontsize=11, color="#0369a1")
    panel_label(ax, "(a)")

    ax = axes[1]
    radius = 0.95 + 0.10 * np.cos(3.0 * theta)
    xx = radius * np.cos(theta)
    yy = 0.75 * radius * np.sin(theta)
    ax.fill(xx, yy, color="#dcfce7", alpha=0.92)
    ax.plot(xx, yy, color="#047857", lw=2.2)
    interior = theta[::45]
    ax.scatter(
        0.68 * np.cos(interior),
        0.50 * np.sin(interior),
        s=18,
        color="#047857",
        zorder=4,
    )
    ax.text(-0.12, 0.04, r"$\mathring{A}$", fontsize=12, color="#047857")
    ax.text(0.58, 0.58, r"$\partial A$", fontsize=11, color="#065f46")
    panel_label(ax, "(b)")

    ax = axes[2]
    ax.fill(xx, yy, color="#ede9fe", alpha=0.92)
    ax.plot(xx, yy, color="#6d28d9", lw=2.2)
    outside_x = np.array((-1.30, -1.05, 1.08, 1.28, 0.15))
    outside_y = np.array((0.45, -0.78, 0.70, -0.42, 1.02))
    ax.scatter(outside_x, outside_y, s=24, marker="x", color="#b91c1c", linewidth=1.5)
    ax.text(-0.18, 0.04, r"$\overline{A}$", fontsize=12, color="#6d28d9")
    ax.text(1.02, 0.78, r"$A^{c}$", fontsize=11, color="#b91c1c")
    panel_label(ax, "(c)")

    for ax in axes:
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.15, 1.15)
        ax.set_facecolor(WHITE)
        ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.03, top=0.98, wspace=0.08)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[0], dpi=170)


def plot_flow_invariance_trapping() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), dpi=170)
    prepare_figure(fig)

    ax = axes[0]
    grid = np.linspace(-2.0, 2.0, 17)
    xx, yy = np.meshgrid(grid, grid)
    uu = -0.65 * xx
    vv = -0.45 * yy
    speed = np.hypot(uu, vv)
    safe_speed = np.where(speed > 0.0, speed, 1.0)
    ax.quiver(xx, yy, uu / safe_speed, vv / safe_speed, color="#64748b", alpha=0.70, scale=28)
    for initial, color in (((1.8, 1.2), "#0369a1"), ((-1.7, 1.1), "#be123c")):
        time = np.linspace(0.0, 5.0, 350)
        trajectory = np.column_stack(
            (
                initial[0] * np.exp(-0.65 * time),
                initial[1] * np.exp(-0.45 * time),
            )
        )
        ax.plot(trajectory[:, 0], trajectory[:, 1], color=color, lw=2.0)
        ax.scatter([trajectory[0, 0]], [trajectory[0, 1]], s=28, color=color)
    ax.scatter([0.0], [0.0], s=36, color=INK, zorder=6)
    style_2d(ax, "$x$", "$y$")
    ax.set_aspect("equal", adjustable="box")
    panel_label(ax, "(a)")

    ax = axes[1]
    theta = np.linspace(0.0, 2.0 * np.pi, 500)
    ax.fill(1.85 * np.cos(theta), 1.25 * np.sin(theta), color="#dbeafe", alpha=0.60)
    ax.plot(1.85 * np.cos(theta), 1.25 * np.sin(theta), color="#0369a1", lw=2.0)
    ax.fill(1.05 * np.cos(theta), 0.62 * np.sin(theta), color="#dcfce7", alpha=0.88)
    ax.plot(1.05 * np.cos(theta), 0.62 * np.sin(theta), color="#047857", lw=2.0)
    ax.text(-1.68, 0.92, "$D$", color="#0369a1", fontsize=12)
    ax.text(-0.88, 0.38, r"$\varphi_t(D)$", color="#047857", fontsize=11)
    for angle in np.linspace(0.25, 2.0 * np.pi + 0.25, 8, endpoint=False):
        start = np.array((1.75 * np.cos(angle), 1.18 * np.sin(angle)))
        end = np.array((1.08 * np.cos(angle), 0.64 * np.sin(angle)))
        arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, color=INK, lw=0.8)
        ax.add_patch(arrow)
    ax.scatter([0.0], [0.0], s=34, color=INK, zorder=6)
    style_2d(ax, "$x$", "$y$")
    ax.set_aspect("equal", adjustable="box")
    panel_label(ax, "(b)")
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.16, top=0.98, wspace=0.25)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[1], dpi=170)


def plot_omega_limit_trapping_region() -> None:
    time = np.linspace(0.0, 18.0, 1800)
    radius = 1.0 + 0.85 * np.exp(-0.34 * time)
    angle = 1.65 * time
    xx = radius * np.cos(angle)
    yy = radius * np.sin(angle)
    theta = np.linspace(0.0, 2.0 * np.pi, 700)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0), dpi=170)
    prepare_figure(fig)
    ax = axes[0]
    ax.fill(1.35 * np.cos(theta), 1.35 * np.sin(theta), color="#dbeafe", alpha=0.72)
    ax.fill(0.70 * np.cos(theta), 0.70 * np.sin(theta), color=WHITE)
    ax.plot(1.35 * np.cos(theta), 1.35 * np.sin(theta), color="#64748b", lw=1.2, linestyle="--")
    ax.plot(0.70 * np.cos(theta), 0.70 * np.sin(theta), color="#64748b", lw=1.2, linestyle="--")
    ax.plot(np.cos(theta), np.sin(theta), color="#047857", lw=2.5)
    ax.plot(xx, yy, color="#b91c1c", lw=1.45)
    ax.scatter([xx[0]], [yy[0]], s=32, color="#b91c1c", zorder=6)
    ax.text(-0.20, 1.05, r"$\omega(x_0)$", color="#047857", fontsize=11)
    style_2d(ax, "$x$", "$y$")
    ax.set_aspect("equal", adjustable="box")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(time, np.abs(radius - 1.0), color="#b91c1c", lw=2.0)
    style_2d(ax, "$t$", r"$\operatorname{dist}(\varphi_t(x_0),\omega(x_0))$")
    ax.set_ylim(bottom=0.0)
    panel_label(ax, "(b)")
    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.16, top=0.98, wspace=0.28)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[2], dpi=170)


def plot_conjugacy_orbital_equivalence() -> None:
    time = np.linspace(0.0, 2.2 * np.pi, 700)
    source = np.column_stack((1.18 * np.cos(time), 0.72 * np.sin(time)))
    target = np.column_stack(
        (
            source[:, 0] + 0.22 * source[:, 1] ** 2,
            source[:, 1] + 0.18 * source[:, 0] * source[:, 1],
        )
    )
    marks = np.array((45, 150, 290, 470, 630))
    reparam_marks = np.array((45, 105, 235, 445, 630))

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.7), dpi=170)
    prepare_figure(fig)
    ax = axes[0]
    ax.plot(source[:, 0], source[:, 1], color="#0369a1", lw=2.2)
    ax.scatter(source[marks, 0], source[marks, 1], color="#0369a1", s=35, zorder=5)
    ax.text(-0.18, 0.02, r"$\varphi_t$", fontsize=12, color="#0369a1")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(target[:, 0], target[:, 1], color="#047857", lw=2.2)
    ax.scatter(target[marks, 0], target[marks, 1], color="#047857", s=35, zorder=5)
    for source_point, target_point in zip(source[marks], target[marks]):
        start = 0.78 * source_point
        end = target_point
        ax.add_patch(
            FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=9, color="#64748b", lw=0.7)
        )
    ax.text(-0.10, 0.03, r"$h\circ\varphi_t=\psi_t\circ h$", fontsize=10, color="#047857")
    panel_label(ax, "(b)")

    ax = axes[2]
    ax.plot(target[:, 0], target[:, 1], color="#6d28d9", lw=2.2)
    ax.scatter(target[reparam_marks, 0], target[reparam_marks, 1], color="#be123c", s=36, zorder=5)
    ax.text(-0.18, 0.02, r"$\psi_{\theta(t)}$", fontsize=12, color="#6d28d9")
    panel_label(ax, "(c)")

    for ax in axes:
        ax.set_facecolor(WHITE)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.55, 1.55)
        ax.set_ylim(-1.10, 1.10)
        ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.03, top=0.98, wspace=0.08)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[3], dpi=170)


def plot_variational_volume_manifolds() -> None:
    theta = np.linspace(0.0, 2.0 * np.pi, 600)
    circle = np.vstack((np.cos(theta), np.sin(theta)))
    transform = np.array(((1.65, 0.58), (0.12, 0.48)))
    ellipse = transform @ circle

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.6), dpi=170)
    prepare_figure(fig)
    ax = axes[0]
    ax.fill(circle[0], circle[1], color="#dbeafe", alpha=0.75)
    ax.plot(circle[0], circle[1], color="#0369a1", lw=1.8)
    ax.fill(ellipse[0], ellipse[1], color="#fee2e2", alpha=0.60)
    ax.plot(ellipse[0], ellipse[1], color="#b91c1c", lw=2.0)
    ax.arrow(0.0, 0.0, 1.0, 0.0, color="#0369a1", width=0.015, head_width=0.10)
    image_vector = transform @ np.array((1.0, 0.0))
    ax.arrow(
        0.0,
        0.0,
        image_vector[0],
        image_vector[1],
        color="#b91c1c",
        width=0.015,
        head_width=0.10,
    )
    ax.text(0.52, 0.13, r"$D\varphi_t(x)v$", fontsize=10, color="#b91c1c")
    panel_label(ax, "(a)")

    ax = axes[1]
    base = np.array(((-0.8, -0.65), (0.55, -0.65), (0.85, 0.45), (-0.5, 0.45)))
    image = (transform @ base.T).T * 0.72
    ax.add_patch(Polygon(base, closed=True, facecolor="#dbeafe", edgecolor="#0369a1", lw=1.8, alpha=0.80))
    ax.add_patch(Polygon(image, closed=True, facecolor="#dcfce7", edgecolor="#047857", lw=1.8, alpha=0.68))
    ax.text(-0.62, -0.18, "$V_0$", fontsize=11, color="#0369a1")
    ax.text(0.28, 0.28, "$V_t$", fontsize=11, color="#047857")
    panel_label(ax, "(b)")

    ax = axes[2]
    grid = np.linspace(-1.75, 1.75, 19)
    xx, yy = np.meshgrid(grid, grid)
    uu, vv = xx, -yy
    speed = np.hypot(uu, vv)
    ax.streamplot(xx, yy, uu, vv, color="#94a3b8", density=0.75, linewidth=0.7, arrowsize=0.7)
    ax.axhline(0.0, color="#b91c1c", lw=2.2, label=r"$W^u$")
    ax.axvline(0.0, color="#0369a1", lw=2.2, label=r"$W^s$")
    ax.scatter([0.0], [0.0], s=32, color=INK, zorder=6)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    panel_label(ax, "(c)")

    for ax in axes:
        style_2d(ax, "$x$", "$y$")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.9, 1.9)
        ax.set_ylim(-1.55, 1.55)
    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.17, top=0.98, wspace=0.30)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[4], dpi=170)


def plot_poincare_floquet_geometry() -> None:
    time = np.linspace(0.0, 14.0, 1100)
    radius = 1.0 + 0.72 * np.exp(-0.28 * time)
    angle = 1.7 * time
    xx = radius * np.cos(angle)
    yy = radius * np.sin(angle)
    theta = np.linspace(0.0, 2.0 * np.pi, 600)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.1), dpi=170)
    prepare_figure(fig)
    ax = axes[0]
    ax.plot(np.cos(theta), np.sin(theta), color="#0369a1", lw=2.4)
    ax.plot(xx, yy, color="#b91c1c", lw=1.4)
    ax.plot([0.55, 1.55], [0.0, 0.0], color="#047857", lw=2.0)
    crossing = np.flatnonzero((yy[:-1] < 0.0) & (yy[1:] >= 0.0) & (xx[:-1] > 0.0))
    ax.scatter(xx[crossing], yy[crossing], s=32, color="#047857", edgecolor=INK, linewidth=0.35, zorder=6)
    ax.text(1.43, 0.08, r"$\Sigma$", color="#047857", fontsize=12)
    ax.text(0.05, 1.07, r"$\gamma$", color="#0369a1", fontsize=12)
    style_2d(ax, "$x$", "$y$")
    ax.set_aspect("equal", adjustable="box")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.plot(np.cos(theta), np.sin(theta), color="#64748b", lw=1.4, linestyle="--")
    multipliers = np.array((1.0 + 0.0j, 0.42 + 0.18j, 0.42 - 0.18j))
    ax.scatter(
        multipliers.real,
        multipliers.imag,
        s=(70, 58, 58),
        color=("#be123c", "#0369a1", "#0369a1"),
        edgecolor=INK,
        linewidth=0.5,
        zorder=5,
    )
    ax.text(1.02, 0.08, r"$\mu_1=1$", fontsize=10, color="#be123c")
    ax.text(0.48, 0.24, r"$\mu_{2,3}$", fontsize=10, color="#0369a1")
    ax.axhline(0.0, color=GRID, lw=0.8)
    ax.axvline(0.0, color=GRID, lw=0.8)
    style_2d(ax, r"$\operatorname{Re}(\mu)$", r"$\operatorname{Im}(\mu)$")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.25, 1.35)
    ax.set_ylim(-1.20, 1.20)
    panel_label(ax, "(b)")
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.16, top=0.98, wspace=0.28)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[5], dpi=170)


def plot_degree_fixed_point() -> None:
    theta = np.linspace(0.0, 2.0 * np.pi, 18, endpoint=False)
    dense = np.linspace(0.0, 2.0 * np.pi, 600)
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.0), dpi=170)
    prepare_figure(fig)
    cases = ((np.array((0.30, 0.18)), "1"), (np.array((1.55, 0.18)), "0"))
    for index, (ax, (zero, degree)) in enumerate(zip(axes, cases)):
        boundary = np.column_stack((np.cos(theta), np.sin(theta)))
        vectors = boundary - zero
        scale = np.linalg.norm(vectors, axis=1)
        unit = vectors / scale[:, None]
        ax.plot(np.cos(dense), np.sin(dense), color=INK, lw=1.4)
        ax.quiver(
            boundary[:, 0],
            boundary[:, 1],
            0.42 * unit[:, 0],
            0.42 * unit[:, 1],
            angles="xy",
            scale_units="xy",
            scale=1.0,
            color="#0369a1",
            width=0.008,
        )
        ax.scatter([zero[0]], [zero[1]], marker="x", s=62, color="#b91c1c", linewidth=2.0, zorder=6)
        ax.text(
            0.5,
            0.045,
            rf"$\deg(F,D,0)={degree}$",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=11,
            color=INK,
            bbox={"facecolor": WHITE, "edgecolor": "none", "alpha": 0.90, "pad": 1.5},
            zorder=10,
        )
        style_2d(ax, "$x$", "$y$")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.45, 1.95)
        ax.set_ylim(-1.45, 1.45)
        panel_label(ax, f"({chr(97 + index)})")
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.20, top=0.98, wspace=0.25)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[6], dpi=170)


def plot_horseshoe_symbolic_dynamics() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.7), dpi=170)
    prepare_figure(fig)

    ax = axes[0]
    ax.add_patch(Rectangle((-1.0, -1.0), 2.0, 2.0, fill=False, edgecolor=INK, lw=1.5))
    ax.add_patch(Rectangle((-0.82, -1.0), 0.48, 2.0, facecolor="#bfdbfe", edgecolor="#0369a1", lw=1.5))
    ax.add_patch(Rectangle((0.34, -1.0), 0.48, 2.0, facecolor="#fecaca", edgecolor="#b91c1c", lw=1.5))
    ax.text(-0.60, 0.0, "$0$", ha="center", va="center", fontsize=14, color="#0369a1")
    ax.text(0.58, 0.0, "$1$", ha="center", va="center", fontsize=14, color="#b91c1c")
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.add_patch(Rectangle((-0.48, -1.35), 0.42, 2.70, facecolor="#bfdbfe", edgecolor="#0369a1", lw=1.5))
    ax.add_patch(Rectangle((0.08, -1.35), 0.42, 2.70, facecolor="#fecaca", edgecolor="#b91c1c", lw=1.5))
    ax.annotate("", xy=(0.95, 0.0), xytext=(-0.95, 0.0), arrowprops={"arrowstyle": "-|>", "color": INK})
    panel_label(ax, "(b)")

    ax = axes[2]
    outer_theta = np.linspace(0.0, np.pi, 260)
    left_x = -0.55 + 0.42 * np.cos(outer_theta)
    left_y = 0.20 + 0.95 * np.sin(outer_theta)
    right_x = 0.55 - 0.42 * np.cos(outer_theta)
    right_y = 0.20 + 0.95 * np.sin(outer_theta)
    ax.plot(left_x, left_y, color="#0369a1", lw=8.0, solid_capstyle="butt")
    ax.plot(right_x, right_y, color="#b91c1c", lw=8.0, solid_capstyle="butt")
    ax.plot([-0.97, -0.97], [-1.05, 0.20], color="#0369a1", lw=8.0)
    ax.plot([0.97, 0.97], [-1.05, 0.20], color="#b91c1c", lw=8.0)
    symbolic = r"$\ldots 0\,1\,1\,0\,1\ldots$"
    ax.text(0.0, -1.28, symbolic, ha="center", va="center", fontsize=11, color=INK)
    panel_label(ax, "(c)")

    for ax in axes:
        ax.set_facecolor(WHITE)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-1.55, 1.45)
        ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.99, bottom=0.03, top=0.98, wspace=0.08)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[7], dpi=170)


def mittag_leffler_relaxation(q: float, time: np.ndarray) -> np.ndarray:
    values = np.empty_like(time, dtype=float)
    for index, point in enumerate(time):
        z = -(float(point) ** q)
        total = 0.0
        for order in range(120):
            term = (z**order) / math.gamma(q * order + 1.0)
            total += term
            if abs(term) < 1.0e-13:
                break
        values[index] = total
    return values


def plot_fractional_memory_kernel_pece() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(10.9, 3.7), dpi=170)
    prepare_figure(fig)

    ax = axes[0]
    lag = np.linspace(0.02, 1.0, 500)
    for q, color in zip((0.4, 0.7, 0.9), ("#6d28d9", "#0369a1", "#047857")):
        kernel = lag ** (q - 1.0) / math.gamma(q)
        ax.plot(lag, kernel, color=color, lw=1.8, label=rf"$q={q:.1f}$")
    style_2d(ax, r"retardo $t-s$", r"$(t-s)^{q-1}/\Gamma(q)$")
    ax.set_ylim(0.0, 5.0)
    ax.legend(frameon=False, fontsize=8)
    panel_label(ax, "(a)")

    ax = axes[1]
    relaxation_time = np.linspace(0.0, 2.5, 260)
    ax.plot(relaxation_time, np.exp(-relaxation_time), color=INK, lw=1.8, linestyle="--", label="$e^{-t}$")
    for q, color in ((0.7, "#0369a1"), (0.9, "#047857")):
        ax.plot(
            relaxation_time,
            mittag_leffler_relaxation(q, relaxation_time),
            color=color,
            lw=1.9,
            label=rf"$E_{{{q:.1f}}}(-t^{{{q:.1f}}})$",
        )
    style_2d(ax, "$t$", "$u(t)$")
    ax.set_ylim(0.0, 1.05)
    ax.legend(frameon=False, fontsize=8)
    panel_label(ax, "(b)")

    ax = axes[2]
    n = 18
    q = 0.75
    indices = np.arange(n + 1)
    age = n - indices
    weights = (age + 1.0) ** q - age**q
    ax.bar(indices, weights, color="#0369a1", edgecolor=INK, linewidth=0.35, width=0.82)
    ax.axvline(n, color="#be123c", lw=1.2, linestyle=":")
    style_2d(ax, "índice histórico $j$", r"$b_{j,n+1}$")
    panel_label(ax, "(c)")
    fig.subplots_adjust(left=0.065, right=0.99, bottom=0.19, top=0.98, wspace=0.32)
    save_figure(fig, DOC_FIGURE_DIR / THEORY_FIGURE_NAMES[8], dpi=170)


def generate_theory_figures() -> None:
    plot_topology_neighborhood_boundary()
    plot_flow_invariance_trapping()
    plot_omega_limit_trapping_region()
    plot_conjugacy_orbital_equivalence()
    plot_variational_volume_manifolds()
    plot_poincare_floquet_geometry()
    plot_degree_fixed_point()
    plot_horseshoe_symbolic_dynamics()
    plot_fractional_memory_kernel_pece()


def generate_lorenz_basin_figures() -> None:
    DOC_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    basin = compute_lorenz_basin_example()
    plot_lorenz_basin_example(basin)
    plot_lorenz_basin_trajectories()


def generate_system_figures(keys, *, projections: bool) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key in keys:
        case = CASES[key]
        meta = SYSTEM_REGISTRY[key]
        params = meta.get("defaults", ())
        initial = meta.get("initial", (0.1, 0.1, 0.1))
        t, x = simulate_system(key, initial, params, case["dt"], case["T"], method_key="rk4")
        t_tail, x_tail = finite_tail(t, x)
        plot_phase_timeseries(key, meta["label"], t_tail, x_tail)
        if projections:
            plot_projections(key, meta["label"], t_tail, x_tail)
        print(f"generated {key}")


def generate_manual_figures() -> None:
    generate_system_figures(MANUAL_SYSTEM_KEYS, projections=False)

    t_lorenz, x_lorenz = lorenz_reference_trajectory()
    plot_lorenz_attractor(t_lorenz, x_lorenz)
    print("generated lorenz_attractor")
    plot_lorenz_projection_grid(t_lorenz, x_lorenz)
    print("generated lorenz_phase_portraits_2d_grid")
    plot_lorenz_spectrum()
    print("generated lorenz_spectrum")
    plot_logistic_bifurcation()
    print("generated logistic_bifurcation")
    plot_lorenz_bifurcation()
    print("generated lorenz_bifurcation_rho")

    basin = compute_lorenz_basin_example()
    plot_lorenz_basin_reading_zones(basin)
    print("generated lorenz_basin_reading_zones")
    plot_lorenz_basin_trajectories()
    print("generated lorenz_basin_trajectories")

    plot_lyapunov_perturbation_concept()
    print("generated lyapunov_perturbation_concept")
    plot_lorenz_lyapunov()
    print("generated lorenz_lyapunov")
    plot_fft_example()
    print("generated lorenz_fft")
    plot_lorenz_poincare_section()
    print("generated lorenz_poincare_section")
    plot_hopf_bifurcation_example()
    print("generated hopf_bifurcation_example")

    generate_theory_figures()
    print("generated " + ", ".join(name.removesuffix(".png") for name in THEORY_FIGURE_NAMES))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--lorenz-basin-only",
        action="store_true",
        help="Regenerate only the two documented Lorenz basin figures.",
    )
    mode.add_argument(
        "--manual-only",
        action="store_true",
        help="Regenerate only figures included by the pedagogical theory manual.",
    )
    args = parser.parse_args(argv)

    if args.lorenz_basin_only:
        generate_lorenz_basin_figures()
        print("generated lorenz_basin and lorenz_basin_trajectories")
        return 0

    if args.manual_only:
        generate_manual_figures()
        return 0

    generate_system_figures(CASES, projections=True)
    plot_fft_example()
    print("generated lorenz_fft")
    generate_lorenz_basin_figures()
    print("generated lorenz_basin and lorenz_basin_trajectories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
