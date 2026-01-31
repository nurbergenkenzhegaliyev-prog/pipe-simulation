from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
    QCheckBox, QVBoxLayout, QGroupBox, QLabel
)


class PipePropertiesDialog(QDialog):
    def __init__(self, length_m: float, diameter_m: float, roughness: float, flow_rate: float, 
                 is_multiphase: bool = False, liquid_flow_rate: float = 0.0, gas_flow_rate: float = 0.0,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipe properties")
        self.setMinimumWidth(320)
        self.is_multiphase = is_multiphase

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

        # Single-phase flow rate
        self.flow_spin = QDoubleSpinBox()
        self.flow_spin.setDecimals(6)
        self.flow_spin.setRange(0.0, 1e3)         # m3/s
        self.flow_spin.setValue(float(flow_rate))
        self.flow_spin.setSuffix(" m³/s")

        # Multi-phase flow rates
        self.liquid_flow_spin = QDoubleSpinBox()
        self.liquid_flow_spin.setDecimals(6)
        self.liquid_flow_spin.setRange(0.0, 1e3)
        self.liquid_flow_spin.setValue(float(liquid_flow_rate))
        self.liquid_flow_spin.setSuffix(" m³/s")

        self.gas_flow_spin = QDoubleSpinBox()
        self.gas_flow_spin.setDecimals(6)
        self.gas_flow_spin.setRange(0.0, 1e3)
        self.gas_flow_spin.setValue(float(gas_flow_rate))
        self.gas_flow_spin.setSuffix(" m³/s")

        form = QFormLayout()
        form.addRow("Length", self.length_spin)
        form.addRow("Diameter", self.diam_spin)
        form.addRow("Roughness", self.rough_spin)
        
        if is_multiphase:
            form.addRow("Liquid Flow Rate", self.liquid_flow_spin)
            form.addRow("Gas Flow Rate", self.gas_flow_spin)
        else:
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

    def values(self) -> tuple[float, float, float, float, float, float]:
        """Returns (length, diameter, roughness, flow_rate, liquid_flow_rate, gas_flow_rate)"""
        return (
            float(self.length_spin.value()),
            float(self.diam_spin.value()),
            float(self.rough_spin.value()),
            float(self.flow_spin.value()) if not self.is_multiphase else 0.0,
            float(self.liquid_flow_spin.value()) if self.is_multiphase else 0.0,
            float(self.gas_flow_spin.value()) if self.is_multiphase else 0.0,
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


class FluidPropertiesDialog(QDialog):
    def __init__(self, fluid=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fluid Properties")
        self.setMinimumWidth(400)

        # Import here to avoid circular dependency
        from app.models.fluid import Fluid
        if fluid is None:
            fluid = Fluid()

        # Multi-phase checkbox
        self.multiphase_cb = QCheckBox("Enable Multi-Phase Flow")
        self.multiphase_cb.setChecked(fluid.is_multiphase)
        self.multiphase_cb.toggled.connect(self._on_multiphase_toggled)

        # Single-phase properties
        single_group = QGroupBox("Single-Phase Properties")
        single_form = QFormLayout()

        self.density_spin = QDoubleSpinBox()
        self.density_spin.setDecimals(2)
        self.density_spin.setRange(0.1, 1e5)
        self.density_spin.setValue(fluid.density)
        self.density_spin.setSuffix(" kg/m³")

        self.viscosity_spin = QDoubleSpinBox()
        self.viscosity_spin.setDecimals(6)
        self.viscosity_spin.setRange(1e-7, 1.0)
        self.viscosity_spin.setValue(fluid.viscosity)
        self.viscosity_spin.setSuffix(" Pa·s")

        single_form.addRow("Density", self.density_spin)
        single_form.addRow("Viscosity", self.viscosity_spin)
        single_group.setLayout(single_form)

        # Multi-phase properties
        multi_group = QGroupBox("Multi-Phase Properties")
        multi_form = QFormLayout()

        self.liquid_density_spin = QDoubleSpinBox()
        self.liquid_density_spin.setDecimals(2)
        self.liquid_density_spin.setRange(0.1, 1e5)
        self.liquid_density_spin.setValue(fluid.liquid_density)
        self.liquid_density_spin.setSuffix(" kg/m³")

        self.gas_density_spin = QDoubleSpinBox()
        self.gas_density_spin.setDecimals(3)
        self.gas_density_spin.setRange(0.001, 1000.0)
        self.gas_density_spin.setValue(fluid.gas_density)
        self.gas_density_spin.setSuffix(" kg/m³")

        self.liquid_viscosity_spin = QDoubleSpinBox()
        self.liquid_viscosity_spin.setDecimals(6)
        self.liquid_viscosity_spin.setRange(1e-7, 1.0)
        self.liquid_viscosity_spin.setValue(fluid.liquid_viscosity)
        self.liquid_viscosity_spin.setSuffix(" Pa·s")

        self.gas_viscosity_spin = QDoubleSpinBox()
        self.gas_viscosity_spin.setDecimals(8)
        self.gas_viscosity_spin.setRange(1e-9, 1e-3)
        self.gas_viscosity_spin.setValue(fluid.gas_viscosity)
        self.gas_viscosity_spin.setSuffix(" Pa·s")

        self.surface_tension_spin = QDoubleSpinBox()
        self.surface_tension_spin.setDecimals(4)
        self.surface_tension_spin.setRange(0.0, 1.0)
        self.surface_tension_spin.setValue(fluid.surface_tension)
        self.surface_tension_spin.setSuffix(" N/m")

        multi_form.addRow("Liquid Density", self.liquid_density_spin)
        multi_form.addRow("Gas Density", self.gas_density_spin)
        multi_form.addRow("Liquid Viscosity", self.liquid_viscosity_spin)
        multi_form.addRow("Gas Viscosity", self.gas_viscosity_spin)
        multi_form.addRow("Surface Tension", self.surface_tension_spin)
        multi_group.setLayout(multi_form)

        self.multi_group = multi_group
        self._on_multiphase_toggled(fluid.is_multiphase)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.multiphase_cb)
        layout.addWidget(single_group)
        layout.addWidget(multi_group)
        layout.addWidget(buttons)

    def _on_multiphase_toggled(self, checked: bool):
        self.multi_group.setEnabled(checked)

    def get_fluid(self):
        from app.models.fluid import Fluid
        return Fluid(
            density=self.density_spin.value(),
            viscosity=self.viscosity_spin.value(),
            is_multiphase=self.multiphase_cb.isChecked(),
            liquid_density=self.liquid_density_spin.value(),
            gas_density=self.gas_density_spin.value(),
            liquid_viscosity=self.liquid_viscosity_spin.value(),
            gas_viscosity=self.gas_viscosity_spin.value(),
            surface_tension=self.surface_tension_spin.value()
        )

