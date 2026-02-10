from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QCheckBox, QVBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QGroupBox,
    QSpinBox, QHeaderView
)
from PyQt6.QtCore import Qt

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


class TransientSimulationDialog(QDialog):
    """Dialog for configuring transient simulation parameters and events."""
    
    def __init__(
        self,
        available_pipes: list = None,
        available_nodes: list = None,
        available_pumps: list = None,
        initial_config: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Transient Simulation Settings")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self.available_pipes = available_pipes or []
        self.available_nodes = available_nodes or []
        self.available_pumps = available_pumps or []
        self.events_data = []
        self._initial_config = initial_config
        
        # Create UI
        layout = QVBoxLayout(self)
        
        # Title
        layout.addWidget(QLabel("<h2>Transient Analysis Configuration</h2>"))
        
        # Simulation parameters group
        params_group = QGroupBox("Simulation Parameters")
        params_layout = QFormLayout()
        
        self.total_time_spin = DialogUiFactory.create_double_spin(
            decimals=2, min_value=0.1, max_value=3600.0, value=10.0, suffix=" s"
        )
        self.time_step_spin = DialogUiFactory.create_double_spin(
            decimals=4, min_value=0.0001, max_value=1.0, value=0.01, suffix=" s"
        )
        self.wave_speed_spin = DialogUiFactory.create_double_spin(
            decimals=0, min_value=100.0, max_value=2000.0, value=1000.0, suffix=" m/s"
        )
        
        params_layout.addRow("Total Time:", self.total_time_spin)
        params_layout.addRow("Time Step:", self.time_step_spin)
        params_layout.addRow("Wave Speed:", self.wave_speed_spin)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Events group
        events_group = QGroupBox("Transient Events")
        events_layout = QVBoxLayout()
        
        # Events table
        self.events_table = QTableWidget(0, 6)
        self.events_table.setHorizontalHeaderLabels([
            "Event Type", "Time (s)", "Duration (s)", "Target", "From", "To"
        ])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        events_layout.addWidget(self.events_table)
        
        # Event buttons
        event_buttons_layout = QHBoxLayout()
        add_valve_btn = QPushButton("Add Valve Closure")
        add_valve_btn.clicked.connect(lambda: self._add_event("valve_closure"))
        add_pump_btn = QPushButton("Add Pump Trip")
        add_pump_btn.clicked.connect(lambda: self._add_event("pump_trip"))
        add_demand_btn = QPushButton("Add Demand Change")
        add_demand_btn.clicked.connect(lambda: self._add_event("demand_change"))
        remove_event_btn = QPushButton("Remove Selected")
        remove_event_btn.clicked.connect(self._remove_selected_event)
        
        event_buttons_layout.addWidget(add_valve_btn)
        event_buttons_layout.addWidget(add_pump_btn)
        event_buttons_layout.addWidget(add_demand_btn)
        event_buttons_layout.addWidget(remove_event_btn)
        event_buttons_layout.addStretch()
        events_layout.addLayout(event_buttons_layout)
        
        events_group.setLayout(events_layout)
        layout.addWidget(events_group)
        
        # Dialog buttons
        layout.addWidget(DialogUiFactory.create_button_box(self))

        if self._initial_config:
            self._load_config(self._initial_config)

    def _load_config(self, config: dict) -> None:
        self.total_time_spin.setValue(float(config.get("total_time", 10.0)))
        self.time_step_spin.setValue(float(config.get("time_step", 0.01)))
        self.wave_speed_spin.setValue(float(config.get("wave_speed", 1000.0)))

        self.events_table.setRowCount(0)
        self.events_data = []

        for event in config.get("events", []):
            row = self.events_table.rowCount()
            self.events_table.insertRow(row)

            event_type = event.get("type", "").strip()
            type_item = QTableWidgetItem(event_type.replace("_", " ").title())
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.events_table.setItem(row, 0, type_item)

            self.events_table.setItem(row, 1, QTableWidgetItem(str(event.get("time", 0.0))))
            self.events_table.setItem(row, 2, QTableWidgetItem(str(event.get("duration", 1.0))))
            self.events_table.setItem(row, 3, QTableWidgetItem(str(event.get("target", ""))))
            self.events_table.setItem(row, 4, QTableWidgetItem(str(event.get("from_value", 0.0))))
            self.events_table.setItem(row, 5, QTableWidgetItem(str(event.get("to_value", 0.0))))

            self.events_data.append({
                "type": event_type,
                "time": float(event.get("time", 0.0)),
                "duration": float(event.get("duration", 1.0)),
                "target": str(event.get("target", "")),
                "from_value": float(event.get("from_value", 0.0)),
                "to_value": float(event.get("to_value", 0.0)),
            })
    
    def _add_event(self, event_type: str):
        """Add a new transient event to the table."""
        row = self.events_table.rowCount()
        self.events_table.insertRow(row)
        
        # Event type
        type_item = QTableWidgetItem(event_type.replace("_", " ").title())
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.events_table.setItem(row, 0, type_item)
        
        # Time
        self.events_table.setItem(row, 1, QTableWidgetItem("0.0"))
        
        # Duration
        default_duration = "0.5" if event_type == "valve_closure" else "2.0"
        self.events_table.setItem(row, 2, QTableWidgetItem(default_duration))
        
        # Target (pipe or node ID)
        if event_type == "valve_closure":
            target = self.available_pipes[0] if self.available_pipes else "pipe_1"
        elif event_type == "pump_trip":
            if self.available_pumps:
                target = self.available_pumps[0]
            else:
                target = self.available_pipes[0] if self.available_pipes else "pipe_1"
        else:
            target = self.available_nodes[0] if self.available_nodes else "node_1"
        self.events_table.setItem(row, 3, QTableWidgetItem(target))
        
        # From value
        from_value = "1.0" if event_type in ["valve_closure", "pump_trip"] else "0.0"
        self.events_table.setItem(row, 4, QTableWidgetItem(from_value))
        
        # To value
        to_value = "0.0" if event_type in ["valve_closure", "pump_trip"] else "0.001"
        self.events_table.setItem(row, 5, QTableWidgetItem(to_value))
        
        # Store event data
        self.events_data.append({
            "type": event_type,
            "time": 0.0,
            "duration": float(default_duration),
            "target": target,
            "from_value": float(from_value),
            "to_value": float(to_value),
        })
    
    def _remove_selected_event(self):
        """Remove the selected event from the table."""
        selected_rows = set(item.row() for item in self.events_table.selectedItems())
        for row in sorted(selected_rows, reverse=True):
            self.events_table.removeRow(row)
            if row < len(self.events_data):
                self.events_data.pop(row)
    
    def get_configuration(self) -> dict:
        """Get the transient simulation configuration.
        
        Returns:
            Dict with simulation parameters and events
        """
        # Read events from table
        events = []
        for row in range(self.events_table.rowCount()):
            event_type = self.events_table.item(row, 0).text().lower().replace(" ", "_")
            time = float(self.events_table.item(row, 1).text() or 0.0)
            duration = float(self.events_table.item(row, 2).text() or 1.0)
            target = self.events_table.item(row, 3).text()
            from_value = float(self.events_table.item(row, 4).text() or 0.0)
            to_value = float(self.events_table.item(row, 5).text() or 0.0)
            
            events.append({
                "type": event_type,
                "time": time,
                "duration": duration,
                "target": target,
                "from_value": from_value,
                "to_value": to_value,
            })
        
        return {
            "total_time": self.total_time_spin.value(),
            "time_step": self.time_step_spin.value(),
            "wave_speed": self.wave_speed_spin.value(),
            "events": events,
        }
