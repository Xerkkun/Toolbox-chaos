from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLabel,
    QGroupBox,
)

from core.lorenz import SYSTEM_REGISTRY, METHOD_REGISTRY, system_defaults
from ui.widgets import make_double_spin, make_help_label


class SystemParameterPanel(QWidget):
    """Reusable dynamic system parameter panel.

    Handles system selection, parameter display, initial conditions,
    and solver method configuration.
    """

    changed = pyqtSignal()
    system_changed = pyqtSignal(str)

    def __init__(
        self,
        show_method: bool = True,
        show_ic: bool = True,
        show_time: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.show_method = show_method
        self.show_ic = show_ic
        self.show_time = show_time

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # 1. Model & Integrator Box
        self.model_box = QGroupBox('Modelo e integrador')
        model_form = QFormLayout(self.model_box)

        self.system_combo = QComboBox()
        for key, meta in SYSTEM_REGISTRY.items():
            suffix = ' [listo]' if meta['implemented'] else ' [pendiente]'
            self.system_combo.addItem(f"{meta['label']}{suffix}", userData=key)
        self.system_combo.currentIndexChanged.connect(self._on_system_combo_changed)
        model_form.addRow(
            make_help_label(
                'Sistema',
                '<b>Sistema caótico</b><br>Selecciona el modelo dinámico.',
            ),
            self.system_combo,
        )

        if self.show_method:
            self.method_combo = QComboBox()
            for key, meta in METHOD_REGISTRY.items():
                suffix = (
                    f" [{meta['backend']}]"
                    if meta['implemented']
                    else ' [pendiente]'
                )
                self.method_combo.addItem(
                    f"{meta['label']}{suffix}", userData=key
                )
            self.method_combo.setCurrentIndex(
                max(0, self.method_combo.findData('rk4'))
            )
            self.method_combo.currentIndexChanged.connect(self._emit_changed)
            model_form.addRow(
                make_help_label(
                    'Método',
                    '<b>Metodo numerico</b><br>Esquema temporal usado por el integrador.',
                ),
                self.method_combo,
            )

        self.model_status = QLabel()
        self.model_status.setWordWrap(True)
        self.model_status.setStyleSheet('font-size: 10px; color: #777777;')
        model_form.addRow(QLabel('Estado'), self.model_status)

        main_layout.addWidget(self.model_box)

        # 2. Parameters Box
        self.params_box = QGroupBox('Parámetros del sistema')
        params_form = QFormLayout(self.params_box)

        self.param_labels: list[QLabel] = []
        self.param_spins: list[QDoubleSpinBox] = []
        for idx in range(7):
            label = QLabel(f'p{idx + 1}')
            spin = make_double_spin(0.0, -10000.0, 10000.0, 6)
            spin.valueChanged.connect(self._emit_changed)
            self.param_labels.append(label)
            self.param_spins.append(spin)
            params_form.addRow(label, spin)

        main_layout.addWidget(self.params_box)

        # 3. Initial Conditions Box
        if self.show_ic:
            self.ic_box = QGroupBox('Condiciones iniciales')
            ic_form = QFormLayout(self.ic_box)

            self.ic_labels: list[QLabel] = []
            self.ic_spins: list[QDoubleSpinBox] = []
            for idx in range(7):
                label = QLabel(f'x{idx + 1}(0)')
                spin = make_double_spin(0.1, -10000.0, 10000.0, 6)
                spin.valueChanged.connect(self._emit_changed)
                self.ic_labels.append(label)
                self.ic_spins.append(spin)
                ic_form.addRow(label, spin)

            main_layout.addWidget(self.ic_box)

        # 4. Simulation Time Box
        if self.show_time:
            self.sim_box = QGroupBox('Simulación base')
            sim_form = QFormLayout(self.sim_box)

            self.dt = make_double_spin(0.01, 1e-6, 1.0, 6)
            self.T = make_double_spin(40.0, 0.01, 10000.0, 3)

            self.dt.valueChanged.connect(self._emit_changed)
            self.T.valueChanged.connect(self._emit_changed)

            sim_form.addRow(
                make_help_label(
                    'dt',
                    '<b>dt</b><br>Paso temporal fijo usado en la integración.',
                ),
                self.dt,
            )
            sim_form.addRow(
                make_help_label(
                    'Tiempo total T',
                    '<b>Tiempo total T</b><br>Duración de la integración.',
                ),
                self.T,
            )

            main_layout.addWidget(self.sim_box)

        self._on_system_combo_changed()

    def current_system_key(self) -> str:
        return self.system_combo.currentData()

    def current_method_key(self) -> str:
        if self.show_method:
            return self.method_combo.currentData()
        return 'rk4'

    def current_params(self) -> list[float]:
        key = self.current_system_key()
        meta = SYSTEM_REGISTRY[key]
        n_params = len(meta.get('param_labels', ()))
        return [self.param_spins[i].value() for i in range(n_params)]

    def current_initial(self) -> tuple[float, ...]:
        if self.show_ic:
            key = self.current_system_key()
            meta = SYSTEM_REGISTRY[key]
            dim = meta.get('dimension', 3)
            return tuple(self.ic_spins[i].value() for i in range(dim))
        return (0.1, 0.1, 0.1)

    @property
    def x0(self):
        return self.ic_spins[0] if len(self.ic_spins) > 0 else None

    @property
    def y0(self):
        return self.ic_spins[1] if len(self.ic_spins) > 1 else None

    @property
    def z0(self):
        return self.ic_spins[2] if len(self.ic_spins) > 2 else None

    def _on_system_combo_changed(self):
        key = self.current_system_key()
        if not key:
            return

        meta = SYSTEM_REGISTRY[key]
        state = 'implementado' if meta['implemented'] else 'pendiente'
        self.model_status.setText(f"{meta['description']} ({state})")

        params, initial = system_defaults(key)
        param_labels = meta.get('param_labels', ())

        # Update params
        for idx, spin in enumerate(self.param_spins):
            spin.blockSignals(True)
            if idx < len(params):
                self.param_labels[idx].setText(param_labels[idx])
                spin.setValue(float(params[idx]))
                spin.setEnabled(True)
                spin.show()
                self.param_labels[idx].show()
            else:
                self.param_labels[idx].setText(f'p{idx + 1}')
                spin.setValue(0.0)
                spin.setEnabled(False)
                spin.hide()
                self.param_labels[idx].hide()
            spin.blockSignals(False)

        # Update initial conditions
        if self.show_ic:
            dim = meta.get('dimension', 3)
            initial_labels = meta.get('initial_labels', ('x(0)', 'y(0)', 'z(0)'))
            for idx, spin in enumerate(self.ic_spins):
                spin.blockSignals(True)
                if idx < dim:
                    label_text = initial_labels[idx] if idx < len(initial_labels) else f'x{idx + 1}(0)'
                    self.ic_labels[idx].setText(label_text)
                    if idx < len(initial):
                        spin.setValue(float(initial[idx]))
                    spin.setEnabled(True)
                    spin.show()
                    self.ic_labels[idx].show()
                else:
                    self.ic_labels[idx].setText(f'x{idx + 1}(0)')
                    spin.setValue(0.1)
                    spin.setEnabled(False)
                    spin.hide()
                    self.ic_labels[idx].hide()
                spin.blockSignals(False)

        # Update dt/T defaults
        if self.show_time:
            self.dt.blockSignals(True)
            self.T.blockSignals(True)
            is_map = meta.get('kind') == 'map'
            self.dt.setValue(1.0 if is_map else 0.01)
            self.T.setValue(1200.0 if is_map else 40.0)
            self.dt.blockSignals(False)
            self.T.blockSignals(False)

        self.system_changed.emit(key)
        self.changed.emit()

    def _emit_changed(self):
        self.changed.emit()
