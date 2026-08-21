from __future__ import annotations

from copy import deepcopy
import html
import json
import logging
import re
import tempfile
from pathlib import Path
from time import perf_counter

import numpy as np

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (
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
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QFrame,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.image_security import ImageSecurityError, confined_png

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    QT_PDF_AVAILABLE = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    QT_PDF_AVAILABLE = False

from core.sprott import decode_code, describe_family


LOGGER = logging.getLogger(__name__)
from core.sprott.explain import explain_code_pipeline, format_explanation_markdown
from core.sprott.catalog import load_favorites, load_synthetic_examples, save_favorite
from core.sprott.gallery import (
    build_metadata,
    delete_gallery_entry,
    gallery_root,
    list_gallery_entries,
    load_gallery_entry,
    save_gallery_entry,
)
from core.sprott.reading_log import (
    ReadingLogError,
    dominant_color, entry_key, load_reading_log,
    marks_icons_text, save_reading_log, set_code, set_mark, set_note,
)
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
from core.paths import bundled_doc_path, sprott_assets_dir
from core.qt_capabilities import create_webengine_view
from ui.math_render import render_math_to_path
from ui.sprott_canvases import Sprott2DCanvas, SprottGalleryThumbnail
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


def _separator() -> QWidget:
    """Return a thin horizontal line widget for use as visual separator in layouts."""
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet('background-color: #cccccc;')
    return sep


class SprottExplorerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.assets_dir = sprott_assets_dir()
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

        # Estado del modo lectura del libro (debe inicializarse antes de _build_examples_tab)
        self._reading_log: dict = {}
        self._reading_entries: list[dict] = []
        self._reading_visible: list[dict] = []
        self._mark_buttons: dict[str, QPushButton] = {}

        self._build_home_tab()
        self._build_tutorial_tab()   # Sube al 2º lugar
        self._build_theory_tab()
        self._build_codes_tab()
        self._build_exploration_tab()
        self._build_examples_tab()
        self._build_gallery_tab()
        self._build_importer_tab()
        self._build_backend_explained_tab()
        self._last_explanation: dict | None = None

    def _go_to_tab(self, name: str):
        for i in range(self.sections.count()):
            if name.lower() in self.sections.tabText(i).lower():
                self.sections.setCurrentIndex(i)
                return

    def _read_asset(self, name: str, fallback: str = '') -> str:
        path = self.assets_dir / name
        if not path.exists():
            return fallback
        return path.read_text(encoding='utf-8')

    def _markdown_browser(self, markdown: str) -> QTextBrowser:
        browser, _status = create_webengine_view()
        html_doc = _markdown_to_clean_html(
            markdown, webengine=browser is not None, asset_root=self.assets_dir
        )
        if browser is not None:
            browser.setHtml(
                html_doc,
                QUrl.fromLocalFile(str(self.assets_dir / 'index.html')),
            )
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
        layout.addWidget(self._markdown_browser(text), stretch=1)

        start_box = QGroupBox('Empieza aqui')
        start_layout = QVBoxLayout(start_box)
        start_note = QLabel(
            'Elige una sola ruta. El explorador te llevara a la pestaña y los controles necesarios.'
        )
        start_note.setWordWrap(True)
        start_layout.addWidget(start_note)

        actions = QHBoxLayout()
        self.home_example_button = QPushButton('1. Probar ejemplo')
        self.home_example_button.setToolTip('Carga un ejemplo sintetico incluido y muestra como simularlo.')
        self.home_example_button.clicked.connect(self.start_guided_example)
        actions.addWidget(self.home_example_button)

        self.home_code_button = QPushButton('2. Decodificar codigo')
        self.home_code_button.setToolTip('Abre el decodificador educativo con un codigo listo para editar.')
        self.home_code_button.clicked.connect(self.open_code_decoder)
        actions.addWidget(self.home_code_button)

        self.home_dic_button = QPushButton('3. Abrir archivo .DIC')
        self.home_dic_button.setToolTip('Selecciona un diccionario local sin copiarlo dentro de la aplicacion.')
        self.home_dic_button.clicked.connect(self.open_local_dictionary_dialog)
        actions.addWidget(self.home_dic_button)
        start_layout.addLayout(actions)

        self.home_status_label = QLabel(
            'Recomendacion para la primera vez: pulsa «1. Probar ejemplo».'
        )
        self.home_status_label.setWordWrap(True)
        start_layout.addWidget(self.home_status_label)
        layout.addWidget(start_box, stretch=0)

        # Styled panel: Modo público vs modo personal
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e4e7ed;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)

        title = QLabel('<b>⚖️ Modo público vs modo personal</b>')
        title.setStyleSheet('font-size: 13px; font-weight: bold; color: #303133; background: transparent; border: none;')
        panel_layout.addWidget(title)

        desc = QLabel(
            '• La aplicación pública no incluye archivos originales de Sprott.<br/>'
            '• Para estudiar el libro físico, selecciona tus archivos .DIC locales.<br/>'
            '• Los archivos se leen desde tu disco y no se copian al programa.<br/>'
            '• Las imágenes generadas se guardan como resultados locales del usuario.'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet('font-size: 12px; color: #606266; line-height: 1.4; background: transparent; border: none;')
        panel_layout.addWidget(desc)

        layout.addWidget(panel, stretch=0)
        self.sections.addTab(widget, 'Inicio')

    def start_guided_example(self):
        """Run the smallest curated example and open its resulting plot."""

        self._go_to_tab('Ejemplos')
        if hasattr(self, 'examples_list') and self.examples_list.count() > 0:
            self.examples_list.setCurrentRow(0)
            self.simulate_selected_example()
            self.home_status_label.setText(
                'Ejemplo inicial simulado. Ya puedes cambiar estilo o volver a Ejemplos para elegir otro.'
            )
        else:
            self.home_status_label.setText('No se encontro un ejemplo sintetico disponible.')

    def open_code_decoder(self):
        """Open and focus the educational compact-code decoder."""

        self._go_to_tab('Codigos')
        if hasattr(self, 'code_edit'):
            self.code_edit.setFocus()
            self.code_edit.selectAll()
        self.home_status_label.setText(
            'Decodificador abierto. Edita el codigo y observa las ecuaciones resultantes.'
        )

    def open_local_dictionary_dialog(self):
        """Ask for a local dictionary and continue in the inventory page."""

        self.browse_local_dic()
        if hasattr(self, 'local_dic_path_edit') and self.local_dic_path_edit.text().strip():
            self._go_to_tab('Inventario')
            self.home_status_label.setText(
                'Archivo local seleccionado. Carga su inventario para elegir un codigo.'
            )

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
        
        self.use_in_exploration_button = QPushButton('→ Usar en Exploración')
        self.use_in_exploration_button.setToolTip('Lleva este código a la pestaña de Exploración para simularlo y graficarlo.')
        self.use_in_exploration_button.clicked.connect(self.use_code_in_exploration)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(self.code_edit)
        row_layout.addWidget(self.decode_button)
        row_layout.addWidget(self.use_in_exploration_button)
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
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        guide = QLabel(
            'Uso recomendado: 1) carga un ejemplo local desde SELECTED.DIC en la pestaña Ejemplos, '
            '2) pulsa Simular codigo local, 3) vuelve aqui para ajustar iteraciones/transitorio si quieres mas detalle. '
            'Generar codigo es didactico; los codigos locales del libro suelen producir figuras mas interesantes.'
        )
        guide.setWordWrap(True)
        guide.setStyleSheet('font-weight: bold; padding: 4px;')
        outer.addWidget(guide, stretch=0)

        # ── Main horizontal splitter: left=controls, right=canvas ─────────
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        outer.addWidget(main_splitter, stretch=1)

        # ── LEFT: controls in a scrollable area ───────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        controls = QGroupBox('Controles con ayuda')
        form = QFormLayout(controls)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem('Mapa 2D rapido (recomendado)', userData=('map', 2, 2, 900, 150, 0.01, 'rk4'))
        self.preset_combo.addItem('Mapa 1D didactico', userData=('map', 1, 2, 700, 100, 0.01, 'rk4'))
        self.preset_combo.addItem('Flujo 3D RK4 corto', userData=('flow', 3, 2, 1600, 250, 0.01, 'rk4'))
        self.preset_combo.addItem('Flujo 3D Euler historico', userData=('flow', 3, 2, 1200, 200, 0.1, 'euler'))
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        self.preset_combo.setToolTip('Ajusta varios controles a una configuracion razonable para aprender sin esperar demasiado.')

        self.preset_status_label = QLabel("Preset aplicado: Mapa 2D rapido (recomendado) → tipo=map, dim=2, orden=2, iter=900, trans=150, h=0.01, método=rk4")
        self.preset_status_label.setStyleSheet('color: gray; font-style: italic; font-size: 10px;')
        self.preset_status_label.setWordWrap(True)

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(['map', 'flow'])
        self.kind_combo.setToolTip(EXPLORATION_HELP['kind'])
        self.kind_combo.currentTextChanged.connect(self._sync_dimension_for_kind)
        self.dimension_combo = QComboBox()
        self.dimension_combo.setToolTip(EXPLORATION_HELP['dimension'])
        self.order_combo = QComboBox()
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

        for value in (1, 2, 3, 4):
            self.dimension_combo.addItem(str(value), userData=value)
        for value in (2, 3, 4, 5):
            self.order_combo.addItem(str(value), userData=value)

        form.addRow(make_help_label('Preset', 'Configuraciones iniciales para aprender rapido.'), self.preset_combo)
        form.addRow('', self.preset_status_label)
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

        self.visual_preset_status_label = QLabel("Simula un código para ver el resultado.")
        self.visual_preset_status_label.setStyleSheet('color: gray; font-style: italic; font-size: 10px;')
        self.visual_preset_status_label.setWordWrap(True)
        self.visual_preset_combo.currentTextChanged.connect(self.apply_visual_preset)
        self.projection_combo = QComboBox()
        self.projection_combo.addItems(PROJECTIONS)
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
        style_form.addRow('', self.visual_preset_status_label)
        style_form.addRow(
            make_help_label(
                'Proyeccion',
                'Proyección 2D, 3D o radial de (x,y,z) sobre la esfera unitaria.',
            ),
            self.projection_combo,
        )
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

        # Assemble left panel in a QScrollArea so controls never clip
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll_content = QWidget()
        left_scroll_vlayout = QVBoxLayout(left_scroll_content)
        left_scroll_vlayout.setContentsMargins(0, 0, 0, 0)
        left_scroll_vlayout.addWidget(controls)
        left_scroll_vlayout.addWidget(style_box)
        left_scroll_vlayout.addStretch()
        left_scroll.setWidget(left_scroll_content)
        left_layout.addWidget(left_scroll, stretch=1)

        # ── RIGHT: canvas + action bar + output splitter ──────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Action bar directly above canvas
        self.action_bar = QWidget()
        action_bar_layout = QHBoxLayout(self.action_bar)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(4)

        self.quick_sim_btn = QPushButton("▶ Simular ejemplo rápido")
        self.quick_sim_btn.setToolTip("Carga el código EWMWAMMMPMMMM con preset Color por profundidad y simula 8000 iteraciones.")
        self.quick_sim_btn.clicked.connect(self.quick_simulate)

        self.rerender_btn = QPushButton("🔄 Re-renderizar")
        self.rerender_btn.setToolTip("Vuelve a trazar la trayectoria actual sin re-simular.")
        self.rerender_btn.clicked.connect(self.rerender_last_result)

        self.save_gallery_btn = QPushButton("💾 Guardar en galería")
        self.save_gallery_btn.setToolTip("Guarda la simulación actual en tu galería local.")
        self.save_gallery_btn.setStyleSheet("font-weight: bold;")
        self.save_gallery_btn.clicked.connect(self.save_current_gallery_entry)

        self.export_png_btn = QPushButton("📤 Exportar PNG")
        self.export_png_btn.setToolTip("Exporta el canvas actual como un archivo PNG.")
        self.export_png_btn.clicked.connect(self.export_current_image)

        self.copy_code_btn = QPushButton("📋 Copiar código")
        self.copy_code_btn.setToolTip("Copia el código actual al portapapeles.")
        self.copy_code_btn.clicked.connect(self.copy_current_code)

        action_bar_layout.addWidget(self.quick_sim_btn)
        action_bar_layout.addWidget(self.rerender_btn)
        action_bar_layout.addWidget(self.save_gallery_btn)
        action_bar_layout.addWidget(self.export_png_btn)
        action_bar_layout.addWidget(self.copy_code_btn)
        right_layout.addWidget(self.action_bar, stretch=0)

        # Empty canvas placeholder
        self.canvas_empty_label = QLabel("No hay trayectoria. Pulsa ▶ Simular ejemplo rápido para ver una gráfica.")
        self.canvas_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_empty_label.setStyleSheet(
            "color: #555555; font-size: 11px; font-weight: bold; background-color: #f7f7f7; "
            "padding: 10px; border: 1px dashed #cccccc; border-radius: 4px; margin-bottom: 2px;"
        )
        right_layout.addWidget(self.canvas_empty_label, stretch=0)

        # Vertical sub-splitter: canvas (top) | output tables (bottom)
        right_vsplit = QSplitter(Qt.Orientation.Vertical)
        right_vsplit.setChildrenCollapsible(False)

        self.sprott_canvas = Sprott2DCanvas(right_widget)
        right_vsplit.addWidget(self.sprott_canvas)

        output_widget = QWidget()
        output_layout = QHBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.explore_output = QTextEdit()
        self.explore_output.setReadOnly(True)
        self.explore_output.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        self.explore_output.setMinimumHeight(80)
        self.search_attempt_table = QTableWidget(0, 7)
        self.search_attempt_table.setHorizontalHeaderLabels(['Intento', 'Codigo', 'Estado', 'Razon', 'Rango x', 'Rango y', 'Lyap rapido'])
        self.search_attempt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.search_attempt_table.cellDoubleClicked.connect(self.simulate_attempt_row)
        self.search_attempt_table.setMinimumHeight(80)
        output_layout.addWidget(self.explore_output, stretch=1)
        output_layout.addWidget(self.search_attempt_table, stretch=1)
        right_vsplit.addWidget(output_widget)

        right_vsplit.setStretchFactor(0, 3)
        right_vsplit.setStretchFactor(1, 1)
        right_layout.addWidget(right_vsplit, stretch=1)

        # Add panels to horizontal splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setSizes([360, 900])

        self.sections.addTab(widget, 'Exploracion')
        self.apply_preset()
        self.apply_visual_preset(self.visual_preset_combo.currentText())


    def _build_examples_tab(self):
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        intro = QLabel(
            'Empieza por un ejemplo sintetico para aprender el flujo. Si tienes los diccionarios del libro descargados, '
            'carga un .DIC local: se usa desde tu disco y no se copia al repositorio.'
        )
        intro.setWordWrap(True)
        intro.setStyleSheet('font-weight: bold; padding: 4px;')
        outer.addWidget(intro, stretch=0)

        # Horizontal splitter: examples | DIC local
        examples_splitter = QSplitter(Qt.Orientation.Horizontal)
        examples_splitter.setChildrenCollapsible(False)
        outer.addWidget(examples_splitter, stretch=1)

        # ── LEFT: synthetic examples ────────────────────────────────────────
        synthetic_box = QGroupBox('Ejemplos sinteticos publicos')
        synthetic_layout = QVBoxLayout(synthetic_box)
        synthetic_layout.addWidget(QLabel('Ejemplos recomendados para empezar'))
        self.recommended_examples_list = QListWidget()
        self.recommended_examples_list.setMinimumHeight(80)
        self.recommended_examples_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.recommended_examples_list.currentRowChanged.connect(self.select_recommended_example)
        synthetic_layout.addWidget(self.recommended_examples_list, stretch=1)
        synthetic_layout.addWidget(QLabel('Coleccion completa'))
        self.examples_list = QListWidget()
        self.examples_list.setToolTip('Ejemplos sinteticos creados para esta toolbox. No vienen de diccionarios historicos.')
        self.examples_list.currentRowChanged.connect(self.show_selected_example)
        synthetic_layout.addWidget(self.examples_list, stretch=2)
        self.example_thumbnail = SprottGalleryThumbnail()
        synthetic_layout.addWidget(self.example_thumbnail, stretch=0)
        self.example_detail = QTextEdit()
        self.example_detail.setReadOnly(True)
        self.example_detail.setMinimumHeight(100)
        self.example_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        synthetic_layout.addWidget(self.example_detail, stretch=2)
        example_buttons = QWidget()
        example_buttons_layout = QHBoxLayout(example_buttons)
        example_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.example_sim_button = QPushButton('Simular')
        self.example_style_button = QPushButton('Simular con estilo recomendado')
        self.example_decode_button = QPushButton('Decodificar')
        self.example_gallery_button = QPushButton('Agregar a galeria')
        self.example_metadata_button = QPushButton('Exportar metadata')
        self.example_sim_button.setToolTip('Carga parametros y simula el codigo del ejemplo.')
        self.example_style_button.setToolTip('Carga parametros, aplica el visual recomendado y simula.')
        self.example_decode_button.setToolTip('Lleva el codigo a la pestana Codigos y lo decodifica.')
        self.example_gallery_button.setToolTip('Simula con visual recomendado y guarda una imagen generada en la galeria local.')
        self.example_metadata_button.setToolTip('Exporta el JSON educativo del ejemplo seleccionado.')
        self.example_sim_button.clicked.connect(lambda: self.simulate_selected_example(apply_visual=False))
        self.example_style_button.clicked.connect(lambda: self.simulate_selected_example(apply_visual=True))
        self.example_decode_button.clicked.connect(self.decode_selected_example)
        self.example_gallery_button.clicked.connect(self.add_selected_example_to_gallery)
        self.example_metadata_button.clicked.connect(self.export_selected_example_metadata)
        for button in (self.example_sim_button, self.example_style_button, self.example_decode_button, self.example_gallery_button, self.example_metadata_button):
            example_buttons_layout.addWidget(button)
        synthetic_layout.addWidget(example_buttons, stretch=0)
        examples_splitter.addWidget(synthetic_box)

        # ── RIGHT: DIC local ───────────────────────────────────────────────
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
            'simulables A-X',
            'especiales implementadas',
            'especiales pendientes',
            'Y valores absolutos',
            '[ potencias',
            '\\ senos',
            '] rotación',
            '^ oscilador',
            'pendientes especiales',
            'errores de parsing',
            'candidatos corregibles',
            'familias Y-Z',
            'familias desconocidas',
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

        # ── Load quantity row + BOOKFIGS shortcut ─────────────────────────
        load_qty_row = QWidget()
        lq_layout = QHBoxLayout(load_qty_row)
        lq_layout.setContentsMargins(0, 0, 0, 0)
        lq_layout.setSpacing(4)
        lq_layout.addWidget(QLabel('Cargar:'))
        self.dic_load_limit_combo = QComboBox()
        self.dic_load_limit_combo.addItem('Todos', userData=None)
        self.dic_load_limit_combo.addItem('350', userData=350)
        self.dic_load_limit_combo.addItem('500', userData=500)
        self.dic_load_limit_combo.addItem('1000', userData=1000)
        self.dic_load_limit_combo.setToolTip('Número máximo de entradas a cargar del archivo .DIC.')
        lq_layout.addWidget(self.dic_load_limit_combo)
        load_all_btn = QPushButton('Cargar BOOKFIGS.DIC completo')
        load_all_btn.setToolTip('Selecciona BOOKFIGS.DIC automáticamente y carga todas las entradas.')
        load_all_btn.clicked.connect(self._load_bookfigs_full)
        lq_layout.addWidget(load_all_btn)
        lq_layout.addStretch()
        local_layout.addWidget(load_qty_row)

        # ── DIC status counter ────────────────────────────────────────────
        self.dic_status_label = QLabel('Sin archivo .DIC cargado.')
        self.dic_status_label.setWordWrap(True)
        self.dic_status_label.setStyleSheet(
            'font-size: 10px; color: #333; padding: 3px 6px; '
            'background: #f0f8ff; border-radius: 3px; border: 1px solid #c8e0f8;'
        )
        local_layout.addWidget(self.dic_status_label)

        # Instructions button (shown if BOOKFIGS.DIC is not found in standard paths)
        has_bookfigs = self._find_local_dic('BOOKFIGS.DIC').exists()
        self.instrucciones_btn = QPushButton('Abrir instrucciones para obtener archivos originales')
        self.instrucciones_btn.setToolTip('Haz clic para ver cómo conseguir los archivos .DIC originales de Sprott.')
        self.instrucciones_btn.clicked.connect(self.show_sprott_instructions)
        self.instrucciones_btn.setStyleSheet("font-weight: bold; color: #0066cc;")
        self.instrucciones_btn.setVisible(not has_bookfigs)
        local_layout.addWidget(self.instrucciones_btn)

        # Button: Probar limpieza de códigos no reconocidos
        self.test_cleaning_btn = QPushButton('Probar limpieza de códigos no reconocidos')
        self.test_cleaning_btn.setToolTip('Revisa códigos con errores o desconocidos e intenta sugerir candidatos correctos.')
        self.test_cleaning_btn.clicked.connect(self.show_cleaning_test_dialog)
        local_layout.addWidget(self.test_cleaning_btn)

        # ── Toggle modo lectura ────────────────────────────────────────────
        self.reading_mode_check = QCheckBox('☰ Modo lectura del libro')
        self.reading_mode_check.setToolTip(
            'Activa tabla enriquecida con marcas, notas y filtros por rango de lineas '
            'para seguir el progreso capitulo a capitulo. Reutiliza los codigos ya cargados.'
        )
        self.reading_mode_check.setStyleSheet('font-weight: bold; padding: 3px 0;')
        self.reading_mode_check.toggled.connect(self.toggle_reading_mode)
        local_layout.addWidget(self.reading_mode_check)

        # ── QStackedWidget: pagina 0 = vista basica, pagina 1 = lectura ──
        self._local_dic_stack = QStackedWidget()

        # -- Pagina 0: vista basica original --
        _page0 = QWidget()
        _p0_layout = QVBoxLayout(_page0)
        _p0_layout.setContentsMargins(0, 0, 0, 0)
        _p0_layout.setSpacing(3)

        self.local_dic_table = QTableWidget(0, 8)
        self.local_dic_table.setHorizontalHeaderLabels(['Linea', 'Codigo', 'Familia', 'Dim', 'Orden', 'F', 'L', 'Soporte'])
        self.local_dic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.local_dic_table.setToolTip('Codigos leidos desde tu archivo .DIC local. No son assets publicos del repositorio.')
        self.local_dic_table.currentCellChanged.connect(lambda row, _col, _prev_row, _prev_col: self.show_selected_local_dic(row))
        self.local_dic_table.cellDoubleClicked.connect(lambda _row, _col: self.simulate_selected_local_dic())
        _p0_layout.addWidget(self.local_dic_table, stretch=1)

        self.local_dic_detail = QTextEdit()
        self.local_dic_detail.setReadOnly(True)
        self.local_dic_detail.setMinimumHeight(100)
        self.local_dic_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        _p0_layout.addWidget(self.local_dic_detail, stretch=1)

        self.local_dic_sim_button = QPushButton('Simular codigo local seleccionado')
        self.local_dic_sim_button.setToolTip('Carga el codigo local en Exploracion y lo simula con el backend C si la familia A-X esta soportada.')
        self.local_dic_sim_button.setEnabled(False)
        self.local_dic_sim_button.clicked.connect(self.simulate_selected_local_dic)
        self.local_dic_style_button = QPushButton('Simular con estilo recomendado')
        self.local_dic_style_button.setToolTip('Carga el codigo local, ajusta parametros largos y aplica un preset visual segun dimension.')
        self.local_dic_style_button.setEnabled(False)
        self.local_dic_style_button.clicked.connect(self.simulate_selected_local_dic_recommended)
        self.local_dic_gallery_limit_combo = QComboBox()
        for value in (10, 25, 50):
            self.local_dic_gallery_limit_combo.addItem(str(value), userData=value)
        self.local_dic_gallery_button = QPushButton('Generar galeria local desde este .DIC')
        self.local_dic_gallery_button.setToolTip('Simula los primeros N codigos visibles y guarda imagenes propias en la galeria local del usuario.')
        self.local_dic_gallery_button.clicked.connect(self.generate_local_gallery_from_dic)
        _local_buttons = QWidget()
        _lb_layout = QHBoxLayout(_local_buttons)
        _lb_layout.setContentsMargins(0, 0, 0, 0)
        _lb_layout.addWidget(self.local_dic_sim_button)
        _lb_layout.addWidget(self.local_dic_style_button)
        _lb_layout.addWidget(QLabel('N'))
        _lb_layout.addWidget(self.local_dic_gallery_limit_combo)
        _lb_layout.addWidget(self.local_dic_gallery_button)
        _p0_layout.addWidget(_local_buttons)

        self._local_dic_stack.addWidget(_page0)

        # -- Pagina 1: panel de lectura del libro --
        self._local_dic_stack.addWidget(self._build_reading_panel())

        local_layout.addWidget(self._local_dic_stack, stretch=1)
        examples_splitter.addWidget(local_box)

        examples_splitter.setStretchFactor(0, 1)
        examples_splitter.setStretchFactor(1, 1)

        self._load_examples()
        if self.local_dic_path_edit.text():
            self.load_local_dic_examples()
        self.sections.addTab(widget, 'Ejemplos')


    def _build_tutorial_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        # The complete pedagogical tutorial lives in the compiled manual so the
        # embedded view, external PDF and distributed documentation stay equal.
        layout.addWidget(self._pdf_guide_or_browser(), 0, 0, 1, 2)
        actions = QGroupBox('Acciones rapidas')
        action_layout = QVBoxLayout(actions)

        # Navigation buttons
        nav_buttons = [
            ('Ir a Ejemplos', lambda: self._go_to_tab('Ejemplos')),
            ('Ir a Exploracion', lambda: self._go_to_tab('Explorac')),
        ]
        for label, callback in nav_buttons:
            btn = QPushButton(label)
            btn.clicked.connect(callback)
            action_layout.addWidget(btn)

        action_layout.addWidget(_separator())

        # Preset buttons — navigate to Exploración AND simulate
        preset_label = QLabel('Presets (navegan a Exploración y simulan):')
        preset_label.setStyleSheet('font-size: 10px; color: #666; font-weight: bold;')
        action_layout.addWidget(preset_label)

        preset_buttons = [
            ('Preset Color por profundidad', 'Color por profundidad'),
            ('Preset Alta densidad', 'Alta densidad'),
            ('Preset Didactico', 'Didactico'),
        ]
        for label, preset_name in preset_buttons:
            btn = QPushButton(label)
            btn.setToolTip(f'Navega a Exploración, aplica el preset «{preset_name}» y simula un ejemplo si no hay trayectoria.')
            btn.clicked.connect(lambda checked=False, p=preset_name: self.tutorial_apply_preset_and_show(p))
            action_layout.addWidget(btn)

        action_layout.addWidget(_separator())

        # Book reading shortcut
        book_btn = QPushButton('📖 Modo lectura del libro físico')
        book_btn.setToolTip('Navega a Ejemplos, carga BOOKFIGS.DIC completo y activa el modo lectura.')
        book_btn.setStyleSheet('font-weight: bold; padding: 4px;')
        book_btn.clicked.connect(self._open_book_reading_mode)
        action_layout.addWidget(book_btn)

        action_layout.addWidget(_separator())

        cite_btn = QPushButton('Copiar cita')
        cite_btn.clicked.connect(self.copy_sprott_citation)
        action_layout.addWidget(cite_btn)

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

        # Panel explicativo al tope
        explanation = QLabel(
            "Este panel te permite gestionar archivos de texto de códigos (.DIC) propios o del libro. "
            "Puedes validar su formato, buscar inconsistencias y cargarlos directamente al Inventario del Explorador."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #444444; font-size: 11px; font-weight: bold; background-color: #f7f7f7; padding: 10px; border-radius: 4px; border: 1px solid #e0e0e0; margin-bottom: 6px;")
        layout.addWidget(explanation, stretch=0)

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
        note.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        layout.addWidget(note, stretch=0)

        self.import_table = QTableWidget(0, 6)
        self.import_table.setHorizontalHeaderLabels(['Nombre', 'Ruta', 'Tipo', 'Tamano', 'Hash', 'Categoria'])
        self.import_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.import_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.import_table, stretch=1)

        # Botón para enviar el archivo DIC seleccionado a la pestaña Ejemplos
        btn_layout = QHBoxLayout()
        self.load_dic_btn = QPushButton("Cargar .DIC seleccionado en Ejemplos")
        self.load_dic_btn.setToolTip("Carga el archivo de códigos seleccionado en la pestaña de Ejemplos para poder visualizar sus códigos.")
        self.load_dic_btn.clicked.connect(self.load_selected_dic_to_examples)
        btn_layout.addWidget(self.load_dic_btn)
        btn_layout.addStretch(1)
        layout.addLayout(btn_layout, stretch=0)

        self.sections.addTab(widget, 'Inventario local')

    def _make_pdf_viewer(self, pdf_path: Path, title: str, fallback_html: str = '') -> QWidget:
        """Reusable validated PDF viewer using the shared widget implementation."""
        from ui.pdf_viewer import make_pdf_viewer
        return make_pdf_viewer(pdf_path, title, fallback_html)

    def _theory_page_browser(self):
        pdf_path = bundled_doc_path('manual_teorico_pedagogico.pdf')
        if not QT_PDF_AVAILABLE and not pdf_path.exists():
            # No PDF and no viewer: fall back to markdown text
            text = (
                self._read_asset('theory_intro.md') + '\n\n'
                + self._read_asset('code_grammar.md') + '\n\n'
                + self._read_asset('examples_readme.md')
            )
            return self._markdown_browser(text)
        return self._make_pdf_viewer(
            pdf_path,
            title='Manual te\u00f3rico pedag\u00f3gico',
        )

    def _pdf_guide_or_browser(self):
        pdf_path = bundled_doc_path('manual_explorador_sprott.pdf')
        if not QT_PDF_AVAILABLE and not pdf_path.exists():
            text = (
                self._read_asset('theory_intro.md') + '\n\n'
                + self._read_asset('code_grammar.md') + '\n\n'
                + self._read_asset('examples_readme.md')
            )
            return self._markdown_browser(text)
        return self._make_pdf_viewer(
            pdf_path,
            title='Manual pedag\u00f3gico del Explorador Sprott',
        )

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
        preset_name = self.preset_combo.currentText()
        self.preset_status_label.setText(
            f"Preset aplicado: {preset_name} → tipo={kind}, dim={dimension}, orden={order}, iter={iterations}, trans={transient}, h={h}, método={method}"
        )

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
        if not self.last_result:
            self.visual_preset_status_label.setText("Simula un código para ver el resultado.")
        else:
            self.visual_preset_status_label.setText(f"Preset visual «{name}» aplicado. Gráfica actualizada.")

    def quick_simulate(self):
        self.explore_code_edit.setText('EWMWAMMMPMMMM')
        self.apply_visual_preset('Color por profundidad')
        self.iter_spin.setValue(8000)
        self.simulate_exploration_code()
        if self.visual_preset_status_label:
            self.visual_preset_status_label.setText(
                '▶ Ejemplo rápido: EWMWAMMMPMMMM, 8000 iter., Color por profundidad. '
                'Pulsa 💾 Guardar en galería para conservarlo.'
            )

    def tutorial_apply_preset_and_show(self, preset_name: str):
        """Navigate to Exploración, apply visual preset, simulate if no trajectory exists."""
        self._go_to_tab('Explorac')
        self.visual_preset_combo.setCurrentText(preset_name)
        self.apply_visual_preset(preset_name)
        if not self.last_result:
            self.load_quick_example_for_preset(preset_name)
        else:
            self.apply_current_style()
        if self.visual_preset_status_label:
            self.visual_preset_status_label.setText(
                f'Preset «{preset_name}» aplicado desde Tutorial. '
                f'Cambió: proyección, color, paleta, fondo, punto, alpha, max_points.'
            )

    def load_quick_example_for_preset(self, preset_name: str):
        """Simulate a quick example to populate the canvas for the given preset."""
        # Try to find a starter example in the built-in list
        starter = None
        if hasattr(self, 'examples') and self.examples:
            for ex in self.examples:
                label = ex.get('label', '') or ex.get('name', '')
                if 'primera' in label.lower() or 'starter' in label.lower() or 'bonita' in label.lower():
                    starter = ex
                    break
            if starter is None:
                starter = self.examples[0]
        if starter:
            try:
                self.apply_example_to_controls(starter, apply_visual=True)
            except Exception as exc:
                LOGGER.warning(
                    'No se pudo aplicar el ejemplo inicial %r; se usará el código rápido.',
                    starter.get('id', starter.get('name', 'sin-id')),
                    exc_info=exc,
                )
        # Fall back to quick default code
        self.quick_simulate()

    def rerender_last_result(self):
        if self.last_result:
            self._plot_result(self.last_result)
            self.visual_preset_status_label.setText("Gráfica re-renderizada.")
        else:
            QMessageBox.information(self, 'Sin datos', 'Simula un código primero para poder re-renderizar.')

    def current_visual_config(self) -> SprottVisualConfig:
        projection = self.projection_combo.currentText()
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

    def use_code_in_exploration(self):
        code_text = self.code_edit.text().strip()
        self.explore_code_edit.setText(code_text)
        self._go_to_tab('Explorac')

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
                estimate = quick_lyapunov_estimate(
                    code,
                    steps=350,
                    h=self.h_spin.value(),
                    method=self.method_combo.currentText(),
                )
                value = (
                    f'{estimate.value:.4g}'
                    if np.isfinite(estimate.value)
                    else str(estimate.value)
                )
                context = [estimate.status, *estimate.warnings]
                lyap = (
                    value
                    if estimate.status == 'ok' and not estimate.warnings
                    else f"{value} [{'; '.join(context)}]"
                )
            except Exception as exc:
                lyap = f'error: {type(exc).__name__}: {exc}'
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
        if hasattr(self, 'canvas_empty_label'):
            self.canvas_empty_label.hide()

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
        
        lines = []
        if self.last_local_entry:
            lines.extend([
                '======================================================================',
                f"ORIGEN: Ejemplo local .DIC — Línea {self.last_local_entry.get('line', '?')}",
                f"Código: {self.last_local_entry.get('code', '')} | Familia: {self.last_local_entry.get('family', '')} ({code.family_name})",
                f"Soporte: {self.last_local_entry.get('support', 'N/A')} | F={self.last_local_entry.get('f_metric', 'N/A')} L={self.last_local_entry.get('l_metric', 'N/A')}",
                '======================================================================',
                '',
            ])

        lines.extend([
            'RESULTADO DE EXPLORACION',
            f'  codigo: {code.raw}',
            f'  familia: {code.family_name}',
            f'  backend: {result.get("backend", "python").upper()}',
            f'  tiempo de calculo: {elapsed_ms:.1f} ms',
        ])
        if attempts is not None:
            lines.append(f'  intentos de busqueda: {attempts}')
        lines.extend([
            f'  estado: {classification["state"]}',
            f'  lectura: {meaning}',
            f'  razon tecnica: {classification["reason"]}',
            f'  muestras post-transitorio finitas: {finite_count}',
            f'  porcentaje descartado por transitorio: {discarded_pct:.1f}%',
            f'  recomendacion visual: {visual_recommendation(result["post_transient"], classification)}',
        ])

        if classification['state'] == 'divergent':
            lines.extend([
                '',
                '⚠ Diverge o no produce puntos finitos.',
                'Sugerencias:',
                ' • Genera otro código aleatorio',
                ' • Si es flujo: reduce h (0.005) o cambia a RK4',
                ' • Sube el transitorio',
                ' • Verifica que la familia sea A-X (simulable)',
            ])

        lines.extend([
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
        self.recommended_examples_list.clear()
        try:
            self.examples = load_synthetic_examples()
        except Exception as exc:
            self.examples = []
            self.examples_list.addItem(f'No se pudieron cargar ejemplos: {exc}')
            return
        for idx, item in enumerate(self.examples):
            label = f"{item.get('category', 'sin categoria')} | {item.get('name', item.get('id', 'example'))}"
            self.examples_list.addItem(label)
            starter = item.get('starter_label')
            if starter:
                self.recommended_examples_list.addItem(f"{starter} -> {item.get('name', item.get('id', 'example'))}")
                self.recommended_examples_list.item(self.recommended_examples_list.count() - 1).setData(256, idx)
        if self.examples:
            self.examples_list.setCurrentRow(0)
            if self.recommended_examples_list.count() > 0:
                self.recommended_examples_list.setCurrentRow(0)

    def select_recommended_example(self, row: int):
        if row < 0:
            return
        item = self.recommended_examples_list.item(row)
        if not item:
            return
        idx = item.data(256)
        if idx is not None and 0 <= int(idx) < len(self.examples):
            self.examples_list.setCurrentRow(int(idx))

    def show_selected_example(self, row: int):
        if row < 0 or row >= len(self.examples):
            return
        item = self.examples[row]
        code = decode_code(item.get('code', ''))
        params = item.get('parameters', {})
        visual = item.get('visual', {})
        thumbnail = item.get('thumbnail', '')
        try:
            thumb_path = confined_png(self.assets_dir, thumbnail) if thumbnail else None
        except ImageSecurityError as exc:
            LOGGER.warning('Miniatura Sprott bloqueada: %s', exc)
            thumb_path = None
        if thumb_path is not None:
            self.example_thumbnail.set_image(thumb_path)
        else:
            self.example_thumbnail.clear()
        lines = [
            f"name: {item.get('name', '')}",
            f"category: {item.get('category', '')}",
            f"starter_label: {item.get('starter_label', '')}",
            f"source: {item.get('source', '')}",
            f"code: {item.get('code', '')}",
            f"family: {code.family_letter} | kind: {code.kind} | dimension: {code.dimension} | order: {code.order}",
            '',
            f"learning_goal: {item.get('learning_goal', '')}",
            f"visual_intent: {item.get('visual_intent', '')}",
            '',
            'recommended parameters:',
            json.dumps(params, indent=2, ensure_ascii=False),
            '',
            'recommended visual:',
            json.dumps(visual, indent=2, ensure_ascii=False),
            '',
            'equations:',
            item.get('equations', ''),
            '',
            f"notes: {item.get('notes', '')}",
        ]
        self.example_detail.setPlainText('\n'.join(lines))

    def _selected_example(self) -> dict | None:
        row = self.examples_list.currentRow()
        if row < 0 or row >= len(self.examples):
            return None
        return self.examples[row]

    def simulate_selected_example(self, apply_visual: bool = True):
        item = self._selected_example()
        if not item:
            return
        self.apply_example_to_controls(item, apply_visual=apply_visual)
        self.simulate_exploration_code()
        self._go_to_tab('Explorac')

    def apply_example_to_controls(self, item: dict, *, apply_visual: bool = True):
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
        if 'method' in params:
            self.method_combo.setCurrentText(str(params['method']))
        if 'divergence_threshold' in params:
            self.divergence_spin.setValue(float(params['divergence_threshold']))
        if apply_visual:
            self.apply_visual_dict(item.get('visual', {}))

    def apply_visual_dict(self, data: dict):
        if not data:
            return
        preset = data.get('preset')
        if preset:
            self.visual_preset_combo.setCurrentText(str(preset))
        setters = [
            ('projection', self.projection_combo.setCurrentText),
            ('color_by', self.color_by_combo.setCurrentText),
            ('palette', self.palette_combo.setCurrentText),
            ('background', self.background_combo.setCurrentText),
            ('draw_mode', self.draw_mode_combo.setCurrentText),
        ]
        for key, setter in setters:
            if key in data:
                setter(str(data[key]))
        if 'point_size' in data:
            self.point_size_spin.setValue(float(data['point_size']))
        if 'alpha' in data:
            self.alpha_spin.setValue(float(data['alpha']))
        if 'max_points' in data:
            self.max_plot_points_spin.setValue(int(data['max_points']))
        if 'show_axes' in data:
            self.axes_check.setChecked(bool(data['show_axes']))
        if 'show_grid' in data:
            self.grid_check.setChecked(bool(data['show_grid']))
        if 'equal_aspect' in data:
            self.equal_aspect_check.setChecked(bool(data['equal_aspect']))
        if 'band_count' in data:
            self.band_count_spin.setValue(int(data['band_count']))
        if 'export_dpi' in data:
            self.export_dpi_spin.setValue(int(data['export_dpi']))

    def decode_selected_example(self):
        item = self._selected_example()
        if not item:
            return
        self.code_edit.setText(item.get('code', ''))
        self.decode_current_code()
        self._go_to_tab('Codigos')

    def add_selected_example_to_gallery(self):
        item = self._selected_example()
        if not item:
            return
        self.apply_example_to_controls(item, apply_visual=True)
        self.simulate_exploration_code()
        self.favorite_note.setText(item.get('learning_goal', item.get('name', '')))
        self.save_current_gallery_entry()
        self._go_to_tab('Galeria')

    def export_selected_example_metadata(self):
        item = self._selected_example()
        if not item:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar metadata del ejemplo sintetico',
            str(gallery_root() / f"{item.get('id', 'sprott_example')}_metadata.json"),
            'JSON (*.json)',
        )
        if not path:
            return
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding='utf-8')

    def browse_local_dic(self):
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            'Seleccionar diccionario local de Sprott',
            str(self.repo_root / 'external'),
            'Sprott dictionaries (*.DIC *.dic);;All files (*)',
        )
        if path:
            self.local_dic_path_edit.setText(path)

    def show_sprott_instructions(self):
        """Show dialog with instructions to obtain original Sprott files."""
        msg = QMessageBox(self)
        msg.setWindowTitle('Instrucciones para obtener archivos originales')
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setTextFormat(Qt.TextFormat.RichText)
        
        text = (
            "<h3>📚 Obtener archivos originales de Sprott</h3>"
            "<p>La aplicación <b>Chaos Toolbox</b> no redistribuye los diccionarios ni archivos "
            "originales del libro de Julien C. Sprott por políticas de distribución y derechos de autor.</p>"
            "<p>Para estudiar el libro físico y cargar todos los ejemplos locales, sigue estos pasos:</p>"
            "<ol>"
            "<li>Visita el sitio oficial del Prof. Julien C. Sprott en la Universidad de Wisconsin-Madison: "
            "<b><a href='http://sprott.physics.wisc.edu'>sprott.physics.wisc.edu</a></b> (o busca <i>'Strange Attractors book disk'</i>).</li>"
            "<li>Descarga el archivo <b>SADISK.ZIP</b> (la versión del disquete original que acompaña al libro).</li>"
            "<li>Extrae los archivos en un directorio local de tu computadora.</li>"
            "<li>Usa el botón <b>«Elegir .DIC»</b> en esta pestaña para seleccionar el archivo deseado en tu disco.</li>"
            "</ol>"
            "<p><b>Descripción de los archivos principales del libro:</b></p>"
            "<ul>"
            "<li><b>BOOKFIGS.DIC:</b> Contiene todos los códigos de las figuras que aparecen impresas en el libro original.</li>"
            "<li><b>SELECTED.DIC:</b> Ejemplos seleccionados de atractores extraños y mapas caóticos.</li>"
            "<li><b>SPECIAL.DIC:</b> Familias especiales de ecuaciones descritas en el libro.</li>"
            "</ul>"
            "<p><i>Nota: Los archivos se leen directamente desde el directorio de tu disco en tiempo de ejecución "
            "y no se copia nada al repositorio ni al código del programa.</i></p>"
        )
        msg.setText(text)
        msg.exec()

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

    def load_local_dic_examples(self, limit=None):
        """Load DIC entries. limit=None loads all entries."""
        path = self.local_dic_path_edit.text().strip()
        self.local_dic_table.setRowCount(0)
        self.local_dic_detail.clear()
        self.local_dic_entries = []
        self.local_dic_visible_entries = []
        if not path:
            self.local_dic_detail.setPlainText('Selecciona primero un archivo .DIC local.')
            if hasattr(self, 'dic_status_label'):
                self.dic_status_label.setText('Sin archivo .DIC cargado.')
            return
        # Resolve limit from combo if not explicitly supplied
        if limit is None and hasattr(self, 'dic_load_limit_combo'):
            limit = self.dic_load_limit_combo.currentData()  # None means all
        try:
            if limit is None:
                self.local_dic_entries = read_dic_entries(path)
            else:
                self.local_dic_entries = read_dic_entries(path, limit=int(limit))
        except Exception as exc:
            self.local_dic_detail.setPlainText(f'No se pudo leer el .DIC local:\n{exc}')
            if hasattr(self, 'dic_status_label'):
                self.dic_status_label.setText(f'Error: {exc}')
            return
        self.apply_local_dic_filter()
        if hasattr(self, 'instrucciones_btn'):
            self.instrucciones_btn.setVisible(not self._find_local_dic('BOOKFIGS.DIC').exists())
        if self.local_dic_entries:
            preferred = 2 if len(self.local_dic_entries) > 2 and Path(path).name.upper() == 'SELECTED.DIC' else 0
            if self.local_dic_table.rowCount() > 0:
                self.local_dic_table.setCurrentCell(min(preferred, self.local_dic_table.rowCount() - 1), 0)
            # Update status counter
            if hasattr(self, 'dic_status_label'):
                total = len(self.local_dic_entries)
                simulable = sum(1 for e in self.local_dic_entries if e.get('support') == 'simulable')
                special = sum(1 for e in self.local_dic_entries if e.get('kind') == 'special')
                visible = len(self.local_dic_visible_entries)
                fname = Path(path).name
                self.dic_status_label.setText(
                    f'Archivo: {fname}  |  Leídos: {total}  |  '
                    f'Simulables: {simulable}  |  Especiales: {special}  |  '
                    f'Visibles (filtro actual): {visible}'
                )
        else:
            self.local_dic_detail.setPlainText('El archivo no contiene codigos reconocibles.')
            if hasattr(self, 'dic_status_label'):
                self.dic_status_label.setText(f'Archivo: {Path(path).name}  |  Sin códigos reconocibles.')

    def _load_bookfigs_full(self):
        """Select BOOKFIGS.DIC and load all entries — shortcut from UI."""
        path = self._find_local_dic('BOOKFIGS.DIC')
        if not path.exists():
            QMessageBox.warning(
                self, 'BOOKFIGS.DIC no encontrado',
                f'No se encontró BOOKFIGS.DIC en las rutas de búsqueda.\n'
                f'Ruta buscada: {path}\n\n'
                'Descarga la carpeta de datos del libro de Sprott y coloca los .DIC en external/sprott_site_bookdisk/...'
            )
            return
        
        # Selecciona BOOKFIGS.DIC en el combo de selección rápida
        idx = self.local_dic_quick_combo.findData('BOOKFIGS.DIC')
        if idx >= 0:
            self.local_dic_quick_combo.setCurrentIndex(idx)
            
        # Pone el selector de cantidad en 'Todos' (su userData es None)
        if hasattr(self, 'dic_load_limit_combo'):
            idx_all = self.dic_load_limit_combo.findData(None)
            if idx_all >= 0:
                self.dic_load_limit_combo.setCurrentIndex(idx_all)
                
        self.local_dic_path_edit.setText(str(path))
        self.load_local_dic_examples(limit=None)

    def _open_book_reading_mode(self):
        """Navigate to Ejemplos, load BOOKFIGS.DIC, and activate reading mode."""
        self._go_to_tab('Ejemplos')
        self._load_bookfigs_full()
        if not self.reading_mode_check.isChecked():
            self.reading_mode_check.setChecked(True)


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
            return support in ('simulable', 'simulable especial')
        if current_filter == 'simulables A-X':
            return support == 'simulable'
        if current_filter == 'especiales implementadas':
            return support == 'simulable especial'
        if current_filter == 'especiales pendientes':
            return support in ('familia especial pendiente', 'especial pendiente: validar AND/OR')
        if current_filter == 'Y valores absolutos':
            return entry.get('family') == 'Y'
        if current_filter == '[ potencias':
            return entry.get('family') == '['
        if current_filter == '\\ senos':
            return entry.get('family') == '\\'
        if current_filter == '] rotación':
            return entry.get('family') == ']'
        if current_filter == '^ oscilador':
            return entry.get('family') == '^'
        if current_filter == 'pendientes especiales':
            return support in ('familia especial pendiente', 'especial pendiente: validar AND/OR')
        if current_filter == 'errores de parsing':
            return support == 'error de parsing (corregible)' or entry.get('parse_strategy') == 'failed'
        if current_filter == 'candidatos corregibles':
            return support == 'error de parsing (corregible)' or entry.get('parse_strategy') == 'soft_cleaning'
        if current_filter == 'familias Y-Z':
            return entry.get('family') in ('Y', 'Z')
        if current_filter == 'familias desconocidas':
            return support == 'familia desconocida'
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
        simulable = entry.get('support') in {'simulable', 'simulable especial'}
        self.local_dic_sim_button.setEnabled(simulable)
        self.local_dic_style_button.setEnabled(simulable)
        if simulable:
            self.local_dic_sim_button.setToolTip(
                'Simula el código seleccionado con su implementación disponible.'
            )
            self.local_dic_style_button.setToolTip(
                'Simula el código seleccionado y aplica el estilo recomendado.'
            )
        else:
            reason = entry.get('support_reason') or entry.get('support', 'no simulable')
            self.local_dic_sim_button.setToolTip(f'No simulable: {reason}')
            self.local_dic_style_button.setToolTip(f'No simulable: {reason}')
        lines = [
            'REFERENCIA LOCAL DEL LIBRO',
            f"archivo: {entry['source_name']}",
            f"linea: {entry['line']}",
            f"linea original completa: {entry.get('raw_line', entry['code'])}",
            f"token original leido: {entry.get('raw_token', entry['code'])}",
            f"codigo normalizado: {entry['code']}",
            f"estrategia del parser: {entry.get('parse_strategy', 'directa')}",
            f"prefijo removido: {entry.get('prefix_removed', '') or '(ninguno)'}",
            f"confianza del candidato: {entry.get('candidate_confidence', 'alta')}",
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
            f"motivo: {entry.get('support_reason', 'Familia A-X implementada.')}",
            f"accion recomendada: {entry.get('recommended_action', 'Puedes simular este código.')}",
            '',
            'Nota: este codigo se lee desde tu archivo local. No se agrega a assets ni al repositorio.',
        ]
        if code.warnings:
            lines.extend(['', 'advertencias:'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.local_dic_detail.setPlainText('\n'.join(lines))

    def show_cleaning_test_dialog(self):
        from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QLabel, QHeaderView
        
        erroneous_entries = []
        for entry in self.local_dic_entries:
            support = entry.get('support')
            if support in ('familia desconocida', 'error de parsing (corregible)', 'error'):
                erroneous_entries.append(entry)
                
        if not erroneous_entries:
            QMessageBox.information(
                self, 'Prueba de Limpieza',
                'No se encontraron códigos no reconocidos o con errores en el archivo .DIC actualmente cargado.'
            )
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle('Prueba de limpieza de códigos no reconocidos')
        dialog.resize(900, 450)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            'Códigos que no se pudieron simular directamente pero para los cuales el parser '
            'encontró candidatos alternativos normalizados:'
        ))
        
        table = QTableWidget(len(erroneous_entries), 6, dialog)
        table.setHorizontalHeaderLabels([
            'Línea', 'Token original', 'Candidato propuesto', 'Estrategia', 'Soporte candidato', 'Acción'
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        for idx, entry in enumerate(erroneous_entries):
            table.setItem(idx, 0, QTableWidgetItem(str(entry.get('line', ''))))
            table.setItem(idx, 1, QTableWidgetItem(str(entry.get('raw_token', ''))))
            table.setItem(idx, 2, QTableWidgetItem(str(entry.get('code', ''))))
            table.setItem(idx, 3, QTableWidgetItem(str(entry.get('parse_strategy', ''))))
            table.setItem(idx, 4, QTableWidgetItem(str(entry.get('support', ''))))
            
            btn = QPushButton('Usar candidato')
            btn.clicked.connect(lambda _, e=entry, d=dialog: self.use_cleaned_candidate(e, d))
            table.setCellWidget(idx, 5, btn)
            
        layout.addWidget(table)
        
        close_btn = QPushButton('Cerrar', dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)
        
        dialog.exec()
        
    def use_cleaned_candidate(self, entry: dict, dialog: QDialog):
        dialog.accept()
        code_text = entry.get('code', '')
        
        self.explore_code_edit.setText(code_text)
        self.code_edit.setText(code_text)
        self.last_source = 'local_dic'
        self.last_local_entry = entry
        
        self._go_to_tab('Exploracion')
        self.quick_simulate()
    def show_special_family_dialog(self, entry: dict, code):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Familia especial de Sprott detectada')
        dialog.resize(550, 220)
        
        layout = QVBoxLayout(dialog)
        
        text = (
            "<b>Este código no falló por limpieza.</b><br/><br/>"
            f"La familia <b>{code.family_letter}</b> ({code.family_name}) pertenece a una "
            "familia especial de Sprott que todavía no está implementada en esta reimplementación.<br/>"
            "Puedes marcarla como pendiente de familia especial o revisar la referencia local."
        )
        lbl = QLabel(text, dialog)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        
        btn_pending = QPushButton('Marcar como pendiente', dialog)
        btn_pending.clicked.connect(lambda: self.mark_special_as_pending(entry, dialog))
        
        btn_backend = QPushButton('Abrir Backend explicado', dialog)
        btn_backend.clicked.connect(lambda: self.open_backend_explained_tab(dialog))
        
        btn_copy = QPushButton('Copiar código', dialog)
        btn_copy.clicked.connect(lambda: self.copy_code_to_clipboard(entry['code'], dialog))
        
        btn_issue = QPushButton('Crear issue/prompt', dialog)
        btn_issue.clicked.connect(lambda: self.create_special_family_issue_prompt(code, dialog))
        
        btn_layout.addWidget(btn_pending)
        btn_layout.addWidget(btn_backend)
        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_issue)
        
        layout.addLayout(btn_layout)
        
        close_btn = QPushButton('Cerrar', dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        dialog.exec()
        
    def mark_special_as_pending(self, entry: dict, dialog: QDialog):
        dialog.accept()
        if hasattr(self, 'dic_status_label'):
            self.dic_status_label.setText(f"Código {entry['code']} marcado como pendiente de familia especial.")
        QMessageBox.information(self, 'Familia especial', f"Código {entry['code']} registrado en el historial como pendiente.")
        
    def open_backend_explained_tab(self, dialog: QDialog):
        dialog.accept()
        self._go_to_tab('Backend explicado')
        
    def copy_code_to_clipboard(self, code_text: str, dialog: QDialog):
        dialog.accept()
        QApplication.clipboard().setText(code_text)
        QMessageBox.information(self, 'Copiado', f"Código {code_text} copiado al portapapeles.")
        
    def create_special_family_issue_prompt(self, code, dialog: QDialog):
        dialog.accept()
        prompt_text = (
            f"Por favor, implementa la familia especial '{code.family_letter}' ({code.family_name}) "
            f"en Chaos Toolbox. Código de prueba: {code.raw}"
        )
        QApplication.clipboard().setText(prompt_text)
        QMessageBox.information(
            self, 'Prompt Creado',
            "Se ha copiado al portapapeles un prompt estructurado para crear la issue/solicitar la implementación."
        )



    def simulate_selected_local_dic(self):
        entry = self._current_local_dic_entry()
        if not entry:
            QMessageBox.information(self, 'Sin codigo local', 'Selecciona un codigo del .DIC local primero.')
            return
        code = decode_code(entry['code'])
        if code.kind == 'special':
            from core.sprott.special_families import SPECIAL_FAMILY_REGISTRY
            family_entry = SPECIAL_FAMILY_REGISTRY.get(code.family_letter)
            if family_entry is None or isinstance(family_entry, dict):
                self.show_special_family_dialog(entry, code)
                return
            
            self.explore_code_edit.setText(entry['code'])
            self.code_edit.setText(entry['code'])
            self.last_source = 'local_dic'
            self.last_local_entry = entry
            
            # Map parameters for special family
            self.kind_combo.setCurrentText('map')
            self.iter_spin.setValue(max(self.iter_spin.value(), 32000))
            self.transient_spin.setValue(max(self.transient_spin.value(), 2000))
            self.divergence_spin.setValue(max(self.divergence_spin.value(), 1e9))
            
            self._set_combo_data(self.dimension_combo, code.dimension)
            self._set_combo_data(self.order_combo, code.order)
            self.simulate_exploration_code()
            self._go_to_tab('Explorac')
            return
            
        elif code.kind not in {'map', 'flow'}:
            QMessageBox.information(self, 'Familia no soportada', 'Esta familia de ecuaciones es desconocida y no se puede simular.')
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
        self._go_to_tab('Explorac')

    def simulate_selected_local_dic_recommended(self):
        entry = self._current_local_dic_entry()
        if not entry:
            QMessageBox.information(self, 'Sin codigo local', 'Selecciona un codigo del .DIC local primero.')
            return
        self.apply_visual_config_to_widgets(self._recommended_visual_for_entry(entry))
        self.simulate_selected_local_dic()

    def _recommended_visual_for_entry(self, entry: dict) -> SprottVisualConfig:
        if entry.get('kind') == 'special':
            config = visual_preset('Alta densidad')
            config.projection = 'x-y'
            config.color_by = 'w'
            config.background = 'negro'
            config.point_size = 1.0
            config.alpha = 0.3
            config.max_points = 32000
            return config
        if entry.get('kind') == 'flow':
            config = visual_preset('Color por profundidad')
            config.projection = '3D x-y-z' if entry.get('dimension', 0) >= 3 else 'x-y'
            config.color_by = 'z'
            config.max_points = 16000
            return config
        if entry.get('dimension', 0) >= 4:
            return visual_preset('Mapa 4D')
        if entry.get('dimension', 0) == 3:
            return visual_preset('Color por profundidad')
        if entry.get('dimension', 0) == 2:
            return visual_preset('Alta densidad')
        config = visual_preset('Didactico')
        config.projection = 'n-x'
        return config

    def apply_visual_config_to_widgets(self, config: SprottVisualConfig):
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

    def generate_local_gallery_from_dic(self):
        if not self.local_dic_visible_entries:
            QMessageBox.information(self, 'Sin codigos', 'Carga y filtra un .DIC local primero.')
            return
        limit = int(self.local_dic_gallery_limit_combo.currentData() or 10)
        saved = 0
        errors = 0
        for entry in self.local_dic_visible_entries:
            if saved >= limit:
                break
            if entry.get('support') != 'simulable':
                continue
            code = decode_code(entry['code'])
            config = self._recommended_visual_for_entry(entry)
            if code.kind == 'map':
                n_iter, transient, h, method = 12000, 2000, 0.01, 'rk4'
            else:
                n_iter, transient, h, method = 6500, 900, 0.01, 'rk4'
            try:
                result = simulate_candidate(
                    entry['code'],
                    n_iter=n_iter,
                    transient=transient,
                    h=h,
                    method=method,
                    divergence_threshold=1e9,
                    backend='c',
                )
                classification = classify_candidate(result['post_transient'], divergence_threshold=1e9)
                self.sprott_canvas.plot_trajectory(
                    result['post_transient'],
                    config,
                    title=f"Local .DIC {entry.get('source_name', '')}:{entry.get('line', '')}",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    tmpdir = Path(tmp)
                    render = self.sprott_canvas.export_image(tmpdir / 'render.png', dpi=config.export_dpi)
                    thumb = self.sprott_canvas.export_thumbnail(tmpdir / 'thumbnail.png')
                    metadata = build_metadata(
                        code=entry['code'],
                        source='local_dic',
                        source_file=entry.get('source_file', ''),
                        source_line=entry.get('line'),
                        simulation={
                            'iterations': n_iter,
                            'transient': transient,
                            'h': h,
                            'method': method,
                            'divergence_threshold': 1e9,
                        },
                        style=config.to_dict(),
                        classification=classification,
                        notes='Imagen generada localmente desde un codigo .DIC proporcionado por el usuario.',
                    )
                    save_gallery_entry(render_path=render, thumbnail_path=thumb, metadata=metadata)
                saved += 1
                QApplication.processEvents()
            except Exception:
                errors += 1
                continue
        self.refresh_gallery()
        QMessageBox.information(self, 'Galeria local', f'Imagenes guardadas: {saved}\nErrores u omitidos: {errors}')

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
        code = metadata.get('code', '?')
        if hasattr(self, 'visual_preset_status_label') and self.visual_preset_status_label:
            self.visual_preset_status_label.setText(
                f'💾 Guardado en galería: código {code} | {entry_dir.name}'
            )
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
        if item.get('source') == 'local_dic':
            lines.extend([
                '',
                f"generado por: {item.get('generated_by', '')}",
                f"atribución: {item.get('attribution', '')}",
                f"nota: {item.get('note', '')}",
            ])
        self.gallery_detail.setPlainText('\n'.join(lines))

    def open_selected_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        try:
            validated = load_gallery_entry(
                item.get('_entry_dir', ''), base=gallery_root()
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, 'Entrada no válida', str(exc))
            return
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(validated.get('_render_path', ''))
        )

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
        self._go_to_tab('Explorac')

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
        try:
            validated = load_gallery_entry(
                item.get('_entry_dir', ''), base=gallery_root()
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, 'Entrada no válida', str(exc))
            return
        render_path = Path(validated['_render_path'])
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar render de galeria',
            str(Path.home() / render_path.name),
            'PNG (*.png)',
        )
        if not path:
            return
        import shutil

        shutil.copyfile(render_path, Path(path))

    def delete_selected_gallery_entry(self):
        item = self._current_gallery_entry()
        if not item:
            return
        answer = QMessageBox.question(
            self,
            'Eliminar entrada',
            '¿Eliminar permanentemente esta entrada de la galería local?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_gallery_entry(
                item.get('_entry_dir', ''), base=gallery_root()
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, 'No se pudo eliminar', str(exc))
            return
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

    def load_selected_dic_to_examples(self):
        row = self.import_table.currentRow()
        if row < 0:
            QMessageBox.information(self, 'Sin selección', 'Selecciona una fila de la tabla primero.')
            return
        path_item = self.import_table.item(row, 1)
        if not path_item:
            return
        path_str = path_item.text().strip()
        path = Path(path_str)
        if not path.exists() or not path.is_file():
            QMessageBox.warning(self, 'Archivo no encontrado', f'El archivo no existe o no es válido: {path_str}')
            return
        if path.suffix.upper() != '.DIC':
            QMessageBox.warning(self, 'No es un archivo .DIC', 'Solo se pueden cargar archivos de texto con extensión .DIC en la sección de Ejemplos.')
            return
        
        self.local_dic_path_edit.setText(str(path))
        self.load_local_dic_examples()
        self._go_to_tab('Ejemplos')
        QMessageBox.information(self, 'Archivo cargado', f'Se ha cargado «{path.name}» en la pestaña de Ejemplos.')


    # -----------------------------------------------------------------------
    # Modo lectura del libro — panel UI y métodos de acción
    # -----------------------------------------------------------------------

    def _build_reading_panel(self) -> QWidget:
        """Construye la página 1 del QStackedWidget: modo lectura del libro."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(4)

        # ── Fila de filtros ────────────────────────────────────────────────
        filter_row = QWidget()
        fr_layout = QHBoxLayout(filter_row)
        fr_layout.setContentsMargins(0, 0, 0, 0)
        fr_layout.setSpacing(6)

        self.reading_filter_combo = QComboBox()
        self.reading_filter_combo.addItems([
            'todos',
            'solo simulables',
            'solo no vistos',
            'solo favoritos',
            'solo pendientes',
            'solo no coincide',
            'solo req. especial',
        ])
        self.reading_filter_combo.setToolTip('Filtra la tabla de lectura por estado de progreso.')
        self.reading_filter_combo.currentIndexChanged.connect(self.apply_reading_filter)

        self.reading_line_from = QSpinBox()
        self.reading_line_from.setRange(0, 999999)
        self.reading_line_from.setValue(0)
        self.reading_line_from.setToolTip('Línea inicial del capítulo actual (0 = sin límite inferior)')
        self.reading_line_from.setFixedWidth(70)
        self.reading_line_from.valueChanged.connect(self.apply_reading_filter)

        self.reading_line_to = QSpinBox()
        self.reading_line_to.setRange(0, 999999)
        self.reading_line_to.setValue(0)
        self.reading_line_to.setToolTip('Línea final del capítulo actual (0 = sin límite superior)')
        self.reading_line_to.setFixedWidth(70)
        self.reading_line_to.valueChanged.connect(self.apply_reading_filter)

        fr_layout.addWidget(QLabel('Filtro:'))
        fr_layout.addWidget(self.reading_filter_combo)
        fr_layout.addWidget(QLabel('  Capítulo (líneas):'))
        fr_layout.addWidget(self.reading_line_from)
        fr_layout.addWidget(QLabel('–'))
        fr_layout.addWidget(self.reading_line_to)
        fr_layout.addStretch(1)
        layout.addWidget(filter_row, stretch=0)

        # ── Splitter horizontal: tabla | detalle ───────────────────────────
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)

        # Tabla de 10 columnas
        self.reading_table = QTableWidget(0, 10)
        self.reading_table.setHorizontalHeaderLabels([
            'Línea', 'Código', 'Familia', 'Dim', 'Orden', 'F', 'L', 'Soporte', 'Marcas', 'Nota',
        ])
        hdr = self.reading_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        for col in (2, 3, 4, 5, 6):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.reading_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.reading_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reading_table.setToolTip('Doble clic para simular el código seleccionado.')
        self.reading_table.currentCellChanged.connect(
            lambda row, _c, _pr, _pc: self.show_selected_reading_entry(row)
        )
        self.reading_table.cellDoubleClicked.connect(lambda _r, _c: self.simulate_reading_entry())
        splitter.addWidget(self.reading_table)

        # Panel de detalle (derecha)
        detail_widget = QWidget()
        dw_layout = QVBoxLayout(detail_widget)
        dw_layout.setContentsMargins(4, 0, 0, 0)
        dw_layout.setSpacing(4)

        _dlabel = QLabel('<b>Detalle del código seleccionado</b>')
        dw_layout.addWidget(_dlabel, stretch=0)

        self.reading_detail = QTextEdit()
        self.reading_detail.setReadOnly(True)
        self.reading_detail.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;"
        )
        dw_layout.addWidget(self.reading_detail, stretch=1)

        # Campo de nota con botón Guardar inline
        _note_row = QWidget()
        _nr_layout = QHBoxLayout(_note_row)
        _nr_layout.setContentsMargins(0, 0, 0, 0)
        _nr_layout.addWidget(QLabel('Nota:'))
        self.reading_note_edit = QLineEdit()
        self.reading_note_edit.setPlaceholderText('Página, observación, capítulo...')
        self.reading_note_edit.returnPressed.connect(self.save_reading_note)
        _nr_layout.addWidget(self.reading_note_edit, stretch=1)
        _save_note_btn = QPushButton('Guardar')
        _save_note_btn.setToolTip('Guarda la nota de lectura para este código (también con Enter).')
        _save_note_btn.clicked.connect(self.save_reading_note)
        _nr_layout.addWidget(_save_note_btn)
        dw_layout.addWidget(_note_row, stretch=0)

        splitter.addWidget(detail_widget)
        splitter.setSizes([340, 300])
        layout.addWidget(splitter, stretch=1)

        # ── Botones fila 1: simulación ─────────────────────────────────────
        _ar1 = QWidget()
        _ar1_l = QHBoxLayout(_ar1)
        _ar1_l.setContentsMargins(0, 0, 0, 0)
        _ar1_l.setSpacing(6)

        self.reading_sim_button = QPushButton('▶ Simular')
        self.reading_sim_button.setToolTip('Simula el código seleccionado con los parámetros actuales.')
        self.reading_sim_button.clicked.connect(self.simulate_reading_entry)

        self.reading_sim_style_button = QPushButton('▶★ Simular con estilo rec.')
        self.reading_sim_style_button.setToolTip('Simula aplicando la configuración visual recomendada para la familia.')
        self.reading_sim_style_button.clicked.connect(self.simulate_reading_entry_recommended)

        self.reading_decode_button = QPushButton('Decodificar')
        self.reading_decode_button.setToolTip('Lleva el código a la pestaña Códigos para ver decodificación detallada.')
        self.reading_decode_button.clicked.connect(self.decode_reading_entry)

        _ar1_l.addWidget(self.reading_sim_button)
        _ar1_l.addWidget(self.reading_sim_style_button)
        _ar1_l.addWidget(self.reading_decode_button)
        _ar1_l.addStretch(1)
        layout.addWidget(_ar1, stretch=0)

        # ── Botones fila 2: galería, cita y marcas ─────────────────────────
        _ar2 = QWidget()
        _ar2_l = QHBoxLayout(_ar2)
        _ar2_l.setContentsMargins(0, 0, 0, 0)
        _ar2_l.setSpacing(4)

        self.reading_gallery_button = QPushButton('📷 Galería')
        self.reading_gallery_button.setToolTip(
            'Simula el código con estilo recomendado y guarda la imagen en la galería local '
            'con metadata enriquecida (línea del .DIC, marcas, nota, cita a Sprott).'
        )
        self.reading_gallery_button.clicked.connect(self.save_reading_to_gallery)

        self.reading_citation_button = QPushButton('📋 Copiar cita')
        self.reading_citation_button.setToolTip('Copia al portapapeles una cita académica apropiada para este código.')
        self.reading_citation_button.clicked.connect(self.copy_reading_citation)

        _ar2_l.addWidget(self.reading_gallery_button)
        _ar2_l.addWidget(self.reading_citation_button)

        _sep = QLabel('  |')
        _sep.setStyleSheet('color: #aaa;')
        _ar2_l.addWidget(_sep)

        # Botones de marca (checkables)
        _marks_config = [
            ('visto',             '✓ Visto',          '#2e7d32', '#e8f5e9'),
            ('favorito',          '★ Favorito',        '#e65100', '#fffde7'),
            ('pendiente',         '⏳ Pendiente',      '#bf360c', '#fff3e0'),
            ('no_coincide',       '✗ No coincide',     '#880e4f', '#fce4ec'),
            ('requiere_especial', '🔧 Req. especial',  '#4a148c', '#f3e5f5'),
        ]
        for mark_key, label, active_fg, active_bg in _marks_config:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setToolTip(f'Marcar / desmarcar "{mark_key}" para el código seleccionado.')
            btn.setStyleSheet(
                f'QPushButton:checked {{ background: {active_bg}; color: {active_fg}; '
                f'font-weight: bold; border: 1px solid {active_fg}; }}'
            )
            btn.toggled.connect(lambda checked, m=mark_key: self.toggle_reading_mark(m, checked))
            self._mark_buttons[mark_key] = btn
            _ar2_l.addWidget(btn)

        layout.addWidget(_ar2, stretch=0)
        return panel

    # ── Estado y persistencia ───────────────────────────────────────────────

    def _reload_reading_log(self):
        """Carga el log de marcas desde el JSON de usuario."""
        try:
            self._reading_log = load_reading_log()
            self._reading_log_load_error = None
        except ReadingLogError as exc:
            self._reading_log = {}
            self._reading_log_load_error = str(exc)
            QMessageBox.warning(
                self,
                'Diario de lectura no disponible',
                f'{exc}\nEl archivo existente no se sobrescribirá automáticamente.',
            )

    def _persist_reading_log(self, candidate_log=None):
        """Guarda el log de marcas al JSON de usuario."""
        load_error = getattr(self, '_reading_log_load_error', None)
        if load_error:
            QMessageBox.warning(
                self,
                'No se guardó el diario de lectura',
                'El diario existente no se sobrescribirá porque no pudo leerse. '
                'Corrige o mueve el archivo y reinicia la aplicación antes de guardar.\n'
                f'Detalle: {load_error}',
            )
            return False
        try:
            save_reading_log(self._reading_log if candidate_log is None else candidate_log)
        except ReadingLogError as exc:
            QMessageBox.warning(self, 'No se guardó el diario de lectura', str(exc))
            return False
        return True

    def _current_reading_entry(self) -> dict | None:
        """Entry actualmente seleccionado en la tabla de lectura, o None."""
        if not hasattr(self, 'reading_table'):
            return None
        row = self.reading_table.currentRow()
        if row < 0 or row >= len(self._reading_visible):
            return None
        return self._reading_visible[row]

    def _current_reading_key(self) -> str:
        """Clave del entry actualmente seleccionado, o ''."""
        entry = self._current_reading_entry()
        if not entry:
            return ''
        return entry_key(entry.get('source_name', ''), entry.get('line', 0))

    # ── Toggle del modo lectura ─────────────────────────────────────────────

    def toggle_reading_mode(self, checked: bool):
        """Alterna entre vista básica (página 0) y modo lectura (página 1)."""
        self._local_dic_stack.setCurrentIndex(1 if checked else 0)
        if checked:
            # Reutilizar entradas ya cargadas si están disponibles
            if hasattr(self, 'local_dic_entries') and self.local_dic_entries:
                self._reading_entries = list(self.local_dic_entries)
            else:
                self._reading_entries = []
            self._reload_reading_log()
            self.apply_reading_filter()

    # ── Filtrado y refresco de tabla ───────────────────────────────────────

    def apply_reading_filter(self, *_args):
        """Filtra _reading_entries → _reading_visible y actualiza la tabla."""
        if not hasattr(self, 'reading_filter_combo'):
            return
        current_filter = self.reading_filter_combo.currentText()
        line_from = self.reading_line_from.value()
        line_to = self.reading_line_to.value()

        visible = []
        for entry in self._reading_entries:
            line = entry.get('line', 0)
            # Filtro por rango de líneas (capítulo)
            if line_from > 0 and line < line_from:
                continue
            if line_to > 0 and line > line_to:
                continue
            # Filtro por marca/estado
            key = entry_key(entry.get('source_name', ''), line)
            log_entry = self._reading_log.get(key, {})
            marks = log_entry.get('marks', [])
            if current_filter == 'solo simulables' and entry.get('support') != 'simulable':
                continue
            if current_filter == 'solo no vistos' and 'visto' in marks:
                continue
            if current_filter == 'solo favoritos' and 'favorito' not in marks:
                continue
            if current_filter == 'solo pendientes' and 'pendiente' not in marks:
                continue
            if current_filter == 'solo no coincide' and 'no_coincide' not in marks:
                continue
            if current_filter == 'solo req. especial' and 'requiere_especial' not in marks:
                continue
            visible.append(entry)

        self._reading_visible = visible
        self._refresh_reading_table()

    def _refresh_reading_table(self):
        """Redibuja reading_table desde _reading_visible."""
        if not hasattr(self, 'reading_table'):
            return
        self.reading_table.setRowCount(0)
        for entry in self._reading_visible:
            line = entry.get('line', 0)
            key = entry_key(entry.get('source_name', ''), line)
            log_entry = self._reading_log.get(key, {})
            marks = log_entry.get('marks', [])
            note = log_entry.get('note', '')

            row = self.reading_table.rowCount()
            self.reading_table.insertRow(row)

            cols = [
                str(line),
                entry.get('code', ''),
                entry.get('family', ''),
                str(entry.get('dimension', '')),
                str(entry.get('order', '')),
                _metric_text(entry.get('f_metric')),
                _metric_text(entry.get('l_metric')),
                entry.get('support', ''),
                marks_icons_text(marks),
                (note[:40] + '…') if len(note) > 40 else note,
            ]
            for col, val in enumerate(cols):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col in {1, 9}:
                    item.setToolTip(str(val))
                self.reading_table.setItem(row, col, item)

            # Color de fondo según marca dominante
            color_hex = dominant_color(marks)
            if color_hex:
                brush = QBrush(QColor(color_hex))
                for col in range(10):
                    it = self.reading_table.item(row, col)
                    if it:
                        it.setBackground(brush)

    def _refresh_reading_row_marks(self, row: int, marks: list[str]):
        """Actualiza color e icono de marcas en una fila ya pintada."""
        if row < 0 or row >= self.reading_table.rowCount():
            return
        # Icono de marcas
        icons_item = self.reading_table.item(row, 8)
        if icons_item:
            icons_item.setText(marks_icons_text(marks))
        # Color de fondo
        color_hex = dominant_color(marks)
        for col in range(10):
            it = self.reading_table.item(row, col)
            if it:
                if color_hex:
                    it.setBackground(QBrush(QColor(color_hex)))
                else:
                    it.setBackground(QBrush())

    # ── Panel de detalle ───────────────────────────────────────────────────

    def show_selected_reading_entry(self, row: int):
        """Rellena el panel de detalle con el código seleccionado en modo lectura."""
        if not hasattr(self, 'reading_detail'):
            return
        if row < 0 or row >= len(self._reading_visible):
            return
        entry = self._reading_visible[row]
        code_text = entry.get('code', '')
        key = entry_key(entry.get('source_name', ''), entry.get('line', 0))
        log_entry = self._reading_log.get(key, {})
        marks = log_entry.get('marks', [])
        note = log_entry.get('note', '')

        try:
            code = decode_code(code_text)
        except Exception as exc:
            LOGGER.warning(
                'No se pudo decodificar la entrada de lectura %s:%s.',
                entry.get('source_name', 'desconocido'), entry.get('line', '?'),
                exc_info=exc,
            )
            self.reading_detail.setPlainText(f'No se pudo decodificar: {code_text}')
            return

        # Ecuaciones reconstruidas (sin simulación)
        eq_text = '(no disponible para esta familia)'
        try:
            if code.kind == 'map':
                from core.sprott.families import PolynomialMapFamily
                fam = PolynomialMapFamily(code.dimension, code.order, code.coefficients)
                eq_text = fam.equations_text()
            elif code.kind == 'flow':
                from core.sprott.families import PolynomialFlowFamily
                fam = PolynomialFlowFamily(code.dimension, code.order, code.coefficients)
                eq_text = fam.equations_text()
        except Exception as exc:
            LOGGER.warning(
                'No se pudieron reconstruir ecuaciones para %s:%s.',
                entry.get('source_name', 'desconocido'), entry.get('line', '?'),
                exc_info=exc,
            )

        # Parámetros recomendados
        if code.kind == 'map':
            rec_params = 'iter: 12 000 | transient: 2 000 | h: N/A'
        elif code.kind == 'flow':
            rec_params = 'iter: 6 000 | transient: 800 | h: 0.01 | método: RK4'
        else:
            rec_params = 'familia especial — no simulable todavía'

        # Visual recomendado (reutiliza lógica existente si está disponible)
        try:
            vis_cfg = self._recommended_visual_for_entry(entry)
            vis_desc = f'proyección {vis_cfg.projection} | color {vis_cfg.color_by} | paleta {vis_cfg.palette}'
        except Exception as exc:
            LOGGER.warning(
                'No se pudo obtener la configuración visual para %s:%s.',
                entry.get('source_name', 'desconocido'), entry.get('line', '?'),
                exc_info=exc,
            )
            vis_desc = '(no disponible)'

        # Advertencia de soporte
        support = entry.get('support', '')
        warning_lines = []
        if support != 'simulable':
            warning_lines.append(f'⚠ No simulable todavía: {support}')
        if code.warnings:
            warning_lines.extend(f'  · {w}' for w in code.warnings)

        lines = [
            f'Código:      {code_text}',
            f'Fuente:      {entry.get("source_name", "")}  línea {entry.get("line", "")}',
            f'Familia:     {code.family_letter} → {code.family_name}',
            f'Tipo:        {code.kind} | Dim: {code.dimension} | Orden: {code.order}',
            f'Coeficientes: {len(code.coefficients)} recibidos',
            '',
            'Ecuaciones:',
            eq_text,
            '',
            f'Params rec.: {rec_params}',
            f'Visual rec.: {vis_desc}',
        ]
        if warning_lines:
            lines += [''] + warning_lines

        self.reading_detail.setPlainText('\n'.join(lines))

        # Nota actual
        self.reading_note_edit.setText(note)

        # Estado de botones de marca
        for mark_key, btn in self._mark_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(mark_key in marks)
            btn.blockSignals(False)

    # ── Acciones ───────────────────────────────────────────────────────────

    def simulate_reading_entry(self):
        """Simula el código seleccionado en modo lectura (sin cambiar visual)."""
        entry = self._current_reading_entry()
        if not entry:
            return
        code_text = entry.get('code', '')
        try:
            code = decode_code(code_text)
        except Exception as exc:
            QMessageBox.warning(self, 'Error de decodificación', str(exc))
            return
        if code.kind not in {'map', 'flow'}:
            QMessageBox.information(
                self, 'Familia no soportada',
                f'La familia «{code.family_name}» no es simulable todavía en esta versión.'
            )
            return
        # Cargar en la pestaña de exploración y simular
        self.explore_code_edit.setText(code_text)
        self.code_edit.setText(code_text)
        self.last_source = 'local_dic'
        self.last_local_entry = entry
        if hasattr(self, '_set_combo_data'):
            self._set_combo_data(self.dimension_combo, code.dimension)
            self._set_combo_data(self.order_combo, code.order)
        if code.kind == 'map':
            self.kind_combo.setCurrentText('map')
            self.iter_spin.setValue(max(self.iter_spin.value(), 12000))
            self.transient_spin.setValue(max(self.transient_spin.value(), 2000))
        else:
            self.kind_combo.setCurrentText('flow')
            self.iter_spin.setValue(max(self.iter_spin.value(), 5000))
            self.transient_spin.setValue(max(self.transient_spin.value(), 800))
            self.h_spin.setValue(min(self.h_spin.value(), 0.01))
        self.simulate_exploration_code()
        self._go_to_tab('Explorac')

    def simulate_reading_entry_recommended(self):
        """Simula el código seleccionado aplicando el visual recomendado."""
        entry = self._current_reading_entry()
        if not entry:
            return
        try:
            cfg = self._recommended_visual_for_entry(entry)
            self.apply_visual_config_to_widgets(cfg)
        except Exception as exc:
            LOGGER.warning(
                'No se pudo aplicar la configuración recomendada para %s:%s.',
                entry.get('source_name', 'desconocido'), entry.get('line', '?'),
                exc_info=exc,
            )
        self.simulate_reading_entry()

    def decode_reading_entry(self):
        """Envía el código a la pestaña Códigos y lo decodifica."""
        entry = self._current_reading_entry()
        if not entry:
            return
        self.code_edit.setText(entry.get('code', ''))
        self.decode_current_code()
        self._go_to_tab('Codigos')

    def save_reading_note(self):
        """Persiste la nota del campo de texto en el log de usuario."""
        key = self._current_reading_key()
        if not key:
            return
        candidate_log = deepcopy(self._reading_log)
        entry = self._current_reading_entry()
        if entry:
            candidate_log = set_code(
                candidate_log, key,
                entry.get('code', ''), entry.get('source_name', ''), entry.get('line', 0)
            )
        candidate_log = set_note(candidate_log, key, self.reading_note_edit.text())
        if not self._persist_reading_log(candidate_log):
            return
        self._reading_log = candidate_log
        # Refrescar celda de nota en la fila actual
        row = self.reading_table.currentRow()
        if 0 <= row < self.reading_table.rowCount():
            note = self.reading_note_edit.text()
            item = self.reading_table.item(row, 9)
            if item:
                item.setText((note[:40] + '…') if len(note) > 40 else note)
                item.setToolTip(note)

    def save_reading_to_gallery(self):
        """Simula el código seleccionado y guarda la imagen en la galería con metadata enriquecida."""
        entry = self._current_reading_entry()
        if not entry:
            QMessageBox.information(self, 'Sin selección', 'Selecciona un código en la tabla primero.')
            return
        code_text = entry.get('code', '')
        try:
            code = decode_code(code_text)
        except Exception as exc:
            QMessageBox.warning(self, 'Error', str(exc))
            return
        if code.kind not in {'map', 'flow'}:
            QMessageBox.information(
                self, 'Familia no soportada',
                'Solo se pueden guardar en galería familias A-X simulables.'
            )
            return

        key = self._current_reading_key()
        log_entry = self._reading_log.get(key, {})
        try:
            cfg = self._recommended_visual_for_entry(entry)
        except Exception:
            cfg = self.current_visual_config()

        n_iter = 12000 if code.kind == 'map' else 6000
        transient = 2000 if code.kind == 'map' else 800

        try:
            result = simulate_candidate(
                code_text, n_iter=n_iter, transient=transient,
                h=0.01, method='rk4', divergence_threshold=1e9, backend='c',
            )
            classification = classify_candidate(result['post_transient'], divergence_threshold=1e9)
            self.sprott_canvas.plot_trajectory(
                result['post_transient'], cfg,
                title=f"Lectura: {entry.get('source_name', '')}:{entry.get('line', '')}",
            )
            with tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                render = self.sprott_canvas.export_image(tmpdir / 'render.png', dpi=cfg.export_dpi)
                thumb = self.sprott_canvas.export_thumbnail(tmpdir / 'thumbnail.png')
                metadata = build_metadata(
                    code=code_text,
                    source='local_dic',
                    source_file=entry.get('source_file', ''),
                    source_line=entry.get('line'),
                    simulation={
                        'iterations': n_iter, 'transient': transient,
                        'h': 0.01, 'method': 'rk4', 'divergence_threshold': 1e9,
                    },
                    style=cfg.to_dict(),
                    classification=classification,
                    notes=log_entry.get('note', ''),
                )
                metadata['dic_source_file'] = entry.get('source_file', '')
                metadata['dic_source_name'] = entry.get('source_name', '')
                metadata['dic_source_line'] = entry.get('line')
                metadata['reading_marks'] = log_entry.get('marks', [])
                metadata['reading_note'] = log_entry.get('note', '')
                metadata['sprott_citation'] = (
                    'Julien C. Sprott, Strange Attractors: Creating Patterns in Chaos, '
                    'M&T Books, 1993. Imagen generada por Chaos Toolbox como reimplementacion '
                    'educativa propia. No redistribuye archivos originales del libro.'
                )
                save_gallery_entry(render_path=render, thumbnail_path=thumb, metadata=metadata)
            self.refresh_gallery()
            QMessageBox.information(
                self, 'Galería',
                f'Imagen guardada en la galería local.\nCódigo: {code_text}',
            )
        except Exception as exc:
            QMessageBox.critical(self, 'Error al guardar en galería', str(exc))

    def copy_reading_citation(self):
        """Copia una cita académica apropiada al portapapeles."""
        entry = self._current_reading_entry()
        code_text = entry.get('code', '') if entry else ''
        citation = (
            'Imagen generada por Chaos Toolbox como reimplementacion educativa inspirada en '
            'Julien C. Sprott, Strange Attractors: Creating Patterns in Chaos, M&T Books, 1993.'
            + (f' Codigo: {code_text}.' if code_text else '')
            + ' No redistribuye archivos ni texto originales del libro.'
        )
        QApplication.clipboard().setText(citation)

    def toggle_reading_mark(self, mark: str, checked: bool):
        """Activa o desactiva una marca para la entrada seleccionada y persiste."""
        key = self._current_reading_key()
        if not key:
            # No hay selección — revertir visualmente el botón
            btn = self._mark_buttons.get(mark)
            if btn:
                btn.blockSignals(True)
                btn.setChecked(not checked)
                btn.blockSignals(False)
            return
        # Asegurarse de que los metadatos del código están en el log
        candidate_log = deepcopy(self._reading_log)
        entry = self._current_reading_entry()
        if entry:
            candidate_log = set_code(
                candidate_log, key,
                entry.get('code', ''), entry.get('source_name', ''), entry.get('line', 0)
            )
        candidate_log = set_mark(candidate_log, key, mark, checked)
        if not self._persist_reading_log(candidate_log):
            btn = self._mark_buttons.get(mark)
            if btn:
                btn.blockSignals(True)
                btn.setChecked(not checked)
                btn.blockSignals(False)
            return
        self._reading_log = candidate_log
        # Actualizar color e iconos de la fila actual
        row = self.reading_table.currentRow()
        marks = self._reading_log.get(key, {}).get('marks', [])
        self._refresh_reading_row_marks(row, marks)


    # -----------------------------------------------------------------------
    # Backend explicado — constructor de subpestaña y acciones
    # -----------------------------------------------------------------------

    def _build_backend_explained_tab(self):
        """Construye la subpestaña 'Backend explicado' con flujo paso a paso."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Encabezado informativo ──────────────────────────────────────────
        intro = QLabel(
            '<b>Backend explicado</b> — muestra el pipeline completo que la toolbox '
            'aplica al código seleccionado: limpieza, decodificación de familia, '
            'conteo de monomios, matriz de coeficientes, ecuaciones, condición inicial, '
            'método de simulación, criterios de clasificación y configuración visual.'
        )
        intro.setWordWrap(True)
        intro.setStyleSheet('padding: 6px; background: #f0f4ff; border-radius: 4px;')
        layout.addWidget(intro, stretch=0)

        # ── Fila de botones ─────────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        self.explain_button = QPushButton('▶  Explicar código actual')
        self.explain_button.setToolTip(
            'Toma el código del campo Exploración y genera una explicación '
            'textual didáctica de todo el pipeline interno.'
        )
        self.explain_button.setStyleSheet(
            'QPushButton { font-weight: bold; padding: 5px 12px; '
            'background: #2563eb; color: white; border-radius: 4px; }'
            'QPushButton:hover { background: #1d4ed8; }'
        )
        self.explain_button.clicked.connect(self.explain_current_code)

        self.export_explain_button = QPushButton('⬇  Exportar explicación Markdown')
        self.export_explain_button.setToolTip(
            'Guarda la explicación generada como archivo .md legible con cualquier editor.'
        )
        self.export_explain_button.setEnabled(False)
        self.export_explain_button.clicked.connect(self.export_explanation_markdown)

        btn_layout.addWidget(self.explain_button)
        btn_layout.addWidget(self.export_explain_button)
        btn_layout.addStretch(1)
        layout.addWidget(btn_row, stretch=0)

        # ── Área de texto con la explicación ────────────────────────────────
        self.explain_output = QTextEdit()
        self.explain_output.setReadOnly(True)
        self.explain_output.setStyleSheet(
            "font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; "
            "background: #ffffff;"
        )
        self.explain_output.setPlainText(
            'Pulsa ▶ Explicar código actual para ver el pipeline completo.\n\n'
            'Se usará el código que aparece en el campo Código de la pestaña Exploración. '
            'Si aún no has simulado nada, el análisis se hace solo con el texto del campo; '
            'si ya simulaste, la configuración visual actual también se incluye.\n\n'
            '=============================================================\n'
            'Familias soportadas por la Chaos Toolbox:\n\n'
            'Soportadas actualmente:\n'
            'A-P: mapas polinomiales 1D-4D, orden 2-5\n'
            'Q-X: flujos polinomiales 3D-4D, orden 2-5\n\n'
            'Reconocidas pero pendientes:\n'
            'Y/Z y familias especiales adicionales\n\n'
            'No reconocidas:\n'
            'caracteres/familias sin entrada en SPECIAL_FAMILIES\n'
            '============================================================='
        )
        layout.addWidget(self.explain_output, stretch=1)

        self.sections.addTab(widget, 'Backend explicado')

    def explain_current_code(self):
        """Genera y muestra la explicación didáctica del pipeline para el código actual."""
        code = self.explore_code_edit.text().strip()
        if not code:
            code = self.code_edit.text().strip()
        if not code:
            self.explain_output.setPlainText('No hay código para explicar. Escribe o genera uno primero.')
            return

        n_iter = self.iter_spin.value()
        transient = self.transient_spin.value()
        h = self.h_spin.value()
        method = self.method_combo.currentText()
        visual_cfg = self.current_visual_config() if hasattr(self, 'projection_combo') else None

        try:
            self._last_explanation = explain_code_pipeline(
                code=code,
                n_iter=n_iter,
                transient=transient,
                h=h,
                method=method,
                visual_config=visual_cfg,
            )
        except Exception as exc:
            self.explain_output.setPlainText(f'Error al generar la explicación:\n{exc}')
            return

        md_text = format_explanation_markdown(self._last_explanation)

        # Renderizar como HTML enriquecido usando el conversor interno de la pestaña
        try:
            html_doc = _markdown_to_clean_html(md_text, webengine=False, asset_root=self.assets_dir)
            self.explain_output.setHtml(html_doc)
        except Exception:
            self.explain_output.setPlainText(md_text)

        self.export_explain_button.setEnabled(True)

        # Navegar a la subpestaña Backend explicado
        self._go_to_tab('Backend explicado')

    def export_explanation_markdown(self):
        """Exporta la explicación actualmente mostrada como archivo .md."""
        if not self._last_explanation:
            QMessageBox.information(
                self,
                'Sin explicación',
                'Genera primero una explicación pulsando ▶ Explicar código actual.',
            )
            return
        code_raw = self._last_explanation.get('raw_code', 'sprott')
        default_name = f'explicacion_{code_raw[:16].replace(" ", "_")}.md'
        path, _filter = QFileDialog.getSaveFileName(
            self,
            'Exportar explicación Markdown',
            str(Path.home() / default_name),
            'Markdown (*.md);;Texto plano (*.txt)',
        )
        if not path:
            return
        md_text = format_explanation_markdown(self._last_explanation)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(md_text, encoding='utf-8')
        QMessageBox.information(
            self,
            'Exportación completada',
            f'Explicación guardada en:\n{path}',
        )


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
                caption = _inline_html(alt.strip())
                try:
                    image_src = _asset_image_src(src.strip(), asset_root)
                except ImageSecurityError as exc:
                    LOGGER.warning('Imagen Markdown bloqueada: %s', exc)
                    parts.append(
                        '<p class="blocked-image">Imagen bloqueada: '
                        f'{caption}</p>'
                    )
                else:
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
                clean_line = re.sub(r"^\d+\.\s+", "", line)
                parts.append(f'<p>{_inline_html(clean_line)}</p>')
            else:
                close_list()
                parts.append(f'<p>{_inline_html(line)}</p>')
    close_list()
    parts.append('</body></html>')
    return ''.join(parts)


def _asset_image_src(src: str, asset_root: Path | None) -> str:
    if asset_root is None:
        raise ImageSecurityError('No se configuro una raiz local para la imagen.')
    return confined_png(asset_root, src).as_uri()


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
