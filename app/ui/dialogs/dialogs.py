from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QCheckBox, QVBoxLayout, QLabel, QComboBox
)

from app.ui.dialogs.components import (
    DialogUiFactory,
    FluidMultiPhaseSection,
    FluidSinglePhaseSection,
)
from app.services.solvers import SolverMethod


class PipePropertiesDialog(QDialog):
    def __init__(self, length_m: float, diameter_m: float, roughness: float, flow_rate: float,
                 minor_loss_k: float = 0.0, is_multiphase: bool = False,
                 liquid_flow_rate: float = 0.0, gas_flow_rate: float = 0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipe properties")
        self.setMinimumWidth(320)
        self.is_multiphase = is_multiphase

        self.length_spin = DialogUiFactory.create_double_spin(
            decimals=3,
            min_value=0.001,
            max_value=1e9,
            value=length_m,
            suffix=" m",
        )

        self.diam_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=1e-6,
            max_value=100.0,
            value=diameter_m,
            suffix=" m",
        )

        self.rough_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1.0,
            value=roughness,
        )

        self.flow_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e3,
            value=flow_rate,
            suffix=" m³/s",
        )

        self.minor_k_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e6,
            value=minor_loss_k,
        )

        self.fitting_preset = QComboBox()
        self.fitting_preset.addItem("Custom (no preset)", None)
        self.fitting_preset.addItem("Elbow 90° (standard)", 0.9)
        self.fitting_preset.addItem("Elbow 90° (long radius)", 0.6)
        self.fitting_preset.addItem("Elbow 45°", 0.4)
        self.fitting_preset.addItem("Tee (through)", 0.6)
        self.fitting_preset.addItem("Tee (branch)", 1.8)
        self.fitting_preset.addItem("Gate valve (open)", 0.15)
        self.fitting_preset.addItem("Globe valve (open)", 10.0)
        self.fitting_preset.addItem("Ball valve (open)", 0.05)
        self.fitting_preset.addItem("Butterfly valve (open)", 0.9)
        self.fitting_preset.addItem("Sudden expansion", 1.0)
        self.fitting_preset.addItem("Sudden contraction", 0.5)
        self.fitting_preset.currentIndexChanged.connect(self._apply_fitting_preset)

        self.liquid_flow_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e3,
            value=liquid_flow_rate,
            suffix=" m³/s",
        )

        self.gas_flow_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e3,
            value=gas_flow_rate,
            suffix=" m³/s",
        )

        form = QFormLayout()
        form.addRow("Length", self.length_spin)
        form.addRow("Diameter", self.diam_spin)
        form.addRow("Roughness", self.rough_spin)
        form.addRow("Fitting Preset", self.fitting_preset)
        form.addRow("Minor Loss K", self.minor_k_spin)
        
        if is_multiphase:
            form.addRow("Liquid Flow Rate", self.liquid_flow_spin)
            form.addRow("Gas Flow Rate", self.gas_flow_spin)
        else:
            form.addRow("Flow rate", self.flow_spin)

        buttons = DialogUiFactory.create_button_box(self)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[float, float, float, float, float, float, float]:
        """Returns (length, diameter, roughness, flow_rate, minor_loss_k, liquid_flow_rate, gas_flow_rate)"""
        return (
            float(self.length_spin.value()),
            float(self.diam_spin.value()),
            float(self.rough_spin.value()),
            float(self.flow_spin.value()) if not self.is_multiphase else 0.0,
            float(self.minor_k_spin.value()),
            float(self.liquid_flow_spin.value()) if self.is_multiphase else 0.0,
            float(self.gas_flow_spin.value()) if self.is_multiphase else 0.0,
        )

    def _apply_fitting_preset(self) -> None:
        preset_value = self.fitting_preset.currentData()
        if preset_value is None:
            return
        self.minor_k_spin.setValue(float(preset_value))


class NodePropertiesDialog(QDialog):
    def __init__(self, is_source: bool, is_sink: bool, pressure_pa: float | None, flow_rate_m3s: float | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Node properties")
        self.setMinimumWidth(380)

        self.source_cb = QCheckBox("Is source")
        self.source_cb.setChecked(bool(is_source))

        self.sink_cb = QCheckBox("Is sink")
        self.sink_cb.setChecked(bool(is_sink and not is_source))

        # For sources: either pressure OR flow_rate
        self.pressure_spin = DialogUiFactory.create_double_spin(
            decimals=3,
            min_value=0.0,
            max_value=1e9,
            value=pressure_pa or 0.0,
            suffix=" Pa",
        )
        
        self.source_flow_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e3,
            value=flow_rate_m3s or 0.0,
            suffix=" m³/s",
        )
        
        # For sinks: only flow_rate (required)
        self.sink_flow_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=0.0,
            max_value=1e3,
            value=flow_rate_m3s or 0.0,
            suffix=" m³/s",
        )

        self.pressure_spin.setEnabled(self.source_cb.isChecked())
        self.source_flow_spin.setEnabled(self.source_cb.isChecked())
        self.sink_flow_spin.setEnabled(self.sink_cb.isChecked())
        
        self.source_cb.toggled.connect(self._on_source_toggled)
        self.sink_cb.toggled.connect(self._on_sink_toggled)

        form = QFormLayout()
        form.addRow(self.source_cb)
        
        # Source properties group
        form.addRow(QLabel("Source properties (choose one):"))
        form.addRow("  Pressure (if set)", self.pressure_spin)
        form.addRow("  Flow rate (if set)", self.source_flow_spin)
        
        form.addRow(self.sink_cb)
        
        # Sink properties group
        form.addRow(QLabel("Sink properties (required):"))
        form.addRow("  Flow rate", self.sink_flow_spin)

        buttons = DialogUiFactory.create_button_box(self)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_source_toggled(self, checked: bool):
        if checked:
            self.sink_cb.setChecked(False)
        self.pressure_spin.setEnabled(checked)
        self.source_flow_spin.setEnabled(checked)

    def _on_sink_toggled(self, checked: bool):
        if checked:
            self.source_cb.setChecked(False)
        self.sink_flow_spin.setEnabled(checked)

    def values(self) -> tuple[bool, bool, float | None, float | None]:
        is_source = self.source_cb.isChecked()
        is_sink = self.sink_cb.isChecked() and not is_source
        
        # Source: pressure is optional, flow_rate is optional (but one should be set)
        source_pressure = float(self.pressure_spin.value()) if is_source and self.pressure_spin.value() > 0 else None
        source_flow = float(self.source_flow_spin.value()) if is_source and self.source_flow_spin.value() > 0 else None
        
        # Sink: always has flow_rate (required)
        sink_flow = float(self.sink_flow_spin.value()) if is_sink else None
        
        # Return (is_source, is_sink, pressure, flow_rate)
        if is_source:
            return is_source, is_sink, source_pressure, source_flow
        elif is_sink:
            return is_source, is_sink, None, sink_flow
        else:
            return False, False, None, None


class PumpPropertiesDialog(QDialog):
    def __init__(self, pressure_ratio: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pump properties")
        self.setMinimumWidth(320)

        self.ratio_spin = DialogUiFactory.create_double_spin(
            decimals=3,
            min_value=0.1,
            max_value=100.0,
            value=pressure_ratio,
        )

        form = QFormLayout()
        form.addRow("Pressure ratio", self.ratio_spin)

        buttons = DialogUiFactory.create_button_box(self)

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

        self.k_spin = DialogUiFactory.create_double_spin(
            decimals=3,
            min_value=0.0,
            max_value=1e6,
            value=k,
        )

        form = QFormLayout()
        form.addRow("K (loss coefficient)", self.k_spin)

        buttons = DialogUiFactory.create_button_box(self)

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

        single_section = FluidSinglePhaseSection.from_fluid(fluid)
        multi_section = FluidMultiPhaseSection.from_fluid(fluid)

        self.density_spin = single_section.density_spin
        self.viscosity_spin = single_section.viscosity_spin
        self.temperature_spin = single_section.temperature_spin
        self.liquid_density_spin = multi_section.liquid_density_spin
        self.gas_density_spin = multi_section.gas_density_spin
        self.liquid_viscosity_spin = multi_section.liquid_viscosity_spin
        self.gas_viscosity_spin = multi_section.gas_viscosity_spin
        self.surface_tension_spin = multi_section.surface_tension_spin

        self._multi_section = multi_section
        self._on_multiphase_toggled(fluid.is_multiphase)

        buttons = DialogUiFactory.create_button_box(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.multiphase_cb)
        layout.addWidget(single_section.group)
        layout.addWidget(multi_section.group)
        layout.addWidget(buttons)

    def _on_multiphase_toggled(self, checked: bool):
        self._multi_section.set_enabled(checked)

    def get_fluid(self):
        from app.models.fluid import Fluid
        return Fluid(
            density=self.density_spin.value(),
            viscosity=self.viscosity_spin.value(),
            temperature_c=self.temperature_spin.value(),
            reference_temperature_c=self.temperature_spin.value(),
            reference_density=self.density_spin.value(),
            reference_viscosity=self.viscosity_spin.value(),
            is_multiphase=self.multiphase_cb.isChecked(),
            liquid_density=self.liquid_density_spin.value(),
            gas_density=self.gas_density_spin.value(),
            liquid_viscosity=self.liquid_viscosity_spin.value(),
            gas_viscosity=self.gas_viscosity_spin.value(),
            surface_tension=self.surface_tension_spin.value()
        )


class SimulationSettingsDialog(QDialog):
    """Dialog for configuring simulation settings like solver method."""
    
    def __init__(self, current_method: SolverMethod = SolverMethod.NEWTON_RAPHSON, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulation Settings")
        self.setMinimumWidth(400)
        
        # Solver method selection
        self.solver_combo = QComboBox()
        self.solver_combo.addItem("Newton-Raphson (Default, Faster)", SolverMethod.NEWTON_RAPHSON)
        self.solver_combo.addItem("Hardy-Cross (Traditional)", SolverMethod.HARDY_CROSS)
        
        # Set current method
        for i in range(self.solver_combo.count()):
            if self.solver_combo.itemData(i) == current_method:
                self.solver_combo.setCurrentIndex(i)
                break
        
        # Description labels
        description_label = QLabel(
            "<b>Solver Method:</b><br/>"
            "<b>Newton-Raphson:</b> Modern method with faster convergence for complex networks. "
            "Recommended for most applications.<br/><br/>"
            "<b>Hardy-Cross:</b> Traditional method, well-tested and reliable. "
            "May require more iterations for large networks."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("QLabel { padding: 10px; background: #f0f0f0; border-radius: 4px; }")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Calculation Method</h3>"))
        layout.addWidget(description_label)
        layout.addSpacing(10)
        
        form = QFormLayout()
        form.addRow("Solver Method:", self.solver_combo)
        layout.addLayout(form)
        
        layout.addStretch(1)
        layout.addWidget(DialogUiFactory.create_button_box(self))
    
    def get_solver_method(self) -> SolverMethod:
        """Get the selected solver method."""
        return self.solver_combo.currentData()
