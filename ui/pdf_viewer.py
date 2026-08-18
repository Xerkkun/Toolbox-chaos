from __future__ import annotations

import html
from pathlib import Path

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTextBrowser,
)

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    QT_PDF_AVAILABLE = True
except Exception:
    QPdfDocument = None
    QPdfView = None
    QT_PDF_AVAILABLE = False


class PdfViewerWidget(QWidget):
    """A reusable, self-contained PDF viewer widget with robust fallback capabilities

    and explicit diagnostics, designed to render documents via PySide6.QtPdf
    or fall back gracefully to a QTextBrowser.
    """

    def __init__(
        self,
        pdf_path: Path | str,
        title: str,
        fallback_html: str = '',
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.pdf_path = Path(pdf_path)
        self.title = title
        self.fallback_html = fallback_html

        self._pdf_document = None
        self._pdf_view = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        status_parts: list[str] = []
        file_ok = self.pdf_path.exists()
        status_parts.append(
            f'Archivo: {"OK " + self.pdf_path.name if file_ok else "NO ENCONTRADO — " + str(self.pdf_path)}'
        )
        status_parts.append(
            f'QtPdf: {"disponible" if QT_PDF_AVAILABLE else "NO disponible"}'
        )

        open_btn = QPushButton(f'Abrir {self.pdf_path.name} externamente')
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self.pdf_path))
            )
        )
        open_btn.setEnabled(file_ok)
        layout.addWidget(open_btn, stretch=0)

        status_label = QLabel()
        status_label.setWordWrap(True)
        status_label.setStyleSheet(
            'font-size: 10px; color: #444; padding: 3px 6px; '
            'background: #f5f5f5; border-radius: 3px; border: 1px solid #ddd;'
        )
        layout.addWidget(status_label, stretch=0)

        viewer_ok = False
        if QT_PDF_AVAILABLE and file_ok:
            try:
                document = QPdfDocument(self)
                load_err = document.load(str(self.pdf_path))
                is_no_error = False
                if hasattr(QPdfDocument, 'Error') and hasattr(
                    QPdfDocument.Error, 'None_'
                ):
                    is_no_error = load_err == QPdfDocument.Error.None_
                else:
                    try:
                        is_no_error = int(load_err) == 0
                    except (ValueError, TypeError):
                        is_no_error = (
                            str(load_err)
                            in ('0', 'Error.None_', 'None_', 'NoError')
                            or 'None' in str(load_err)
                        )

                page_count = document.pageCount()
                load_ok = is_no_error and (page_count > 0)
                status_parts.append(
                    f'load()={repr(load_err)}, páginas={page_count}'
                )
                if not load_ok:
                    status_parts.append('⚠ El PDF no cargó correctamente')
                else:
                    view = QPdfView(self)
                    view.setDocument(document)
                    if hasattr(view, 'setZoomMode'):
                        view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
                    if hasattr(view, 'setPageMode'):
                        view.setPageMode(QPdfView.PageMode.MultiPage)

                    # Keep references alive
                    self._pdf_document = document
                    self._pdf_view = view
                    layout.addWidget(view, stretch=1)
                    viewer_ok = True
            except Exception as exc:
                status_parts.append(f'Error: {exc}')
        elif not QT_PDF_AVAILABLE:
            status_parts.append(
                'Instala PySide6-Addons de la misma versión que PySide6 '
                'para habilitar el visor embebido'
            )

        status_label.setText('  \u2502  '.join(status_parts))

        if not viewer_ok:
            fallback = QTextBrowser()
            fallback.setOpenExternalLinks(True)
            if self.fallback_html:
                fallback.setHtml(self.fallback_html)
            else:
                pdf_uri = QUrl.fromLocalFile(str(self.pdf_path)).toString()
                fallback.setHtml(
                    '<html><body style="font-family: Segoe UI, Arial, sans-serif; margin: 14px;">'
                    f'<h2>{html.escape(self.title)}</h2>'
                    '<p>El visor embebido no está disponible (ver estado arriba).</p>'
                    f'<p><a href="{html.escape(pdf_uri)}">Abrir PDF externamente</a></p>'
                    '</body></html>'
                )
            layout.addWidget(fallback, stretch=1)


def make_pdf_viewer(
    pdf_path: Path | str, title: str, fallback_html: str = ''
) -> QWidget:
    """Helper function matching the signature of the previous implementation."""
    return PdfViewerWidget(pdf_path, title, fallback_html)
