from __future__ import annotations

import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PyQt6.QtWidgets import QSizePolicy


SPECTRUM_STYLE = {
    'nodo estable': {'color': '#1f77b4', 'marker': 'o'},
    'nodo inestable': {'color': '#d62728', 'marker': 'o'},
    'silla': {'color': '#ff7f0e', 'marker': '^'},
    'foco estable': {'color': '#2ca02c', 'marker': 'o'},
    'foco inestable': {'color': '#9467bd', 'marker': 'o'},
    'silla-foco': {'color': '#e377c2', 'marker': '^'},
    'no hiperbólico': {'color': '#7f7f7f', 'marker': 's'},
    'indeterminado': {'color': '#8c564b', 'marker': 'D'},
}


class _BaseCanvas(FigureCanvas):
    def __init__(self, fig, parent=None):
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()


class Mpl3DCanvas(_BaseCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        super().__init__(self.fig, parent)
        self.reset_plot()

    def reset_plot(self):
        self.ax.clear()
        self.ax.set_title('Atractor 3D')
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')
        self.fig.subplots_adjust(left=0.05, right=0.98, bottom=0.07, top=0.92)
        self.draw_idle()

    def plot_lorenz(self, x, y, z):
        self.ax.clear()
        self.ax.plot(x, y, z, linewidth=0.8)
        self.ax.scatter([x[0]], [y[0]], [z[0]], s=30)
        self.ax.scatter([x[-1]], [y[-1]], [z[-1]], s=30)
        self.ax.set_title('Atractor 3D')
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('y')
        self.ax.set_zlabel('z')
        self.fig.subplots_adjust(left=0.05, right=0.98, bottom=0.07, top=0.92)
        self.draw_idle()


class MplBifCanvas(_BaseCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig, parent)
        self.reset_plot()

    def reset_plot(self):
        self.ax.clear()
        self.ax.set_title('Diagrama de bifurcación')
        self.ax.set_xlabel(r'$\rho$')
        self.ax.set_ylabel(r'$z$ en el evento')
        self.fig.subplots_adjust(left=0.10, right=0.98, bottom=0.12, top=0.92)
        self.draw_idle()

    def plot_bifurcation(self, param_values, event_values, title, xlabel, ylabel):
        self.ax.clear()
        if len(param_values) > 0:
            self.ax.plot(
                param_values,
                event_values,
                linestyle='None',
                marker='.',
                markersize=1.2,
                color='black',
                rasterized=True,
            )
            xmin = float(np.min(param_values))
            xmax = float(np.max(param_values))
            ymin = float(np.min(event_values))
            ymax = float(np.max(event_values))
            padx = max(0.5, 0.015 * max(abs(xmin), abs(xmax), 1.0))
            pady = max(0.5, 0.03 * max(abs(ymin), abs(ymax), 1.0))
            self.ax.set_xlim(xmin - padx, xmax + padx)
            self.ax.set_ylim(ymin - pady, ymax + pady)
        else:
            self.ax.text(0.5, 0.5, 'No hubo cruces registrados.', ha='center', va='center', transform=self.ax.transAxes)
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(alpha=0.14, linewidth=0.6)
        self.fig.subplots_adjust(left=0.10, right=0.98, bottom=0.12, top=0.92)
        self.draw_idle()


class MplBasinCanvas(_BaseCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        gs = self.fig.add_gridspec(1, 2, width_ratios=[22, 1], wspace=0.08)
        self.ax = self.fig.add_subplot(gs[0, 0])
        self.cax = self.fig.add_subplot(gs[0, 1])
        super().__init__(self.fig, parent)
        self.cbar = None
        self.reset_plot()

    def reset_plot(self):
        self.ax.clear()
        self.cax.clear()
        self.cax.set_visible(False)
        self.ax.set_title('Cuenca / clasificación')
        self.ax.set_xlabel(r'$x_0$')
        self.ax.set_ylabel(r'$y_0$')
        self.ax.set_aspect('auto')
        self.draw_idle()

    def plot_basin(self, basin, extent, rho_value, z0_fixed, equilibrium_data=None, show_equilibria=False):
        self.ax.clear()
        self.cax.clear()
        self.cax.set_visible(True)

        cmap = ListedColormap([
            '#000000',
            '#87ceeb',
            '#d62728',
            '#2ca02c',
            '#1f77b4',
        ])

        im = self.ax.imshow(
            basin,
            origin='lower',
            extent=extent,
            interpolation='nearest',
            aspect='auto',
            cmap=cmap,
            vmin=-0.5,
            vmax=4.5,
        )

        self.ax.set_title(f'Cuenca en el plano z={z0_fixed:.4g} (rho={rho_value:.4g})')
        self.ax.set_xlabel(r'$x_0$')
        self.ax.set_ylabel(r'$y_0$')
        self.ax.set_aspect('auto')

        if show_equilibria and equilibrium_data:
            self._draw_equilibria_projection(equilibrium_data, extent)

        self.cbar = self.fig.colorbar(im, cax=self.cax, ticks=np.arange(5))
        self.cbar.ax.set_yticklabels(['escape', 'caótica', 'E+', 'E-', 'origen'])
        self.draw_idle()

    def _draw_equilibria_projection(self, equilibrium_data, extent):
        x_min, x_max, y_min, y_max = extent
        for eq in equilibrium_data:
            x, y, _z = eq['point']
            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                continue

            label = eq['name']
            local_type = eq.get('local_type', 'indeterminado')

            if 'estable' in local_type:
                marker = 'o'
                size = 75
            elif 'silla' in local_type:
                marker = '^'
                size = 82
            elif 'no hiperbólico' in local_type:
                marker = 's'
                size = 75
            else:
                marker = 'X'
                size = 80

            self.ax.scatter(
                [x],
                [y],
                marker=marker,
                s=size,
                facecolors='white',
                edgecolors='black',
                linewidths=1.25,
                zorder=5,
            )
            self.ax.annotate(
                label,
                (x, y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                color='white',
                bbox=dict(boxstyle='round,pad=0.18', facecolor='black', alpha=0.65, edgecolor='white'),
                zorder=6,
            )


class MplSpectrumCanvas(_BaseCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig, parent)
        self.reset_plot()

    def reset_plot(self):
        self.ax.clear()
        self.ax.axhline(0.0, linewidth=0.9, color='0.35')
        self.ax.axvline(0.0, linewidth=0.9, color='0.35')
        self.ax.set_title('Plano complejo de autovalores')
        self.ax.set_xlabel(r'$\Re(\lambda)$')
        self.ax.set_ylabel(r'$\Im(\lambda)$')
        self.ax.grid(alpha=0.25)
        self.fig.subplots_adjust(left=0.11, right=0.98, bottom=0.12, top=0.92)
        self.draw_idle()

    def _style_for_type(self, local_type: str):
        return SPECTRUM_STYLE.get(local_type, SPECTRUM_STYLE['indeterminado'])

    def plot_spectrum(self, equilibria, selected_name='all', title='Plano complejo de autovalores'):
        self.ax.clear()
        self.ax.axhline(0.0, linewidth=0.9, color='0.35')
        self.ax.axvline(0.0, linewidth=0.9, color='0.35')
        self.ax.set_xlabel(r'$\Re(\lambda)$')
        self.ax.set_ylabel(r'$\Im(\lambda)$')
        self.ax.grid(alpha=0.25)

        xs, ys = [], []
        legend_handles = []
        legend_seen = set()

        def add_points(eq, annotate=False):
            vals = eq.get('eigvals', [])
            local_type = eq.get('local_type', 'indeterminado')
            style = self._style_for_type(local_type)
            x = np.real(vals)
            y = np.imag(vals)
            self.ax.scatter(
                x,
                y,
                s=60 if annotate else 52,
                zorder=3,
                color=style['color'],
                marker=style['marker'],
                edgecolors='black',
                linewidths=0.4,
            )
            xs.extend(float(v) for v in x)
            ys.extend(float(v) for v in y)
            if annotate:
                for idx, val in enumerate(vals, start=1):
                    xv = float(np.real(val))
                    yv = float(np.imag(val))
                    self.ax.annotate(
                        fr'$\lambda_{idx}$',
                        (xv, yv),
                        xytext=(6, 6),
                        textcoords='offset points',
                        fontsize=9,
                        bbox=dict(boxstyle='round,pad=0.18', facecolor='white', alpha=0.82, edgecolor='black'),
                    )
            if local_type not in legend_seen:
                legend_handles.append(
                    Line2D([0], [0], marker=style['marker'], color='w', label=local_type,
                           markerfacecolor=style['color'], markeredgecolor='black', markersize=7)
                )
                legend_seen.add(local_type)

        if selected_name == 'all':
            self.ax.set_title(title)
            displayed = []
            seen_signature = set()
            for eq in equilibria:
                vals = np.asarray(eq.get('eigvals', []), dtype=np.complex128)
                signature = tuple(np.round(np.sort_complex(vals), 10))
                if signature in seen_signature:
                    continue
                displayed.append(eq)
                seen_signature.add(signature)
            for eq in displayed:
                add_points(eq, annotate=False)
                centroid = np.mean(eq['eigvals']) if len(eq.get('eigvals', [])) else 0.0
                self.ax.annotate(eq['name'], (float(np.real(centroid)), float(np.imag(centroid))), xytext=(5, 6), textcoords='offset points', fontsize=8)
        else:
            eq = next((item for item in equilibria if item['name'] == selected_name), None)
            if eq is not None:
                add_points(eq, annotate=True)
                self.ax.set_title(f"Autovalores en el equilibrio {eq['name']}")

        if legend_handles:
            self.ax.legend(handles=legend_handles, loc='best', fontsize=8, title='Tipo local')

        if xs and ys:
            pad_x = max(1.0, 0.12 * max(abs(min(xs)), abs(max(xs)), 1.0))
            pad_y = max(1.0, 0.12 * max(abs(min(ys)), abs(max(ys)), 1.0))
            self.ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
            self.ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)
        else:
            self.ax.set_xlim(-1.0, 1.0)
            self.ax.set_ylim(-1.0, 1.0)

        self.fig.subplots_adjust(left=0.11, right=0.98, bottom=0.12, top=0.92)
        self.draw_idle()
