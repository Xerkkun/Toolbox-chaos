"""No-code dynamical-system editor backed by Hidden Attractors FO."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.hidden_engine import (
    engine_status,
    simulate_system_definition,
    validate_system_definition,
)


class NoCodeSystemTab(QWidget):
    """Create, validate, simulate, import, and export systems without Python."""

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.last_definition: dict | None = None
        self.last_result = None
        self._build_ui()
        self._load_example("Lorenz")

    @staticmethod
    def _double(value: float, minimum: float, maximum: float, decimals: int = 5):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setValue(value)
        return box

    def _build_ui(self):
        root = QHBoxLayout(self)
        splitter = QSplitter()
        root.addWidget(splitter)

        controls = QWidget()
        left = QVBoxLayout(controls)

        intro = QLabel(
            "Define variables, parametros y ecuaciones con notacion matematica. "
            "El analizador restringido no ejecuta codigo ni permite imports."
        )
        intro.setWordWrap(True)
        left.addWidget(intro)

        status = engine_status()
        self.engine_label = QLabel(status.message)
        self.engine_label.setWordWrap(True)
        self.engine_label.setStyleSheet(
            "color: #166534;" if status.available else "color: #991b1b;"
        )
        left.addWidget(self.engine_label)

        definition_box = QGroupBox("Definicion del sistema")
        form = QFormLayout(definition_box)
        self.name_edit = QLineEdit()
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("Flujo continuo", "flow")
        self.kind_combo.addItem("Mapa discreto", "map")
        self.variables_edit = QLineEdit()
        self.parameters_edit = QTextEdit()
        self.parameters_edit.setMaximumHeight(82)
        self.equations_edit = QTextEdit()
        self.equations_edit.setMinimumHeight(100)
        self.initial_edit = QLineEdit()
        form.addRow("Nombre", self.name_edit)
        form.addRow("Tipo", self.kind_combo)
        form.addRow("Variables (separadas por coma)", self.variables_edit)
        form.addRow("Parametros (nombre=valor)", self.parameters_edit)
        form.addRow("Ecuaciones (una por variable)", self.equations_edit)
        form.addRow("Estado inicial", self.initial_edit)
        left.addWidget(definition_box)

        numerical_box = QGroupBox("Contrato numerico")
        numerical = QFormLayout(numerical_box)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["rk4", "heun"])
        self.step_spin = self._double(0.01, 1.0e-6, 10.0, 6)
        self.duration_spin = self._double(30.0, 1.0e-4, 100000.0, 4)
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 10_000_000)
        self.iterations_spin.setValue(1000)
        self.transient_spin = QSpinBox()
        self.transient_spin.setRange(0, 9_999_999)
        self.transient_spin.setValue(100)
        self.divergence_spin = self._double(1.0e6, 1.0, 1.0e12, 2)
        numerical.addRow("Metodo del flujo", self.method_combo)
        numerical.addRow("Paso h", self.step_spin)
        numerical.addRow("Duracion", self.duration_spin)
        numerical.addRow("Iteraciones del mapa", self.iterations_spin)
        numerical.addRow("Muestras transitorias", self.transient_spin)
        numerical.addRow("Umbral de divergencia", self.divergence_spin)
        left.addWidget(numerical_box)

        examples = QHBoxLayout()
        for label in ("Lorenz", "Rossler", "Mapa logistico"):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, name=label: self._load_example(name))
            examples.addWidget(button)
        left.addLayout(examples)

        actions = QHBoxLayout()
        self.validate_button = QPushButton("Validar definicion")
        self.validate_button.clicked.connect(self.validate_definition)
        self.simulate_button = QPushButton("Simular y graficar")
        self.simulate_button.clicked.connect(self.simulate)
        actions.addWidget(self.validate_button)
        actions.addWidget(self.simulate_button)
        left.addLayout(actions)

        files = QHBoxLayout()
        load_button = QPushButton("Abrir JSON")
        load_button.clicked.connect(self.load_json)
        save_button = QPushButton("Guardar JSON")
        save_button.clicked.connect(self.save_json)
        files.addWidget(load_button)
        files.addWidget(save_button)
        left.addLayout(files)

        self.result_label = QLabel("Sin simulacion.")
        self.result_label.setWordWrap(True)
        left.addWidget(self.result_label)
        left.addStretch()

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        self.figure = Figure(constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        plot_layout.addWidget(self.canvas)

        note = QLabel(
            "Una trayectoria numerica no prueba por si sola caos, estabilidad ni existencia de un atractor."
        )
        note.setWordWrap(True)
        plot_layout.addWidget(note)

        splitter.addWidget(controls)
        splitter.addWidget(plot_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([430, 900])

    @staticmethod
    def _csv(text: str) -> list[str]:
        return [part.strip() for part in text.split(",") if part.strip()]

    @staticmethod
    def _numbers(text: str) -> list[float]:
        return [float(part.strip()) for part in text.split(",") if part.strip()]

    @staticmethod
    def _parameters(text: str) -> dict[str, float]:
        values: dict[str, float] = {}
        for raw_line in text.replace(";", "\n").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "=" not in line:
                raise ValueError(f"Parametro invalido: {line}. Usa nombre=valor.")
            name, raw_value = line.split("=", 1)
            name = name.strip()
            if not name:
                raise ValueError("El nombre de un parametro no puede estar vacio.")
            values[name] = float(raw_value.strip())
        return values

    def definition(self) -> dict:
        variables = self._csv(self.variables_edit.text())
        equations = [line.strip() for line in self.equations_edit.toPlainText().splitlines() if line.strip()]
        return {
            "name": self.name_edit.text().strip(),
            "kind": self.kind_combo.currentData(),
            "variables": variables,
            "parameters": self._parameters(self.parameters_edit.toPlainText()),
            "equations": equations,
            "initial_state": self._numbers(self.initial_edit.text()),
            "description": "Sistema creado desde el editor visual de Toolbox Chaos.",
        }

    def validate_definition(self, *, notify: bool = True) -> bool:
        try:
            canonical = validate_system_definition(self.definition())
        except Exception as exc:
            self.result_label.setText(f"Definicion invalida: {exc}")
            if notify:
                QMessageBox.critical(self, "Definicion invalida", str(exc))
            return False
        self.last_definition = dict(canonical)
        self.result_label.setText(
            f"Definicion valida: {len(canonical['variables'])} variables, tipo {canonical['kind']}."
        )
        if notify:
            QMessageBox.information(self, "Definicion valida", "El sistema puede simularse de forma segura.")
        return True

    def simulate(self):
        if not self.validate_definition(notify=False):
            return
        definition = self.last_definition or self.definition()
        try:
            result = simulate_system_definition(
                definition,
                step_size=self.step_spin.value(),
                duration=self.duration_spin.value(),
                iterations=self.iterations_spin.value(),
                method=self.method_combo.currentText(),
                divergence_norm=self.divergence_spin.value(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error de simulacion", str(exc))
            self.result_label.setText(f"No se pudo simular: {exc}")
            return

        self.last_result = result
        if self.main_window is not None:
            self.main_window.last_t = result.times
            self.main_window.last_X = result.states
            self.main_window.last_system_key = f"custom:{result.system_name}"
            self.main_window.last_params = dict(result.parameters)
        self._plot_result()
        self.result_label.setText(
            f"Estado: {result.status}. Pasos completados: "
            f"{result.completed_steps}/{result.requested_steps}. Motor: Hidden Attractors FO."
        )

    def _plot_result(self):
        result = self.last_result
        states = np.asarray(result.states, dtype=float)
        transient = min(self.transient_spin.value(), max(0, len(states) - 1))
        states = states[transient:]
        times = np.asarray(result.times, dtype=float)[transient:]
        self.figure.clear()
        if states.shape[1] >= 3:
            axis = self.figure.add_subplot(111, projection="3d")
            axis.plot(states[:, 0], states[:, 1], states[:, 2], linewidth=0.55)
            axis.set(xlabel="x1", ylabel="x2", zlabel="x3")
        elif states.shape[1] == 2:
            axis = self.figure.add_subplot(111)
            axis.plot(states[:, 0], states[:, 1], linewidth=0.7)
            axis.set(xlabel="x1", ylabel="x2")
        else:
            axis = self.figure.add_subplot(111)
            axis.plot(times, states[:, 0], linewidth=0.8)
            axis.set(xlabel="t / iteracion", ylabel="x1")
        axis.set_title(result.system_name)
        self.canvas.draw_idle()

    def _load_example(self, name: str):
        examples = {
            "Lorenz": {
                "name": "Lorenz visual",
                "kind": "flow",
                "variables": "x, y, z",
                "parameters": "sigma=10\nrho=28\nbeta=2.6666666667",
                "equations": "sigma*(y-x)\nx*(rho-z)-y\nx*y-beta*z",
                "initial": "1, 1, 1",
                "duration": 30.0,
            },
            "Rossler": {
                "name": "Rossler visual",
                "kind": "flow",
                "variables": "x, y, z",
                "parameters": "a=0.2\nb=0.2\nc=5.7",
                "equations": "-y-z\nx+a*y\nb+z*(x-c)",
                "initial": "0.1, 0.1, 0.1",
                "duration": 100.0,
            },
            "Mapa logistico": {
                "name": "Mapa logistico",
                "kind": "map",
                "variables": "x",
                "parameters": "r=3.9",
                "equations": "r*x*(1-x)",
                "initial": "0.2",
                "duration": 1000.0,
            },
        }
        item = examples[name]
        self.name_edit.setText(item["name"])
        self.kind_combo.setCurrentIndex(0 if item["kind"] == "flow" else 1)
        self.variables_edit.setText(item["variables"])
        self.parameters_edit.setPlainText(item["parameters"])
        self.equations_edit.setPlainText(item["equations"])
        self.initial_edit.setText(item["initial"])
        self.duration_spin.setValue(item["duration"])
        self.result_label.setText(f"Ejemplo {name} cargado. Valida o simula cuando estes listo.")

    def save_json(self):
        if not self.validate_definition(notify=False):
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar sistema", "sistema_dinamico.json", "JSON (*.json)")
        if path:
            Path(path).write_text(json.dumps(self.last_definition, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir sistema", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            canonical = validate_system_definition(data)
        except Exception as exc:
            QMessageBox.critical(self, "Archivo invalido", str(exc))
            return
        self.name_edit.setText(canonical["name"])
        self.kind_combo.setCurrentIndex(0 if canonical["kind"] == "flow" else 1)
        self.variables_edit.setText(", ".join(canonical["variables"]))
        self.parameters_edit.setPlainText("\n".join(f"{key}={value}" for key, value in canonical["parameters"].items()))
        self.equations_edit.setPlainText("\n".join(canonical["equations"]))
        self.initial_edit.setText(", ".join(str(value) for value in canonical["initial_state"]))
        self.last_definition = dict(canonical)
        self.result_label.setText(f"Sistema cargado desde {path}.")


__all__ = ["NoCodeSystemTab"]
