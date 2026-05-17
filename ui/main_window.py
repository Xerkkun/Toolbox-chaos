from __future__ import annotations

import os

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.lorenz import (
    METHOD_REGISTRY,
    SYSTEM_REGISTRY,
    NativeChaosError,
    UnsupportedMethodError,
    UnsupportedSystemError,
    bifurcation_poincare_lorenz,
    compute_basin_plane_z_lorenz_xiong,
    lorenz_equilibria,
    lorenz_simulate,
    method_is_available,
    require_supported,
    system_is_available,
)
from ui.canvases import Mpl3DCanvas, MplBasinCanvas, MplBifCanvas, MplSpectrumCanvas
from ui.widgets import make_double_spin, make_help_label, make_int_spin

try:
    from PyQt6.QtPdf import QPdfDocument
    from PyQt6.QtPdfWidgets import QPdfView
    QT_PDF_AVAILABLE = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    QT_PDF_AVAILABLE = False


HELP = {
    'system': '<b>Sistema caótico</b><br>Selecciona el modelo dinámico. En esta versión solo Lorenz está implementado; las demás entradas funcionan como placeholders para futuras extensiones.',
    'method': '<b>Método numérico</b><br>Esquema temporal usado por el integrador. En esta versión las simulaciones pesadas usan backend nativo en C para Euler, Heun y RK4.',
    'sigma': '<b>σ</b><br>Parámetro de Prandtl del sistema de Lorenz. Controla el acoplamiento entre x e y.',
    'rho': '<b>ρ</b><br>Parámetro de Rayleigh reducido. En Lorenz se usa con frecuencia como parámetro de bifurcación.',
    'beta': '<b>β</b><br>Parámetro geométrico/disipativo del sistema de Lorenz.',
    'x0': '<b>x(0)</b><br>Condición inicial de la primera variable del estado.',
    'y0': '<b>y(0)</b><br>Condición inicial de la segunda variable del estado.',
    'z0': '<b>z(0)</b><br>Condición inicial de la tercera variable del estado.',
    'dt': '<b>dt</b><br>Paso temporal fijo. Valores menores dan mayor resolución, pero aumentan el costo computacional.',
    'T': '<b>T</b><br>Tiempo total de integración para la trayectoria mostrada.',
    'bif_rho_min': '<b>ρ mínimo</b><br>Inicio del barrido paramétrico en la pestaña de bifurcación.',
    'bif_rho_max': '<b>ρ máximo</b><br>Fin del barrido paramétrico en la pestaña de bifurcación.',
    'bif_n_rho': '<b>Nρ</b><br>Número de muestras del parámetro en el barrido de bifurcación.',
    'bif_dt': '<b>dt bif.</b><br>Paso temporal usado en el cálculo del diagrama de bifurcación.',
    'bif_T_trans': '<b>Transitorio</b><br>Tiempo descartado antes de registrar eventos de la sección de Poincaré.',
    'bif_T_keep': '<b>Ventana útil</b><br>Tiempo posterior al transitorio en el que sí se registran eventos.',
    'bif_max_points': '<b>Cruces por ρ</b><br>Número máximo de intersecciones guardadas por valor del parámetro.',
    'bif_cont': '<b>Usar continuación</b><br>Reutiliza el estado final del parámetro anterior como semilla del siguiente.',
    'basin_xmin': '<b>x0 mínimo</b><br>Límite inferior del plano inicial para la cuenca de atracción.',
    'basin_xmax': '<b>x0 máximo</b><br>Límite superior del plano inicial para la cuenca de atracción.',
    'basin_ymin': '<b>y0 mínimo</b><br>Límite inferior en y para el plano inicial.',
    'basin_ymax': '<b>y0 máximo</b><br>Límite superior en y para el plano inicial.',
    'basin_z0': '<b>z0 fijo</b><br>Valor fijo de z del plano donde se barre la cuenca.',
    'basin_nx': '<b>Nx</b><br>Número de puntos de discretización en x.',
    'basin_ny': '<b>Ny</b><br>Número de puntos de discretización en y.',
    'basin_dt': '<b>dt cuenca</b><br>Paso temporal de integración usado para clasificar cada condición inicial.',
    'basin_T_total': '<b>Tiempo total</b><br>Horizonte temporal usado para clasificar la condición inicial dentro de la cuenca.',
    'show_eq': '<b>Superponer equilibrios</b><br>Dibuja la proyección (x,y) de los equilibrios sobre el plano de la cuenca.',
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Banco de pruebas de sistemas caóticos')
        self.resize(1720, 980)

        pg.setConfigOptions(antialias=True)

        self.last_basin = None
        self.last_basin_extent = None
        self.last_basin_rho = None
        self.last_basin_z0 = None
        self.last_equilibria = []

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_scroll.setWidget(controls)

        model_box = QGroupBox('Modelo e integrador')
        model_form = QFormLayout(model_box)

        self.system_combo = QComboBox()
        for key, meta in SYSTEM_REGISTRY.items():
            suffix = ' [listo]' if meta['implemented'] else ' [pendiente]'
            self.system_combo.addItem(f"{meta['label']}{suffix}", userData=key)
        self.system_combo.currentIndexChanged.connect(self.on_system_changed)

        self.method_combo = QComboBox()
        for key, meta in METHOD_REGISTRY.items():
            suffix = f" [{meta['backend']}]" if meta['implemented'] else ' [pendiente]'
            self.method_combo.addItem(f"{meta['label']}{suffix}", userData=key)
        self.method_combo.setCurrentIndex(max(0, self.method_combo.findData('rk4')))
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)

        self.model_status = QLabel()
        self.model_status.setWordWrap(True)
        self.model_status.setStyleSheet('font-size: 10px; color: #dddddd;')

        model_form.addRow(make_help_label('Sistema', HELP['system']), self.system_combo)
        model_form.addRow(make_help_label('Método', HELP['method']), self.method_combo)
        model_form.addRow(QLabel('Estado'), self.model_status)

        params_box = QGroupBox('Parámetros del sistema')
        params_form = QFormLayout(params_box)

        self.sigma = make_double_spin(10.0, 0.001, 1000.0, 3)
        self.rho = make_double_spin(28.0, 0.001, 1000.0, 3)
        self.beta = make_double_spin(8.0 / 3.0, 0.001, 1000.0, 6)

        params_form.addRow(make_help_label('σ', HELP['sigma']), self.sigma)
        params_form.addRow(make_help_label('ρ', HELP['rho']), self.rho)
        params_form.addRow(make_help_label('β', HELP['beta']), self.beta)

        ic_box = QGroupBox('Condiciones iniciales')
        ic_form = QFormLayout(ic_box)

        self.x0 = make_double_spin(0.1, -1000.0, 1000.0, 6)
        self.y0 = make_double_spin(0.1, -1000.0, 1000.0, 6)
        self.z0 = make_double_spin(0.1, -1000.0, 1000.0, 6)

        ic_form.addRow(make_help_label('x(0)', HELP['x0']), self.x0)
        ic_form.addRow(make_help_label('y(0)', HELP['y0']), self.y0)
        ic_form.addRow(make_help_label('z(0)', HELP['z0']), self.z0)

        sim_box = QGroupBox('Simulación base')
        sim_form = QFormLayout(sim_box)

        self.dt = make_double_spin(0.01, 1e-6, 1.0, 6)
        self.T = make_double_spin(40.0, 0.01, 10000.0, 3)

        sim_form.addRow(make_help_label('dt', HELP['dt']), self.dt)
        sim_form.addRow(make_help_label('Tiempo total T', HELP['T']), self.T)

        btn_run = QPushButton('Simular trayectoria')
        btn_defaults = QPushButton('Restaurar valores')
        btn_clear = QPushButton('Limpiar')
        btn_run.clicked.connect(self.run_simulation)
        btn_defaults.clicked.connect(self.restore_defaults)
        btn_clear.clicked.connect(self.clear_plots)

        bif_box = QGroupBox('Bifurcación')
        bif_form = QFormLayout(bif_box)

        self.bif_rho_min = make_double_spin(0.0, -500.0, 500.0, 3)
        self.bif_rho_max = make_double_spin(80.0, -500.0, 500.0, 3)
        self.bif_n_rho = make_int_spin(700, 10, 5000)
        self.bif_dt = make_double_spin(0.003, 1e-5, 1.0, 6)
        self.bif_T_trans = make_double_spin(120.0, 0.0, 10000.0, 3)
        self.bif_T_keep = make_double_spin(180.0, 0.1, 10000.0, 3)
        self.bif_max_points = make_int_spin(450, 1, 2000)
        self.bif_use_cont = QCheckBox('Usar continuación')
        self.bif_use_cont.setChecked(False)
        self.bif_use_cont.setToolTip(HELP['bif_cont'])

        bif_form.addRow(make_help_label('ρ mínimo', HELP['bif_rho_min']), self.bif_rho_min)
        bif_form.addRow(make_help_label('ρ máximo', HELP['bif_rho_max']), self.bif_rho_max)
        bif_form.addRow(make_help_label('Nρ', HELP['bif_n_rho']), self.bif_n_rho)
        bif_form.addRow(make_help_label('dt bif.', HELP['bif_dt']), self.bif_dt)
        bif_form.addRow(make_help_label('Transitorio', HELP['bif_T_trans']), self.bif_T_trans)
        bif_form.addRow(make_help_label('Ventana útil', HELP['bif_T_keep']), self.bif_T_keep)
        bif_form.addRow(make_help_label('Cruces por ρ', HELP['bif_max_points']), self.bif_max_points)
        bif_form.addRow(make_help_label('Continuación', HELP['bif_cont']), self.bif_use_cont)

        btn_bif = QPushButton('Calcular bifurcación')
        btn_bif.clicked.connect(self.compute_bifurcation)

        basin_box = QGroupBox('Cuenca / clasificación en el plano (x0,y0)')
        basin_form = QFormLayout(basin_box)

        self.basin_xmin = make_double_spin(-25.0, -1000.0, 1000.0, 3)
        self.basin_xmax = make_double_spin(25.0, -1000.0, 1000.0, 3)
        self.basin_ymin = make_double_spin(-25.0, -1000.0, 1000.0, 3)
        self.basin_ymax = make_double_spin(25.0, -1000.0, 1000.0, 3)
        self.basin_z0 = make_double_spin(1.0, -1000.0, 1000.0, 6)
        self.basin_nx = make_int_spin(60, 10, 500)
        self.basin_ny = make_int_spin(60, 10, 500)
        self.basin_dt = make_double_spin(0.02, 1e-5, 1.0, 6)
        self.basin_T_total = make_double_spin(12.0, 0.1, 10000.0, 3)

        basin_form.addRow(make_help_label('x0 mínimo', HELP['basin_xmin']), self.basin_xmin)
        basin_form.addRow(make_help_label('x0 máximo', HELP['basin_xmax']), self.basin_xmax)
        basin_form.addRow(make_help_label('y0 mínimo', HELP['basin_ymin']), self.basin_ymin)
        basin_form.addRow(make_help_label('y0 máximo', HELP['basin_ymax']), self.basin_ymax)
        basin_form.addRow(make_help_label('z0 fijo', HELP['basin_z0']), self.basin_z0)
        basin_form.addRow(make_help_label('Nx', HELP['basin_nx']), self.basin_nx)
        basin_form.addRow(make_help_label('Ny', HELP['basin_ny']), self.basin_ny)
        basin_form.addRow(make_help_label('dt cuenca', HELP['basin_dt']), self.basin_dt)
        basin_form.addRow(make_help_label('Tiempo total', HELP['basin_T_total']), self.basin_T_total)

        btn_basin = QPushButton('Calcular cuenca / clasificación')
        btn_basin.clicked.connect(self.compute_basin)

        self.info_label = QLabel('Listo.')
        self.info_label.setWordWrap(True)

        controls_layout.addWidget(model_box)
        controls_layout.addWidget(params_box)
        controls_layout.addWidget(ic_box)
        controls_layout.addWidget(sim_box)
        controls_layout.addWidget(btn_run)
        controls_layout.addWidget(btn_defaults)
        controls_layout.addWidget(btn_clear)
        controls_layout.addWidget(bif_box)
        controls_layout.addWidget(btn_bif)
        controls_layout.addWidget(basin_box)
        controls_layout.addWidget(btn_basin)
        controls_layout.addWidget(self.info_label)
        controls_layout.addStretch()

        self.tabs = QTabWidget()
        self.build_3d_tab()
        self.build_2d_tab()
        self.build_time_tab()
        self.build_bifurcation_tab()
        self.build_basin_tab()
        self.build_spectrum_tab()
        self.build_dictionary_tab()

        splitter.addWidget(controls_scroll)
        splitter.addWidget(self.tabs)
        splitter.setSizes([410, 1310])

        self.on_system_changed()
        self.on_method_changed()
        self.run_simulation()
        self.update_equilibrium_info()

    def current_system_key(self) -> str:
        return self.system_combo.currentData()

    def current_method_key(self) -> str:
        return self.method_combo.currentData()

    def _make_tab_toolbar(self, title, save_callback=None):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setStyleSheet('font-weight: bold;')
        layout.addWidget(label)
        layout.addStretch(1)

        if save_callback is not None:
            btn_save = QPushButton('Guardar gráfica...')
            btn_save.setMaximumWidth(150)
            btn_save.clicked.connect(save_callback)
            layout.addWidget(btn_save)
        return bar

    def _make_note_strip(self, text: str):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet('font-size: 10px; color: #dddddd; padding: 2px 4px;')
        label.setMaximumHeight(36)
        return label

    def build_3d_tab(self):
        self.tab_3d = QWidget()
        layout = QVBoxLayout(self.tab_3d)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self._make_tab_toolbar('Atractor 3D', self.save_3d_plot), stretch=0)
        self.canvas3d = Mpl3DCanvas(self.tab_3d)
        layout.addWidget(self.canvas3d, stretch=1)
        self.tabs.addTab(self.tab_3d, 'Atractor 3D')

    def build_2d_tab(self):
        self.tab_2d = QWidget()
        outer_layout = QVBoxLayout(self.tab_2d)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(4)
        outer_layout.addWidget(self._make_tab_toolbar('Retratos 2D', self.save_2d_plots), stretch=0)

        self.plots_2d_widget = QWidget()
        portraits_layout = QGridLayout(self.plots_2d_widget)

        self.xy_plot = pg.PlotWidget(title='Plano XY')
        self.xz_plot = pg.PlotWidget(title='Plano XZ')
        self.yz_plot = pg.PlotWidget(title='Plano YZ')

        self.xy_plot.setLabel('bottom', 'x')
        self.xy_plot.setLabel('left', 'y')
        self.xz_plot.setLabel('bottom', 'x')
        self.xz_plot.setLabel('left', 'z')
        self.yz_plot.setLabel('bottom', 'y')
        self.yz_plot.setLabel('left', 'z')

        self.xy_curve = self.xy_plot.plot([], [], pen=pg.mkPen(width=1.5))
        self.xz_curve = self.xz_plot.plot([], [], pen=pg.mkPen(width=1.5))
        self.yz_curve = self.yz_plot.plot([], [], pen=pg.mkPen(width=1.5))

        portraits_layout.addWidget(self.xy_plot, 0, 0)
        portraits_layout.addWidget(self.xz_plot, 0, 1)
        portraits_layout.addWidget(self.yz_plot, 1, 0, 1, 2)
        outer_layout.addWidget(self.plots_2d_widget, stretch=1)
        self.tabs.addTab(self.tab_2d, 'Retratos 2D')

    def build_time_tab(self):
        self.tab_time = QWidget()
        outer_layout = QVBoxLayout(self.tab_time)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(4)
        outer_layout.addWidget(self._make_tab_toolbar('Series temporales', self.save_time_plots), stretch=0)

        self.plots_time_widget = QWidget()
        time_layout = QGridLayout(self.plots_time_widget)

        self.xt_plot = pg.PlotWidget(title='x(t)')
        self.yt_plot = pg.PlotWidget(title='y(t)')
        self.zt_plot = pg.PlotWidget(title='z(t)')

        self.xt_plot.setLabel('bottom', 't')
        self.xt_plot.setLabel('left', 'x')
        self.yt_plot.setLabel('bottom', 't')
        self.yt_plot.setLabel('left', 'y')
        self.zt_plot.setLabel('bottom', 't')
        self.zt_plot.setLabel('left', 'z')

        self.xt_curve = self.xt_plot.plot([], [], pen=pg.mkPen(width=1.5))
        self.yt_curve = self.yt_plot.plot([], [], pen=pg.mkPen(width=1.5))
        self.zt_curve = self.zt_plot.plot([], [], pen=pg.mkPen(width=1.5))

        time_layout.addWidget(self.xt_plot, 0, 0)
        time_layout.addWidget(self.yt_plot, 1, 0)
        time_layout.addWidget(self.zt_plot, 2, 0)
        outer_layout.addWidget(self.plots_time_widget, stretch=1)
        self.tabs.addTab(self.tab_time, 'Series temporales')

    def build_bifurcation_tab(self):
        self.tab_bif = QWidget()
        layout = QVBoxLayout(self.tab_bif)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self._make_tab_toolbar('Diagrama de bifurcación', self.save_bif_plot), stretch=0)
        layout.addWidget(
            self._make_note_strip(
                'Método actual: sección de Poincaré x = 0 con cruce x>0 → x≤0, con interpolación lineal del evento y trazado tipo MATLAB con puntos negros finos. Para una nube nítida conviene usar dt pequeño, transitorio largo y ventana útil amplia.'
            ),
            stretch=0,
        )
        self.canvas_bif = MplBifCanvas(self.tab_bif)
        layout.addWidget(self.canvas_bif, stretch=1)
        self.tabs.addTab(self.tab_bif, 'Bifurcación')

    def build_basin_tab(self):
        self.tab_basin = QWidget()
        main_layout = QVBoxLayout(self.tab_basin)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        main_layout.addWidget(self._make_tab_toolbar('Cuenca de atracción / clasificación', self.save_basin_plot), stretch=0)

        top_row = QWidget()
        top_row_layout = QHBoxLayout(top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(8)
        top_row_layout.addWidget(
            self._make_note_strip('Plano z = z0 fijo. La superposición dibuja solo la proyección (x,y) de los equilibrios.'),
            stretch=1,
        )
        self.chk_show_equilibria = QCheckBox('Superponer equilibrios')
        self.chk_show_equilibria.setChecked(True)
        self.chk_show_equilibria.setToolTip(HELP['show_eq'])
        self.chk_show_equilibria.toggled.connect(self.refresh_basin_canvas)
        top_row_layout.addWidget(self.chk_show_equilibria, stretch=0)
        main_layout.addWidget(top_row, stretch=0)

        self.canvas_basin = MplBasinCanvas(self.tab_basin)
        main_layout.addWidget(self.canvas_basin, stretch=1)

        eq_box = QGroupBox('Equilibrios')
        eq_layout = QVBoxLayout(eq_box)
        self.eq_values_label = QLabel('')
        self.eq_values_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.eq_values_label.setWordWrap(True)
        self.eq_values_label.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; padding: 4px;")
        eq_layout.addWidget(self.eq_values_label)
        main_layout.addWidget(eq_box, stretch=0)
        self.tabs.addTab(self.tab_basin, 'Cuenca de atracción')

    def build_spectrum_tab(self):
        self.tab_spectrum = QWidget()
        layout = QVBoxLayout(self.tab_spectrum)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self._make_tab_toolbar('Plano complejo de autovalores', self.save_spectrum_plot), stretch=0)
        layout.addWidget(
            self._make_note_strip('La gráfica colorea automáticamente los autovalores según el tipo local del equilibrio. En el Lorenz clásico, O tiene tres autovalores reales, mientras que E+ y E- tienen un autovalor real y un par complejo conjugado.'),
            stretch=0,
        )
        selector_bar = QWidget()
        selector_layout = QHBoxLayout(selector_bar)
        selector_layout.setContentsMargins(2, 2, 2, 2)
        selector_layout.setSpacing(8)
        selector_layout.addWidget(QLabel('Equilibrio'))
        self.spectrum_selector = QComboBox()
        self.spectrum_selector.currentIndexChanged.connect(self.refresh_spectrum_canvas)
        selector_layout.addWidget(self.spectrum_selector)
        selector_layout.addStretch(1)
        layout.addWidget(selector_bar, stretch=0)
        self.canvas_spectrum = MplSpectrumCanvas(self.tab_spectrum)
        layout.addWidget(self.canvas_spectrum, stretch=1)
        self.spectrum_info = QLabel('')
        self.spectrum_info.setWordWrap(True)
        layout.addWidget(self.spectrum_info, stretch=0)
        self.tabs.addTab(self.tab_spectrum, 'Autovalores')

    def build_dictionary_tab(self):
        self.tab_dict = QWidget()
        layout = QVBoxLayout(self.tab_dict)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.addWidget(self._make_tab_toolbar('Diccionario de conceptos', None), stretch=0)
        if QT_PDF_AVAILABLE:
            note = self._make_note_strip('Esta pestaña usa un PDF previamente compilado para mantener tipografía, ecuaciones y maquetación estables. Si QtPdf no está disponible, se usa una vista HTML mínima de respaldo.')
        else:
            note = self._make_note_strip('QtPdf no está disponible en este entorno; se muestra una vista HTML mínima y se puede abrir el PDF externo.')
        layout.addWidget(note, stretch=0)

        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        self.dictionary_pdf_path = os.path.join(assets_dir, 'chaos_dictionary.pdf')

        self.dict_open_pdf_btn = QPushButton('Abrir PDF externo')
        self.dict_open_pdf_btn.clicked.connect(self.open_dictionary_pdf)
        if not os.path.exists(self.dictionary_pdf_path):
            self.dict_open_pdf_btn.setEnabled(False)
        layout.addWidget(self.dict_open_pdf_btn, stretch=0)

        viewer_added = False
        if QT_PDF_AVAILABLE and os.path.exists(self.dictionary_pdf_path):
            try:
                self.dict_pdf_document = QPdfDocument(self)
                self.dict_pdf_view = QPdfView(self.tab_dict)
                self.dict_pdf_view.setDocument(self.dict_pdf_document)
                self.dict_pdf_document.load(self.dictionary_pdf_path)
                if hasattr(self.dict_pdf_view, 'setZoomMode'):
                    self.dict_pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
                if hasattr(self.dict_pdf_view, 'setPageMode'):
                    self.dict_pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
                layout.addWidget(self.dict_pdf_view, stretch=1)
                viewer_added = True
            except Exception:
                viewer_added = False

        if not viewer_added:
            self.dict_browser = QTextBrowser()
            self.dict_browser.setOpenExternalLinks(True)
            self.dict_browser.setHtml(self._dictionary_html())
            layout.addWidget(self.dict_browser, stretch=1)

        self.tabs.addTab(self.tab_dict, 'Diccionario')

    def open_dictionary_pdf(self):
        if hasattr(self, 'dictionary_pdf_path') and os.path.exists(self.dictionary_pdf_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.dictionary_pdf_path))

    def _dictionary_html(self) -> str:
        pdf_uri = QUrl.fromLocalFile(self.dictionary_pdf_path).toString()
        return (
            '<html><body style="font-family: Segoe UI, Arial, sans-serif; margin: 14px;">'
            '<h2>Diccionario de conceptos</h2>'
            '<p>La vista profesional de esta pestaña está preparada como PDF compilado. '
            'Abre el PDF externo si el visor embebido no está disponible en tu instalación de Qt.</p>'
            f'<p><a href="{pdf_uri}">Abrir chaos_dictionary.pdf</a></p>'
            '</body></html>'
        )
    def _suggested_path(self, default_name, extension):
        if not default_name.lower().endswith(extension):
            default_name = f'{default_name}{extension}'
        return os.path.join(os.path.expanduser('~'), default_name)

    def _ensure_suffix(self, file_path, selected_filter):
        base, ext = os.path.splitext(file_path)
        if ext:
            return file_path
        filter_map = {
            'PNG (*.png)': '.png',
            'PDF (*.pdf)': '.pdf',
            'SVG (*.svg)': '.svg',
            'JPEG (*.jpg *.jpeg)': '.jpg',
            'BMP (*.bmp)': '.bmp',
        }
        return base + filter_map.get(selected_filter, '.png')

    def _save_matplotlib_figure(self, fig, default_name):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Guardar gráfica',
            self._suggested_path(default_name, '.png'),
            'PNG (*.png);;PDF (*.pdf);;SVG (*.svg);;JPEG (*.jpg *.jpeg)',
        )
        if not file_path:
            return
        file_path = self._ensure_suffix(file_path, selected_filter)
        fig.savefig(file_path, dpi=300, bbox_inches='tight')
        self.info_label.setText(f'Gráfica guardada en:\n{file_path}')

    def _save_widget_snapshot(self, widget, default_name):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Guardar gráfica',
            self._suggested_path(default_name, '.png'),
            'PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)',
        )
        if not file_path:
            return
        file_path = self._ensure_suffix(file_path, selected_filter)
        pixmap = widget.grab()
        pixmap.save(file_path)
        self.info_label.setText(f'Gráfica guardada en:\n{file_path}')

    def save_3d_plot(self):
        self._save_matplotlib_figure(self.canvas3d.fig, 'caos_atractor_3d')

    def save_2d_plots(self):
        self._save_widget_snapshot(self.plots_2d_widget, 'caos_retratos_2d')

    def save_time_plots(self):
        self._save_widget_snapshot(self.plots_time_widget, 'caos_series_temporales')

    def save_bif_plot(self):
        self._save_matplotlib_figure(self.canvas_bif.fig, 'caos_bifurcacion')

    def save_basin_plot(self):
        self._save_matplotlib_figure(self.canvas_basin.fig, 'caos_cuenca')

    def save_spectrum_plot(self):
        self._save_matplotlib_figure(self.canvas_spectrum.fig, 'caos_autovalores')

    def on_system_changed(self):
        key = self.current_system_key()
        meta = SYSTEM_REGISTRY[key]
        state = 'implementado' if meta['implemented'] else 'pendiente'
        self.model_status.setText(
            f"Sistema: {meta['label']} ({state}). {meta['description']}\n"
            'El panel de parámetros visible corresponde al Lorenz hasta que se agreguen formularios específicos por sistema.'
        )
        self.setWindowTitle(f"Banco de pruebas de sistemas caóticos - {meta['label']}")
        self.update_equilibrium_info()

    def on_method_changed(self):
        key = self.current_method_key()
        meta = METHOD_REGISTRY[key]
        extra = 'Disponible en backend C.' if meta['implemented'] else 'Entrada registrada para implementación futura.'
        self.info_label.setText(
            f"Método seleccionado: {meta['label']} | familia: {meta['family']} | backend: {meta['backend']}. {extra}"
        )

    def _guard_supported(self):
        try:
            require_supported(self.current_system_key(), self.current_method_key())
        except UnsupportedSystemError as exc:
            QMessageBox.information(self, 'Sistema pendiente', str(exc))
            return False
        except UnsupportedMethodError as exc:
            QMessageBox.information(self, 'Método pendiente', str(exc))
            return False
        return True

    def restore_defaults(self):
        self.system_combo.setCurrentIndex(max(0, self.system_combo.findData('lorenz')))
        self.method_combo.setCurrentIndex(max(0, self.method_combo.findData('rk4')))

        self.sigma.setValue(10.0)
        self.rho.setValue(28.0)
        self.beta.setValue(8.0 / 3.0)
        self.x0.setValue(0.1)
        self.y0.setValue(0.1)
        self.z0.setValue(0.1)
        self.dt.setValue(0.01)
        self.T.setValue(40.0)

        self.bif_rho_min.setValue(0.0)
        self.bif_rho_max.setValue(80.0)
        self.bif_n_rho.setValue(700)
        self.bif_dt.setValue(0.003)
        self.bif_T_trans.setValue(120.0)
        self.bif_T_keep.setValue(180.0)
        self.bif_max_points.setValue(450)
        self.bif_use_cont.setChecked(False)

        self.basin_xmin.setValue(-25.0)
        self.basin_xmax.setValue(25.0)
        self.basin_ymin.setValue(-25.0)
        self.basin_ymax.setValue(25.0)
        self.basin_z0.setValue(1.0)
        self.basin_nx.setValue(60)
        self.basin_ny.setValue(60)
        self.basin_dt.setValue(0.02)
        self.basin_T_total.setValue(12.0)
        self.chk_show_equilibria.setChecked(True)

        self.info_label.setText('Valores restaurados.')
        self.run_simulation()
        self.update_equilibrium_info()

    def clear_plots(self):
        self.xy_curve.setData([], [])
        self.xz_curve.setData([], [])
        self.yz_curve.setData([], [])
        self.xt_curve.setData([], [])
        self.yt_curve.setData([], [])
        self.zt_curve.setData([], [])
        self.canvas3d.reset_plot()
        self.canvas_bif.reset_plot()
        self.canvas_basin.reset_plot()
        self.canvas_spectrum.reset_plot()
        self.last_basin = None
        self.last_basin_extent = None
        self.last_basin_rho = None
        self.last_basin_z0 = None
        self.info_label.setText('Gráficas limpiadas.')
        self.update_equilibrium_info()

    def run_simulation(self):
        if not self._guard_supported():
            return

        sigma = self.sigma.value()
        rho = self.rho.value()
        beta = self.beta.value()
        x0 = self.x0.value()
        y0 = self.y0.value()
        z0 = self.z0.value()
        dt = self.dt.value()
        T = self.T.value()
        method_key = self.current_method_key()

        if dt <= 0 or T <= 0:
            QMessageBox.critical(self, 'Error', 'dt y T deben ser positivos.')
            return

        n = int(T / dt) + 1
        if n > 2_000_000:
            QMessageBox.critical(self, 'Error', 'La simulación base es demasiado grande. Reduce T o aumenta dt.')
            return

        self.info_label.setText('Simulando trayectoria con backend nativo en C...')
        QApplication.processEvents()
        try:
            t, X = lorenz_simulate(x0, y0, z0, sigma, rho, beta, dt, T, method_key=method_key)
        except NativeChaosError as exc:
            QMessageBox.critical(self, 'Error de backend nativo', str(exc))
            return

        x = X[:, 0]
        y = X[:, 1]
        z = X[:, 2]

        self.xy_curve.setData(x, y)
        self.xz_curve.setData(x, z)
        self.yz_curve.setData(y, z)
        self.xt_curve.setData(t, x)
        self.yt_curve.setData(t, y)
        self.zt_curve.setData(t, z)

        max_3d_points = 18000
        if len(x) > max_3d_points:
            idx = np.linspace(0, len(x) - 1, max_3d_points).astype(int)
            x3, y3, z3 = x[idx], y[idx], z[idx]
        else:
            x3, y3, z3 = x, y, z
        self.canvas3d.plot_lorenz(x3, y3, z3)
        self.update_equilibrium_info()

        meta = METHOD_REGISTRY[method_key]
        self.info_label.setText(
            f"Trayectoria simulada en C.\nPuntos: {n}\ndt = {dt}\nT = {T}\nMétodo: {meta['label']}"
        )

    def compute_bifurcation(self):
        if not self._guard_supported():
            return
        if self.current_system_key() != 'lorenz':
            QMessageBox.information(self, 'Pendiente', 'La bifurcación actual está implementada solo para Lorenz.')
            return

        sigma = self.sigma.value()
        beta = self.beta.value()
        x0 = self.x0.value()
        y0 = self.y0.value()
        z0 = self.z0.value()
        rho_min = self.bif_rho_min.value()
        rho_max = self.bif_rho_max.value()
        n_rho = self.bif_n_rho.value()
        dt = self.bif_dt.value()
        T_trans = self.bif_T_trans.value()
        T_keep = self.bif_T_keep.value()
        max_points = self.bif_max_points.value()
        use_cont = self.bif_use_cont.isChecked()
        method_key = self.current_method_key()

        if dt <= 0 or T_keep <= 0 or n_rho < 2:
            QMessageBox.critical(self, 'Error', 'Parámetros inválidos para bifurcación.')
            return
        if rho_max <= rho_min:
            QMessageBox.critical(self, 'Error', 'Se requiere ρ máximo > ρ mínimo.')
            return

        total_steps = n_rho * int((T_trans + T_keep) / dt)
        if total_steps > 220_000_000:
            QMessageBox.critical(self, 'Error', 'El cálculo solicitado es excesivo para la interfaz.')
            return

        self.info_label.setText('Calculando diagrama de bifurcación con backend nativo en C...')
        QApplication.processEvents()
        try:
            rho_vals, z_vals = bifurcation_poincare_lorenz(
                x0,
                y0,
                z0,
                sigma,
                beta,
                rho_min,
                rho_max,
                n_rho,
                dt,
                T_trans,
                T_keep,
                max_points,
                1 if use_cont else 0,
                method_key=method_key,
            )
        except NativeChaosError as exc:
            QMessageBox.critical(self, 'Error de backend nativo', str(exc))
            return

        self.canvas_bif.plot_bifurcation(
            rho_vals,
            z_vals,
            'Diagrama de bifurcación por sección de Poincaré',
            r'$\rho$',
            r'$z$ en el cruce $x=0$',
        )
        self.tabs.setCurrentWidget(self.tab_bif)
        modo = 'con continuación' if use_cont else 'sin continuación (CI fijas)'
        self.info_label.setText(
            f"Bifurcación calculada en C.\nPuntos graficados: {len(rho_vals)}\nBarrido en ρ de {rho_min} a {rho_max} con {n_rho} muestras.\nMétodo: {METHOD_REGISTRY[method_key]['label']} | {modo}.\nReferencia de esquema: sección de Poincaré como en Lazaros Moysis (MATLAB File Exchange)."
        )

    def compute_basin(self):
        if not self._guard_supported():
            return
        if self.current_system_key() != 'lorenz':
            QMessageBox.information(self, 'Pendiente', 'La cuenca actual está implementada solo para Lorenz.')
            return

        sigma = self.sigma.value()
        rho = self.rho.value()
        beta = self.beta.value()
        x_min = self.basin_xmin.value()
        x_max = self.basin_xmax.value()
        y_min = self.basin_ymin.value()
        y_max = self.basin_ymax.value()
        z0_fixed = self.basin_z0.value()
        nx = self.basin_nx.value()
        ny = self.basin_ny.value()
        dt = self.basin_dt.value()
        T_total = self.basin_T_total.value()
        method_key = self.current_method_key()

        if dt <= 0 or T_total <= 0 or nx < 2 or ny < 2:
            QMessageBox.critical(self, 'Error', 'Parámetros inválidos para la cuenca.')
            return
        if x_max <= x_min or y_max <= y_min:
            QMessageBox.critical(self, 'Error', 'Los límites del plano deben ser crecientes.')
            return

        self.info_label.setText('Calculando cuenca con backend nativo en C...')
        QApplication.processEvents()
        try:
            basin = compute_basin_plane_z_lorenz_xiong(
                sigma,
                rho,
                beta,
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
                method_key=method_key,
            )
        except NativeChaosError as exc:
            QMessageBox.critical(self, 'Error de backend nativo', str(exc))
            return

        self.last_basin = basin
        self.last_basin_extent = [x_min, x_max, y_min, y_max]
        self.last_basin_rho = rho
        self.last_basin_z0 = z0_fixed
        self.update_equilibrium_info()
        self.refresh_basin_canvas()
        self.tabs.setCurrentWidget(self.tab_basin)
        self.info_label.setText(
            f"Cuenca calculada en C.\nResolución: {nx} x {ny}\nrho = {rho}, z0 = {z0_fixed}\nMétodo: {METHOD_REGISTRY[method_key]['label']}"
        )

    def refresh_basin_canvas(self):
        if self.last_basin is None or self.last_basin_extent is None:
            return
        self.canvas_basin.plot_basin(
            self.last_basin,
            self.last_basin_extent,
            self.last_basin_rho,
            self.last_basin_z0,
        )
    def _populate_spectrum_selector(self):
        self.spectrum_selector.blockSignals(True)
        self.spectrum_selector.clear()
        self.spectrum_selector.addItem('Todos', userData='all')
        for eq in self.last_equilibria:
            label = eq['name']
            if eq['name'] == 'E-':
                label = 'E- (mismo espectro que E+)'
            self.spectrum_selector.addItem(label, userData=eq['name'])
        idx = self.spectrum_selector.findData('O')
        if idx < 0:
            idx = 0
        self.spectrum_selector.setCurrentIndex(idx)
        self.spectrum_selector.blockSignals(False)

    def refresh_spectrum_canvas(self):
        selection = self.spectrum_selector.currentData() if hasattr(self, 'spectrum_selector') else 'all'
        self.canvas_spectrum.plot_spectrum(self.last_equilibria, selected_name=selection, title='Autovalores del Jacobiano en los equilibrios')
        if not self.last_equilibria:
            self.spectrum_info.setText('No hay datos espectrales para el sistema actual.')
            return
        if selection == 'all':
            self.spectrum_info.setText('Se muestran los espectros sin duplicar firmas repetidas. En el Lorenz clásico, E+ y E- comparten exactamente el mismo espectro por simetría; por eso la vista global no debe interpretarse como seis autovalores distintos de un mismo equilibrio.')
            return
        eq = next((item for item in self.last_equilibria if item['name'] == selection), None)
        if eq is None:
            self.spectrum_info.setText('')
            return
        eig_txt = ', '.join(self._format_complex(v) for v in eq.get('eigvals', []))
        if eq['name'] == 'O':
            extra = ' En el origen se observan tres autovalores reales.'
        else:
            extra = ' En este equilibrio aparece un autovalor real y un par complejo conjugado; E+ y E- comparten el mismo espectro.'
        self.spectrum_info.setText(
            f"{eq['name']}: λ = [{eig_txt}] | tipo local: {eq.get('local_type','')} | clasificación: {eq.get('classification','')}.{extra}"
        )

    def update_equilibrium_info(self):
        if self.current_system_key() != 'lorenz':
            self.last_equilibria = []
            self.eq_values_label.setText('Los equilibrios analíticos todavía están conectados solo al sistema de Lorenz.')
            self.canvas_spectrum.reset_plot()
            self.spectrum_info.setText('')
            self.refresh_basin_canvas()
            return

        sigma = self.sigma.value()
        rho = self.rho.value()
        beta = self.beta.value()
        self.last_equilibria = lorenz_equilibria(sigma, rho, beta)
        self.eq_values_label.setText(self._format_equilibrium_values(self.last_equilibria))
        self._populate_spectrum_selector()
        self.refresh_spectrum_canvas()
        self.refresh_basin_canvas()

    def _format_equilibrium_values(self, equilibria):
        lines = []
        for eq in equilibria:
            point = eq['point']
            lines.append(f"{eq['name']} = ({point[0]:.6g}, {point[1]:.6g}, {point[2]:.6g})")
        return '\n'.join(lines)

    def _format_complex(self, value, tol=1e-10):
        real = float(np.real(value))
        imag = float(np.imag(value))
        if abs(imag) < tol:
            return f'{real:.6g}'
        sign = '+' if imag >= 0 else '-'
        return f'{real:.6g}{sign}{abs(imag):.6g}j'
