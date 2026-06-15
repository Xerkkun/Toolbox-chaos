from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from ui.sprott_explorer_tab import SprottExplorerTab
from ui.tab_controls import (
    Tab3DWidget,
    Tab2DWidget,
    TabTimeSeriesWidget,
    TabComparisonWidget,
    TabFFTWidget,
    TabLyapunovWidget,
    TabBifurcationWidget,
    TabBasinWidget,
    TabSpectrumWidget,
    TabCoexistenceWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Banco de pruebas de sistemas caóticos')

        # Adaptive sizing — respect monitor boundaries
        _screen = QApplication.primaryScreen()
        _avail = _screen.availableGeometry() if _screen else None
        if _avail:
            _w = min(1720, int(_avail.width() * 0.92))
            _h = min(980, int(_avail.height() * 0.90))
            _w = max(_w, 1150)
            _h = max(_h, 720)
            self.resize(_w, _h)
            self.move(
                _avail.x() + (_avail.width() - _w) // 2,
                _avail.y() + (_avail.height() - _h) // 2,
            )
        else:
            self.resize(1400, 900)

        # Shared state for trajectory / simulation results
        self.last_t = None
        self.last_X = None
        self.last_system_key = None
        self.last_params = None

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Main Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Status bottom bar
        self.info_label = QLabel('Listo.')
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            'font-size: 11px; color: #555555; padding: 4px; background: #f9f9f9; border-top: 1px solid #e0e0e0;'
        )
        main_layout.addWidget(self.info_label)

        # Build tabs
        self.build_3d_tab()
        self.build_2d_tab()
        self.build_time_tab()
        self.build_method_comparison_tab()
        self.build_fft_tab()
        self.build_lyapunov_tab()
        self.build_bifurcation_tab()
        self.build_basin_tab()
        self.build_spectrum_tab()
        self.build_coexistence_tab()
        self.build_dictionary_tab()
        self.build_sprott_explorer_tab()

        self.tabs.currentChanged.connect(self.on_main_tab_changed)

    def build_3d_tab(self):
        self.tab_3d_widget = Tab3DWidget(self, self)
        self.tabs.addTab(self.tab_3d_widget, 'Atractor 3D')

    def build_2d_tab(self):
        self.tab_2d_widget = Tab2DWidget(self, self)
        self.tabs.addTab(self.tab_2d_widget, 'Retratos 2D')

    def build_time_tab(self):
        self.tab_time_widget = TabTimeSeriesWidget(self, self)
        self.tabs.addTab(self.tab_time_widget, 'Series temporales')

    def build_method_comparison_tab(self):
        self.tab_method_compare_widget = TabComparisonWidget(self, self)
        self.tabs.addTab(self.tab_method_compare_widget, 'Comparar metodos')

    def build_fft_tab(self):
        self.tab_fft_widget = TabFFTWidget(self, self)
        self.tabs.addTab(self.tab_fft_widget, 'FFT')

    def build_lyapunov_tab(self):
        self.tab_lyap_widget = TabLyapunovWidget(self, self)
        self.tabs.addTab(self.tab_lyap_widget, 'Lyapunov')

    def build_bifurcation_tab(self):
        self.tab_bif_widget = TabBifurcationWidget(self, self)
        self.tabs.addTab(self.tab_bif_widget, 'Bifurcación')

    def build_basin_tab(self):
        self.tab_basin_widget = TabBasinWidget(self, self)
        self.tabs.addTab(self.tab_basin_widget, 'Cuenca de atracción')

    def build_spectrum_tab(self):
        self.tab_spectrum_widget = TabSpectrumWidget(self, self)
        self.tabs.addTab(self.tab_spectrum_widget, 'Autovalores')

    def build_coexistence_tab(self):
        self.tab_coexistence_widget = TabCoexistenceWidget(self, self)
        self.tabs.addTab(self.tab_coexistence_widget, 'Coexistencia')

    def build_dictionary_tab(self):
        self.tab_dict = QWidget()
        layout = QVBoxLayout(self.tab_dict)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        assets_dir = Path(__file__).resolve().parent.parent / 'assets'
        self.dictionary_pdf_path = str(assets_dir / 'chaos_dictionary.pdf')

        from ui.pdf_viewer import PdfViewerWidget

        self.pdf_viewer = PdfViewerWidget(
            pdf_path=self.dictionary_pdf_path,
            title='Diccionario de conceptos',
            fallback_html=self._dictionary_html(),
            parent=self.tab_dict,
        )
        layout.addWidget(self.pdf_viewer, stretch=1)
        self.tabs.addTab(self.tab_dict, 'Diccionario')

    def build_sprott_explorer_tab(self):
        self.tab_sprott = SprottExplorerTab(self)
        self.tabs.addTab(self.tab_sprott, 'Explorador Sprott')

    def on_main_tab_changed(self, _index):
        is_sprott = (
            hasattr(self, 'tab_sprott')
            and self.tabs.currentWidget() is self.tab_sprott
        )
        if hasattr(self, 'info_label'):
            if is_sprott:
                self.info_label.setText(
                    'Explorador Sprott: los controles de sistemas clasicos quedan ocultos; carga/crea codigos, simula, ajusta estilo y guarda/exporta dentro de esta pestana.'
                )
            else:
                self.info_label.setText('Listo.')

    def open_dictionary_pdf(self):
        if hasattr(self, 'dictionary_pdf_path') and os.path.exists(
            self.dictionary_pdf_path
        ):
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(self.dictionary_pdf_path)
            )

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
        }
        for filter_text, suffix in filter_map.items():
            if filter_text in selected_filter:
                return f'{file_path}{suffix}'
        return file_path


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
