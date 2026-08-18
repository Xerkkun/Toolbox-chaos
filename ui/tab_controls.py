from __future__ import annotations

import os
import numpy as np

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QSplitter,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLabel,
    QFormLayout,
    QGroupBox,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QStackedWidget,
)
import pyqtgraph as pg

from core.lorenz import (
    SYSTEM_REGISTRY,
    METHOD_REGISTRY,
    simulate_system,
    bifurcation_generic,
    bifurcation_poincare_lorenz,
    compute_basin_generic,
    compute_basin_plane_z_lorenz_xiong,
    equilibria_for_system,
)
from core.diagnostics import (
    compare_integrator_methods,
    integer_qr_benettin_lyapunov,
    trajectory_spectrum,
)
from ui.canvases import (
    BASIN_RESIDUAL_LABEL,
    Mpl3DCanvas,
    MplBifCanvas,
    MplMethodComparisonCanvas,
    MplFFTCanvas,
    MplLyapunovCanvas,
    MplBasinCanvas,
    MplSpectrumCanvas,
)
from ui.widgets import make_double_spin, make_int_spin
from ui.parameter_panels import SystemParameterPanel
from core.coexistence import load_coexisting_attractors

COLOR_OPTIONS = {
    'Negro': '#111827',
    'Gris': '#4b5563',
    'Azul': '#2563eb',
    'Azul claro': '#0ea5e9',
    'Rojo': '#dc2626',
    'Rosa': '#db2777',
    'Verde': '#16a34a',
    'Lima': '#65a30d',
    'Morado': '#7c3aed',
    'Violeta': '#9333ea',
    'Naranja': '#ea580c',
    'Amarillo': '#ca8a04',
    'Cian': '#0891b2',
    'Turquesa': '#0d9488',
}

BASIN_DEFAULTS = {
    'lorenz': (-60.0, 60.0, -60.0, 60.0, 1.0, 0.02, 18.0),
    'rossler': (-8.0, 8.0, -8.0, 8.0, 0.0, 0.02, 80.0),
    'chua': (-4.0, 4.0, -4.0, 4.0, 0.0, 0.01, 80.0),
    'chen': (-30.0, 30.0, -30.0, 30.0, 1.0, 0.01, 25.0),
    'wang_chen_no_equilibrium': (-1.0, 10.0, -25.0, 10.0, 0.4716, 0.01, 200.0),
    'nazarimehr_line_equilibrium': (-2.0, 4.0, -2.0, 2.0, 0.0, 0.01, 200.0),
    'lu': (-30.0, 30.0, -30.0, 30.0, 1.0, 0.01, 25.0),
    'duffing_ueda': (-3.0, 3.0, -3.0, 3.0, 0.0, 0.01, 80.0),
    'rabinovich_fabrikant': (-3.0, 3.0, -3.0, 3.0, 0.5, 0.005, 40.0),
    'rikitake': (-5.0, 5.0, -5.0, 5.0, 0.1, 0.01, 60.0),
    'sprott_a': (-3.0, 3.0, -3.0, 3.0, 0.1, 0.01, 60.0),
    'thomas': (-8.0, 8.0, -8.0, 8.0, 0.0, 0.02, 80.0),
    'hindmarsh_rose': (-4.0, 4.0, -8.0, 8.0, 0.0, 0.01, 80.0),
}


def get_system_variables(system_key: str) -> list[str]:
    meta = SYSTEM_REGISTRY[system_key]
    labels = meta.get('initial_labels', ('x(0)', 'y(0)', 'z(0)'))
    variables = []
    for label in labels:
        var = label.split('(0)')[0].strip()
        if var == '-':
            var = f"v{len(variables)+1}"
        variables.append(var)
    dim = meta.get('dimension', len(variables))
    while len(variables) < dim:
        variables.append(f"v{len(variables)+1}")
    return variables[:dim]


def bifurcation_capability(metadata: dict) -> tuple[bool, str]:
    """Return the UI capability derived from declared parameter metadata."""

    reason = metadata.get(
        'bifurcation_unavailable_reason',
        'Bifurcación no disponible.',
    )
    if not metadata.get('bifurcation_supported', True):
        return False, reason

    labels = tuple(metadata.get('param_labels') or ())
    defaults = tuple(metadata.get('defaults') or ())
    parameter_index = metadata.get('bifurcation_param')
    valid_index = (
        isinstance(parameter_index, int)
        and not isinstance(parameter_index, bool)
        and 0 <= parameter_index < len(labels)
        and parameter_index < len(defaults)
    )
    if not valid_index:
        return (
            False,
            metadata.get(
                'bifurcation_unavailable_reason',
                'Bifurcación no disponible: el sistema no declara un parámetro '
                'de barrido válido.',
            ),
        )
    return True, ''


def suggested_path(default_name: str, extension: str) -> str:
    if not default_name.lower().endswith(extension):
        default_name = f"{default_name}{extension}"
    return os.path.join(os.path.expanduser("~"), default_name)


def ensure_suffix(file_path: str, selected_filter: str) -> str:
    base, ext = os.path.splitext(file_path)
    if ext:
        return file_path
    filter_map = {
        'PNG (*.png)': '.png',
        'PDF (*.pdf)': '.pdf',
        'SVG (*.svg)': '.svg',
        'JPEG (*.jpg *.jpeg)': '.jpg',
    }
    for filter_text, suffix in filter_map.items():
        if filter_text in selected_filter:
            return f"{file_path}{suffix}"
    return file_path


def format_complex(value, tol=1e-10):
    real = float(np.real(value))
    imag = float(np.imag(value))
    if abs(imag) < tol:
        return f'{real:.6g}'
    sign = '+' if imag >= 0 else '-'
    return f'{real:.6g}{sign}{abs(imag):.6g}j'


class BaseTabWidget(QWidget):
    """Base class for self-contained tabs using a QSplitter.

    Left side contains controls wrapped in a QScrollArea.
    Right side contains display / results canvas.
    """

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        # Main Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # Left Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(280)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(8)
        self.scroll.setWidget(self.scroll_content)
        self.splitter.addWidget(self.scroll)

        # Right Display Widget
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.right_widget)

        # Set default splitter sizing
        self.splitter.setSizes([380, 1000])

    def save_matplotlib_figure(self, fig, default_name):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Guardar gráfica',
            suggested_path(default_name, '.png'),
            'PNG (*.png);;PDF (*.pdf);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)',
        )
        if not file_path:
            return
        file_path = ensure_suffix(file_path, selected_filter)
        fig.savefig(file_path, dpi=300, bbox_inches='tight')
        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText(
                f'Gráfica guardada en:\n{file_path}'
            )

    def save_widget_snapshot(self, widget, default_name):
        from PySide6.QtGui import QPainter
        from PySide6.QtGui import QPdfWriter

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Guardar gráfica',
            suggested_path(default_name, '.png'),
            'PNG (*.png);;PDF (*.pdf);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)',
        )
        if not file_path:
            return
        file_path = ensure_suffix(file_path, selected_filter)
        if file_path.lower().endswith('.pdf'):
            writer = QPdfWriter(file_path)
            writer.setResolution(300)
            painter = QPainter(writer)
            scale_x = writer.width() / max(1, widget.width())
            scale_y = writer.height() / max(1, widget.height())
            painter.scale(scale_x, scale_y)
            widget.render(painter)
            painter.end()
            if hasattr(self.main_window, 'info_label'):
                self.main_window.info_label.setText(
                    f'Gráfica guardada en:\n{file_path}'
                )
            return
        pixmap = widget.grab()
        pixmap.save(file_path)
        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText(
                f'Gráfica guardada en:\n{file_path}'
            )


class Tab3DWidget(BaseTabWidget):
    """Tab for 3D Attractor visualization."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=True, show_ic=True, show_time=True, parent=self
        )
        self.param_panel.system_changed.connect(self._on_system_changed)
        self.scroll_layout.addWidget(self.param_panel)

        # Visual Options Group
        self.visual_box = QGroupBox('Opciones visuales')
        vis_layout = QFormLayout(self.visual_box)

        self.color_combo = QComboBox()

        for label, val in COLOR_OPTIONS.items():
            self.color_combo.addItem(label, userData=val)
        self.color_combo.setCurrentIndex(
            max(0, self.color_combo.findText('Negro'))
        )
        vis_layout.addRow(QLabel('Color atractor'), self.color_combo)

        self.chk_proj = QCheckBox('Superponer proyecciones')
        vis_layout.addRow(self.chk_proj)

        self.scroll_layout.addWidget(self.visual_box)

        # Action Buttons
        self.btn_run = QPushButton('Generar atractor 3D')
        self.btn_run.clicked.connect(self.run_simulation)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_atractor_3d'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display with Stacked Widget
        self.stacked_widget = QStackedWidget(self.right_widget)
        self.canvas = Mpl3DCanvas(self.stacked_widget)
        self.stacked_widget.addWidget(self.canvas)

        # Placeholder label for non-3D systems
        self.placeholder_label = QLabel(
            "El atractor 3D no está disponible para sistemas con dimensión distinta de 3.\n"
            "Use las pestañas de 'Retratos 2D' o 'Series temporales' para visualizarlo."
        )
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #4b5563; padding: 20px;"
        )
        self.stacked_widget.addWidget(self.placeholder_label)

        self.right_layout.addWidget(self.stacked_widget)

        # Trigger initial dimension check
        self._on_system_changed(self.param_panel.current_system_key())

    def _on_system_changed(self, system_key: str):
        meta = SYSTEM_REGISTRY.get(system_key, {})
        dim = meta.get('dimension', 3)
        if dim == 3:
            self.stacked_widget.setCurrentIndex(0)
            self.btn_run.setEnabled(True)
            self.btn_save.setEnabled(True)
        else:
            self.stacked_widget.setCurrentIndex(1)
            self.btn_run.setEnabled(False)
            self.btn_save.setEnabled(False)

    def run_simulation(self):
        sys_key = self.param_panel.current_system_key()
        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        dt = self.param_panel.dt.value()
        T = self.param_panel.T.value()
        method = self.param_panel.current_method_key()

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText(
                'Simulando trayectoria 3D...'
            )

        try:
            t, X = simulate_system(
                sys_key, initial, params, dt, T, method_key=method
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulación', str(exc))
            return

        # Store in shared state if main_window exists
        if self.main_window:
            self.main_window.last_t = t
            self.main_window.last_X = X[:, :3]
            self.main_window.last_system_key = sys_key
            self.main_window.last_params = params

        # Limit points to avoid lag
        max_points = 18000
        if len(X) > max_points:
            idx = np.linspace(0, len(X) - 1, max_points).astype(int)
            x3, y3, z3 = X[idx, 0], X[idx, 1], X[idx, 2]
        else:
            x3, y3, z3 = X[:, 0], X[:, 1], X[:, 2]

        color = self.color_combo.currentData() or '#111827'
        show_proj = self.chk_proj.isChecked()
        self.canvas.plot_lorenz(
            x3, y3, z3, show_projections=show_proj, color=color
        )

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText(
                f'Generado atractor 3D para {sys_key} ({len(t)} pasos).'
            )


class Tab2DWidget(BaseTabWidget):
    """Tab for 2D Phase Portrait projections."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=True, show_ic=True, show_time=True, parent=self
        )
        self.param_panel.system_changed.connect(self._on_system_changed)
        self.scroll_layout.addWidget(self.param_panel)

        # Visual options
        self.visual_box = QGroupBox('Estilo')
        vis_layout = QFormLayout(self.visual_box)
        self.color_combo = QComboBox()

        for label, val in COLOR_OPTIONS.items():
            self.color_combo.addItem(label, userData=val)
        self.color_combo.setCurrentIndex(
            max(0, self.color_combo.findText('Negro'))
        )
        vis_layout.addRow(QLabel('Color'), self.color_combo)
        self.scroll_layout.addWidget(self.visual_box)

        # Projections checklist box
        self.projections_box = QGroupBox('Proyecciones 2D')
        self.projections_layout = QVBoxLayout(self.projections_box)
        self.scroll_layout.addWidget(self.projections_box)

        # Buttons
        self.btn_run = QPushButton('Generar retratos 2D')
        self.btn_run.clicked.connect(self.run_simulation)
        self.scroll_layout.addWidget(self.btn_run)

        # Optional use-last button
        self.btn_last = QPushButton('Usar última trayectoria')
        self.btn_last.clicked.connect(self.use_last_trajectory)
        self.scroll_layout.addWidget(self.btn_last)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_widget_snapshot(
                self.plots_2d_widget, 'caos_retratos_2d'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.plots_2d_widget = QWidget()
        self.plots_grid_layout = QGridLayout(self.plots_2d_widget)
        self.plots_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.plots_grid_layout.setSpacing(10)

        self.right_layout.addWidget(self.plots_2d_widget)

        # Initialize checklist and grid
        self._on_system_changed(self.param_panel.current_system_key())

    def _on_system_changed(self, system_key: str):
        meta = SYSTEM_REGISTRY.get(system_key, {})
        dim = meta.get('dimension', 3)
        initial_labels = meta.get('initial_labels', ('x(0)', 'y(0)', 'z(0)'))
        self.var_names = [lbl.replace('(0)', '').strip() for lbl in initial_labels]
        if len(self.var_names) < dim:
            self.var_names += [f'x{i+1}' for i in range(len(self.var_names), dim)]
        elif len(self.var_names) > dim:
            self.var_names = self.var_names[:dim]

        # Generate combinations
        import itertools
        self.combo_pairs = list(itertools.combinations(range(dim), 2))

        # Clear old checkboxes
        while self.projections_layout.count():
            item = self.projections_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.checkboxes = []
        for i, j in self.combo_pairs:
            lbl_text = f"Plano {self.var_names[i]}-{self.var_names[j]}"
            chk = QCheckBox(lbl_text)
            chk.setChecked(True)  # Check all by default
            chk.toggled.connect(self._update_plots_grid)
            self.projections_layout.addWidget(chk)
            self.checkboxes.append(chk)

        self.current_trajectory = None
        self._update_plots_grid()

    def _update_plots_grid(self):
        # Clear old plots from grid
        while self.plots_grid_layout.count():
            item = self.plots_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.plot_widgets = []
        self.plot_curves = []
        self.plot_pairs = []

        # Find checked projections
        checked_pairs = []
        for chk, pair in zip(self.checkboxes, self.combo_pairs):
            if chk.isChecked():
                checked_pairs.append(pair)

        if not checked_pairs:
            lbl = QLabel("Seleccione al menos una proyección 2D de la barra lateral.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 13px; color: #777777;")
            self.plots_grid_layout.addWidget(lbl, 0, 0)
            return

        n_plots = len(checked_pairs)
        cols = int(np.ceil(np.sqrt(n_plots)))
        rows = int(np.ceil(n_plots / cols))

        for idx, (i, j) in enumerate(checked_pairs):
            row = idx // cols
            col = idx % cols

            plot = pg.PlotWidget(title=f"Plano {self.var_names[i]}-{self.var_names[j]}")
            plot.setBackground('w')
            plot.showGrid(x=True, y=True, alpha=0.22)
            plot.setAspectLocked(True, ratio=1.0)
            
            for axis_name in ('left', 'bottom'):
                axis = plot.getAxis(axis_name)
                axis.setPen(pg.mkPen('#111827'))
                axis.setTextPen(pg.mkPen('#111827'))

            plot.setLabel('bottom', self.var_names[i])
            plot.setLabel('left', self.var_names[j])

            curve = plot.plot([], [], pen=pg.mkPen(width=1.5))

            self.plots_grid_layout.addWidget(plot, row, col)
            self.plot_widgets.append(plot)
            self.plot_curves.append(curve)
            self.plot_pairs.append((i, j))

        self._plot_current_data()

    def _plot_current_data(self):
        if not hasattr(self, 'current_trajectory') or self.current_trajectory is None or len(self.current_trajectory) == 0:
            return
        color = self.color_combo.currentData() or '#111827'
        pen = pg.mkPen(color, width=1.5)
        for curve, (i, j) in zip(self.plot_curves, self.plot_pairs):
            if i < self.current_trajectory.shape[1] and j < self.current_trajectory.shape[1]:
                curve.setData(self.current_trajectory[:, i], self.current_trajectory[:, j])
                curve.setPen(pen)

    def run_simulation(self):
        sys_key = self.param_panel.current_system_key()
        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        dt = self.param_panel.dt.value()
        T = self.param_panel.T.value()
        method = self.param_panel.current_method_key()

        try:
            t, X = simulate_system(
                sys_key, initial, params, dt, T, method_key=method
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulación', str(exc))
            return

        if self.main_window:
            self.main_window.last_t = t
            self.main_window.last_X = X
            self.main_window.last_system_key = sys_key
            self.main_window.last_params = params

        self.current_trajectory = X
        self._plot_current_data()

    def use_last_trajectory(self):
        if (
            not self.main_window
            or self.main_window.last_X is None
            or self.main_window.last_X.shape[0] == 0
        ):
            QMessageBox.information(
                self,
                'Sin trayectoria',
                'No hay trayectoria compartida previa. Simula primero en Atractor 3D o ejecuta una simulación local.',
            )
            return

        sys_key = self.param_panel.current_system_key()
        last_sys = getattr(self.main_window, 'last_system_key', None)
        if last_sys != sys_key:
            QMessageBox.warning(
                self,
                'Incompatibilidad',
                f'La trayectoria guardada pertenece a {last_sys}, pero el sistema seleccionado es {sys_key}. Por favor ejecute una simulación local.',
            )
            return

        self.current_trajectory = self.main_window.last_X
        self._plot_current_data()


class TabTimeSeriesWidget(BaseTabWidget):
    """Tab for Time Series Plots (x(t), y(t), z(t))."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=True, show_ic=True, show_time=True, parent=self
        )
        self.param_panel.system_changed.connect(self._on_system_changed)
        self.scroll_layout.addWidget(self.param_panel)

        # Style box
        self.style_box = QGroupBox('Estilo')
        self.st_layout = QFormLayout(self.style_box)
        self.scroll_layout.addWidget(self.style_box)

        # Buttons
        self.btn_run = QPushButton('Generar series temporales')
        self.btn_run.clicked.connect(self.run_simulation)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_last = QPushButton('Usar última trayectoria')
        self.btn_last.clicked.connect(self.use_last_trajectory)
        self.scroll_layout.addWidget(self.btn_last)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_widget_snapshot(
                self.plots_time_widget, 'caos_series_temporales'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.right_scroll = QScrollArea(self.right_widget)
        self.right_scroll.setWidgetResizable(True)
        self.plots_time_widget = QWidget()
        self.time_layout = QVBoxLayout(self.plots_time_widget)
        self.right_scroll.setWidget(self.plots_time_widget)
        self.right_layout.addWidget(self.right_scroll)

        # Initialize checklist and plots
        self._on_system_changed(self.param_panel.current_system_key())

    def _on_system_changed(self, system_key: str):
        meta = SYSTEM_REGISTRY.get(system_key, {})
        dim = meta.get('dimension', 3)
        initial_labels = meta.get('initial_labels', ('x(0)', 'y(0)', 'z(0)'))
        self.var_names = [lbl.replace('(0)', '').strip() for lbl in initial_labels]
        if len(self.var_names) < dim:
            self.var_names += [f'x{i+1}' for i in range(len(self.var_names), dim)]
        elif len(self.var_names) > dim:
            self.var_names = self.var_names[:dim]

        # 1. Update style control comboboxes
        while self.st_layout.count():
            item = self.st_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.color_combos = []
        for i in range(dim):
            lbl_text = f"Color {self.var_names[i]}(t)"
            combo = QComboBox()
            for label, val in COLOR_OPTIONS.items():
                combo.addItem(label, userData=val)
            default_colors = ['Azul', 'Rojo', 'Verde', 'Naranja', 'Morado', 'Negro', 'Gris']
            color_idx = i % len(default_colors)
            combo.setCurrentIndex(max(0, combo.findText(default_colors[color_idx])))
            combo.currentIndexChanged.connect(self._plot_current_data)
            self.st_layout.addRow(QLabel(lbl_text), combo)
            self.color_combos.append(combo)

        # 2. Update plot widgets
        while self.time_layout.count():
            item = self.time_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.plot_widgets = []
        self.plot_curves = []
        for i in range(dim):
            var_name = self.var_names[i]
            plot = pg.PlotWidget(title=f"{var_name}(t)")
            plot.setBackground('w')
            plot.showGrid(x=True, y=True, alpha=0.22)
            plot.setMinimumHeight(200)

            for axis_name in ('left', 'bottom'):
                axis = plot.getAxis(axis_name)
                axis.setPen(pg.mkPen('#111827'))
                axis.setTextPen(pg.mkPen('#111827'))

            plot.setLabel('bottom', 't')
            plot.setLabel('left', var_name)

            curve = plot.plot([], [], pen=pg.mkPen(width=1.5))
            self.time_layout.addWidget(plot)
            self.plot_widgets.append(plot)
            self.plot_curves.append(curve)

        self.current_t = None
        self.current_X = None

    def _plot_current_data(self):
        if not hasattr(self, 'current_t') or self.current_t is None or len(self.current_t) == 0:
            return
        if not hasattr(self, 'current_X') or self.current_X is None or len(self.current_X) == 0:
            return

        for idx, curve in enumerate(self.plot_curves):
            if idx < self.current_X.shape[1]:
                color = self.color_combos[idx].currentData() or '#111827'
                curve.setData(self.current_t, self.current_X[:, idx])
                curve.setPen(pg.mkPen(color, width=1.5))

    def run_simulation(self):
        sys_key = self.param_panel.current_system_key()
        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        dt = self.param_panel.dt.value()
        T = self.param_panel.T.value()
        method = self.param_panel.current_method_key()

        try:
            t, X = simulate_system(
                sys_key, initial, params, dt, T, method_key=method
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulación', str(exc))
            return

        if self.main_window:
            self.main_window.last_t = t
            self.main_window.last_X = X
            self.main_window.last_system_key = sys_key
            self.main_window.last_params = params

        self.current_t = t
        self.current_X = X
        self._plot_current_data()

    def use_last_trajectory(self):
        if (
            not self.main_window
            or self.main_window.last_X is None
            or self.main_window.last_t is None
            or self.main_window.last_X.shape[0] == 0
        ):
            QMessageBox.information(
                self,
                'Sin trayectoria',
                'No hay trayectoria compartida previa.',
            )
            return

        sys_key = self.param_panel.current_system_key()
        last_sys = getattr(self.main_window, 'last_system_key', None)
        if last_sys != sys_key:
            QMessageBox.warning(
                self,
                'Incompatibilidad',
                f'La trayectoria guardada pertenece a {last_sys}, pero el sistema seleccionado es {sys_key}. Por favor ejecute una simulación local.',
            )
            return

        self.current_t = self.main_window.last_t
        self.current_X = self.main_window.last_X
        self._plot_current_data()


class TabFFTWidget(BaseTabWidget):
    """Tab for amplitude-spectrum and Welch-PSD analysis."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=True, show_ic=True, show_time=True, parent=self
        )
        self.scroll_layout.addWidget(self.param_panel)

        # FFT Options Group
        self.fft_box = QGroupBox('Parámetros de FFT')
        fft_layout = QFormLayout(self.fft_box)

        self.spectral_method_combo = QComboBox()
        self.spectral_method_combo.addItem('PSD de Welch (recomendado)', 'psd_welch')
        self.spectral_method_combo.addItem('Espectro de amplitud', 'fft')
        fft_layout.addRow(QLabel('Método'), self.spectral_method_combo)

        self.transient_spin = make_double_spin(5.0, 0.0, 10000.0, 3)
        fft_layout.addRow(QLabel('Descartar transitorio (s)'), self.transient_spin)

        self.min_freq_spin = make_double_spin(0.0, -100000.0, 100000.0, 3)
        self.max_freq_spin = make_double_spin(0.0, -100000.0, 100000.0, 3)
        fft_layout.addRow(QLabel('Frecuencia mínima (0=auto)'), self.min_freq_spin)
        fft_layout.addRow(QLabel('Frecuencia máxima (0=auto)'), self.max_freq_spin)

        self.scroll_layout.addWidget(self.fft_box)

        # Buttons
        self.btn_run = QPushButton('Calcular FFT/PSD')
        self.btn_run.clicked.connect(self.run_simulation)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_last = QPushButton('Usar última trayectoria')
        self.btn_last.clicked.connect(self.use_last_trajectory)
        self.scroll_layout.addWidget(self.btn_last)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_espectro'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplFFTCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

    def run_simulation(self):
        sys_key = self.param_panel.current_system_key()
        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        dt = self.param_panel.dt.value()
        T = self.param_panel.T.value()
        method = self.param_panel.current_method_key()

        try:
            t, X = simulate_system(
                sys_key, initial, params, dt, T, method_key=method
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulación', str(exc))
            return

        if self.main_window:
            self.main_window.last_t = t
            self.main_window.last_X = X[:, :3]
            self.main_window.last_system_key = sys_key
            self.main_window.last_params = params

        self._calculate_fft(t, X)

    def use_last_trajectory(self):
        if (
            not self.main_window
            or self.main_window.last_X is None
            or self.main_window.last_t is None
            or self.main_window.last_X.shape[0] == 0
        ):
            QMessageBox.information(
                self,
                'Sin trayectoria',
                'No hay trayectoria compartida previa.',
            )
            return
        self._calculate_fft(self.main_window.last_t, self.main_window.last_X)

    def _calculate_fft(self, t, X):
        sys_key = (
            self.main_window.last_system_key
            if self.main_window
            else self.param_panel.current_system_key()
        )
        transient = self.transient_spin.value()
        idx_trans = t >= transient
        if not np.any(idx_trans):
            QMessageBox.warning(
                self,
                'Transitorio muy largo',
                'El transitorio a descartar es mayor o igual al tiempo total.',
            )
            return

        t_cropped = t[idx_trans]
        X_cropped = X[idx_trans]

        min_freq = self.min_freq_spin.value()
        max_freq = self.max_freq_spin.value()
        use_bounds = not (abs(min_freq) < 1e-12 and abs(max_freq) < 1e-12)
        if use_bounds and max_freq <= min_freq:
            QMessageBox.critical(
                self,
                'Error de FFT',
                'La frecuencia máxima debe ser mayor que la mínima.',
            )
            return

        selected_method = self.spectral_method_combo.currentData()
        try:
            freqs, spectra, actual_method = trajectory_spectrum(
                t_cropped,
                X_cropped,
                method=selected_method,
                min_frequency=min_freq if use_bounds else None,
                max_frequency=max_freq if use_bounds else None,
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de análisis espectral', str(exc))
            return

        colors = ['#2563eb', '#dc2626', '#16a34a']
        if actual_method == 'psd_welch':
            method_label = 'PSD de Welch'
            value_label = 'PSD [unidad²/Hz]'
        else:
            method_label = 'Espectro de amplitud'
            value_label = 'Amplitud [unidad]'
        title = f"{method_label} - {SYSTEM_REGISTRY.get(sys_key, {'label': sys_key})['label']}"
        self.canvas.plot_fft(
            freqs,
            spectra,
            title,
            colors=colors,
            auto_crop=not use_bounds,
            value_label=value_label,
            line_plot=actual_method == 'psd_welch',
        )


class TabBifurcationWidget(BaseTabWidget):
    """Tab for Bifurcation analysis."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.coex_cases = load_coexisting_attractors()
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=False, show_ic=True, show_time=False, parent=self
        )
        self.param_panel.system_changed.connect(
            self._update_bifurcation_defaults
        )
        self.scroll_layout.addWidget(self.param_panel)

        # Dimension Display
        self.lbl_dimension = QLabel('Dimensión detectada: 3')
        self.lbl_dimension.setStyleSheet('font-weight: bold; color: #2563eb; padding: 2px;')
        self.scroll_layout.addWidget(self.lbl_dimension)

        # Bifurcation Parameters Group
        self.bif_box = QGroupBox('Barrido de bifurcación')
        bif_layout = QFormLayout(self.bif_box)

        self.sweep_param_combo = QComboBox()
        bif_layout.addRow(QLabel('Parámetro de bifurcación'), self.sweep_param_combo)

        self.obs_var_combo = QComboBox()
        bif_layout.addRow(QLabel('Variable observada'), self.obs_var_combo)

        self.bif_min = make_double_spin(0.0, -500.0, 500.0, 3)
        self.bif_max = make_double_spin(80.0, -500.0, 500.0, 3)
        self.bif_n = make_int_spin(350, 10, 5000)
        self.bif_dt = make_double_spin(0.01, 1e-5, 1.0, 6)
        self.bif_trans = make_double_spin(80.0, 0.0, 10000.0, 3)
        self.bif_keep = make_double_spin(120.0, 0.1, 10000.0, 3)
        self.max_points = make_int_spin(250, 1, 2000)
        self.use_cont = QCheckBox('Usar continuación')

        bif_layout.addRow(QLabel('Mínimo'), self.bif_min)
        bif_layout.addRow(QLabel('Máximo'), self.bif_max)
        bif_layout.addRow(QLabel('N (Parámetros)'), self.bif_n)
        bif_layout.addRow(QLabel('dt integrador'), self.bif_dt)
        bif_layout.addRow(QLabel('Transitorio descartado'), self.bif_trans)
        bif_layout.addRow(QLabel('Tiempo útil'), self.bif_keep)
        bif_layout.addRow(QLabel('Máx cruces por param'), self.max_points)
        bif_layout.addRow(self.use_cont)

        self.scroll_layout.addWidget(self.bif_box)

        # Coexisting Attractors Group
        self.coex_box = QGroupBox('Atractores coexistentes')
        coex_layout = QFormLayout(self.coex_box)

        self.chk_compare = QCheckBox('Comparar atractores coexistentes')
        self.chk_compare.toggled.connect(self._toggle_coexistence_ui)
        coex_layout.addRow(self.chk_compare)

        self.combo_attr_a = QComboBox()
        self.combo_attr_b = QComboBox()
        self.combo_attr_a.currentIndexChanged.connect(self._on_attr_a_changed)
        self.combo_attr_b.currentIndexChanged.connect(self._on_attr_b_changed)
        coex_layout.addRow(QLabel('Atractor A'), self.combo_attr_a)
        coex_layout.addRow(QLabel('Atractor B'), self.combo_attr_b)

        # Initial Conditions for A and B
        self.ic_a_x = make_double_spin(0.1, -500.0, 500.0, 4)
        self.ic_a_y = make_double_spin(0.1, -500.0, 500.0, 4)
        self.ic_a_z = make_double_spin(0.1, -500.0, 500.0, 4)
        self.ic_b_x = make_double_spin(0.1, -500.0, 500.0, 4)
        self.ic_b_y = make_double_spin(0.1, -500.0, 500.0, 4)
        self.ic_b_z = make_double_spin(0.1, -500.0, 500.0, 4)

        coex_layout.addRow(QLabel('CI A [x, y, z]'), self.ic_a_x)
        coex_layout.addRow(self.ic_a_y)
        coex_layout.addRow(self.ic_a_z)
        coex_layout.addRow(QLabel('CI B [x, y, z]'), self.ic_b_x)
        coex_layout.addRow(self.ic_b_y)
        coex_layout.addRow(self.ic_b_z)

        # Color combos for A and B
        self.color_attr_a = QComboBox()
        self.color_attr_b = QComboBox()
        for label, val in COLOR_OPTIONS.items():
            self.color_attr_a.addItem(label, userData=val)
            self.color_attr_b.addItem(label, userData=val)
        self.color_attr_a.setCurrentIndex(self.color_attr_a.findText('Rojo'))
        self.color_attr_b.setCurrentIndex(self.color_attr_b.findText('Azul'))

        coex_layout.addRow(QLabel('Color A'), self.color_attr_a)
        coex_layout.addRow(QLabel('Color B'), self.color_attr_b)

        self.scroll_layout.addWidget(self.coex_box)

        # Warning/Error display area
        self.lbl_warning = QLabel()
        self.lbl_warning.setWordWrap(True)
        self.lbl_warning.setStyleSheet('color: #dc2626; font-size: 11px; font-weight: bold; margin: 4px;')
        self.scroll_layout.addWidget(self.lbl_warning)

        # Action Buttons
        self.btn_run = QPushButton('Calcular bifurcación')
        self.btn_run.clicked.connect(self.run_bifurcation)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_bifurcacion'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplBifCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

        self._update_bifurcation_defaults(self.param_panel.current_system_key())

    def _update_bifurcation_defaults(self, system_key: str):
        meta = SYSTEM_REGISTRY[system_key]
        dim = meta.get('dimension', 3)
        self.lbl_dimension.setText(f'Dimensión detectada: {dim}')
        supported, unavailable_reason = bifurcation_capability(meta)
        self.btn_run.setEnabled(supported)
        if supported:
            self.lbl_warning.setText('')
        else:
            self.lbl_warning.setStyleSheet(
                'color: #dc2626; font-size: 11px; font-weight: bold; margin: 4px;'
            )
            self.lbl_warning.setText(unavailable_reason)

        # Sweep parameter combo
        self.sweep_param_combo.blockSignals(True)
        self.sweep_param_combo.clear()
        labels = meta.get('param_labels', ())
        for label in labels:
            self.sweep_param_combo.addItem(label)

        bif_idx = meta.get('bifurcation_param')
        if bif_idx is not None and bif_idx < self.sweep_param_combo.count():
            self.sweep_param_combo.setCurrentIndex(bif_idx)
        self.sweep_param_combo.blockSignals(False)

        # Observed variable combo
        self.obs_var_combo.blockSignals(True)
        self.obs_var_combo.clear()
        variables = get_system_variables(system_key)
        for var in variables:
            self.obs_var_combo.addItem(var)
        # Default observed variable is z (idx 2) or last variable
        self.obs_var_combo.setCurrentIndex(min(2, len(variables) - 1))
        self.obs_var_combo.blockSignals(False)

        low, high = meta.get('bifurcation_range', (0.0, 1.0))
        self.bif_min.setValue(float(low))
        self.bif_max.setValue(float(high))

        is_map = meta.get('kind') == 'map'
        self.bif_dt.setValue(1.0 if is_map else 0.01)
        self.bif_trans.setValue(600.0 if is_map else 80.0)
        self.bif_keep.setValue(500.0 if is_map else 120.0)
        self.bif_n.setValue(350)
        self.max_points.setValue(250)

        # Update coexisting attractors combo
        self.combo_attr_a.blockSignals(True)
        self.combo_attr_b.blockSignals(True)
        self.combo_attr_a.clear()
        self.combo_attr_b.clear()

        # Find coexistence case in metadata or yaml
        coex_attractors = meta.get('coexisting_attractors', [])
        if not coex_attractors:
            # Check if exists in yaml cases
            yaml_case = next((c for c in self.coex_cases if c.get('system_key') == system_key), None)
            if yaml_case:
                coex_attractors = yaml_case.get('attractors', [])

        if coex_attractors:
            self.coex_box.setEnabled(True)
            self.coex_box.setTitle('Atractores coexistentes')
            self.chk_compare.setEnabled(True)
            for attr in coex_attractors:
                lbl = attr.get('label', 'Atractor')
                ic = attr.get('initial_condition', [0.1, 0.1, 0.1])
                self.combo_attr_a.addItem(f"{lbl} {ic}", userData=attr)
                self.combo_attr_b.addItem(f"{lbl} {ic}", userData=attr)

            if self.combo_attr_a.count() >= 2:
                self.combo_attr_a.setCurrentIndex(0)
                self.combo_attr_b.setCurrentIndex(1)
        else:
            self.coex_box.setEnabled(False)
            self.coex_box.setTitle('Atractores coexistentes [No registrado]')
            self.chk_compare.setChecked(False)
            self.chk_compare.setEnabled(False)
            if supported:
                self.lbl_warning.setStyleSheet(
                    'color: #6b7280; font-size: 11px; margin: 4px;'
                )
                self.lbl_warning.setText(
                    'Info: este sistema no tiene atractores coexistentes registrados.'
                )

        self.combo_attr_a.blockSignals(False)
        self.combo_attr_b.blockSignals(False)
        self._toggle_coexistence_ui()

    def _toggle_coexistence_ui(self):
        enabled = self.chk_compare.isChecked()
        self.combo_attr_a.setEnabled(enabled)
        self.combo_attr_b.setEnabled(enabled)
        self.color_attr_a.setEnabled(enabled)
        self.color_attr_b.setEnabled(enabled)
        self.ic_a_x.setEnabled(enabled)
        self.ic_a_y.setEnabled(enabled)
        self.ic_a_z.setEnabled(enabled)
        self.ic_b_x.setEnabled(enabled)
        self.ic_b_y.setEnabled(enabled)
        self.ic_b_z.setEnabled(enabled)
        
        if enabled:
            self._on_attr_a_changed()
            self._on_attr_b_changed()

    def _on_attr_a_changed(self):
        idx = self.combo_attr_a.currentIndex()
        if idx >= 0:
            attr = self.combo_attr_a.currentData()
            ic = attr.get('initial_condition', [0.1, 0.1, 0.1])
            self.ic_a_x.setValue(ic[0])
            self.ic_a_y.setValue(ic[1])
            self.ic_a_z.setValue(ic[2])

    def _on_attr_b_changed(self):
        idx = self.combo_attr_b.currentIndex()
        if idx >= 0:
            attr = self.combo_attr_b.currentData()
            ic = attr.get('initial_condition', [0.1, 0.1, 0.1])
            self.ic_b_x.setValue(ic[0])
            self.ic_b_y.setValue(ic[1])
            self.ic_b_z.setValue(ic[2])

    def run_bifurcation(self):
        sys_key = self.param_panel.current_system_key()
        meta = SYSTEM_REGISTRY[sys_key]
        params = self.param_panel.current_params()
        method = self.param_panel.current_method_key()
        dim = meta.get('dimension', 3)

        supported, message = bifurcation_capability(meta)
        if not supported:
            self.lbl_warning.setText(message)
            QMessageBox.information(self, 'No disponible', message)
            return

        bif_idx = self.sweep_param_combo.currentIndex()
        obs_idx = self.obs_var_combo.currentIndex()

        p_min = self.bif_min.value()
        p_max = self.bif_max.value()
        n_p = self.bif_n.value()
        dt = self.bif_dt.value()
        transient = self.bif_trans.value()
        keep = self.bif_keep.value()
        max_pts = self.max_points.value()
        cont = self.use_cont.isChecked()

        # Reset warning style to error style at the start of each run
        self.lbl_warning.setStyleSheet(
            'color: #dc2626; font-size: 11px; font-weight: bold; margin: 4px;'
        )
        self.lbl_warning.setText('')

        # Validation Checks
        if self.sweep_param_combo.count() == 0 or bif_idx < 0:
            err = (
                f"El sistema {meta['label']} no tiene parámetros disponibles "
                "para el barrido de bifurcación. "
                "Selecciona un sistema con parámetros definidos."
            )
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Parámetro faltante', err)
            return

        if obs_idx < 0:
            err = f"Selecciona una variable observada válida para el sistema."
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Variable observada inválida', err)
            return

        if p_min >= p_max:
            err = f"El rango de bifurcación es inválido: el valor mínimo ({p_min}) debe ser menor que el máximo ({p_max})."
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Rango inválido', err)
            return

        if dt <= 0:
            err = f"El paso temporal dt ({dt}) debe ser positivo."
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Paso dt inválido', err)
            return

        if n_p <= 0:
            err = f"El número de muestras N ({n_p}) debe ser un entero positivo."
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Número de muestras inválido', err)
            return

        if transient < 0 or keep <= 0:
            err = f"El tiempo transitorio ({transient}) y útil ({keep}) deben ser positivos."
            self.lbl_warning.setText(err)
            QMessageBox.critical(self, 'Tiempos de simulación inválidos', err)
            return

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Calculando bifurcación...')

        labels = meta.get('param_labels', ())
        x_label = labels[bif_idx] if bif_idx < len(labels) else 'parámetro'
        title = f"Diagrama de bifurcación - {meta['label']}"
        y_label = f"Eventos ({self.obs_var_combo.currentText()})"

        try:
            if self.chk_compare.isChecked():
                # Compare coexisting attractors
                initial_a = [self.ic_a_x.value(), self.ic_a_y.value(), self.ic_a_z.value()]
                initial_b = [self.ic_b_x.value(), self.ic_b_y.value(), self.ic_b_z.value()]
                
                # Fetch specific parameter set if loaded from cases.
                # Guard: only replace params if ALL labels are present in
                # the YAML parameter_set; otherwise fall back to panel params
                # to avoid truncated param lists causing IndexError.
                case = next(
                    (c for c in self.coex_cases if c.get('system_key') == sys_key), None
                )
                if case and 'parameter_set' in case:
                    p_set = case['parameter_set']
                    rebuilt = [p_set[name] for name in labels if name in p_set]
                    if len(rebuilt) == len(params):
                        params = rebuilt
                    # else: partial match — keep original panel params

                # Attractor A Sweep
                if sys_key == 'lorenz' and bif_idx == 1 and obs_idx == 2:
                    rho_vals_a, z_vals_a = bifurcation_poincare_lorenz(
                        initial_a[0], initial_a[1], initial_a[2],
                        params[0], params[2],
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method
                    )
                else:
                    rho_vals_a, z_vals_a = bifurcation_generic(
                        sys_key, initial_a, params, bif_idx,
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method, observed_var_idx=obs_idx
                    )
                
                # Attractor B Sweep
                if sys_key == 'lorenz' and bif_idx == 1 and obs_idx == 2:
                    rho_vals_b, z_vals_b = bifurcation_poincare_lorenz(
                        initial_b[0], initial_b[1], initial_b[2],
                        params[0], params[2],
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method
                    )
                else:
                    rho_vals_b, z_vals_b = bifurcation_generic(
                        sys_key, initial_b, params, bif_idx,
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method, observed_var_idx=obs_idx
                    )
                
                datasets = [
                    {
                        'param_values': rho_vals_a,
                        'event_values': z_vals_a,
                        'label': self.combo_attr_a.currentText().split('[')[0].strip(),
                        'color': self.color_attr_a.currentData()
                    },
                    {
                        'param_values': rho_vals_b,
                        'event_values': z_vals_b,
                        'label': self.combo_attr_b.currentText().split('[')[0].strip(),
                        'color': self.color_attr_b.currentData()
                    }
                ]
                self.canvas.plot_bifurcation_multi(datasets, title, x_label, y_label)
            else:
                # Single sweep
                initial = self.param_panel.current_initial()
                
                if sys_key == 'lorenz' and bif_idx == 1 and obs_idx == 2:
                    rho_vals, z_vals = bifurcation_poincare_lorenz(
                        initial[0], initial[1], initial[2],
                        params[0], params[2],
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method
                    )
                else:
                    rho_vals, z_vals = bifurcation_generic(
                        sys_key, initial, params, bif_idx,
                        p_min, p_max, n_p, dt, transient, keep, max_pts, cont,
                        method_key=method, observed_var_idx=obs_idx
                    )
                self.canvas.plot_bifurcation(
                    rho_vals, z_vals, title, x_label, y_label, color='#111827'
                )
        except Exception as exc:
            self.lbl_warning.setText(f"Error: {exc}")
            QMessageBox.critical(self, 'Error de cálculo', str(exc))
            return

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Bifurcación calculada.')


class TabBasinWidget(BaseTabWidget):
    """Tab for Basins of Attraction."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=True, show_ic=False, show_time=False, parent=self
        )
        self.param_panel.system_changed.connect(self._update_basin_defaults)
        self.scroll_layout.addWidget(self.param_panel)

        # Basin Grid Params Group
        self.basin_box = QGroupBox('Región y resolución')
        basin_layout = QFormLayout(self.basin_box)

        self.xmin = make_double_spin(-25.0, -1000.0, 1000.0, 3)
        self.xmax = make_double_spin(25.0, -1000.0, 1000.0, 3)
        self.ymin = make_double_spin(-25.0, -1000.0, 1000.0, 3)
        self.ymax = make_double_spin(25.0, -1000.0, 1000.0, 3)
        self.z0 = make_double_spin(1.0, -1000.0, 1000.0, 6)
        self.nx = make_int_spin(60, 10, 500)
        self.ny = make_int_spin(60, 10, 500)
        self.dt = make_double_spin(0.02, 1e-5, 1.0, 6)
        self.T_total = make_double_spin(12.0, 0.1, 10000.0, 3)
        self.chk_eq = QCheckBox('Superponer equilibrios')
        self.chk_eq.setChecked(True)

        basin_layout.addRow(QLabel('x0 mín'), self.xmin)
        basin_layout.addRow(QLabel('x0 máx'), self.xmax)
        basin_layout.addRow(QLabel('y0 mín'), self.ymin)
        basin_layout.addRow(QLabel('y0 máx'), self.ymax)
        basin_layout.addRow(QLabel('z0 fijo'), self.z0)
        basin_layout.addRow(QLabel('Nx (ancho)'), self.nx)
        basin_layout.addRow(QLabel('Ny (alto)'), self.ny)
        basin_layout.addRow(QLabel('dt integrador'), self.dt)
        basin_layout.addRow(QLabel('Tiempo total'), self.T_total)
        basin_layout.addRow(self.chk_eq)

        self.scroll_layout.addWidget(self.basin_box)

        # Action Buttons
        self.btn_run = QPushButton('Calcular cuenca')
        self.btn_run.clicked.connect(self.run_basin)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_cuenca'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplBasinCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

        # Equilibria label
        eq_box = QGroupBox('Equilibrios')
        eq_layout = QVBoxLayout(eq_box)
        self.eq_label = QLabel('Equilibrios no calculados.')
        self.eq_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.eq_label.setWordWrap(True)
        self.eq_label.setStyleSheet("font-family: monospace; padding: 4px;")
        eq_layout.addWidget(self.eq_label)
        self.right_layout.addWidget(eq_box)

        self.last_basin = None
        self.last_basin_extent = None
        self.last_basin_rho = None
        self.last_basin_z0 = None
        self.last_equilibria = []

        self._update_basin_defaults(self.param_panel.current_system_key())

    def _update_basin_defaults(self, system_key: str):
        meta = SYSTEM_REGISTRY[system_key]
        supported = meta.get('kind') == 'flow' and int(meta.get('dimension', 0)) == 3
        self.btn_run.setEnabled(supported)
        defaults = BASIN_DEFAULTS.get(
            system_key, (-10.0, 10.0, -10.0, 10.0, 0.0, 0.02, 40.0)
        )
        x_min, x_max, y_min, y_max, z0, dt, t_total = defaults
        self.xmin.setValue(float(x_min))
        self.xmax.setValue(float(x_max))
        self.ymin.setValue(float(y_min))
        self.ymax.setValue(float(y_max))
        self.z0.setValue(float(z0))
        self.dt.setValue(float(dt))
        self.T_total.setValue(float(t_total))

    def run_basin(self):
        sys_key = self.param_panel.current_system_key()
        meta = SYSTEM_REGISTRY[sys_key]
        params = self.param_panel.current_params()
        method = self.param_panel.current_method_key()

        if meta.get('kind') != 'flow' or int(meta.get('dimension', 0)) != 3:
            QMessageBox.information(
                self,
                'No disponible',
                'El cálculo de cuencas de atracción solo está soportado para flujos 3D.',
            )
            return

        x_min = self.xmin.value()
        x_max = self.xmax.value()
        y_min = self.ymin.value()
        y_max = self.ymax.value()
        z0_fixed = self.z0.value()
        nx = self.nx.value()
        ny = self.ny.value()
        dt = self.dt.value()
        T_total = self.T_total.value()

        if x_max <= x_min or y_max <= y_min:
            QMessageBox.critical(
                self, 'Error', 'Los límites del plano deben ser crecientes.'
            )
            return

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Calculando cuenca...')

        try:
            if sys_key == 'lorenz':
                basin = compute_basin_plane_z_lorenz_xiong(
                    params[0],
                    params[1],
                    params[2],
                    z0_fixed,
                    x_min,
                    x_max,
                    y_min,
                    y_max,
                    nx,
                    ny,
                    dt,
                    T_total,
                    2.0,
                    1e3,
                    method_key=method,
                )
            else:
                basin = compute_basin_generic(
                    sys_key,
                    params,
                    z0_fixed,
                    x_min,
                    x_max,
                    y_min,
                    y_max,
                    nx,
                    ny,
                    dt,
                    T_total,
                    method_key=method,
                )
            self.last_equilibria = equilibria_for_system(sys_key, params)
        except Exception as exc:
            QMessageBox.critical(self, 'Error de cuenca', str(exc))
            return

        self.last_basin = basin
        self.last_basin_extent = (x_min, x_max, y_min, y_max)
        self.last_basin_rho = (
            params[1] if len(params) > 1 else (params[0] if params else 0.0)
        )
        self.last_basin_z0 = z0_fixed

        # Format equilibria text
        lines = []
        for eq in self.last_equilibria:
            if eq.get('manifold_description'):
                lines.append(eq['manifold_description'])
                continue
            point = eq['point']
            lines.append(
                f"{eq['name']} = ({point[0]:.6g}, {point[1]:.6g}, {point[2]:.6g})"
            )
        self.eq_label.setText(
            '\n'.join(lines) if lines else 'No se encontraron equilibrios.'
        )

        self._refresh_canvas()

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Cuenca calculada.')

    def _refresh_canvas(self):
        if self.last_basin is None:
            return

        sys_key = self.param_panel.current_system_key()
        if sys_key == 'lorenz':
            labels = {
                0: 'Escape',
                1: BASIN_RESIDUAL_LABEL,
                2: 'Converge a E+',
                3: 'Converge a E-',
                4: 'Converge a O',
                5: 'Periódico',
            }
        else:
            labels = {0: 'Escape', 1: BASIN_RESIDUAL_LABEL}
            for idx, eq in enumerate(self.last_equilibria):
                labels[2 + idx] = f"Converge a {eq.get('name', f'E{idx + 1}')}"
            labels[2 + len(self.last_equilibria)] = 'Periódico'

        self.canvas.plot_basin(
            self.last_basin,
            self.last_basin_extent,
            self.last_basin_rho,
            self.last_basin_z0,
            equilibrium_data=self.last_equilibria,
            show_equilibria=self.chk_eq.isChecked(),
            class_labels=labels,
        )


class TabLyapunovWidget(BaseTabWidget):
    """Tab for Lyapunov Exponents computation."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=False, show_ic=True, show_time=False, parent=self
        )
        self.scroll_layout.addWidget(self.param_panel)

        # Lyapunov Params Group
        self.lyap_box = QGroupBox('Parámetros Lyapunov')
        lyap_layout = QFormLayout(self.lyap_box)

        self.dt = make_double_spin(0.01, 1e-6, 1.0, 6)
        self.t_burn = make_double_spin(5.0, 0.0, 100000.0, 3)
        self.t_final = make_double_spin(40.0, 0.01, 100000.0, 3)
        self.reorth = make_int_spin(10, 1, 100000)

        self.integrator_label = QLabel('RK4 fijo (estado y sistema variacional)')
        lyap_layout.addRow(QLabel('Integrador'), self.integrator_label)
        lyap_layout.addRow(QLabel('dt integrador'), self.dt)
        lyap_layout.addRow(QLabel('Burn-in time'), self.t_burn)
        lyap_layout.addRow(QLabel('Tiempo final'), self.t_final)
        lyap_layout.addRow(QLabel('QR cada N pasos'), self.reorth)

        self.scroll_layout.addWidget(self.lyap_box)

        # Action Buttons
        self.btn_run = QPushButton('Calcular exponentes de Lyapunov')
        self.btn_run.clicked.connect(self.run_lyapunov)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_lyapunov'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplLyapunovCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

        self.lyap_info = QLabel('Exponentes no calculados.')
        self.lyap_info.setWordWrap(True)
        self.lyap_info.setStyleSheet("font-family: monospace;")
        self.right_layout.addWidget(self.lyap_info)

    def run_lyapunov(self):
        sys_key = self.param_panel.current_system_key()
        meta = SYSTEM_REGISTRY[sys_key]
        if meta.get('kind') != 'flow' or int(meta.get('dimension', 0)) != 3:
            QMessageBox.information(
                self,
                'No disponible',
                'Lyapunov QR-Benettin entero está disponible solo para flujos ODE 3D.',
            )
            return

        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        h = self.dt.value()
        if h <= 0:
            QMessageBox.critical(self, 'Error', 'dt debe ser positivo.')
            return

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Estimando exponentes Lyapunov...')

        try:
            result = integer_qr_benettin_lyapunov(
                sys_key,
                initial,
                params,
                h,
                self.t_final.value(),
                t_burn=self.t_burn.value(),
                reorthonormalize_every=self.reorth.value(),
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de Lyapunov', str(exc))
            return

        title = f"Lyapunov - {SYSTEM_REGISTRY[sys_key]['label']} ({result.method_id})"
        self.canvas.plot_lyapunov(
            result.exponents, result.times, result.convergence, title
        )

        lambdas = ', '.join(f"{v:.6g}" for v in result.exponents)
        self.lyap_info.setText(
            f"Espectro Lyapunov: [{lambdas}]\n"
            f"Estado: {result.status} | método: {result.method_id} | "
            f"h={result.step_size:g} | burn-in={result.burn_time:g} | "
            f"medición={result.measurement_time:g} | "
            f"QR cada {result.reorthonormalize_every} pasos."
        )

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Lyapunov calculado.')


class TabSpectrumWidget(BaseTabWidget):
    """Tab for Equilibrium and Eigenvalues analysis (Spectrum)."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=False, show_ic=False, show_time=False, parent=self
        )
        self.param_panel.system_changed.connect(
            self._on_system_changed
        )
        self.scroll_layout.addWidget(self.param_panel)

        # Equilibria select
        self.spec_box = QGroupBox('Autovalores')
        spec_layout = QFormLayout(self.spec_box)

        self.eq_combo = QComboBox()
        self.eq_combo.currentIndexChanged.connect(self._plot_spectrum)
        spec_layout.addRow(QLabel('Equilibrio'), self.eq_combo)

        self.scroll_layout.addWidget(self.spec_box)

        # Buttons
        self.btn_run = QPushButton('Calcular equilibrios y autovalores')
        self.btn_run.clicked.connect(self.run_spectrum)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_autovalores'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplSpectrumCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

        self.spec_info = QLabel('Autovalores no calculados.')
        self.spec_info.setWordWrap(True)
        self.spec_info.setStyleSheet("font-family: monospace;")
        self.right_layout.addWidget(self.spec_info)

        self.last_equilibria = []
        self._on_system_changed(self.param_panel.current_system_key())

    def _on_system_changed(self, system_key: str):
        self.eq_combo.clear()
        self.last_equilibria = []
        self.canvas.reset_plot()
        self.spec_info.setText('Autovalores no calculados.')

    def run_spectrum(self):
        sys_key = self.param_panel.current_system_key()
        meta = SYSTEM_REGISTRY[sys_key]
        if meta.get('kind') not in {'flow'}:
            QMessageBox.information(
                self,
                'No disponible',
                'El cálculo de equilibrios analítico/numérico solo está soportado para flujos ODE.',
            )
            return

        params = self.param_panel.current_params()
        try:
            self.last_equilibria = equilibria_for_system(sys_key, params)
        except Exception as exc:
            QMessageBox.critical(
                self, 'Error al calcular equilibrios', str(exc)
            )
            return

        self.eq_combo.blockSignals(True)
        self.eq_combo.clear()
        self.eq_combo.addItem('Todos', userData='all')
        for eq in self.last_equilibria:
            self.eq_combo.addItem(eq['name'], userData=eq['name'])
        self.eq_combo.blockSignals(False)

        self._plot_spectrum()

    def _plot_spectrum(self):
        if not self.last_equilibria:
            return

        sel = self.eq_combo.currentData()
        sys_key = self.param_panel.current_system_key()
        title = f"Plano complejo de autovalores - {SYSTEM_REGISTRY[sys_key]['label']}"
        self.canvas.plot_spectrum(
            self.last_equilibria, selected_name=sel or 'all', title=title
        )

        if sel == 'all' or not sel:
            lines = []
            for eq in self.last_equilibria:
                pt = eq['point']
                eigs = ', '.join(format_complex(v) for v in eq.get('eigvals', []))
                lines.append(
                    f"{eq['name']} = ({pt[0]:.4g}, {pt[1]:.4g}, {pt[2]:.4g}) | eigs: [{eigs}]"
                )
            self.spec_info.setText('\n'.join(lines))
        else:
            eq = next((e for e in self.last_equilibria if e['name'] == sel), None)
            if eq:
                pt = eq['point']
                eigs = ', '.join(format_complex(v) for v in eq.get('eigvals', []))
                self.spec_info.setText(
                    f"{eq['name']} = ({pt[0]:.4g}, {pt[1]:.4g}, {pt[2]:.4g})\n"
                    f"Autovalores: [{eigs}]\n"
                    f"Tipo local: {eq.get('local_type', 'indeterminado')}\n"
                    f"Clasificación: {eq.get('classification', '')}"
                )


class TabComparisonWidget(BaseTabWidget):
    """Tab for Integrator Methods Comparison."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.param_panel = SystemParameterPanel(
            show_method=False, show_ic=True, show_time=True, parent=self
        )
        self.scroll_layout.addWidget(self.param_panel)

        # Methods checklist Group
        self.meth_box = QGroupBox('Integradores a comparar')
        meth_layout = QVBoxLayout(self.meth_box)

        self.checks: dict[str, QCheckBox] = {}
        self.colors: dict[str, QComboBox] = {}

        default_colors = [
            'Negro',
            'Azul',
            'Rojo',
            'Verde',
            'Morado',
            'Naranja',
        ]
        idx = 0
        for key, meta in METHOD_REGISTRY.items():
            if not meta.get('implemented'):
                continue
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            chk = QCheckBox(meta['label'])
            chk.setChecked(True)
            row_layout.addWidget(chk, stretch=2)

            combo = QComboBox()
            for l, v in COLOR_OPTIONS.items():
                combo.addItem(l, userData=v)
            combo.setCurrentIndex(
                max(0, combo.findText(default_colors[idx % len(default_colors)]))
            )
            row_layout.addWidget(combo, stretch=1)

            meth_layout.addWidget(row)
            self.checks[key] = chk
            self.colors[key] = combo
            idx += 1

        self.scroll_layout.addWidget(self.meth_box)

        # Buttons
        self.btn_run = QPushButton('Comparar integradores')
        self.btn_run.clicked.connect(self.run_comparison)
        self.scroll_layout.addWidget(self.btn_run)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_comparacion_integradores'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = MplMethodComparisonCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

    def run_comparison(self):
        sys_key = self.param_panel.current_system_key()
        params = self.param_panel.current_params()
        initial = self.param_panel.current_initial()
        dt = self.param_panel.dt.value()
        T = self.param_panel.T.value()

        if dt <= 0 or T <= 0:
            QMessageBox.critical(self, 'Error', 'dt y T deben ser positivos.')
            return

        selected_methods = [key for key, chk in self.checks.items() if chk.isChecked()]
        if not selected_methods:
            QMessageBox.information(
                self, 'Sin métodos', 'Selecciona al menos un método para comparar.'
            )
            return

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Comparando métodos...')

        try:
            series = compare_integrator_methods(
                sys_key, initial, params, dt, T, methods=selected_methods
            )
            color_map = {
                key: combo.currentData() or '#111827'
                for key, combo in self.colors.items()
            }
            styled_series = [
                (label, t, X, color_map.get(method_key, '#111827'))
                for method_key, (label, t, X) in zip(selected_methods, series)
            ]
        except Exception as exc:
            QMessageBox.critical(self, 'Error de comparación', str(exc))
            return

        title = f"Comparación de integradores - {SYSTEM_REGISTRY[sys_key]['label']}"
        self.canvas.plot_comparison(styled_series, title)

        if hasattr(self.main_window, 'info_label'):
            self.main_window.info_label.setText('Comparación calculada.')


class TabCoexistenceWidget(BaseTabWidget):
    """Tab for Coexisting Attractors simulation and basin checking."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(main_window, parent)
        self.cases = load_coexisting_attractors()
        self.init_ui()

    def init_ui(self):
        # Left Panel Controls
        self.case_box = QGroupBox('Atractores coexistentes')
        case_layout = QFormLayout(self.case_box)

        self.case_combo = QComboBox()
        for idx, case in enumerate(self.cases):
            self.case_combo.addItem(case.get('system_name', 'Caso'), userData=idx)
        self.case_combo.currentIndexChanged.connect(self._on_case_changed)
        case_layout.addRow(QLabel('Caso reportado'), self.case_combo)

        self.attractor_combo = QComboBox()
        case_layout.addRow(QLabel('Atractor'), self.attractor_combo)

        self.scroll_layout.addWidget(self.case_box)

        # Reference information display
        self.ref_box = QGroupBox('Bibliografía y notas')
        ref_layout = QVBoxLayout(self.ref_box)
        self.ref_text = QTextEdit()
        self.ref_text.setReadOnly(True)
        self.ref_text.setMinimumHeight(120)
        self.ref_text.setStyleSheet("font-size: 11px;")
        ref_layout.addWidget(self.ref_text)
        self.scroll_layout.addWidget(self.ref_box)

        # Simulation Time Settings
        self.time_box = QGroupBox('Parámetros de simulación')
        time_layout = QFormLayout(self.time_box)
        self.dt = make_double_spin(0.01, 1e-6, 1.0, 6)
        self.T = make_double_spin(80.0, 0.01, 10000.0, 3)
        time_layout.addRow(QLabel('dt'), self.dt)
        time_layout.addRow(QLabel('Tiempo T'), self.T)
        self.scroll_layout.addWidget(self.time_box)

        # Buttons
        self.btn_load = QPushButton('Cargar parámetros del caso')
        self.btn_load.clicked.connect(self.load_parameters)
        self.scroll_layout.addWidget(self.btn_load)

        self.btn_sim_one = QPushButton('Simular atractor seleccionado')
        self.btn_sim_one.clicked.connect(self.simulate_one)
        self.scroll_layout.addWidget(self.btn_sim_one)

        self.btn_sim_all = QPushButton('Simular todos los atractores')
        self.btn_sim_all.clicked.connect(self.simulate_all)
        self.scroll_layout.addWidget(self.btn_sim_all)

        self.btn_basin = QPushButton('Calcular cuenca para este caso')
        self.btn_basin.clicked.connect(self.calculate_basin)
        self.scroll_layout.addWidget(self.btn_basin)

        # Redirection buttons
        self.redirection_box = QGroupBox('Enviar a otras pestañas')
        red_layout = QVBoxLayout(self.redirection_box)

        self.btn_send_3d = QPushButton('Enviar a Atractor 3D')
        self.btn_send_3d.clicked.connect(lambda: self.send_to_tab('Atractor 3D'))
        red_layout.addWidget(self.btn_send_3d)

        self.btn_send_basin = QPushButton('Enviar a Cuencas')
        self.btn_send_basin.clicked.connect(lambda: self.send_to_tab('Cuenca de atracción'))
        red_layout.addWidget(self.btn_send_basin)

        self.btn_send_bif = QPushButton('Enviar a Bifurcación')
        self.btn_send_bif.clicked.connect(lambda: self.send_to_tab('Bifurcación'))
        red_layout.addWidget(self.btn_send_bif)

        self.scroll_layout.addWidget(self.redirection_box)

        self.btn_save = QPushButton('Guardar gráfica...')
        self.btn_save.clicked.connect(
            lambda: self.save_matplotlib_figure(
                self.canvas.fig, 'caos_coexistencia'
            )
        )
        self.scroll_layout.addWidget(self.btn_save)

        self.scroll_layout.addStretch()

        # Right Panel Display
        self.canvas = Mpl3DCanvas(self.right_widget)
        self.right_layout.addWidget(self.canvas)

        self._on_case_changed()

    def current_case(self) -> dict | None:
        idx = self.case_combo.currentData()
        if idx is not None and 0 <= idx < len(self.cases):
            return self.cases[idx]
        return None

    def _on_case_changed(self):
        case = self.current_case()
        if not case:
            return

        ref = case.get('reference', {})
        ref_str = (
            f"Autores: {ref.get('authors','')}\n"
            f"Año: {ref.get('year','')}\n"
            f"Título: {ref.get('title','')}\n"
            f"Revista/Congreso: {ref.get('venue','')}\n"
            f"DOI: {ref.get('doi','') or 'N/A'}\n\n"
            f"Notas: {case.get('notes','')}\n\n"
            f"Parámetros: {case.get('parameter_set',{})}"
        )
        self.ref_text.setText(ref_str)

        self.attractor_combo.clear()
        for idx, attr in enumerate(case.get('attractors', [])):
            label = f"{attr.get('label','Atractor')} {attr.get('initial_condition',[])}"
            self.attractor_combo.addItem(label, userData=idx)

    def load_parameters(self):
        case = self.current_case()
        if not case:
            return
        QMessageBox.information(
            self,
            'Cargado',
            f"Parámetros cargados en la pestaña Coexistencia para {case.get('system_name')}.\n"
            "Puedes usar las acciones de 'Enviar a' para propagar a otros visores.",
        )

    def simulate_one(self):
        case = self.current_case()
        if not case:
            return

        sys_key = case.get('system_key')
        raw_params = case.get('parameter_set', {})

        # Build parameters in correct order based on SYSTEM_REGISTRY
        meta = SYSTEM_REGISTRY[sys_key]
        param_labels = meta.get('param_labels', ())
        params = [float(raw_params.get(l, 0.0)) for l in param_labels]

        attr_idx = self.attractor_combo.currentData()
        if attr_idx is None:
            return
        attractor = case.get('attractors', [])[attr_idx]
        initial = tuple(attractor.get('initial_condition', [0.1, 0.1, 0.1]))

        dt = self.dt.value()
        T = self.T.value()

        try:
            t, X = simulate_system(sys_key, initial, params, dt, T, method_key='rk4')
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulación', str(exc))
            return

        self.canvas.ax.clear()
        self.canvas.ax.plot(
            X[:, 0], X[:, 1], X[:, 2], linewidth=0.9, color='#2563eb',
            label=f"{attractor.get('label')} {initial}"
        )
        self.canvas.ax.scatter([X[0, 0]], [X[0, 1]], [X[0, 2]], s=30, color='blue')
        self.canvas.ax.scatter([X[-1, 0]], [X[-1, 1]], [X[-1, 2]], s=30, color='red')
        self.canvas.ax.set_title(f"Atractor Coexistente - {case.get('system_name')}")
        self.canvas.ax.set_xlabel('x')
        self.canvas.ax.set_ylabel('y')
        self.canvas.ax.set_zlabel('z')
        self.canvas.ax.legend(fontsize=8)
        self.canvas.draw_idle()

    def simulate_all(self):
        case = self.current_case()
        if not case:
            return

        sys_key = case.get('system_key')
        raw_params = case.get('parameter_set', {})

        meta = SYSTEM_REGISTRY[sys_key]
        param_labels = meta.get('param_labels', ())
        params = [float(raw_params.get(l, 0.0)) for l in param_labels]

        dt = self.dt.value()
        T = self.T.value()

        self.canvas.ax.clear()
        colors = ['#dc2626', '#2563eb', '#16a34a', '#7c3aed', '#ea580c']

        for idx, attractor in enumerate(case.get('attractors', [])):
            initial = tuple(attractor.get('initial_condition', [0.1, 0.1, 0.1]))
            color = colors[idx % len(colors)]
            try:
                t, X = simulate_system(
                    sys_key, initial, params, dt, T, method_key='rk4'
                )
                self.canvas.ax.plot(
                    X[:, 0], X[:, 1], X[:, 2], linewidth=0.9, color=color,
                    label=f"{attractor.get('label')} {initial}"
                )
                self.canvas.ax.scatter([X[0, 0]], [X[0, 1]], [X[0, 2]], s=25, color=color)
            except Exception as exc:
                QMessageBox.warning(
                    self, 'Error en simulación', f"No se pudo simular {attractor.get('label')}: {exc}"
                )

        self.canvas.ax.set_title(f"Coexistencia de Atractores - {case.get('system_name')}")
        self.canvas.ax.set_xlabel('x')
        self.canvas.ax.set_ylabel('y')
        self.canvas.ax.set_zlabel('z')
        self.canvas.ax.legend(fontsize=8)
        self.canvas.draw_idle()

    def calculate_basin(self):
        # Redirect to Basin tab and load parameters
        self.send_to_tab('Cuenca de atracción')
        # Trigger simulation in Basin tab if active
        if self.main_window:
            basin_tab = getattr(self.main_window, 'tab_basin_widget', None)
            if basin_tab:
                basin_tab.run_basin()

    def send_to_tab(self, target_tab_name: str):
        if not self.main_window or not self.main_window.tabs:
            return

        case = self.current_case()
        if not case:
            return

        sys_key = case.get('system_key')
        raw_params = case.get('parameter_set', {})

        # Build order
        meta = SYSTEM_REGISTRY[sys_key]
        param_labels = meta.get('param_labels', ())
        params = [float(raw_params.get(l, 0.0)) for l in param_labels]

        # Selected attractor initial condition
        attr_idx = self.attractor_combo.currentData()
        attractors = case.get('attractors', [])
        initial = (
            attractors[attr_idx].get('initial_condition', [0.1, 0.1, 0.1])
            if attr_idx is not None and attr_idx < len(attractors)
            else [0.1, 0.1, 0.1]
        )

        # Loop tabs and find the target
        tabs = self.main_window.tabs
        target_widget = None
        for i in range(tabs.count()):
            if tabs.tabText(i).lower() in target_tab_name.lower():
                tabs.setCurrentIndex(i)
                target_widget = tabs.widget(i)
                break

        if target_widget:
            # Look for a SystemParameterPanel inside the target widget
            panel = target_widget.findChild(SystemParameterPanel)
            if panel:
                # Set system
                sys_idx = panel.system_combo.findData(sys_key)
                if sys_idx >= 0:
                    panel.system_combo.setCurrentIndex(sys_idx)
                # Set params
                for idx, val in enumerate(params):
                    if idx < len(panel.param_spins):
                        panel.param_spins[idx].setValue(val)
                # Set initial condition
                if panel.show_ic and len(initial) >= 3:
                    panel.x0.setValue(initial[0])
                    panel.y0.setValue(initial[1])
                    panel.z0.setValue(initial[2])
