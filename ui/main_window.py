from __future__ import annotations

import os
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Event

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtCore import QProcess, QSettings, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from core.app_metadata import (
    ACADEMIC_NOTICE,
    APP_DEVELOPER,
    APP_DESCRIPTION,
    APP_LICENSE,
    APP_NAME,
    APP_ORGANIZATION,
    APP_RELEASE_DATE,
    APP_RELEASE_STATUS,
    APP_VERSION,
    APP_YEAR,
    APP_DOI,
    APP_DOI_URL,
    DEFAULT_RELEASE_API_URL,
    DOCUMENTATION_ENTRY,
    RELEASE_API_ENV,
    UPDATE_CHECK_INTERVAL_DAYS,
)
from core.paths import bundled_doc_path, ensure_user_data_dir, resource_path
from core.time_policy import utc_today_iso
from core.update_checker import (
    UpdateCheckError,
    UpdateDownloadError,
    UpdateInfo,
    VerifiedUpdate,
    check_for_updates,
    download_verified_update,
    verify_update_before_launch,
)
from core.hidden_engine import engine_status
from ui.custom_system_tab import NoCodeSystemTab
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
        self.settings = QSettings(APP_ORGANIZATION, APP_NAME)
        self._update_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='chaos-updates')
        self._update_future: Future | None = None
        self._update_timer: QTimer | None = None
        self._download_future: Future | None = None
        self._download_timer: QTimer | None = None
        self._update_cancel_event = Event()
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')

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

        self._create_menus()

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
        self.build_custom_system_tab()
        self.build_sprott_explorer_tab()

        self.tabs.currentChanged.connect(self.on_main_tab_changed)
        QTimer.singleShot(1500, self._maybe_check_updates_on_startup)

    def _create_menus(self):
        # 1. Menú Archivo
        file_menu = self.menuBar().addMenu('Archivo')

        results_action = QAction('Abrir carpeta de resultados', self)
        results_action.triggered.connect(self.open_results_folder)
        file_menu.addAction(results_action)

        file_menu.addSeparator()

        exit_action = QAction('Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 2. Menú Ayuda
        help_menu = self.menuBar().addMenu('Ayuda')

        docs_action = QAction('Documentacion', self)
        docs_action.triggered.connect(self.open_documentation)
        help_menu.addAction(docs_action)

        help_menu.addSeparator()

        updates_action = QAction('Buscar actualizaciones', self)
        updates_action.triggered.connect(lambda: self._start_update_check(silent=False))
        help_menu.addAction(updates_action)

        self.auto_update_action = QAction('Revisar actualizaciones automaticamente', self)
        self.auto_update_action.setCheckable(True)
        auto_enabled = self.settings.value('updates/automatic_enabled', True, type=bool)
        self.auto_update_action.setChecked(auto_enabled)
        self.auto_update_action.toggled.connect(
            lambda checked: self.settings.setValue('updates/automatic_enabled', checked)
        )
        help_menu.addAction(self.auto_update_action)

        help_menu.addSeparator()

        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)


    def open_documentation(self):
        doc_path = resource_path(DOCUMENTATION_ENTRY)
        if not doc_path.exists():
            doc_path = resource_path('README.md')
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(doc_path)))

    def open_results_folder(self):
        target = ensure_user_data_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Acerca de {APP_NAME}')
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser(dialog)
        browser.setOpenExternalLinks(True)
        docs_path = resource_path(DOCUMENTATION_ENTRY)
        release_source = self._release_api_url() or f'Configurable con {RELEASE_API_ENV}'
        browser.setHtml(
            '<html><body style="font-family: Segoe UI, Arial, sans-serif; line-height: 1.45;">'
            f'<h2>{APP_NAME}</h2>'
            f'<p><b>Version:</b> {APP_VERSION}<br>'
            f'<b>Desarrolladora:</b> {APP_DEVELOPER}<br>'
            f'<b>Código propio:</b> {APP_LICENSE}<br>'
            '<b>Dependencias de terceros:</b> conservan sus licencias; consulte '
            '<code>THIRD_PARTY_NOTICES.md</code> incluido con la aplicación.<br>'
            f'<b>Anio:</b> {APP_YEAR}<br>'
            f'<b>Estado:</b> {APP_RELEASE_STATUS} ({APP_RELEASE_DATE})<br>'
            f'<b>DOI de proyecto/archivo actual:</b> <a href="{APP_DOI_URL}">{APP_DOI}</a></p>'
            f'<p>{APP_DESCRIPTION}</p>'
            f'<p><b>Cómo citar / How to cite:</b><br>'
            '<span style="font-family: Consolas, monospace; background-color: #f3f4f6; padding: 6px; display: block; border-left: 4px solid #3b82f6; font-size: 11px; color: #1f2937;">'
            f'Moreno Lopez, M. F. (2026). <i>Fyskode Chaotic Systems Toolbox</i> '
            f'(Version {APP_VERSION}). '
            f'Project archive DOI: {APP_DOI}'
            '</span></p>'
            f'<p><b>Creditos principales:</b> Python, PySide6, NumPy, Matplotlib, pyqtgraph y PyInstaller.</p>'
            f'<p><b>Documentacion local:</b> {docs_path}</p>'
            f'<p><b>Fuente de actualizaciones:</b> {release_source}</p>'
            '<p><b>Sistemas personalizados:</b> El editor visual permite definir flujos y mapas mediante '
            'expresiones restringidas, validarlos y simularlos con Hidden Attractors FO cuando el motor '
            'compatible esta disponible.</p>'
            f'<p><b>Uso academico:</b> {ACADEMIC_NOTICE}</p>'
            '</body></html>'
        )
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.resize(580, 480)
        dialog.exec()

    def _release_api_url(self) -> str:
        environment_override = os.environ.get(RELEASE_API_ENV, '').strip()
        if environment_override:
            return environment_override
        configured = self.settings.value('updates/release_api_url', '', type=str)
        return str(configured or '').strip() or DEFAULT_RELEASE_API_URL

    def _maybe_check_updates_on_startup(self):
        if not self.settings.value('updates/automatic_enabled', True, type=bool):
            return
        if not self._release_api_url():
            return
        last = self.settings.value('updates/last_check_date', '', type=str)
        if last:
            try:
                elapsed = (date.fromisoformat(utc_today_iso()) - date.fromisoformat(last)).days
                if elapsed < UPDATE_CHECK_INTERVAL_DAYS:
                    return
            except ValueError:
                pass
        self._start_update_check(silent=True)

    def _start_update_check(self, *, silent: bool):
        if self._update_future and not self._update_future.done():
            if not silent:
                QMessageBox.information(self, 'Actualizaciones', 'Ya hay una revision de actualizaciones en curso.')
            return
        release_api_url = self._release_api_url()
        if not release_api_url:
            if not silent:
                QMessageBox.information(
                    self,
                    'Actualizaciones',
                    'No hay fuente de releases configurada. Define '
                    f'{RELEASE_API_ENV} con la URL de GitHub Releases latest, por ejemplo '
                    'https://api.github.com/repos/OWNER/REPO/releases/latest.',
                )
            return
        if hasattr(self, 'info_label'):
            self.info_label.setText('Buscando actualizaciones...')
        self._update_future = self._update_executor.submit(
            check_for_updates,
            installed_version=APP_VERSION,
            release_api_url=release_api_url,
        )
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(250)
        self._update_timer.timeout.connect(lambda: self._poll_update_future(self._update_future, silent=silent))
        self._update_timer.start()

    def _poll_update_future(self, future: Future | None, *, silent: bool):
        if future is None or not future.done():
            return
        if self._update_timer:
            self._update_timer.stop()
            self._update_timer.deleteLater()
            self._update_timer = None
        try:
            info = future.result()
        except UpdateCheckError as exc:
            if hasattr(self, 'info_label'):
                self.info_label.setText('Listo.')
            if not silent:
                QMessageBox.warning(self, 'Actualizaciones', str(exc))
            return
        self.settings.setValue('updates/last_check_date', utc_today_iso())
        self._handle_update_info(info, silent=silent)

    def _handle_update_info(self, info: UpdateInfo, *, silent: bool):
        if hasattr(self, 'info_label'):
            self.info_label.setText('Listo.')
        if not info.update_available:
            if not silent:
                QMessageBox.information(
                    self,
                    'Actualizaciones',
                    f'{APP_NAME} {info.installed_version} ya está actualizado. '
                    f'La versión estable más reciente es {info.latest_version}.',
                )
            return

        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle('Actualizacion disponible')
        message.setText(f'Hay una nueva version de {APP_NAME}.')
        details = (
            f'Instalada: {info.installed_version}\n'
            f'Disponible: {info.latest_version}\n'
            f'Publicada: {info.published_at}\n'
            f'Artefacto: {info.asset_name or "no encontrado para esta plataforma"}\n\n'
            f'{info.summary}'
        )
        if info.download_url and not info.checksum_url:
            details += (
                '\n\nEl release no incluye SHA256SUMS. La descarga integrada está '
                'deshabilitada para evitar ejecutar un archivo sin verificar.'
            )
        message.setInformativeText(details)
        download_button = None
        if info.download_url and info.checksum_url:
            download_button = message.addButton(
                'Descargar y verificar', QMessageBox.ButtonRole.AcceptRole
            )
        notes_button = None
        if info.release_notes_url:
            notes_button = message.addButton(
                'Ver notas del release', QMessageBox.ButtonRole.ActionRole
            )
        later_button = message.addButton(
            'Recordar después', QMessageBox.ButtonRole.RejectRole
        )
        message.exec()
        clicked = message.clickedButton()
        if clicked is download_button:
            self._start_update_download(info)
        elif clicked is notes_button and info.release_notes_url:
            QDesktopServices.openUrl(QUrl(info.release_notes_url))
        elif clicked is later_button:
            return

    def _start_update_download(self, info: UpdateInfo):
        if self._download_future and not self._download_future.done():
            QMessageBox.information(
                self,
                'Actualizaciones',
                'Ya hay una descarga de actualización en curso.',
            )
            return
        update_directory = ensure_user_data_dir() / 'updates'
        self._update_cancel_event = Event()
        if hasattr(self, 'info_label'):
            self.info_label.setText(
                f'Descargando y verificando {info.asset_name or "el instalador"}...'
            )
        self._download_future = self._update_executor.submit(
            download_verified_update,
            info=info,
            destination_dir=update_directory,
            cancel_event=self._update_cancel_event,
        )
        self._download_timer = QTimer(self)
        self._download_timer.setInterval(250)
        self._download_timer.timeout.connect(self._poll_update_download_future)
        self._download_timer.start()

    def _poll_update_download_future(self):
        future = self._download_future
        if future is None or not future.done():
            return
        if self._download_timer:
            self._download_timer.stop()
            self._download_timer.deleteLater()
            self._download_timer = None
        if hasattr(self, 'info_label'):
            self.info_label.setText('Listo.')
        try:
            verified = future.result()
        except (UpdateCheckError, UpdateDownloadError) as exc:
            QMessageBox.warning(self, 'Actualización no descargada', str(exc))
            return
        self._offer_verified_installer(verified)

    def _offer_verified_installer(self, verified: VerifiedUpdate):
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Question)
        message.setWindowTitle('Instalador verificado')
        reused = ' (archivo local reutilizado)' if verified.reused_existing_file else ''
        message.setText(
            f'{APP_NAME} {verified.version} fue descargado y verificado con SHA-256{reused}.'
        )
        message.setInformativeText(
            'SHA-256 verifica la integridad frente al manifiesto, pero no sustituye '
            'una firma de código; los instaladores actuales aún no están '
            'firmados. Guarda tu trabajo antes de continuar. ¿Deseas ejecutar ahora '
            'el instalador? La instalación no se inicia automáticamente.'
        )
        message.setDetailedText(
            f'Archivo: {verified.path}\n'
            f'Tamaño: {verified.size} bytes\n'
            f'SHA-256: {verified.sha256}'
        )
        run_button = message.addButton(
            'Ejecutar instalador', QMessageBox.ButtonRole.AcceptRole
        )
        message.addButton('Más tarde', QMessageBox.ButtonRole.RejectRole)
        message.exec()
        if message.clickedButton() is not run_button:
            return
        try:
            started = self._launch_verified_installer(verified)
        except UpdateDownloadError as exc:
            QMessageBox.warning(self, 'Instalador modificado', str(exc))
            return
        if not started:
            QMessageBox.warning(
                self,
                'No se pudo iniciar el instalador',
                f'El archivo verificado permanece disponible en:\n{verified.path}',
            )
            return
        if hasattr(self, 'info_label'):
            self.info_label.setText(
                'Instalador iniciado con confirmación del usuario.'
            )

    @staticmethod
    def _launch_verified_installer(verified: VerifiedUpdate) -> bool:
        installer = verify_update_before_launch(verified)
        if sys.platform.startswith('win'):
            started = QProcess.startDetached(
                str(installer), [], str(installer.parent)
            )
            if isinstance(started, tuple):
                return bool(started[0])
            return bool(started)
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(installer)))

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
        self.tabs.addTab(self.tab_fft_widget, 'Espectro')

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

        from ui.pdf_viewer import PdfViewerWidget

        self.manual_tabs = QTabWidget(self.tab_dict)
        manual_specs = (
            (
                'Usuario',
                'manual_usuario_toolbox_chaos.pdf',
                'Manual de usuario de Toolbox Chaos',
            ),
            (
                'Teoría y diccionario',
                'manual_teorico_pedagogico.pdf',
                'Manual teórico pedagógico de sistemas dinámicos y caos',
            ),
            (
                'Explorador Sprott',
                'manual_explorador_sprott.pdf',
                'Manual pedagógico del Explorador Sprott',
            ),
        )
        self.manual_viewers = {}
        self.manual_pdf_paths = {}
        for tab_label, filename, title in manual_specs:
            pdf_path = bundled_doc_path(filename)
            viewer = PdfViewerWidget(
                pdf_path=pdf_path,
                title=title,
                fallback_html=self._manual_fallback_html(title, pdf_path),
                parent=self.manual_tabs,
            )
            self.manual_pdf_paths[filename] = str(pdf_path)
            self.manual_viewers[filename] = viewer
            self.manual_tabs.addTab(viewer, tab_label)

        # Compatibility aliases retained for capture helpers and extensions.
        self.dictionary_pdf_path = self.manual_pdf_paths[
            'manual_teorico_pedagogico.pdf'
        ]
        self.pdf_viewer = self.manual_viewers[
            'manual_teorico_pedagogico.pdf'
        ]
        layout.addWidget(self.manual_tabs, stretch=1)
        self.tabs.addTab(self.tab_dict, 'Manuales')

    def build_custom_system_tab(self):
        self.tab_custom_system = NoCodeSystemTab(self, self)
        self.tabs.addTab(self.tab_custom_system, 'Crear sistema')

    def build_sprott_explorer_tab(self):
        self.tab_sprott = SprottExplorerTab(self)
        self.tabs.addTab(self.tab_sprott, 'Explorador Sprott')

    def on_main_tab_changed(self, _index):
        is_sprott = (
            hasattr(self, 'tab_sprott')
            and self.tabs.currentWidget() is self.tab_sprott
        )
        if hasattr(self, 'info_label'):
            is_custom = (
                hasattr(self, 'tab_custom_system')
                and self.tabs.currentWidget() is self.tab_custom_system
            )
            if is_sprott:
                self.info_label.setText(
                    'Explorador Sprott: los controles de sistemas clasicos quedan ocultos; carga/crea codigos, simula, ajusta estilo y guarda/exporta dentro de esta pestana.'
                )
            elif is_custom:
                status = engine_status()
                self.info_label.setText(
                    'Editor visual de sistemas: ' + status.message
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

    def _manual_fallback_html(self, title: str, pdf_path: Path) -> str:
        pdf_uri = QUrl.fromLocalFile(str(pdf_path)).toString()
        return (
            '<html><body style="font-family: Segoe UI, Arial, sans-serif; margin: 14px;">'
            f'<h2>{title}</h2>'
            '<p>Este manual está disponible como PDF. Abre el archivo de forma '
            'externa si el visor embebido no está disponible.</p>'
            f'<p><a href="{pdf_uri}">Abrir manual</a></p>'
            '</body></html>'
        )

    def closeEvent(self, event):
        self._update_cancel_event.set()
        self._update_executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
