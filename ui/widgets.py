from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QWidget,
)


class HelpButton(QToolButton):
    def __init__(self, help_html: str, parent=None):
        super().__init__(parent)
        self._help_html = help_html
        self.setText('?')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(help_html)
        self.setWhatsThis(help_html)
        self.setAutoRaise(True)
        self.setFixedSize(16, 16)
        self.setStyleSheet(
            'QToolButton {'
            ' border: 1px solid #777;'
            ' border-radius: 8px;'
            ' font-size: 10px;'
            ' font-weight: bold;'
            ' padding: 0px;'
            '}'
        )
        self.clicked.connect(self.show_help_dialog)

    def show_help_dialog(self):
        box = QMessageBox(self)
        box.setWindowTitle('Ayuda del parámetro')
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(self._help_html)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()


def make_double_spin(value, minimum, maximum, decimals, step=None):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setValue(value)
    if step is None:
        step = 10 ** (-max(1, decimals - 1))
    box.setSingleStep(step)
    return box



def make_int_spin(value, minimum, maximum, step=1):
    box = QSpinBox()
    box.setRange(minimum, maximum)
    box.setSingleStep(step)
    box.setValue(value)
    return box



def make_help_button(help_html: str) -> QToolButton:
    return HelpButton(help_html)



def make_help_label(text: str, help_html: str | None = None) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    label = QLabel(text)
    label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
    layout.addWidget(label)

    if help_html:
        layout.addWidget(make_help_button(help_html), alignment=Qt.AlignmentFlag.AlignTop)

    layout.addStretch(1)
    return widget
