from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
    QCheckBox, QVBoxLayout
)


class PipePropertiesDialog(QDialog):
    def __init__(self, length_m: float, diameter_m: float, roughness: float, flow_rate: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipe properties")
        self.setMinimumWidth(320)

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setDecimals(3)
        self.length_spin.setRange(0.001, 1e9)     # meters
        self.length_spin.setValue(float(length_m))
        self.length_spin.setSuffix(" m")

        self.diam_spin = QDoubleSpinBox()
        self.diam_spin.setDecimals(6)
        self.diam_spin.setRange(1e-6, 100.0)      # meters
        self.diam_spin.setValue(float(diameter_m))
        self.diam_spin.setSuffix(" m")

        self.rough_spin = QDoubleSpinBox()
        self.rough_spin.setDecimals(6)
        self.rough_spin.setRange(0.0, 1.0)        # dimensionless absolute roughness approximation
        self.rough_spin.setValue(float(roughness))

        self.flow_spin = QDoubleSpinBox()
        self.flow_spin.setDecimals(6)
        self.flow_spin.setRange(0.0, 1e3)         # m3/s
        self.flow_spin.setValue(float(flow_rate))
        self.flow_spin.setSuffix(" m³/s")

        form = QFormLayout()
        form.addRow("Length", self.length_spin)
        form.addRow("Diameter", self.diam_spin)
        form.addRow("Roughness", self.rough_spin)
        form.addRow("Flow rate", self.flow_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[float, float, float, float]:
        return (
            float(self.length_spin.value()),
            float(self.diam_spin.value()),
            float(self.rough_spin.value()),
            float(self.flow_spin.value()),
        )


class NodePropertiesDialog(QDialog):
    def __init__(self, is_source: bool, is_sink: bool, pressure_pa: float | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node properties")
        self.setMinimumWidth(320)

        self.source_cb = QCheckBox("Is source (fixed pressure)")
        self.source_cb.setChecked(bool(is_source))

        self.sink_cb = QCheckBox("Is sink")
        self.sink_cb.setChecked(bool(is_sink and not is_source))

        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setDecimals(3)
        self.pressure_spin.setRange(0.0, 1e9)   # Pa
        self.pressure_spin.setSuffix(" Pa")
        self.pressure_spin.setValue(float(pressure_pa or 0.0))
        self.pressure_spin.setEnabled(self.source_cb.isChecked())
        self.source_cb.toggled.connect(self._on_source_toggled)
        self.sink_cb.toggled.connect(self._on_sink_toggled)

        form = QFormLayout()
        form.addRow(self.source_cb)
        form.addRow(self.sink_cb)
        form.addRow("Pressure", self.pressure_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_source_toggled(self, checked: bool):
        if checked:
            self.sink_cb.setChecked(False)
        self.pressure_spin.setEnabled(checked)

    def _on_sink_toggled(self, checked: bool):
        if checked:
            self.source_cb.setChecked(False)
        if not self.source_cb.isChecked():
            self.pressure_spin.setEnabled(False)

    def values(self) -> tuple[bool, bool, float | None]:
        is_source = self.source_cb.isChecked()
        is_sink = self.sink_cb.isChecked() and not is_source
        pressure = float(self.pressure_spin.value()) if is_source else None
        return is_source, is_sink, pressure


class PumpPropertiesDialog(QDialog):
    def __init__(self, pressure_ratio: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pump properties")
        self.setMinimumWidth(320)

        self.ratio_spin = QDoubleSpinBox()
        self.ratio_spin.setDecimals(3)
        self.ratio_spin.setRange(0.1, 100.0)
        self.ratio_spin.setValue(float(pressure_ratio))

        form = QFormLayout()
        form.addRow("Pressure ratio", self.ratio_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def value(self) -> float:
        return float(self.ratio_spin.value())


class ValvePropertiesDialog(QDialog):
    def __init__(self, k: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Valve properties")
        self.setMinimumWidth(320)

        self.k_spin = QDoubleSpinBox()
        self.k_spin.setDecimals(3)
        self.k_spin.setRange(0.0, 1e6)
        self.k_spin.setValue(float(k))

        form = QFormLayout()
        form.addRow("K (loss coefficient)", self.k_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def value(self) -> float:
        return float(self.k_spin.value())
