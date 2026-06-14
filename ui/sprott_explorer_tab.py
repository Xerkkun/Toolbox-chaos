from __future__ import annotations

import html
import json
import os
import re
import tempfile
from pathlib import Path
from time import perf_counter

import numpy as np

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = os.environ.get('QT_QPA_PLATFORM', '').lower() != 'offscreen'
except Exception:
    QWebEngineView = None
    WEBENGINE_AVAILABLE = False

try:
    from PyQt6.QtPdf import QPdfDocument
    from PyQt6.QtPdfWidgets import QPdfView
    QT_PDF_AVAILABLE = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    QT_PDF_AVAILABLE = False

from core.sprott import decode_code, describe_family
from core.sprott.catalog import favorites_path, load_favorites, load_synthetic_examples, save_favorite
from core.sprott.gallery import build_metadata, gallery_root, list_gallery_entries, save_gallery_entry
from core.sprott.references import index_local_reference_folder, read_dic_entries
from core.sprott.search import classify_candidate, generate_random_code, quick_lyapunov_estimate, simulate_candidate
from core.sprott.visual import (
    BACKGROUNDS,
    COLOR_MODES,
    DRAW_MODES,
    PALETTES,
    PROJECTIONS,
    VISUAL_PRESETS,
    SprottVisualConfig,
    trajectory_stats,
    visual_preset,
    visual_recommendation,
)
from ui.math_render import render_math_to_path
from ui.sprott_canvases import Sprott2DCanvas
from ui.widgets import make_help_label


EXPLORATION_HELP = {
    'kind': '<b>Tipo</b><br>Mapa: regla discreta x(n+1)=F(x(n)). Flujo: EDO dx/dt=F(x) integrada numericamente.',
    'dimension': '<b>Dimension</b><br>Numero de variables del sistema. En mapas puede ser 1-4; en flujos Sprott iniciales se usa 3 o 4.',
    'order': '<b>Orden</b><br>Grado maximo del polinomio. Orden 2 es cuadratico; ordenes altos tienen mas coeficientes y son mas costosos.',
    'iterations': '<b>Iteraciones/pasos</b><br>Cuantos pasos se calculan. Mas pasos revelan mejor la estructura, pero tardan mas.',
    'transient': '<b>Transitorio</b><br>Puntos iniciales descartados. Sirve para no graficar el arranque antes de que la orbita llegue a su comportamiento tipico.',
    'divergence': '<b>Tolerancia de divergencia</b><br>Si la norma del estado supera este valor, la simulacion se marca como divergente y se detiene.',
    'seed': '<b>Semilla</b><br>Controla la generacion aleatoria. Misma semilla produce el mismo codigo.',
    'h': '<b>Paso h</b><br>Paso temporal para flujos. Mapas ignoran este valor. h pequeno es mas estable pero requiere mas pasos.',
    'method': '<b>Metodo de flujo</b><br>Euler es historico y rapido; RK4 es una extension moderna mas estable para docencia.',
    'code': '<b>Codigo</b><br>Primera letra: familia. Las demas letras codifican coeficientes. Puedes pegar un codigo o generarlo.',
}


BUTTON_HELP = {
    'generate': 'Crea un codigo sintetico aleatorio con los controles de tipo, dimension, orden y semilla.',
    'simulate': 'Decodifica el codigo, simula la trayectoria en C, descarta el transitorio, clasifica y grafica.',
    'search': 'Prueba varios codigos sinteticos y conserva el primer candidato acotado no colapsado. No es prueba de caos.',
    'pause': 'Reservado para una busqueda futura en segundo plano con QThread.',
    'decode': 'Traduce el codigo a familia, numero de coeficientes y ecuaciones polinomiales.',
}


class SprottExplorerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.assets_dir = Path(__file__).resolve().parents[1] / 'assets' / 'sprott'
        self.repo_root = Path(__file__).resolve().parents[1]
        self.examples = []
        self.local_dic_entries = []
        self.local_dic_visible_entries = []
        self.gallery_entries = []
        self.search_attempts = []
        self.last_result = None
        self.last_classification = None
        self.last_source = 'manual'
        self.last_local_entry = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.sections = QTabWidget()
        layout.addWidget(self.sections)

        self._build_home_tab()
        self._build_theory_tab()
        self._build_codes_tab()
        self._build_exploration_tab()
        self._build_examples_tab()
        self._build_tutorial_tab()
        self._build_gallery_tab()
        self._build_importer_tab()

    def _read_asset(self, name: str, fallback: str = '') -> str:
        path = self.assets_dir / name
        if not path.exists():
            return fallback
        return path.read_text(encoding='utf-8')

    def _markdown_browser(self, markdown: str) -> QTextBrowser:
        html_doc = _markdown_to_clean_html(markdown, webengine=WEBENGINE_AVAILABLE, asset_root=self.assets_dir)
        if WEBENGINE_AVAILABLE:
            browser = QWebEngineView()
            browser.setHtml(html_doc, QUrl.fromLocalFile(str(self.repo_root / 'assets' / 'sprott' / 'index.html')))
            return browser
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(html_doc)
        return browser

    def _build_home_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = (
            '# Explorador Sprott\n\n'
            'Esta seccion explora una idea central del software historico de Julien C. Sprott: '
            'representar ecuaciones con codigos compactos, simular muchas variantes y filtrar '
            'trayectorias interesantes.\n\n'
            'Flujo de trabajo recomendado:\n\n'
            '1. Abre **Ejemplos** y simula un ejemplo sintetico.\n'
            '2. Mira **Codigos** para ver como el texto se convierte en ecuaciones.\n'
            '3. En **Exploracion**, genera codigos nuevos y observa si divergen, colapsan o quedan como candidatos.\n\n'
            '**Importante:** candidato caotico aqui significa acotado y no colapsado bajo filtros rapidos. '
            'No es una certificacion matematica final. Si quieres una figura interesante sin tocar parametros, '
            've a **Ejemplos**, selecciona un codigo local de `SELECTED.DIC` y pulsa **Simular codigo local**.\n\n'
            + self._read_asset('attribution.md')
        )
        layout.addWidget(self._markdown_browser(text))
        self.sections.addTab(widget, 'Inicio')

    def _build_theory_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self._theory_page_browser())
        self.sections.addTab(widget, 'Teoria')

    def _build_codes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_box = QGroupBox('Decodificador educativo')
        form = QFormLayout(form_box)
        self.code_edit = QLineEdit('EWMWAMMMPMMMM')
        self.code_edit.setToolTip(EXPLORATION_HELP['code'])
        self.decode_button = QPushButton('Decodificar')
        self.decode_button.setToolTip(BUTTON_HELP['decode'])
        self.decode_button.clicked.connect(self.decode_current_code)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.code_edit)
        row_layout.addWidget(self.decode_button)
        form.addRow(make_help_label('Codigo tipo Sprott', EXPLORATION_HELP['code']), row)
        layout.addWidget(form_box, stretch=0)

        self.decode_output = QTextEdit()
        self.decode_output.setReadOnly(True)
        self.decode_output.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        layout.addWidget(self.decode_output, stretch=1)
        self.sections.addTab(widget, 'Codigos')
        self.decode_current_code()

    def _build_exploration_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        guide = QLabel(
            'Uso recomendado: 1) carga un ejemplo local desde SELECTED.DIC en la pestana Ejemplos, '
            '2) pulsa Simular codigo local, 3) vuelve aqui para ajustar iteraciones/transitorio si quieres mas detalle. '
            'Generar codigo es didactico; los codigos locales del libro suelen producir figuras mas interesantes.'
        )
        guide.setWordWrap(True)
        guide.setStyleSheet('font-weight: bold; padding: 4px;')
        layout.addWidget(guide, 0, 0, 1, 2)

        controls = QGroupBox('Controles con ayuda')
        form = QFormLayout(controls)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem('Mapa 2D rapido (recomendado)', userData=('map', 2, 2, 900, 150, 0.01, 'rk4'))
        self.preset_combo.addItem('Mapa 1D didactico', userData=('map', 1, 2, 700, 100, 0.01, 'rk4'))
        self.preset_combo.addItem('Flujo 3D RK4 corto', userData=('flow', 3, 2, 1600, 250, 0.01, 'rk4'))
        self.preset_combo.addItem('Flujo 3D Euler historico', userData=('flow', 3, 2, 1200, 200, 0.1, 'euler'))
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        self.preset_combo.setToolTip('Ajusta varios controles a una configuracion razonable para aprender sin esperar demasiado.')

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(['map', 'flow'])
        self.kind_combo.setToolTip(EXPLORATION_HELP['kind'])
        self.kind_combo.currentTextChanged.connect(self._sync_dimension_for_kind)
        self.dimension_combo = QComboBox()
        for value in (1, 2, 3, 4):
            self.dimension_combo.addItem(str(value), userData=value)
        self.dimension_combo.setToolTip(EXPLORATION_HELP['dimension'])
        self.order_combo = QComboBox()
        for value in (2, 3, 4, 5):
            self.order_combo.addItem(str(value), userData=value)
        self.order_combo.setToolTip(EXPLORATION_HELP['order'])
        self.iter_spin = _int_spin(900, 10, 200000, EXPLORATION_HELP['iterations'])
        self.transient_spin = _int_spin(150, 0, 100000, EXPLORATION_HELP['transient'])
        self.divergence_spin = _double_spin(1e6, 1.0, 1e12, 2, EXPLORATION_HELP['divergence'])
        self.seed_spin = _int_spin(1, 0, 2_147_483_647, EXPLORATION_HELP['seed'])
        self.max_attempts_spin = _int_spin(24, 1, 500, 'Intentos maximos de busqueda en esta corrida.')
        self.h_spin = _double_spin(0.01, 1e-5, 1.0, 5, EXPLORATION_HELP['h'])
        self.method_combo = QComboBox()
        self.method_combo.addItems(['rk4', 'euler'])
        self.method_combo.setToolTip(EXPLORATION_HELP['method'])
        self.criteria_combo = QComboBox()
        self.criteria_combo.addItems(['candidate_chaotic', 'acotado', 'cualquier no divergente'])
        self.criteria_combo.setToolTip('Criterio minimo para detener busqueda. Lyapunov completo queda para una fase posterior.')
        self.explore_code_edit = QLineEdit('EWMWAMMMPMMMM')
        self.explore_code_edit.setToolTip(EXPLORATION_HELP['code'])

        form.addRow(make_help_label('Preset', 'Configuraciones iniciales para aprender rapido.'), self.preset_combo)
        form.addRow(make_help_label('Tipo', EXPLORATION_HELP['kind']), self.kind_combo)
        form.addRow(make_help_label('Dimension', EXPLORATION_HELP['dimension']), self.dimension_combo)
        form.addRow(make_help_label('Orden', EXPLORATION_HELP['order']), self.order_combo)
        form.addRow(make_help_label('Iteraciones/pasos', EXPLORATION_HELP['iterations']), self.iter_spin)
        form.addRow(make_help_label('Transitorio', EXPLORATION_HELP['transient']), self.transient_spin)
        form.addRow(make_help_label('Tolerancia divergencia', EXPLORATION_HELP['divergence']), self.divergence_spin)
        form.addRow(make_help_label('Semilla aleatoria', EXPLORATION_HELP['seed']), self.seed_spin)
        form.addRow(make_help_label('Intentos maximos', 'Limite de codigos probados por Buscar candidato.'), self.max_attempts_spin)
        form.addRow(make_help_label('Criterio minimo', 'Estado minimo aceptado para detener la busqueda.'), self.criteria_combo)
        form.addRow(make_help_label('Paso h', EXPLORATION_HELP['h']), self.h_spin)
        form.addRow(make_help_label('Metodo flujo', EXPLORATION_HELP['method']), self.method_combo)
        form.addRow(make_help_label('Codigo', EXPLORATION_HELP['code']), self.explore_code_edit)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.generate_button = QPushButton('Generar codigo')
        self.simulate_button = QPushButton('Simular y graficar')
        self.search_button = QPushButton('Buscar candidato')
        self.pause_button = QPushButton('Pausar busqueda')
        self.pause_button.setEnabled(False)
        for key, button in (
            ('generate', self.generate_button),
            ('simulate', self.simulate_button),
            ('search', self.search_button),
            ('pause', self.pause_button),
        ):
            button.setToolTip(BUTTON_HELP[key])
            button_layout.addWidget(button)
        self.generate_button.clicked.connect(self.generate_code)
        self.simulate_button.clicked.connect(self.simulate_exploration_code)
        self.search_button.clicked.connect(self.search_candidate)
        form.addRow(button_row)

        style_box = QGroupBox('Estilo visual')
        style_form = QFormLayout(style_box)
        self.visual_preset_combo = QComboBox()
        self.visual_preset_combo.addItems(list(VISUAL_PRESETS.keys()))
        self.visual_preset_combo.currentTextChanged.connect(self.apply_visual_preset)
        self.projection_combo = QComboBox()
        self.projection_combo.addItems(PROJECTIONS + ['esfera (pendiente)'])
        self.projection_combo.setToolTip('Selecciona que variables se proyectan o si se dibuja 3D x-y-z.')
        self.color_by_combo = QComboBox()
        self.color_by_combo.addItems(COLOR_MODES)
        self.color_by_combo.setToolTip('Variable usada para colorear puntos. En dimension baja se reutiliza la variable disponible.')
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(PALETTES)
        self.background_combo = QComboBox()
        self.background_combo.addItems(BACKGROUNDS)
        self.draw_mode_combo = QComboBox()
        self.draw_mode_combo.addItems(DRAW_MODES)
        self.point_size_spin = _double_spin(0.7, 0.05, 50.0, 2, 'Tamano del punto en la figura.')
        self.alpha_spin = _double_spin(0.75, 0.02, 1.0, 2, 'Opacidad de puntos o linea.')
        self.max_plot_points_spin = _int_spin(20000, 64, 300000, 'Maximo de puntos graficados tras el transitorio.')
        self.band_count_spin = _int_spin(0, 0, 64, '0 usa color continuo; valores como 12 o 16 producen bandas.')
        self.export_dpi_spin = _int_spin(220, 72, 600, 'Resolucion de exportacion para PNG/PDF.')
        self.axes_check = QCheckBox('Mostrar ejes')
        self.grid_check = QCheckBox('Mostrar grid')
        self.equal_aspect_check = QCheckBox('Aspect ratio igual')
        self.apply_style_button = QPushButton('Aplicar estilo')
        self.export_image_button = QPushButton('Exportar imagen actual')
        self.export_json_button = QPushButton('Exportar metadatos JSON')
        self.export_csv_button = QPushButton('Exportar datos CSV')
        self.copy_code_button = QPushButton('Copiar codigo')
        self.copy_citation_button = QPushButton('Copiar cita')
        for button in (self.apply_style_button, self.export_image_button, self.export_json_button, self.export_csv_button, self.copy_code_button, self.copy_citation_button):
            button.setToolTip('Accion sobre la simulacion y estilo visual actuales.')
        self.apply_style_button.clicked.connect(self.apply_current_style)
        self.export_image_button.clicked.connect(self.export_current_image)
        self.export_json_button.clicked.connect(self.export_current_metadata)
        self.export_csv_button.clicked.connect(self.export_current_csv)
        self.copy_code_button.clicked.connect(self.copy_current_code)
        self.copy_citation_button.clicked.connect(self.copy_sprott_citation)

        style_form.addRow(make_help_label('Preset visual', 'Estilos inspirados por el flujo visual del libro, generados desde datos propios.'), self.visual_preset_combo)
        style_form.addRow(make_help_label('Proyeccion', 'Proyeccion 2D o 3D. Esfera queda marcada como pendiente.'), self.projection_combo)
        style_form.addRow(make_help_label('Color por', 'Constante, tiempo, variable, radio o diferencia entre iterados.'), self.color_by_combo)
        style_form.addRow(make_help_label('Paleta', 'Mapa de colores para puntos con color variable.'), self.palette_combo)
        style_form.addRow(make_help_label('Fondo', 'Color de fondo de la figura y exportacion.'), self.background_combo)
        style_form.addRow(make_help_label('Modo dibujo', 'Puntos, linea, linea+puntos o densidad/heatmap.'), self.draw_mode_combo)
        style_form.addRow(make_help_label('Tamano punto', 'Punto pequeno ayuda en alta densidad.'), self.point_size_spin)
        style_form.addRow(make_help_label('Opacidad', 'Alpha bajo revela densidad en nubes de muchos puntos.'), self.alpha_spin)
        style_form.addRow(make_help_label('Max puntos', 'Submuestreo visual. No cambia los datos simulados.'), self.max_plot_points_spin)
        style_form.addRow(make_help_label('Bandas', 'Cuantiza el color para estilos por franjas.'), self.band_count_spin)
        style_form.addRow(make_help_label('DPI export', 'Resolucion para PNG/PDF exportado.'), self.export_dpi_spin)
        style_toggles = QWidget()
        toggles_layout = QHBoxLayout(style_toggles)
        toggles_layout.setContentsMargins(0, 0, 0, 0)
        toggles_layout.addWidget(self.axes_check)
        toggles_layout.addWidget(self.grid_check)
        toggles_layout.addWidget(self.equal_aspect_check)
        style_form.addRow(style_toggles)
        style_buttons = QWidget()
        style_buttons_layout = QHBoxLayout(style_buttons)
        style_buttons_layout.setContentsMargins(0, 0, 0, 0)
        for button in (self.apply_style_button, self.export_image_button, self.export_json_button, self.export_csv_button):
            style_buttons_layout.addWidget(button)
        style_form.addRow(style_buttons)
        copy_buttons = QWidget()
        copy_buttons_layout = QHBoxLayout(copy_buttons)
        copy_buttons_layout.setContentsMargins(0, 0, 0, 0)
        copy_buttons_layout.addWidget(self.copy_code_button)
        copy_buttons_layout.addWidget(self.copy_citation_button)
        style_form.addRow(copy_buttons)

        layout.addWidget(controls, 1, 0)
        layout.addWidget(style_box, 2, 0)
        self.sprott_canvas = Sprott2DCanvas(widget)
        layout.addWidget(self.sprott_canvas, 1, 1, 2, 1)

        self.explore_output = QTextEdit()
        self.explore_output.setReadOnly(True)
        self.explore_output.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        layout.addWidget(self.explore_output, 3, 0)
        self.search_attempt_table = QTableWidget(0, 7)
        self.search_attempt_table.setHorizontalHeaderLabels(['Intento', 'Codigo', 'Estado', 'Razon', 'Rango x', 'Rango y', 'Lyap rapido'])
        self.search_attempt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.search_attempt_table.cellDoubleClicked.connect(self.simulate_attempt_row)
        layout.addWidget(self.search_attempt_table, 3, 1)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 3)
        layout.setRowStretch(3, 1)
        self.sections.addTab(widget, 'Exploracion')
        self.apply_preset()
        self.apply_visual_preset(self.visual_preset_combo.currentText())

    def _build_examples_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        intro = QLabel(
            'Empieza por un ejemplo sintetico para aprender el flujo. Si tienes los diccionarios del libro descargados, '
            'carga un .DIC local: se usa desde tu disco y no se copia al repositorio.'
        )
        intro.setWordWrap(True)
        intro.setStyleSheet('font-weight: bold; padding: 4px;')
        layout.addWidget(intro, 0, 0, 1, 2)

        synthetic_box = QGroupBox('Ejemplos sinteticos publicos')
        synthetic_layout = QVBoxLayout(synthetic_box)
        self.examples_list = QListWidget()
        self.examples_list.setToolTip('Ejemplos sinteticos creados para esta toolbox. No vienen de diccionarios historicos.')
        self.examples_list.currentRowChanged.connect(self.show_selected_example)
        synthetic_layout.addWidget(self.examples_list, stretch=1)
        self.example_detail = QTextEdit()
        self.example_detail.setReadOnly(True)
        self.example_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        self.example_sim_button = QPushButton('Simular ejemplo sintetico')
        self.example_sim_button.setToolTip('Carga el codigo del ejemplo, ajusta iteraciones/transitorio y ejecuta la simulacion en C.')
        self.example_sim_button.clicked.connect(self.simulate_selected_example)
        synthetic_layout.addWidget(self.example_detail, stretch=1)
        synthetic_layout.addWidget(self.example_sim_button, stretch=0)
        layout.addWidget(synthetic_box, 1, 0)

        local_box = QGroupBox('Ejemplos del libro desde .DIC local')
        local_layout = QVBoxLayout(local_box)
        local_note = QLabel(
            'Si tienes la descarga local de Sprott, esta lista lee SELECTED.DIC/BOOKFIGS.DIC desde external/. '
            'Selecciona una linea y pulsa el boton inferior. La toolbox no copia estos archivos al repositorio.'
        )
        local_note.setWordWrap(True)
        local_layout.addWidget(local_note)
        quick_row = QWidget()
        quick_layout = QHBoxLayout(quick_row)
        quick_layout.setContentsMargins(0, 0, 0, 0)
        self.local_dic_quick_combo = QComboBox()
        self.local_dic_quick_combo.addItem('Autodetectar SELECTED.DIC', userData='SELECTED.DIC')
        self.local_dic_quick_combo.addItem('BOOKFIGS.DIC', userData='BOOKFIGS.DIC')
        self.local_dic_quick_combo.addItem('SPECIAL.DIC', userData='SPECIAL.DIC')
        self.local_dic_quick_combo.addItem('Archivo manual', userData='')
        self.local_dic_quick_combo.currentIndexChanged.connect(self.apply_dic_quick_selector)
        self.local_dic_filter_combo = QComboBox()
        self.local_dic_filter_combo.addItems([
            'todos',
            'solo simulables',
            'mapas 2D',
            'mapas 3D',
            'mapas 4D',
            'flujos 3D',
            'flujos 4D',
            'familias especiales',
            'L positivo',
            'F alta',
        ])
        self.local_dic_filter_combo.currentIndexChanged.connect(self.apply_local_dic_filter)
        quick_layout.addWidget(QLabel('Diccionario'))
        quick_layout.addWidget(self.local_dic_quick_combo, stretch=1)
        quick_layout.addWidget(QLabel('Filtro'))
        quick_layout.addWidget(self.local_dic_filter_combo, stretch=1)
        local_layout.addWidget(quick_row)
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        default_dic = self._find_local_dic('SELECTED.DIC')
        self.local_dic_path_edit = QLineEdit(str(default_dic) if default_dic.exists() else '')
        self.local_dic_path_edit.setToolTip('Ruta a BOOKFIGS.DIC, SELECTED.DIC o SPECIAL.DIC descargado localmente. No se redistribuye.')
        browse_dic = QPushButton('Elegir .DIC')
        browse_dic.setToolTip('Selecciona un diccionario local del libro. La app solo lo lee desde tu disco.')
        browse_dic.clicked.connect(self.browse_local_dic)
        load_dic = QPushButton('Cargar codigos')
        load_dic.setToolTip('Lee codigos del .DIC local y los lista como referencias externas locales.')
        load_dic.clicked.connect(lambda: self.load_local_dic_examples())
        path_layout.addWidget(self.local_dic_path_edit, stretch=1)
        path_layout.addWidget(browse_dic)
        path_layout.addWidget(load_dic)
        local_layout.addWidget(path_row)
        self.local_dic_table = QTableWidget(0, 8)
        self.local_dic_table.setHorizontalHeaderLabels(['Linea', 'Codigo', 'Familia', 'Dim', 'Orden', 'F', 'L', 'Soporte'])
        self.local_dic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.local_dic_table.setToolTip('Codigos leidos desde tu archivo .DIC local. No son assets publicos del repositorio.')
        self.local_dic_table.currentCellChanged.connect(lambda row, _col, _prev_row, _prev_col: self.show_selected_local_dic(row))
        self.local_dic_table.cellDoubleClicked.connect(lambda _row, _col: self.simulate_selected_local_dic())
        local_layout.addWidget(self.local_dic_table, stretch=1)
        self.local_dic_detail = QTextEdit()
        self.local_dic_detail.setReadOnly(True)
        self.local_dic_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        local_layout.addWidget(self.local_dic_detail, stretch=1)
        self.local_dic_sim_button = QPushButton('Simular codigo local seleccionado')
        self.local_dic_sim_button.setToolTip('Carga el codigo local en Exploracion y lo simula con el backend C si la familia A-X esta soportada.')
        self.local_dic_sim_button.clicked.connect(self.simulate_selected_local_dic)
        self.local_dic_style_button = QPushButton('Simular con estilo recomendado')
        self.local_dic_style_button.setToolTip('Carga el codigo local, ajusta parametros largos y aplica un preset visual segun dimension.')
        self.local_dic_style_button.clicked.connect(self.simulate_selected_local_dic_recommended)
        local_buttons = QWidget()
        local_buttons_layout = QHBoxLayout(local_buttons)
        local_buttons_layout.setContentsMargins(0, 0, 0, 0)
        local_buttons_layout.addWidget(self.local_dic_sim_button)
        local_buttons_layout.addWidget(self.local_dic_style_button)
        local_layout.addWidget(local_buttons)
        layout.addWidget(local_box, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

        self._load_examples()
        if self.local_dic_path_edit.text():
            self.load_local_dic_examples(limit=120)
        self.sections.addTab(widget, 'Ejemplos')

    def _build_tutorial_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        text = (
            '# Tutorial Sprott\n\n'
            '## 1. Ver una figura rapidamente\n'
            'Abre Ejemplos, carga `SELECTED.DIC`, filtra `solo simulables`, selecciona un codigo y pulsa '
            '**Simular con estilo recomendado**. Despues cambia `Color por` a `z` o `tiempo` y exporta.\n\n'
            '## 2. Entender un codigo\n'
            'Copia el codigo, abre Codigos, decodifica y compara familia, dimension, orden y ecuaciones con la trayectoria.\n\n'
            '## 3. Crear una imagen propia\n'
            'En Exploracion usa `map`, dimension 3, orden 2, genera un codigo, busca candidato, aumenta iteraciones '
            'y prueba color por `z`, `radio` o `tiempo`.\n\n'
            '## 4. Mejorar una imagen pobre\n'
            'Si parece una linea simple, aumenta iteraciones/transitorio o cambia proyeccion. Si diverge, reduce `h` '
            'en flujos o usa RK4. Si esta muy dispersa, baja tamano de punto y opacidad.\n\n'
            '## 5. Exportar y citar\n'
            'Exporta PNG/CSV/JSON o agrega la imagen a Galeria. Cita a Sprott y no redistribuyas archivos originales.'
        )
        layout.addWidget(self._markdown_browser(text), 0, 0, 1, 2)
        actions = QGroupBox('Acciones rapidas')
        action_layout = QVBoxLayout(actions)
        buttons = [
            ('Ir a Ejemplos', lambda: self.sections.setCurrentIndex(4)),
            ('Ir a Exploracion', lambda: self.sections.setCurrentIndex(3)),
            ('Preset Color por profundidad', lambda: self.visual_preset_combo.setCurrentText('Color por profundidad')),
            ('Preset Alta densidad', lambda: self.visual_preset_combo.setCurrentText('Alta densidad')),
            ('Preset Didactico', lambda: self.visual_preset_combo.setCurrentText('Didactico')),
            ('Copiar cita', self.copy_sprott_citation),
        ]
        for label, callback in buttons:
            button = QPushButton(label)
            button.clicked.connect(callback)
            action_layout.addWidget(button)
        action_layout.addStretch(1)
        layout.addWidget(actions, 0, 2)
        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(2, 0)
        self.sections.addTab(widget, 'Tutorial')

    def _build_gallery_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.favorite_note = QLineEdit()
        self.favorite_note.setPlaceholderText('Notas de la imagen generada')
        self.favorite_note.setToolTip('Texto libre para recordar por que guardaste esta imagen.')
        save_button = QPushButton('Agregar imagen actual a galeria local')
        save_button.setToolTip('Guarda render.png, thumbnail.png y metadata.json en tu carpeta de usuario.')
        save_button.clicked.connect(self.save_current_gallery_entry)
        refresh_button = QPushButton('Actualizar lista')
        refresh_button.setToolTip('Recarga la carpeta local de galeria.')
        refresh_button.clicked.connect(self.refresh_gallery)
        top_layout.addWidget(self.favorite_note, stretch=1)
        top_layout.addWidget(save_button)
        top_layout.addWidget(refresh_button)
        layout.addWidget(top, 0, 0, 1, 2)
        self.favorites_label = QLabel(f'Galeria local: {gallery_root()}')
        self.favorites_label.setWordWrap(True)
        layout.addWidget(self.favorites_label, 1, 0, 1, 2)
        self.favorites_list = QListWidget()
        self.favorites_list.currentRowChanged.connect(self.show_gallery_entry)
        layout.addWidget(self.favorites_list, 2, 0)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.gallery_detail = QTextEdit()
        self.gallery_detail.setReadOnly(True)
        self.gallery_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        right_layout.addWidget(self.gallery_detail, stretch=1)
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_open_button = QPushButton('Abrir')
        self.gallery_resim_button = QPushButton('Re-simular')
        self.gallery_edit_style_button = QPushButton('Editar estilo')
        self.gallery_export_button = QPushButton('Exportar')
        self.gallery_delete_button = QPushButton('Eliminar de galeria local')
        self.gallery_open_button.clicked.connect(self.open_selected_gallery_entry)
        self.gallery_resim_button.clicked.connect(self.resimulate_selected_gallery_entry)
        self.gallery_edit_style_button.clicked.connect(self.edit_style_from_gallery_entry)
        self.gallery_export_button.clicked.connect(self.export_selected_gallery_render)
        self.gallery_delete_button.clicked.connect(self.delete_selected_gallery_entry)
        for button in (self.gallery_open_button, self.gallery_resim_button, self.gallery_edit_style_button, self.gallery_export_button, self.gallery_delete_button):
            button_layout.addWidget(button)
        right_layout.addWidget(button_row, stretch=0)
        layout.addWidget(right, 2, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        self.refresh_gallery()
        self.sections.addTab(widget, 'Galeria')

    def _build_importer_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        controls = QWidget()
        row = QHBoxLayout(controls)
        row.setContentsMargins(0, 0, 0, 0)
        self.import_folder_edit = QLineEdit()
        self.import_folder_edit.setToolTip('Carpeta local donde tienes referencias descargadas por tu cuenta.')
        browse_button = QPushButton('Seleccionar carpeta')
        browse_button.setToolTip('Abre un selector de carpeta. No copia archivos al repositorio.')
        browse_button.clicked.connect(self.browse_import_folder)
        index_button = QPushButton('Indexar')
        index_button.setToolTip('Lista archivos reconocidos sin ejecutarlos ni modificarlos.')
        index_button.clicked.connect(self.index_import_folder)
        self.hash_check = QCheckBox('Calcular hash')
        self.hash_check.setToolTip('Calcula SHA-256. Es mas lento en carpetas grandes, pero ayuda a identificar archivos.')
        row.addWidget(self.import_folder_edit, stretch=1)
        row.addWidget(browse_button)
        row.addWidget(index_button)
        row.addWidget(self.hash_check)
        layout.addWidget(controls, stretch=0)

        note = QLabel('El importador solo inventaria referencias locales. No ejecuta EXE, no modifica originales y no copia archivos al repo.')
        note.setWordWrap(True)
        layout.addWidget(note, stretch=0)

        self.import_table = QTableWidget(0, 6)
        self.import_table.setHorizontalHeaderLabels(['Nombre', 'Ruta', 'Tipo', 'Tamano', 'Hash', 'Categoria'])
        self.import_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.import_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.import_table, stretch=1)
        self.sections.addTab(widget, 'Importador local')

    def _theory_page_browser(self):
        pdf_path = self.assets_dir / 'sprott_theory.pdf'
        if pdf_path.exists() and not QT_PDF_AVAILABLE:
            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            pdf_uri = QUrl.fromLocalFile(str(pdf_path)).toString()
            browser.setHtml(
                '<html><body style="font-family: Segoe UI, Arial, sans-serif; margin: 14px;">'
                '<h2>Teoria del Explorador Sprott</h2>'
                '<p>Esta pestana esta preparada como PDF compilado para mantener tipografia, '
                'ecuaciones y maquetacion estables. QtPdf no esta disponible en este entorno.</p>'
                f'<p><a href="{html.escape(pdf_uri)}">Abrir sprott_theory.pdf</a></p>'
                '</body></html>'
            )
            return browser
        if QT_PDF_AVAILABLE and pdf_path.exists():
            widget = QWidget()
            layout = QVBoxLayout(widget)
            note = QLabel('Esta pestana usa un PDF compilado para mantener tipografia, ecuaciones y maquetacion estables.')
            note.setWordWrap(True)
            note.setStyleSheet('font-weight: bold; padding: 4px;')
            layout.addWidget(note, stretch=0)
            open_button = QPushButton('Abrir PDF externo')
            open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path))))
            layout.addWidget(open_button, stretch=0)
            view = QPdfView(widget)
            document = QPdfDocument(view)
            view.setDocument(document)
            document.load(str(pdf_path))
            if hasattr(view, 'setZoomMode'):
                view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            if hasattr(view, 'setPageMode'):
                view.setPageMode(QPdfView.PageMode.MultiPage)
            view._sprott_pdf_document = document
            layout.addWidget(view, stretch=1)
            return widget
        text = self._read_asset('theory_intro.md') + '\n\n' + self._read_asset('code_grammar.md') + '\n\n' + self._read_asset('examples_readme.md')
        return self._markdown_browser(text)

    def _pdf_guide_or_browser(self):
        pdf_path = self.assets_dir / 'sprott_explorer_guide.pdf'
        if QT_PDF_AVAILABLE and pdf_path.exists():
            view = QPdfView(self)
            document = QPdfDocument(view)
            view.setDocument(document)
            document.load(str(pdf_path))
            if hasattr(view, 'setZoomMode'):
                view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            if hasattr(view, 'setPageMode'):
                view.setPageMode(QPdfView.PageMode.MultiPage)
            view._sprott_pdf_document = document
            return view
        text = self._read_asset('theory_intro.md') + '\n\n' + self._read_asset('code_grammar.md') + '\n\n' + self._read_asset('examples_readme.md')
        return self._markdown_browser(text)

    def apply_preset(self):
        data = self.preset_combo.currentData()
        if not data:
            return
        kind, dimension, order, iterations, transient, h, method = data
        self.kind_combo.setCurrentText(kind)
        self._set_combo_data(self.dimension_combo, dimension)
        self._set_combo_data(self.order_combo, order)
        self.iter_spin.setValue(iterations)
        self.transient_spin.setValue(transient)
        self.h_spin.setValue(h)
        self.method_combo.setCurrentText(method)

    def apply_visual_preset(self, name: str):
        config = visual_preset(name)
        self.projection_combo.setCurrentText(config.projection)
        self.color_by_combo.setCurrentText(config.color_by)
        self.palette_combo.setCurrentText(config.palette)
        self.background_combo.setCurrentText(config.background)
        self.draw_mode_combo.setCurrentText(config.draw_mode)
        self.point_size_spin.setValue(config.point_size)
        self.alpha_spin.setValue(config.alpha)
        self.max_plot_points_spin.setValue(config.max_points)
        self.band_count_spin.setValue(config.band_count)
        self.export_dpi_spin.setValue(config.export_dpi)
        self.axes_check.setChecked(config.show_axes)
        self.grid_check.setChecked(config.show_grid)
        self.equal_aspect_check.setChecked(config.equal_aspect)
        self.apply_current_style()

    def current_visual_config(self) -> SprottVisualConfig:
        projection = self.projection_combo.currentText()
        if projection.startswith('esfera'):
            projection = '3D x-y-z'
        return SprottVisualConfig(
            projection=projection,
            color_by=self.color_by_combo.currentText(),
            palette=self.palette_combo.currentText(),
            background=self.background_combo.currentText(),
            point_size=self.point_size_spin.value(),
            alpha=self.alpha_spin.value(),
            max_points=self.max_plot_points_spin.value(),
            show_axes=self.axes_check.isChecked(),
            show_grid=self.grid_check.isChecked(),
            equal_aspect=self.equal_aspect_check.isChecked(),
            draw_mode=self.draw_mode_combo.currentText(),
            export_dpi=self.export_dpi_spin.value(),
            band_count=self.band_count_spin.value(),
        )

    def apply_current_style(self):
        if self.last_result:
            self._plot_result(self.last_result)

    def current_simulation_metadata(self) -> dict:
        return {
            'iterations': self.iter_spin.value(),
            'transient': self.transient_spin.value(),
            'h': self.h_spin.value(),
            'method': self.method_combo.currentText(),
            'divergence_threshold': self.divergence_spin.value(),
        }

    def _sync_dimension_for_kind(self):
        if self.kind_combo.currentText() == 'flow' and self.dimension_combo.currentData() not in {3, 4}:
            self._set_combo_data(self.dimension_combo, 3)

    @staticmethod
    def _set_combo_data(combo: QComboBox, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def decode_current_code(self):
        code = decode_code(self.code_edit.text())
        family = describe_family(code.family_letter)
        lines = [
            'LECTURA DEL CODIGO',
            f'  codigo original: {code.raw}',
            f'  familia: {code.family_letter} -> {code.family_name}',
            f'  tipo: {code.kind}',
            f'  dimension: {code.dimension}',
            f'  orden polinomial: {code.order}',
            f'  coeficientes esperados: {family["coefficient_count"]}',
            f'  coeficientes leidos: {len(code.coefficients)}',
            '',
            'INTERPRETACION',
            '  La primera letra escoge la familia. Las letras restantes son numeros.',
            '  M significa 0.0; letras antes de M son negativas; letras despues de M son positivas.',
            '',
            'COEFICIENTES',
        ]
        lines.extend(f'  c{idx:03d} = {value:.6g}' for idx, value in enumerate(code.coefficients))
        try:
            result = simulate_candidate(code.raw, n_iter=1, transient=0)
            lines.extend(['', 'ECUACIONES RECONSTRUIDAS', result['equations']])
        except Exception as exc:
            lines.extend(['', f'ECUACIONES: no disponibles ({exc})'])
        if code.warnings:
            lines.extend(['', 'ADVERTENCIAS'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.decode_output.setPlainText('\n'.join(lines))

    def generate_code(self):
        rng = np.random.default_rng(self.seed_spin.value())
        try:
            code = generate_random_code(
                self.kind_combo.currentText(),
                self.dimension_combo.currentData(),
                self.order_combo.currentData(),
                rng,
            )
        except ValueError as exc:
            QMessageBox.warning(self, 'Familia no soportada', str(exc))
            return
        self.explore_code_edit.setText(code)
        self.code_edit.setText(code)
        self.last_source = 'manual'
        self.last_local_entry = None
        self.decode_current_code()
        self.explore_output.setPlainText('Codigo generado. Pulsa "Simular y graficar" para ver su trayectoria.')

    def simulate_exploration_code(self):
        code = self.explore_code_edit.text().strip()
        if not code:
            self.generate_code()
            code = self.explore_code_edit.text().strip()
        if not (self.last_local_entry and self.last_local_entry.get('code') == code) and self.last_source not in {'random_search', 'synthetic'}:
            self.last_source = 'manual'
            self.last_local_entry = None
        started = perf_counter()
        try:
            self.last_result = simulate_candidate(
                code,
                n_iter=self.iter_spin.value(),
                transient=self.transient_spin.value(),
                h=self.h_spin.value(),
                method=self.method_combo.currentText(),
                divergence_threshold=self.divergence_spin.value(),
                backend='c',
            )
            self.last_classification = classify_candidate(
                self.last_result['post_transient'],
                divergence_threshold=self.divergence_spin.value(),
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error de simulacion Sprott', str(exc))
            return
        elapsed_ms = 1000.0 * (perf_counter() - started)
        self._plot_result(self.last_result)
        self._show_result_summary(self.last_result, self.last_classification, elapsed_ms)
        self.code_edit.setText(code)
        self.decode_current_code()

    def search_candidate(self):
        rng = np.random.default_rng(self.seed_spin.value())
        started = perf_counter()
        last = None
        max_attempts = self.max_attempts_spin.value()
        local_codes = []
        local_sources = []
        if self.local_dic_entries:
            current = max(0, self._current_local_dic_row())
            visible = self.local_dic_visible_entries or self.local_dic_entries
            ordered = visible[current:] + visible[:current]
            local_codes = [entry['code'] for entry in ordered[:max_attempts]]
            local_sources = ordered[:max_attempts]
        self.search_attempts = []
        self.search_attempt_table.setRowCount(0)
        for attempt in range(1, max_attempts + 1):
            if attempt <= len(local_codes):
                code = local_codes[attempt - 1]
                source = 'local_dic'
                local_entry = local_sources[attempt - 1]
            else:
                code = generate_random_code(
                    self.kind_combo.currentText(),
                    self.dimension_combo.currentData(),
                    self.order_combo.currentData(),
                    rng,
                )
                source = 'random_search'
                local_entry = None
            result = simulate_candidate(
                code,
                n_iter=self.iter_spin.value(),
                transient=self.transient_spin.value(),
                h=self.h_spin.value(),
                method=self.method_combo.currentText(),
                divergence_threshold=self.divergence_spin.value(),
                backend='c',
            )
            classification = classify_candidate(result['post_transient'], divergence_threshold=self.divergence_spin.value())
            self._record_search_attempt(attempt, code, result, classification)
            last = (attempt, code, result, classification)
            if self._criteria_met(classification):
                self.last_source = source
                self.last_local_entry = local_entry
                break
        if last is None:
            return
        attempt, code, result, classification = last
        self.explore_code_edit.setText(code)
        self.code_edit.setText(code)
        self.last_result = result
        self.last_classification = classification
        if not self._criteria_met(classification):
            self.last_source = 'random_search'
            self.last_local_entry = None
        elapsed_ms = 1000.0 * (perf_counter() - started)
        self._plot_result(result)
        self._show_result_summary(result, classification, elapsed_ms, attempts=attempt)
        self.decode_current_code()

    def _criteria_met(self, classification: dict) -> bool:
        state = classification.get('state')
        criterion = self.criteria_combo.currentText()
        if criterion == 'candidate_chaotic':
            return state == 'candidate_chaotic'
        if criterion == 'acotado':
            return state in {'candidate_chaotic', 'periodic_or_low_complexity', 'fixed_point', 'unknown'}
        return state != 'divergent'

    def _record_search_attempt(self, attempt: int, code: str, result: dict, classification: dict):
        stats = trajectory_stats(result['post_transient'])
        ranges = stats.get('ranges', [])
        lyap = ''
        if classification.get('state') == 'candidate_chaotic':
            try:
                lyap = f'{quick_lyapunov_estimate(code, steps=350):.4g}'
            except Exception:
                lyap = ''
        record = {
            'attempt': attempt,
            'code': code,
            'state': classification.get('state', ''),
            'reason': classification.get('reason', ''),
            'range_x': _range_text(ranges, 0),
            'range_y': _range_text(ranges, 1),
            'lyapunov': lyap,
        }
        self.search_attempts.append(record)
        row = self.search_attempt_table.rowCount()
        self.search_attempt_table.insertRow(row)
        for col, value in enumerate([attempt, code, record['state'], record['reason'], record['range_x'], record['range_y'], lyap]):
            item = QTableWidgetItem(str(value))
            if col in {1, 3}:
                item.setToolTip(str(value))
            self.search_attempt_table.setItem(row, col, item)

    def simulate_attempt_row(self, row: int, _col: int):
        if row < 0 or row >= len(self.search_attempts):
            return
        self.explore_code_edit.setText(self.search_attempts[row]['code'])
        self.last_source = 'random_search'
        self.last_local_entry = None
        self.simulate_exploration_code()

    def _plot_result(self, result: dict):
        trajectory = np.asarray(result['post_transient'], dtype=float)
        title = f"Trayectoria post-transitorio - {result['code'].family_letter}"
        self.sprott_canvas.plot_trajectory(trajectory, self.current_visual_config(), title=title)

    def _show_result_summary(self, result: dict, classification: dict, elapsed_ms: float, attempts: int | None = None):
        code = result['code']
        stats = trajectory_stats(result['post_transient'])
        finite_count = int(stats.get('finite_count', 0))
        ranges = stats.get('ranges', [])
        means = stats.get('means', [])
        stds = stats.get('stds', [])
        discarded = int(max(0, len(result.get('trajectory', [])) - len(result.get('post_transient', []))))
        discarded_pct = 100.0 * discarded / max(1, len(result.get('trajectory', [])))
        meaning = {
            'divergent': 'La orbita escapo o produjo valores no finitos.',
            'fixed_point': 'La orbita parece terminar en un punto fijo.',
            'periodic_or_low_complexity': 'La cola parece repetitiva o de baja complejidad.',
            'candidate_chaotic': 'La orbita quedo acotada y no colapso; requiere Lyapunov/espectro/dimension.',
            'unknown': 'No hay evidencia suficiente con esta simulacion corta.',
        }.get(classification['state'], 'Estado no documentado.')
        lines = [
            'RESULTADO DE EXPLORACION',
            f'  codigo: {code.raw}',
            f'  familia: {code.family_name}',
            f'  backend: {result.get("backend", "python").upper()}',
            f'  tiempo de calculo: {elapsed_ms:.1f} ms',
        ]
        if attempts is not None:
            lines.append(f'  intentos de busqueda: {attempts}')
        lines.extend([
            f'  estado: {classification["state"]}',
            f'  lectura: {meaning}',
            f'  razon tecnica: {classification["reason"]}',
            f'  muestras post-transitorio finitas: {finite_count}',
            f'  porcentaje descartado por transitorio: {discarded_pct:.1f}%',
            f'  recomendacion visual: {visual_recommendation(result["post_transient"], classification)}',
            '',
            'RANGOS Y MOMENTOS',
        ])
        names = ['x', 'y', 'z', 'w']
        for idx, (lo, hi) in enumerate(ranges):
            name = names[idx] if idx < len(names) else f'x{idx}'
            mean = means[idx] if idx < len(means) else float('nan')
            std = stds[idx] if idx < len(stds) else float('nan')
            lines.append(f'  {name}: rango=[{lo:.6g}, {hi:.6g}], media={mean:.6g}, std={std:.6g}')
        lines.extend([
            '',
            'QUE ESTAS VIENDO',
            '  La grafica muestra la orbita despues de descartar el transitorio.',
            f'  Proyeccion actual: {self.current_visual_config().projection}; color por: {self.current_visual_config().color_by}.',
            '',
            'ECUACIONES',
            result['equations'],
        ])
        if code.warnings:
            lines.extend(['', 'ADVERTENCIAS'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.explore_output.setPlainText('\n'.join(lines))

    def export_current_image(self):
        if not self.last_result:
            QMessageBox.information(self, 'Sin simulacion', 'Simula un codigo antes de exportar.')
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar imagen Sprott',
            str(gallery_root() / f'{self.last_result["code"].raw}.png'),
            'PNG (*.png);;PDF (*.pdf);;SVG (*.svg)',
        )
        if not path:
            return
        self.sprott_canvas.export_image(path, dpi=self.export_dpi_spin.value())

    def export_current_metadata(self):
        if not self.last_result:
            QMessageBox.information(self, 'Sin simulacion', 'Simula un codigo antes de exportar metadatos.')
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar metadatos Sprott',
            str(gallery_root() / f'{self.last_result["code"].raw}_metadata.json'),
            'JSON (*.json)',
        )
        if not path:
            return
        metadata = self._current_metadata()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')

    def export_current_csv(self):
        if not self.last_result:
            QMessageBox.information(self, 'Sin simulacion', 'Simula un codigo antes de exportar datos.')
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar trayectoria Sprott',
            str(gallery_root() / f'{self.last_result["code"].raw}_trajectory.csv'),
            'CSV (*.csv)',
        )
        if not path:
            return
        values = np.asarray(self.last_result['post_transient'], dtype=float)
        values = values[np.all(np.isfinite(values), axis=1)]
        names = ['x', 'y', 'z', 'w']
        header = ['n'] + [names[i] if i < len(names) else f'x{i}' for i in range(values.shape[1])]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open('w', encoding='utf-8', newline='') as handle:
            handle.write(','.join(header) + '\n')
            for idx, row in enumerate(values):
                handle.write(','.join([str(idx)] + [f'{value:.17g}' for value in row]) + '\n')

    def copy_current_code(self):
        QApplication.clipboard().setText(self.explore_code_edit.text().strip())

    def copy_sprott_citation(self):
        citation = (
            'Imagen generada por Chaos Toolbox como reimplementacion educativa inspirada en '
            'Julien C. Sprott, Strange Attractors: Creating Patterns in Chaos, M&T Books, 1993. '
            'No redistribuye archivos originales de Sprott.'
        )
        QApplication.clipboard().setText(citation)

    def _current_metadata(self, notes: str = '') -> dict:
        code_text = self.last_result['code'].raw if self.last_result else self.explore_code_edit.text().strip()
        source_file = ''
        source_line = None
        if self.last_local_entry:
            source_file = self.last_local_entry.get('source_file', '')
            source_line = self.last_local_entry.get('line')
        return build_metadata(
            code=code_text,
            source=self.last_source,
            source_file=source_file,
            source_line=source_line,
            simulation=self.current_simulation_metadata(),
            style=self.current_visual_config().to_dict(),
            classification=self.last_classification or {},
            notes=notes or self.favorite_note.text() if hasattr(self, 'favorite_note') else notes,
        )

    def _load_examples(self):
        self.examples_list.clear()
        try:
            self.examples = load_synthetic_examples()
        except Exception as exc:
            self.examples = []
            self.examples_list.addItem(f'No se pudieron cargar ejemplos: {exc}')
            return
        for item in self.examples:
            self.examples_list.addItem(item.get('name', item.get('id', 'example')))
        if self.examples:
            self.examples_list.setCurrentRow(0)

    def show_selected_example(self, row: int):
        if row < 0 or row >= len(self.examples):
            return
        item = self.examples[row]
        lines = [
            f"name: {item.get('name', '')}",
            f"source: {item.get('source', '')}",
            f"code: {item.get('code', '')}",
            '',
            'equations:',
            item.get('equations', ''),
            '',
            f"notes: {item.get('notes', '')}",
        ]
        self.example_detail.setPlainText('\n'.join(lines))

    def simulate_selected_example(self):
        row = self.examples_list.currentRow()
        if row < 0 or row >= len(self.examples):
            return
        item = self.examples[row]
        params = item.get('parameters', {})
        self.explore_code_edit.setText(item.get('code', ''))
        self.last_source = 'synthetic'
        self.last_local_entry = None
        self.iter_spin.setValue(int(params.get('iterations', self.iter_spin.value())))
        self.transient_spin.setValue(int(params.get('transient', self.transient_spin.value())))
        if 'h' in params:
            self.h_spin.setValue(float(params['h']))
        if 'kind' in params:
            self.kind_combo.setCurrentText(str(params['kind']))
        if 'dimension' in params:
            self._set_combo_data(self.dimension_combo, int(params['dimension']))
        if 'order' in params:
            self._set_combo_data(self.order_combo, int(params['order']))
        self.simulate_exploration_code()
        self.sections.setCurrentIndex(3)

    def browse_local_dic(self):
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            'Seleccionar diccionario local de Sprott',
            str(self.repo_root / 'external'),
            'Sprott dictionaries (*.DIC *.dic);;All files (*)',
        )
        if path:
            self.local_dic_path_edit.setText(path)

    def _find_local_dic(self, name: str) -> Path:
        candidates = [
            self.repo_root / 'external' / 'sprott_site_bookdisk' / 'files' / 'fractals' / 'bookdisk' / name,
            self.repo_root / 'external' / 'sprott_site_full' / 'files' / 'fractals' / 'bookdisk' / name,
            self.repo_root / 'external' / 'sprott_site_theory' / 'files' / 'fractals' / 'bookdisk' / name,
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    def apply_dic_quick_selector(self, *_args):
        name = self.local_dic_quick_combo.currentData()
        if not name:
            return
        path = self._find_local_dic(str(name))
        self.local_dic_path_edit.setText(str(path) if path.exists() else '')

    def load_local_dic_examples(self, limit=300):
        path = self.local_dic_path_edit.text().strip()
        self.local_dic_table.setRowCount(0)
        self.local_dic_detail.clear()
        self.local_dic_entries = []
        self.local_dic_visible_entries = []
        if not path:
            self.local_dic_detail.setPlainText('Selecciona primero un archivo .DIC local.')
            return
        try:
            self.local_dic_entries = read_dic_entries(path, limit=int(limit))
        except Exception as exc:
            self.local_dic_detail.setPlainText(f'No se pudo leer el .DIC local:\n{exc}')
            return
        self.apply_local_dic_filter()
        if self.local_dic_entries:
            preferred = 2 if len(self.local_dic_entries) > 2 and Path(path).name.upper() == 'SELECTED.DIC' else 0
            if self.local_dic_table.rowCount() > 0:
                self.local_dic_table.setCurrentCell(min(preferred, self.local_dic_table.rowCount() - 1), 0)
        else:
            self.local_dic_detail.setPlainText('El archivo no contiene codigos reconocibles.')

    def apply_local_dic_filter(self, *_args):
        current_filter = self.local_dic_filter_combo.currentText() if hasattr(self, 'local_dic_filter_combo') else 'todos'
        self.local_dic_visible_entries = [entry for entry in self.local_dic_entries if self._entry_matches_filter(entry, current_filter)]
        self.local_dic_table.setRowCount(len(self.local_dic_visible_entries))
        for row, entry in enumerate(self.local_dic_visible_entries):
            values = [
                entry.get('line', ''),
                entry.get('code', ''),
                entry.get('family', ''),
                entry.get('dimension', ''),
                entry.get('order', ''),
                _metric_text(entry.get('f_metric')),
                _metric_text(entry.get('l_metric')),
                entry.get('support', ''),
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if col in {1, 7}:
                    cell.setToolTip(str(value))
                self.local_dic_table.setItem(row, col, cell)
        if self.local_dic_visible_entries:
            self.local_dic_table.setCurrentCell(0, 0)
        elif self.local_dic_entries:
            self.local_dic_detail.setPlainText('El filtro actual no deja codigos visibles.')

    def _entry_matches_filter(self, entry: dict, current_filter: str) -> bool:
        kind = entry.get('kind')
        dim = entry.get('dimension')
        support = entry.get('support')
        if current_filter == 'solo simulables':
            return support == 'simulable'
        if current_filter == 'mapas 2D':
            return kind == 'map' and dim == 2
        if current_filter == 'mapas 3D':
            return kind == 'map' and dim == 3
        if current_filter == 'mapas 4D':
            return kind == 'map' and dim == 4
        if current_filter == 'flujos 3D':
            return kind == 'flow' and dim == 3
        if current_filter == 'flujos 4D':
            return kind == 'flow' and dim == 4
        if current_filter == 'familias especiales':
            return kind == 'special'
        if current_filter == 'L positivo':
            return entry.get('l_metric') is not None and entry.get('l_metric') > 0
        if current_filter == 'F alta':
            return entry.get('f_metric') is not None and entry.get('f_metric') >= 2.0
        return True

    def _current_local_dic_row(self) -> int:
        if hasattr(self, 'local_dic_table'):
            return self.local_dic_table.currentRow()
        return -1

    def _current_local_dic_entry(self) -> dict | None:
        row = self._current_local_dic_row()
        if row < 0 or row >= len(self.local_dic_visible_entries):
            return None
        return self.local_dic_visible_entries[row]

    def show_selected_local_dic(self, row: int):
        if row < 0 or row >= len(self.local_dic_visible_entries):
            return
        entry = self.local_dic_visible_entries[row]
        code = decode_code(entry['code'])
        lines = [
            'REFERENCIA LOCAL DEL LIBRO',
            f"archivo: {entry['source_name']}",
            f"linea: {entry['line']}",
            f"codigo: {entry['code']}",
            f"metricas originales en linea: {' '.join(entry.get('metrics', []))}",
            '',
            'Lectura por la reimplementacion actual:',
            f'familia: {code.family_letter} -> {code.family_name}',
            f'tipo: {code.kind}',
            f'dimension: {code.dimension}',
            f'orden: {code.order}',
            f'coeficientes leidos: {len(code.coefficients)}',
            f"F: {_metric_text(entry.get('f_metric'))}",
            f"L: {_metric_text(entry.get('l_metric'))}",
            f"soporte: {entry.get('support', '')}",
            '',
            'Nota: este codigo se lee desde tu archivo local. No se agrega a assets ni al repositorio.',
        ]
        if code.warnings:
            lines.extend(['', 'advertencias:'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.local_dic_detail.setPlainText('\n'.join(lines))

    def simulate_selected_local_dic(self):
        entry = self._current_local_dic_entry()
        if not entry:
            QMessageBox.information(self, 'Sin codigo local', 'Selecciona un codigo del .DIC local primero.')
            return
        code = decode_code(entry['code'])
        if code.kind not in {'map', 'flow'}:
            QMessageBox.information(self, 'Familia no soportada', 'Esta fase simula familias polinomiales A-X. Las especiales quedan pendientes.')
            return
        self.explore_code_edit.setText(entry['code'])
        self.code_edit.setText(entry['code'])
        self.last_source = 'local_dic'
        self.last_local_entry = entry
        if code.kind == 'map':
            self.kind_combo.setCurrentText('map')
            self.iter_spin.setValue(max(self.iter_spin.value(), 12000))
            self.transient_spin.setValue(max(self.transient_spin.value(), 2000))
            self.divergence_spin.setValue(max(self.divergence_spin.value(), 1e9))
        else:
            self.kind_combo.setCurrentText('flow')
            self.iter_spin.setValue(max(self.iter_spin.value(), 5000))
            self.transient_spin.setValue(max(self.transient_spin.value(), 800))
            self.h_spin.setValue(min(self.h_spin.value(), 0.01))
            self.divergence_spin.setValue(max(self.divergence_spin.value(), 1e9))
        self._set_combo_data(self.dimension_combo, code.dimension)
        self._set_combo_data(self.order_combo, code.order)
        self.simulate_exploration_code()
        self.sections.setCurrentIndex(3)

    def simulate_selected_local_dic_recommended(self):
        entry = self._current_local_dic_entry()
        if not entry:
            QMessageBox.information(self, 'Sin codigo local', 'Selecciona un codigo del .DIC local primero.')
            return
        if entry.get('dimension', 0) >= 4:
            self.visual_preset_combo.setCurrentText('Mapa 4D')
        elif entry.get('dimension', 0) == 3:
            self.visual_preset_combo.setCurrentText('Color por profundidad')
        else:
            self.visual_preset_combo.setCurrentText('Sprott libro blanco')
        self.simulate_selected_local_dic()

    def save_current_favorite(self):
        if not self.last_result:
            QMessageBox.information(self, 'Sin simulacion', 'Simula un codigo antes de guardarlo como favorito.')
            return
        code = self.last_result['code']
        entry = {
            'code': code.raw,
            'equations': self.last_result.get('equations', ''),
            'parameters': {
                'iterations': self.iter_spin.value(),
                'transient': self.transient_spin.value(),
                'h': self.h_spin.value(),
                'method': self.method_combo.currentText(),
            },
            'metrics': self.last_classification or {},
            'notes': self.favorite_note.text(),
        }
        path = save_favorite(entry)
        self.favorites_label.setText(f'Archivo local: {path}')
        self.refresh_favorites()

    def save_current_gallery_entry(self):
        if not self.last_result:
            QMessageBox.information(self, 'Sin simulacion', 'Simula un codigo antes de agregarlo a la galeria.')
            return
        root = gallery_root()
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            render = self.sprott_canvas.export_image(tmpdir / 'render.png', dpi=self.export_dpi_spin.value())
            thumb = self.sprott_canvas.export_thumbnail(tmpdir / 'thumbnail.png')
            metadata = self._current_metadata(notes=self.favorite_note.text())
            entry_dir = save_gallery_entry(render_path=render, thumbnail_path=thumb, metadata=metadata)
        self.favorites_label.setText(f'Galeria local: {gallery_root()}')
        self.refresh_gallery()
        QMessageBox.information(self, 'Galeria local', f'Imagen guardada en:\n{entry_dir}')

    def refresh_favorites(self):
        self.favorites_list.clear()
        try:
            favorites = load_favorites()
        except Exception as exc:
            self.favorites_list.addItem(f'No se pudieron leer favoritos: {exc}')
            return
        for item in favorites:
            self.favorites_list.addItem(f"{item.get('date', '')} | {item.get('code', '')} | {item.get('notes', '')}")

    def refresh_gallery(self):
        self.favorites_list.clear()
        self.gallery_entries = list_gallery_entries()
        if not self.gallery_entries:
            self.favorites_list.addItem('Sin imagenes generadas todavia.')
            self.gallery_detail.setPlainText('Simula un codigo y pulsa "Agregar imagen actual a galeria local".')
            return
        for item in self.gallery_entries:
            self.favorites_list.addItem(f"{item.get('date', '')[:19]} | {item.get('code', '')} | {item.get('notes', '')}")
        self.favorites_list.setCurrentRow(0)

    def _current_gallery_entry(self) -> dict | None:
        row = self.favorites_list.currentRow()
        if row < 0 or row >= len(self.gallery_entries):
            return None
        return self.gallery_entries[row]

    def show_gallery_entry(self, row: int):
        if row < 0 or row >= len(self.gallery_entries):
            return
        item = self.gallery_entries[row]
        lines = [
            'ENTRADA DE GALERIA',
            f"codigo: {item.get('code', '')}",
            f"fecha: {item.get('date', '')}",
            f"fuente: {item.get('source', '')}",
            f"archivo origen: {item.get('source_file', '')}",
            f"linea origen: {item.get('source_line', '')}",
            f"render: {item.get('_render_path', '')}",
            f"thumbnail: {item.get('_thumbnail_path', '')}",
            '',
            'estilo:',
            json.dumps(item.get('style', {}), indent=2, ensure_ascii=False),
            '',
            'simulacion:',
            json.dumps(item.get('simulation', {}), indent=2, ensure_ascii=False),
            '',
            f"notas: {item.get('notes', '')}",
            '',
            item.get('attribution_warning', ''),
        ]
        self.gallery_detail.setPlainText('\n'.join(lines))

    def open_selected_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(item.get('_render_path', '')))

    def resimulate_selected_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        self.explore_code_edit.setText(item.get('code', ''))
        simulation = item.get('simulation', {})
        self.iter_spin.setValue(int(simulation.get('iterations', self.iter_spin.value())))
        self.transient_spin.setValue(int(simulation.get('transient', self.transient_spin.value())))
        self.h_spin.setValue(float(simulation.get('h', self.h_spin.value())))
        self.method_combo.setCurrentText(str(simulation.get('method', self.method_combo.currentText())))
        self.divergence_spin.setValue(float(simulation.get('divergence_threshold', self.divergence_spin.value())))
        self.edit_style_from_gallery_entry()
        self.last_source = 'manual'
        self.last_local_entry = None
        self.simulate_exploration_code()
        self.sections.setCurrentIndex(3)

    def edit_style_from_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        style = SprottVisualConfig.from_dict(item.get('style', {}))
        self.projection_combo.setCurrentText(style.projection)
        self.color_by_combo.setCurrentText(style.color_by)
        self.palette_combo.setCurrentText(style.palette)
        self.background_combo.setCurrentText(style.background)
        self.draw_mode_combo.setCurrentText(style.draw_mode)
        self.point_size_spin.setValue(style.point_size)
        self.alpha_spin.setValue(style.alpha)
        self.max_plot_points_spin.setValue(style.max_points)
        self.band_count_spin.setValue(style.band_count)
        self.export_dpi_spin.setValue(style.export_dpi)
        self.axes_check.setChecked(style.show_axes)
        self.grid_check.setChecked(style.show_grid)
        self.equal_aspect_check.setChecked(style.equal_aspect)
        self.apply_current_style()

    def export_selected_gallery_render(self):
        item = self._current_gallery_entry()
        if not item:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar render de galeria',
            str(Path.home() / Path(item.get('_render_path', 'render.png')).name),
            'PNG (*.png)',
        )
        if not path:
            return
        Path(path).write_bytes(Path(item.get('_render_path', '')).read_bytes())

    def delete_selected_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        entry_dir = Path(item.get('_entry_dir', ''))
        if entry_dir.exists() and (entry_dir / 'metadata.json').exists():
            import shutil
            shutil.rmtree(entry_dir)
        self.refresh_gallery()

    def browse_import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Seleccionar carpeta local de referencias')
        if folder:
            self.import_folder_edit.setText(folder)

    def index_import_folder(self):
        folder = self.import_folder_edit.text().strip()
        if not folder:
            QMessageBox.information(self, 'Sin carpeta', 'Selecciona una carpeta local primero.')
            return
        try:
            inventory = index_local_reference_folder(folder, include_hash=self.hash_check.isChecked())
        except Exception as exc:
            QMessageBox.critical(self, 'Error de importador local', str(exc))
            return
        self.import_table.setRowCount(len(inventory))
        for row, item in enumerate(inventory):
            values = [item['name'], item['path'], item['type'], str(item['size']), item['hash'], item['category']]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 1:
                    cell.setToolTip(value)
                self.import_table.setItem(row, col, cell)


def _range_text(ranges: list, index: int) -> str:
    if index >= len(ranges):
        return ''
    lo, hi = ranges[index]
    return f'[{lo:.4g}, {hi:.4g}]'


def _metric_text(value) -> str:
    if value is None or value == '':
        return ''
    try:
        return f'{float(value):.5g}'
    except Exception:
        return str(value)


def _int_spin(value: int, minimum: int, maximum: int, tooltip: str = '') -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    if tooltip:
        spin.setToolTip(tooltip)
    return spin


def _double_spin(value: float, minimum: float, maximum: float, decimals: int, tooltip: str = '') -> QDoubleSpinBox:
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(decimals)
    spin.setValue(value)
    spin.setSingleStep(10 ** (-max(1, decimals - 1)))
    if tooltip:
        spin.setToolTip(tooltip)
    return spin


def _markdown_to_clean_html(markdown: str, *, webengine: bool = False, asset_root: Path | None = None) -> str:
    parts = []
    css = """
    body { font-family: Segoe UI, Arial, sans-serif; color: #172033; background: #ffffff; margin: 22px; line-height: 1.52; font-size: 15px; }
    h1 { font-size: 26px; margin: 0 0 12px 0; color: #102033; }
    h2 { font-size: 20px; margin: 18px 0 8px 0; color: #102033; border-bottom: 1px solid #d8dee9; padding-bottom: 4px; }
    h3 { font-size: 16px; margin: 14px 0 6px 0; color: #102033; }
    p { margin: 7px 0; }
    ul { margin-top: 4px; }
    li { margin: 4px 0; }
    code { background: #eef2f7; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; }
    figure { margin: 14px 0 18px 0; }
    figure img { max-width: 100%; border: 1px solid #d8dee9; border-radius: 6px; background: #ffffff; }
    figcaption { margin-top: 5px; color: #526070; font-size: 13px; }
    .equation { margin: 14px auto; padding: 12px 16px; text-align: center; border: 1px solid #ccd6e0; border-left: 4px solid #2563eb; background: #f8fafc; max-width: 860px; border-radius: 6px; box-shadow: 0 1px 3px rgba(15,23,42,0.08); }
    .equation img { max-width: 100%; border: 0; background: transparent; }
    .inline-eq { vertical-align: middle; border: 0; background: transparent; }
    """
    if webengine:
        css += """
        body { max-width: 1120px; margin-left: auto; margin-right: auto; }
        p { max-width: 980px; }
        """
    parts.append(f'<html><head><style>{css}</style></head><body>')

    blocks = re.split(r'(\$\$.*?\$\$)', markdown, flags=re.DOTALL)
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append('</ul>')
            in_list = False

    for block in blocks:
        if not block:
            continue
        if block.startswith('$$') and block.endswith('$$'):
            close_list()
            expr = block[2:-2].strip()
            uri = render_math_to_path(f'${expr}$', size=19, color='#0f172a')
            parts.append(f'<div class="equation"><img src="{html.escape(uri)}" alt="{html.escape(expr)}"></div>')
            continue
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line:
                close_list()
                continue
            if line.startswith('#'):
                close_list()
                level = min(3, len(line) - len(line.lstrip('#')))
                title = line[level:].strip()
                parts.append(f'<h{level}>{_inline_html(title)}</h{level}>')
            elif re.match(r'^!\[[^\]]*\]\([^)]+\)$', line):
                close_list()
                alt, src = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', line).groups()
                image_src = _asset_image_src(src.strip(), asset_root)
                caption = _inline_html(alt.strip())
                parts.append(
                    '<figure>'
                    f'<img src="{html.escape(image_src)}" alt="{html.escape(alt.strip())}">'
                    f'<figcaption>{caption}</figcaption>'
                    '</figure>'
                )
            elif line.startswith(('- ', '* ')):
                if not in_list:
                    parts.append('<ul>')
                    in_list = True
                parts.append(f'<li>{_inline_html(line[2:].strip())}</li>')
            elif re.match(r'^\d+\.\s+', line):
                close_list()
                parts.append(f'<p>{_inline_html(re.sub(r"^\d+\.\s+", "", line))}</p>')
            else:
                close_list()
                parts.append(f'<p>{_inline_html(line)}</p>')
    close_list()
    parts.append('</body></html>')
    return ''.join(parts)


def _asset_image_src(src: str, asset_root: Path | None) -> str:
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', src):
        return src
    if asset_root is None:
        return src
    path = Path(src)
    if not path.is_absolute():
        path = asset_root / path
    try:
        return path.resolve().as_uri()
    except ValueError:
        return src


def _inline_html(text: str) -> str:
    protected = []

    def protect_code(match):
        protected.append(f'<code>{html.escape(match.group(1))}</code>')
        return f'\x00{len(protected) - 1}\x00'

    text = re.sub(r'`([^`]+)`', protect_code, text)
    out = html.escape(text)
    out = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', out)

    def replace_inline(match):
        expr = match.group(1).strip()
        uri = render_math_to_path(f'${expr}$', size=14, color='#0f172a')
        return f'<img class="inline-eq" src="{html.escape(uri)}" alt="{html.escape(expr)}">'

    out = re.sub(r'(?<!\\)\$([^$\n]+?)(?<!\\)\$', replace_inline, out)
    out = out.replace(r'\$', '$')
    for idx, value in enumerate(protected):
        out = out.replace(f'\x00{idx}\x00', value)
    return out
