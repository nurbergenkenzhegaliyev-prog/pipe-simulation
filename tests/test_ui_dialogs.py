"""
Tests for UI dialog classes.

This module tests all dialog components for correct initialization, 
widget state management, and value retrieval.
"""

import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

# Initialize QApplication for GUI testing
app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestPipePropertiesDialogBasics:
    """Test basic initialization and value retrieval for PipePropertiesDialog."""

    def test_initialization_with_defaults(self):
        """Test dialog initializes with provided default values."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
        )
        assert dialog is not None
        assert dialog.windowTitle() == "Pipe properties"

    def test_initialization_multiphase(self):
        """Test dialog initializes with multiphase flow settings."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=50.0,
            diameter_m=0.1,
            roughness=0.00045,
            flow_rate=0.0,
            is_multiphase=True,
            liquid_flow_rate=0.015,
            gas_flow_rate=0.005,
        )
        assert dialog.is_multiphase is True

    def test_get_values_single_phase(self):
        """Test values() returns correct tuple for single-phase flow."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
            minor_loss_k=0.5,
        )
        length, diameter, roughness, flow, k, liq_flow, gas_flow = dialog.values()
        
        assert length == 100.0
        assert diameter == 0.05
        assert roughness == 0.00005
        assert flow == 0.02
        assert k == 0.5
        assert liq_flow == 0.0  # Not set in single phase
        assert gas_flow == 0.0  # Not set in single phase

    def test_get_values_multiphase(self):
        """Test values() returns correct tuple for multiphase flow."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=50.0,
            diameter_m=0.1,
            roughness=0.00045,
            flow_rate=0.0,
            is_multiphase=True,
            liquid_flow_rate=0.015,
            gas_flow_rate=0.005,
        )
        length, diameter, roughness, flow, k, liq_flow, gas_flow = dialog.values()
        
        assert length == 50.0
        assert diameter == 0.1
        assert flow == 0.0  # Zero for multiphase
        assert liq_flow == 0.015
        assert gas_flow == 0.005

    def test_fitting_preset_elbow_90_standard(self):
        """Test applying elbow 90° standard preset."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
            minor_loss_k=0.0,
        )
        # Set to elbow 90° standard preset
        dialog.fitting_preset.setCurrentIndex(1)  # Index 1 is 0.9
        
        _, _, _, _, k, _, _ = dialog.values()
        assert k == 0.9

    def test_fitting_preset_ball_valve(self):
        """Test applying ball valve preset."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
            minor_loss_k=0.0,
        )
        # Find and set ball valve preset (0.05)
        dialog.fitting_preset.setCurrentIndex(8)  # Ball valve open
        
        _, _, _, _, k, _, _ = dialog.values()
        assert k == 0.05

    def test_fitting_preset_globe_valve(self):
        """Test applying globe valve preset."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
            minor_loss_k=0.0,
        )
        # Find and set globe valve preset (10.0)
        dialog.fitting_preset.setCurrentIndex(7)  # Globe valve open
        
        _, _, _, _, k, _, _ = dialog.values()
        assert k == 10.0

    def test_custom_fitting_preset(self):
        """Test custom preset leaves K value unchanged."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
            minor_loss_k=2.5,
        )
        # Custom preset is index 0
        dialog.fitting_preset.setCurrentIndex(0)
        
        _, _, _, _, k, _, _ = dialog.values()
        assert k == 2.5  # Unchanged

    def test_length_boundary_values(self):
        """Test length spin box accepts boundary values."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.00005,
            flow_rate=0.02,
        )
        
        # Try setting minimum and maximum values
        dialog.length_spin.setValue(0.001)  # Min
        assert dialog.length_spin.value() == 0.001
        
        dialog.length_spin.setValue(1e9)  # Max
        assert dialog.length_spin.value() == 1e9

    def test_diameter_precision(self):
        """Test diameter spin box maintains precision."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.123456,
            roughness=0.00005,
            flow_rate=0.02,
        )
        
        assert dialog.diam_spin.value() == pytest.approx(0.123456, rel=1e-6)

    def test_roughness_zero_value(self):
        """Test roughness can be set to zero."""
        from app.ui.dialogs.dialogs import PipePropertiesDialog
        
        dialog = PipePropertiesDialog(
            length_m=100.0,
            diameter_m=0.05,
            roughness=0.0,
            flow_rate=0.02,
        )
        
        _, _, roughness, _, _, _, _ = dialog.values()
        assert roughness == 0.0


class TestNodePropertiesDialogLogic:
    """Test node properties dialog with mutual exclusivity logic."""

    def test_initialization_as_source(self):
        """Test dialog initializes with source configuration."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=True,
            is_sink=False,
            pressure_pa=101325.0,
            flow_rate_m3s=0.01,
        )
        assert dialog.source_cb.isChecked() is True
        assert dialog.sink_cb.isChecked() is False

    def test_initialization_as_sink(self):
        """Test dialog initializes with sink configuration."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=False,
            is_sink=True,
            pressure_pa=None,
            flow_rate_m3s=0.005,
        )
        assert dialog.source_cb.isChecked() is False
        assert dialog.sink_cb.isChecked() is True

    def test_source_flow_rate_enabled_on_source(self):
        """Test source flow rate field is enabled when source is checked."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=True,
            is_sink=False,
            pressure_pa=101325.0,
            flow_rate_m3s=0.01,
        )
        assert dialog.source_flow_spin.isEnabled() is True

    def test_source_flow_rate_disabled_on_sink(self):
        """Test source flow rate field is disabled when source is unchecked."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=False,
            is_sink=True,
            pressure_pa=None,
            flow_rate_m3s=0.005,
        )
        assert dialog.source_flow_spin.isEnabled() is False

    def test_sink_flow_rate_enabled_on_sink(self):
        """Test sink flow rate field is enabled when sink is checked."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=False,
            is_sink=True,
            pressure_pa=None,
            flow_rate_m3s=0.005,
        )
        assert dialog.sink_flow_spin.isEnabled() is True

    def test_sink_flow_rate_disabled_on_source(self):
        """Test sink flow rate field is disabled when only source is checked."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=True,
            is_sink=False,
            pressure_pa=101325.0,
            flow_rate_m3s=0.01,
        )
        assert dialog.sink_flow_spin.isEnabled() is False

    def test_source_sink_mutual_exclusivity(self):
        """Test source and sink checkboxes are mutually exclusive."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=True,
            is_sink=False,
            pressure_pa=101325.0,
        )
        
        # Activate sink - source should deactivate
        dialog.sink_cb.setChecked(True)
        assert dialog.source_cb.isChecked() is False
        assert dialog.sink_cb.isChecked() is True
        
        # Activate source - sink should deactivate
        dialog.source_cb.setChecked(True)
        assert dialog.source_cb.isChecked() is True
        assert dialog.sink_cb.isChecked() is False

    def test_get_values_source(self):
        """Test values() returns correct tuple for source node."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=True,
            is_sink=False,
            pressure_pa=101325.0,
            flow_rate_m3s=0.01,
        )
        
        is_source, is_sink, pressure, flow = dialog.values()
        assert is_source is True
        assert is_sink is False
        assert pressure == 101325.0
        assert flow == 0.01

    def test_get_values_sink(self):
        """Test values() returns correct tuple for sink node."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=False,
            is_sink=True,
            pressure_pa=None,
            flow_rate_m3s=0.005,
        )
        
        is_source, is_sink, pressure, flow = dialog.values()
        assert is_source is False
        assert is_sink is True
        assert pressure is None
        assert flow == 0.005

    def test_get_values_neutral(self):
        """Test values() returns False, False, None, None when neither checked."""
        from app.ui.dialogs.dialogs import NodePropertiesDialog
        
        dialog = NodePropertiesDialog(
            is_source=False,
            is_sink=False,
            pressure_pa=101325.0,
        )
        
        # Uncheck both
        dialog.source_cb.setChecked(False)
        dialog.sink_cb.setChecked(False)
        
        is_source, is_sink, pressure, flow = dialog.values()
        assert is_source is False
        assert is_sink is False
        assert pressure is None
        assert flow is None


class TestPumpPropertiesDialog:
    """Test pump properties dialog."""

    def test_initialization(self):
        """Test pump dialog initializes with pressure ratio."""
        from app.ui.dialogs.dialogs import PumpPropertiesDialog
        
        dialog = PumpPropertiesDialog(pressure_ratio=1.5)
        assert dialog.windowTitle() == "Pump properties"
        assert dialog.ratio_spin.value() == 1.5

    def test_value_retrieval(self):
        """Test pump dialog returns correct pressure ratio."""
        from app.ui.dialogs.dialogs import PumpPropertiesDialog
        
        dialog = PumpPropertiesDialog(pressure_ratio=2.0)
        assert dialog.value() == 2.0

    def test_ratio_minimum(self):
        """Test pump pressure ratio minimum boundary."""
        from app.ui.dialogs.dialogs import PumpPropertiesDialog
        
        dialog = PumpPropertiesDialog(pressure_ratio=0.1)
        dialog.ratio_spin.setValue(0.1)
        assert dialog.ratio_spin.value() == 0.1

    def test_ratio_maximum(self):
        """Test pump pressure ratio maximum boundary."""
        from app.ui.dialogs.dialogs import PumpPropertiesDialog
        
        dialog = PumpPropertiesDialog(pressure_ratio=100.0)
        dialog.ratio_spin.setValue(100.0)
        assert dialog.ratio_spin.value() == 100.0


class TestValvePropertiesDialog:
    """Test valve properties dialog."""

    def test_initialization(self):
        """Test valve dialog initializes with K coefficient."""
        from app.ui.dialogs.dialogs import ValvePropertiesDialog
        
        dialog = ValvePropertiesDialog(k=10.0)
        assert dialog.windowTitle() == "Valve properties"
        assert dialog.k_spin.value() == 10.0

    def test_value_retrieval(self):
        """Test valve dialog returns correct K value."""
        from app.ui.dialogs.dialogs import ValvePropertiesDialog
        
        dialog = ValvePropertiesDialog(k=0.05)
        assert dialog.value() == 0.05

    def test_k_zero_value(self):
        """Test valve K can be set to zero."""
        from app.ui.dialogs.dialogs import ValvePropertiesDialog
        
        dialog = ValvePropertiesDialog(k=0.0)
        assert dialog.value() == 0.0

    def test_k_large_value(self):
        """Test valve K can handle large values."""
        from app.ui.dialogs.dialogs import ValvePropertiesDialog
        
        dialog = ValvePropertiesDialog(k=1e6)
        dialog.k_spin.setValue(1e6)
        assert dialog.k_spin.value() == 1e6


class TestFluidPropertiesDialog:
    """Test fluid properties dialog for single and multiphase fluids."""

    def test_initialization_default_fluid(self):
        """Test fluid dialog initializes with default water properties."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        assert dialog.windowTitle() == "Fluid Properties"
        assert dialog.multiphase_cb.isChecked() is False

    def test_initialization_with_fluid(self):
        """Test fluid dialog initializes with provided fluid."""
        from app.models.fluid import Fluid
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        water = Fluid(density=998.0, viscosity=1e-3)
        dialog = FluidPropertiesDialog(fluid=water)
        
        assert dialog.density_spin.value() == 998.0
        assert dialog.viscosity_spin.value() == 1e-3

    def test_single_phase_density(self):
        """Test single-phase fluid density can be set."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        dialog.density_spin.setValue(850.0)  # Oil
        assert dialog.density_spin.value() == 850.0

    def test_single_phase_viscosity(self):
        """Test single-phase fluid viscosity can be set."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        dialog.viscosity_spin.setValue(50e-3)  # More viscous
        assert dialog.viscosity_spin.value() == 50e-3

    def test_single_phase_temperature(self):
        """Test single-phase fluid temperature can be set."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        dialog.temperature_spin.setValue(25.0)
        assert dialog.temperature_spin.value() == 25.0

    def test_multiphase_toggle_enables_sections(self):
        """Test toggling multiphase enables multiphase property sections."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        assert dialog.multiphase_cb.isChecked() is False
        
        dialog.multiphase_cb.setChecked(True)
        assert dialog.multiphase_cb.isChecked() is True

    def test_get_fluid_single_phase(self):
        """Test get_fluid() returns Fluid object for single-phase."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        dialog.density_spin.setValue(1000.0)
        dialog.viscosity_spin.setValue(1e-3)
        
        fluid = dialog.get_fluid()
        assert fluid.density == 1000.0
        assert fluid.viscosity == 1e-3
        assert fluid.is_multiphase is False

    def test_get_fluid_multiphase(self):
        """Test get_fluid() returns Fluid object for multiphase."""
        from app.ui.dialogs.dialogs import FluidPropertiesDialog
        
        dialog = FluidPropertiesDialog()
        dialog.multiphase_cb.setChecked(True)
        dialog.liquid_density_spin.setValue(998.0)
        dialog.gas_density_spin.setValue(1.2)
        
        fluid = dialog.get_fluid()
        assert fluid.is_multiphase is True
        assert fluid.liquid_density == 998.0
        assert fluid.gas_density == 1.2


class TestSimulationSettingsDialog:
    """Test simulation settings dialog for solver method selection."""

    def test_initialization_default(self):
        """Test dialog initializes with Newton-Raphson as default."""
        from app.ui.dialogs.dialogs import SimulationSettingsDialog
        from app.services.solvers import SolverMethod
        
        dialog = SimulationSettingsDialog()
        assert dialog.windowTitle() == "Simulation Settings"
        assert dialog.get_solver_method() == SolverMethod.NEWTON_RAPHSON

    def test_initialization_with_hardy_cross(self):
        """Test dialog initializes with Hardy-Cross method."""
        from app.ui.dialogs.dialogs import SimulationSettingsDialog
        from app.services.solvers import SolverMethod
        
        dialog = SimulationSettingsDialog(current_method=SolverMethod.HARDY_CROSS)
        assert dialog.get_solver_method() == SolverMethod.HARDY_CROSS

    def test_solver_combo_has_two_options(self):
        """Test solver combo box has both method options."""
        from app.ui.dialogs.dialogs import SimulationSettingsDialog
        
        dialog = SimulationSettingsDialog()
        assert dialog.solver_combo.count() == 2

    def test_change_solver_method(self):
        """Test changing solver method via combo box."""
        from app.ui.dialogs.dialogs import SimulationSettingsDialog
        from app.services.solvers import SolverMethod
        
        dialog = SimulationSettingsDialog()
        assert dialog.get_solver_method() == SolverMethod.NEWTON_RAPHSON
        
        dialog.solver_combo.setCurrentIndex(1)  # Hardy-Cross
        assert dialog.get_solver_method() == SolverMethod.HARDY_CROSS


class TestTransientSimulationDialogBasics:
    """Test transient simulation dialog initialization and parameters."""

    def test_initialization_default(self):
        """Test transient dialog initializes with default values."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        assert dialog.windowTitle() == "Transient Simulation Settings"
        assert dialog.total_time_spin.value() == 10.0
        assert dialog.time_step_spin.value() == 0.01
        assert dialog.wave_speed_spin.value() == 1000.0

    def test_initialization_with_available_elements(self):
        """Test dialog initializes with available pipes, nodes, pumps."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(
            available_pipes=["pipe_1", "pipe_2"],
            available_nodes=["node_1", "node_2"],
            available_pumps=["pump_1"],
        )
        assert dialog.available_pipes == ["pipe_1", "pipe_2"]
        assert dialog.available_nodes == ["node_1", "node_2"]
        assert dialog.available_pumps == ["pump_1"]

    def test_total_time_parameters(self):
        """Test total time parameter can be set."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        dialog.total_time_spin.setValue(20.0)
        assert dialog.total_time_spin.value() == 20.0

    def test_time_step_parameters(self):
        """Test time step parameter can be set."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        dialog.time_step_spin.setValue(0.001)
        assert dialog.time_step_spin.value() == 0.001

    def test_wave_speed_parameters(self):
        """Test wave speed parameter can be set."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        dialog.wave_speed_spin.setValue(1200.0)
        assert dialog.wave_speed_spin.value() == 1200.0

    def test_events_table_initially_empty(self):
        """Test events table starts empty."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        assert dialog.events_table.rowCount() == 0

    def test_add_valve_closure_event(self):
        """Test adding valve closure event to table."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(available_pipes=["pipe_1"])
        dialog._add_event("valve_closure")
        
        assert dialog.events_table.rowCount() == 1
        event_type = dialog.events_table.item(0, 0).text()
        assert "Valve Closure" in event_type

    def test_add_pump_trip_event(self):
        """Test adding pump trip event to table."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(available_pumps=["pump_1"])
        dialog._add_event("pump_trip")
        
        assert dialog.events_table.rowCount() == 1
        event_type = dialog.events_table.item(0, 0).text()
        assert "Pump Trip" in event_type

    def test_add_demand_change_event(self):
        """Test adding demand change event to table."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(available_nodes=["node_1"])
        dialog._add_event("demand_change")
        
        assert dialog.events_table.rowCount() == 1
        event_type = dialog.events_table.item(0, 0).text()
        assert "Demand Change" in event_type

    def test_remove_selected_event(self):
        """Test removing event from table."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(available_pipes=["pipe_1"])
        dialog._add_event("valve_closure")
        assert dialog.events_table.rowCount() == 1
        
        # Select and remove the first row
        dialog.events_table.selectRow(0)
        dialog._remove_selected_event()
        assert dialog.events_table.rowCount() == 0

    def test_multiple_events(self):
        """Test adding multiple events."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(
            available_pipes=["pipe_1"],
            available_nodes=["node_1"],
            available_pumps=["pump_1"]
        )
        dialog._add_event("valve_closure")
        dialog._add_event("pump_trip")
        dialog._add_event("demand_change")
        
        assert dialog.events_table.rowCount() == 3

    def test_get_configuration_no_events(self):
        """Test get_configuration() returns parameters without events."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog()
        dialog.total_time_spin.setValue(15.0)
        dialog.time_step_spin.setValue(0.005)
        dialog.wave_speed_spin.setValue(1100.0)
        
        config = dialog.get_configuration()
        assert config["total_time"] == 15.0
        assert config["time_step"] == 0.005
        assert config["wave_speed"] == 1100.0
        assert config["events"] == []

    def test_get_configuration_with_events(self):
        """Test get_configuration() includes event data."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        dialog = TransientSimulationDialog(available_pipes=["pipe_1"])
        dialog._add_event("valve_closure")
        
        # Modify event values
        dialog.events_table.item(0, 1).setText("1.0")  # Time
        dialog.events_table.item(0, 2).setText("0.5")  # Duration
        
        config = dialog.get_configuration()
        assert len(config["events"]) == 1
        assert config["events"][0]["type"] == "valve_closure"
        assert config["events"][0]["time"] == 1.0
        assert config["events"][0]["duration"] == 0.5

    def test_load_configuration(self):
        """Test loading configuration from dict."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        
        initial_config = {
            "total_time": 20.0,
            "time_step": 0.02,
            "wave_speed": 1200.0,
            "events": [
                {
                    "type": "valve_closure",
                    "time": 5.0,
                    "duration": 1.0,
                    "target": "pipe_1",
                    "from_value": 1.0,
                    "to_value": 0.0,
                }
            ]
        }
        
        dialog = TransientSimulationDialog(initial_config=initial_config)
        
        assert dialog.total_time_spin.value() == 20.0
        assert dialog.time_step_spin.value() == 0.02
        assert dialog.wave_speed_spin.value() == 1200.0
        assert dialog.events_table.rowCount() == 1

    def test_event_type_not_editable(self):
        """Test event type column is not editable."""
        from app.ui.dialogs.dialogs import TransientSimulationDialog
        from PyQt6.QtCore import Qt
        
        dialog = TransientSimulationDialog(available_pipes=["pipe_1"])
        dialog._add_event("valve_closure")
        
        event_type_item = dialog.events_table.item(0, 0)
        # Check that ItemIsEditable flag is NOT set
        assert not (event_type_item.flags() & Qt.ItemFlag.ItemIsEditable)
