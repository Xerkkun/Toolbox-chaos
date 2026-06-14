from __future__ import annotations

import html
import os
import re
from pathlib import Path
from time import perf_counter

import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
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
from core.sprott.references import index_local_reference_folder, read_dic_entries
from core.sprott.search import classify_candidate, generate_random_code, simulate_candidate
from ui.math_render import render_math_to_path
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
        self.last_result = None
        self.last_classification = None

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
        self.h_spin = _double_spin(0.01, 1e-5, 1.0, 5, EXPLORATION_HELP['h'])
        self.method_combo = QComboBox()
        self.method_combo.addItems(['rk4', 'euler'])
        self.method_combo.setToolTip(EXPLORATION_HELP['method'])
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

        layout.addWidget(controls, 1, 0)
        self.explore_plot = pg.PlotWidget(title='Trayectoria Sprott')
        self.explore_plot.setBackground('w')
        self.explore_plot.showGrid(x=True, y=True, alpha=0.2)
        layout.addWidget(self.explore_plot, 1, 1, 2, 1)

        self.explore_output = QTextEdit()
        self.explore_output.setReadOnly(True)
        self.explore_output.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        layout.addWidget(self.explore_output, 2, 0)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(2, 1)
        self.sections.addTab(widget, 'Exploracion')
        self.apply_preset()

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
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        default_dic = self.repo_root / 'external' / 'sprott_site_bookdisk' / 'files' / 'fractals' / 'bookdisk' / 'SELECTED.DIC'
        self.local_dic_path_edit = QLineEdit(str(default_dic) if default_dic.exists() else '')
        self.local_dic_path_edit.setToolTip('Ruta a BOOKFIGS.DIC, SELECTED.DIC o SPECIAL.DIC descargado localmente. No se redistribuye.')
        browse_dic = QPushButton('Elegir .DIC')
        browse_dic.setToolTip('Selecciona un diccionario local del libro. La app solo lo lee desde tu disco.')
        browse_dic.clicked.connect(self.browse_local_dic)
        load_dic = QPushButton('Cargar codigos')
        load_dic.setToolTip('Lee codigos del .DIC local y los lista como referencias externas locales.')
        load_dic.clicked.connect(self.load_local_dic_examples)
        path_layout.addWidget(self.local_dic_path_edit, stretch=1)
        path_layout.addWidget(browse_dic)
        path_layout.addWidget(load_dic)
        local_layout.addWidget(path_row)
        self.local_dic_list = QListWidget()
        self.local_dic_list.setToolTip('Codigos leidos desde tu archivo .DIC local. No son assets publicos del repositorio.')
        self.local_dic_list.currentRowChanged.connect(self.show_selected_local_dic)
        local_layout.addWidget(self.local_dic_list, stretch=1)
        self.local_dic_detail = QTextEdit()
        self.local_dic_detail.setReadOnly(True)
        self.local_dic_detail.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        local_layout.addWidget(self.local_dic_detail, stretch=1)
        self.local_dic_sim_button = QPushButton('Simular codigo local seleccionado')
        self.local_dic_sim_button.setToolTip('Carga el codigo local en Exploracion y lo simula con el backend C si la familia A-X esta soportada.')
        self.local_dic_sim_button.clicked.connect(self.simulate_selected_local_dic)
        local_layout.addWidget(self.local_dic_sim_button)
        layout.addWidget(local_box, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

        self._load_examples()
        if self.local_dic_path_edit.text():
            self.load_local_dic_examples(limit=120)
        self.sections.addTab(widget, 'Ejemplos')

    def _build_gallery_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.favorite_note = QLineEdit()
        self.favorite_note.setPlaceholderText('Notas del favorito')
        self.favorite_note.setToolTip('Texto libre para recordar por que guardaste este codigo.')
        save_button = QPushButton('Guardar favorito actual')
        save_button.setToolTip('Guarda codigo, ecuaciones, parametros, clasificacion y notas en tu carpeta de usuario.')
        save_button.clicked.connect(self.save_current_favorite)
        refresh_button = QPushButton('Actualizar lista')
        refresh_button.setToolTip('Recarga el JSON local de favoritos.')
        refresh_button.clicked.connect(self.refresh_favorites)
        top_layout.addWidget(self.favorite_note, stretch=1)
        top_layout.addWidget(save_button)
        top_layout.addWidget(refresh_button)
        layout.addWidget(top, stretch=0)
        self.favorites_label = QLabel(f'Archivo local: {favorites_path()}')
        self.favorites_label.setWordWrap(True)
        layout.addWidget(self.favorites_label, stretch=0)
        self.favorites_list = QListWidget()
        layout.addWidget(self.favorites_list, stretch=1)
        self.refresh_favorites()
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
        self.decode_current_code()
        self.explore_output.setPlainText('Codigo generado. Pulsa "Simular y graficar" para ver su trayectoria.')

    def simulate_exploration_code(self):
        code = self.explore_code_edit.text().strip()
        if not code:
            self.generate_code()
            code = self.explore_code_edit.text().strip()
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
        max_attempts = 24
        local_codes = []
        if self.local_dic_entries:
            current = max(0, self.local_dic_list.currentRow())
            ordered = self.local_dic_entries[current:] + self.local_dic_entries[:current]
            local_codes = [entry['code'] for entry in ordered[:max_attempts]]
        for attempt in range(1, max_attempts + 1):
            if attempt <= len(local_codes):
                code = local_codes[attempt - 1]
            else:
                code = generate_random_code(
                    self.kind_combo.currentText(),
                    self.dimension_combo.currentData(),
                    self.order_combo.currentData(),
                    rng,
                )
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
            last = (attempt, code, result, classification)
            if classification['state'] == 'candidate_chaotic':
                break
        if last is None:
            return
        attempt, code, result, classification = last
        self.explore_code_edit.setText(code)
        self.code_edit.setText(code)
        self.last_result = result
        self.last_classification = classification
        elapsed_ms = 1000.0 * (perf_counter() - started)
        self._plot_result(result)
        self._show_result_summary(result, classification, elapsed_ms, attempts=attempt)
        self.decode_current_code()

    def _plot_result(self, result: dict):
        trajectory = np.asarray(result['post_transient'], dtype=float)
        trajectory = trajectory[np.all(np.isfinite(trajectory), axis=1)]
        self.explore_plot.clear()
        if len(trajectory) == 0:
            self.explore_plot.setTitle('Sin muestras finitas')
            return
        max_points = 7000
        if len(trajectory) > max_points:
            idx = np.linspace(0, len(trajectory) - 1, max_points).astype(int)
            trajectory = trajectory[idx]
        if trajectory.shape[1] == 1:
            self.explore_plot.plot(np.arange(len(trajectory)), trajectory[:, 0], pen=pg.mkPen('#111827', width=1.1))
            self.explore_plot.setLabel('bottom', 'n')
            self.explore_plot.setLabel('left', 'x')
        else:
            self.explore_plot.plot(trajectory[:, 0], trajectory[:, 1], pen=None, symbol='o', symbolSize=2, symbolBrush='#111827')
            self.explore_plot.setLabel('bottom', 'x')
            self.explore_plot.setLabel('left', 'y')
        self.explore_plot.setTitle(f"Trayectoria post-transitorio - {result['code'].family_letter} ({len(trajectory)} puntos graficados)")

    def _show_result_summary(self, result: dict, classification: dict, elapsed_ms: float, attempts: int | None = None):
        code = result['code']
        finite_count = int(np.sum(np.all(np.isfinite(result['post_transient']), axis=1)))
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
            '',
            'QUE ESTAS VIENDO',
            '  La grafica muestra la orbita despues de descartar el transitorio.',
            '  En dimension 1 se grafica x contra n. En dimension mayor se muestra la proyeccion x-y.',
            '',
            'ECUACIONES',
            result['equations'],
        ])
        if code.warnings:
            lines.extend(['', 'ADVERTENCIAS'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.explore_output.setPlainText('\n'.join(lines))

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

    def load_local_dic_examples(self, limit=300):
        path = self.local_dic_path_edit.text().strip()
        self.local_dic_list.clear()
        self.local_dic_detail.clear()
        self.local_dic_entries = []
        if not path:
            self.local_dic_detail.setPlainText('Selecciona primero un archivo .DIC local.')
            return
        try:
            self.local_dic_entries = read_dic_entries(path, limit=int(limit))
        except Exception as exc:
            self.local_dic_detail.setPlainText(f'No se pudo leer el .DIC local:\n{exc}')
            return
        for entry in self.local_dic_entries:
            metrics = ' '.join(entry.get('metrics', [])[:2])
            suffix = f' | {metrics}' if metrics else ''
            self.local_dic_list.addItem(f"{entry['line']:04d} | {entry['code']}{suffix}")
        if self.local_dic_entries:
            preferred = 2 if len(self.local_dic_entries) > 2 and Path(path).name.upper() == 'SELECTED.DIC' else 0
            self.local_dic_list.setCurrentRow(preferred)
        else:
            self.local_dic_detail.setPlainText('El archivo no contiene codigos reconocibles.')

    def show_selected_local_dic(self, row: int):
        if row < 0 or row >= len(self.local_dic_entries):
            return
        entry = self.local_dic_entries[row]
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
            '',
            'Nota: este codigo se lee desde tu archivo local. No se agrega a assets ni al repositorio.',
        ]
        if code.warnings:
            lines.extend(['', 'advertencias:'])
            lines.extend(f'  - {warning}' for warning in code.warnings)
        self.local_dic_detail.setPlainText('\n'.join(lines))

    def simulate_selected_local_dic(self):
        row = self.local_dic_list.currentRow()
        if row < 0 or row >= len(self.local_dic_entries):
            QMessageBox.information(self, 'Sin codigo local', 'Selecciona un codigo del .DIC local primero.')
            return
        entry = self.local_dic_entries[row]
        code = decode_code(entry['code'])
        if code.kind not in {'map', 'flow'}:
            QMessageBox.information(self, 'Familia no soportada', 'Esta fase simula familias polinomiales A-X. Las especiales quedan pendientes.')
            return
        self.explore_code_edit.setText(entry['code'])
        self.code_edit.setText(entry['code'])
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

    def refresh_favorites(self):
        self.favorites_list.clear()
        try:
            favorites = load_favorites()
        except Exception as exc:
            self.favorites_list.addItem(f'No se pudieron leer favoritos: {exc}')
            return
        for item in favorites:
            self.favorites_list.addItem(f"{item.get('date', '')} | {item.get('code', '')} | {item.get('notes', '')}")

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
