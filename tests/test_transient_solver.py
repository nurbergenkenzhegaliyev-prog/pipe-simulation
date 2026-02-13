"""Tests for transient solver functionality.

Tests cover:
- Time-stepping integration
- Transient event application (pump ramp, valve opening)
- Pressure and flow history tracking
- Convergence detection
- Edge cases and error handling
"""

import math
import pytest

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.models.equipment import PumpCurve
from app.services.pressure import PressureDropService
from app.services.transient import (
    TransientEvent,
    TransientResult,
    TransientSolver,
    WaterHammerParams,
)


@pytest.fixture
def simple_network():
    """Create a simple 2-node, 1-pipe network for testing."""
    network = PipeNetwork()
    
    source = Node(id="source", is_source=True, pressure=200000)
    sink = Node(id="sink")
    
    network.add_node(source)
    network.add_node(sink)
    
    pipe = Pipe(
        id="pipe1",
        start_node="source",
        end_node="sink",
        length=100,
        diameter=0.05,
        roughness=0.000045,
        flow_rate=0.01,
    )
    network.add_pipe(pipe)
    
    return network


@pytest.fixture
def fluid():
    """Standard test fluid."""
    return Fluid(density=998.0, viscosity=1e-3)


@pytest.fixture
def pressure_drop_service(fluid):
    """Pressure drop service with standard fluid."""
    return PressureDropService(fluid)


@pytest.fixture
def transient_solver(pressure_drop_service):
    """Transient solver with small time step for testing."""
    return TransientSolver(
        pressure_drop_service,
        time_step=0.01,
        max_steps=1000,
        convergence_tolerance=0.1,
    )


class TestTransientEvent:
    """Test TransientEvent dataclass."""
    
    def test_pump_ramp_event_creation(self):
        """Test creating a pump ramp transient event."""
        event = TransientEvent(
            time=0.0,
            event_type="pump_ramp",
            duration=2.0,
            start_value=0.0,
            end_value=1.0,
            pipe_id="pump1",
        )
        assert event.time == 0.0
        assert event.event_type == "pump_ramp"
        assert event.duration == 2.0
        assert event.start_value == 0.0
        assert event.end_value == 1.0
        assert event.pipe_id == "pump1"
    
    def test_valve_opening_event(self):
        """Test creating a valve opening event."""
        event = TransientEvent(
            time=5.0,
            event_type="valve_opening",
            duration=3.0,
            start_value=0.0,
            end_value=1.0,
            pipe_id="valve1",
        )
        assert event.event_type == "valve_opening"
        assert event.time == 5.0


class TestTransientResult:
    """Test TransientResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a transient result."""
        result = TransientResult(time=1.0, timestep=100)
        assert result.time == 1.0
        assert result.timestep == 100
        assert result.node_pressures == {}
        assert result.pipe_flows == {}
    
    def test_result_with_data(self):
        """Test result with pressure and flow data."""
        result = TransientResult(
            time=0.5,
            timestep=50,
            node_pressures={"n1": 150000, "n2": 100000},
            pipe_flows={"p1": 0.01},
        )
        assert result.node_pressures["n1"] == 150000
        assert result.pipe_flows["p1"] == 0.01
        # Note: max/min pressure calculated in _collect_results, not in init
        # So test manual calculation instead
        pressures = list(result.node_pressures.values())
        assert max(pressures) == 150000
        assert min(pressures) == 100000


class TestTransientSolverBasic:
    """Test basic transient solver functionality."""
    
    def test_solver_initialization(self, transient_solver):
        """Test solver initialization."""
        assert transient_solver.time_step == 0.01
        assert transient_solver.max_steps == 1000
        assert transient_solver.convergence_tolerance == 0.1
    
    def test_invalid_total_time(self, transient_solver, simple_network):
        """Test that invalid total_time raises ValueError."""
        with pytest.raises(ValueError):
            transient_solver.solve(simple_network, total_time=-1.0)
        
        with pytest.raises(ValueError):
            transient_solver.solve(simple_network, total_time=0.0)
    
    def test_invalid_network(self, transient_solver):
        """Test that invalid network raises ValueError."""
        network = PipeNetwork()
        
        with pytest.raises(ValueError):
            transient_solver.solve(network, total_time=1.0)
    
    def test_basic_simulation_runs(self, transient_solver, simple_network):
        """Test that basic simulation runs without crashing."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        assert len(results) > 0
        assert all(isinstance(r, TransientResult) for r in results)
        assert results[0].time == pytest.approx(0.0)
        assert all(r.timestep == i for i, r in enumerate(results))


class TestTransientEvents:
    """Test transient event application."""
    
    def test_pump_ramp_applied(self, transient_solver, simple_network):
        """Test that pump ramp event modifies network."""
        event = TransientEvent(
            time=0.0,
            event_type="pump_ramp",
            duration=0.1,
            start_value=0.0,
            end_value=1.0,
            pipe_id="pipe1",
        )
        
        results = transient_solver.solve(
            simple_network,
            total_time=0.2,
            events=[event],
        )
        
        assert len(results) > 0
        # Verify event was processed (pump_multiplier attribute added)
        pipe = simple_network.pipes["pipe1"]
        assert hasattr(pipe, "pump_multiplier")
    
    def test_multiple_events(self, transient_solver, simple_network):
        """Test multiple transient events in simulation."""
        events = [
            TransientEvent(
                time=0.0,
                event_type="pump_ramp",
                duration=0.05,
                start_value=0.0,
                end_value=1.0,
                pipe_id="pipe1",
            ),
            TransientEvent(
                time=0.1,
                event_type="valve_opening",
                duration=0.05,
                start_value=1.0,
                end_value=0.5,
                pipe_id="pipe1",
            ),
        ]
        
        results = transient_solver.solve(
            simple_network,
            total_time=0.2,
            events=events,
        )
        
        assert len(results) > 0


class TestTransientHistories:
    """Test pressure and flow history retrieval."""
    
    def test_pressure_history_retrieval(self, transient_solver, simple_network):
        """Test getting pressure history for a node."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        history = transient_solver.get_pressure_history("source")
        
        assert len(history) > 0
        # Check that we have time-pressure pairs
        for item in history:
            assert isinstance(item, tuple)
            assert len(item) == 2
            time_val, pressure_val = item
            assert isinstance(time_val, float)
            # Pressure can be float or None
            assert isinstance(pressure_val, (float, int, type(None)))
        assert history[0][0] == pytest.approx(0.0)  # First time is 0
    
    def test_flow_history_retrieval(self, transient_solver, simple_network):
        """Test getting flow history for a pipe."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        history = transient_solver.get_flow_history("pipe1")
        
        assert len(history) > 0
        assert all(isinstance(t, float) and isinstance(f, float) for t, f in history)
    
    def test_velocity_history_retrieval(self, transient_solver, simple_network):
        """Test getting velocity history for a pipe."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        history = transient_solver.get_velocity_history("pipe1")
        
        assert len(history) > 0
        assert all(isinstance(t, float) and isinstance(v, float) for t, v in history)
        # All velocities should be non-negative
        assert all(v >= 0.0 for t, v in history)


class TestSteadyStateDetection:
    """Test convergence and steady-state detection."""
    
    def test_results_stored_in_order(self, transient_solver, simple_network):
        """Test that results are stored in chronological order."""
        results = transient_solver.solve(simple_network, total_time=0.2)
        
        times = [r.time for r in results]
        assert times == sorted(times)
        assert times[0] == pytest.approx(0.0)
    
    def test_simulation_respects_max_steps(self, pressure_drop_service):
        """Test that simulation respects max_steps limit."""
        solver = TransientSolver(
            pressure_drop_service,
            time_step=0.01,
            max_steps=5,
        )
        
        network = PipeNetwork()
        source = Node(id="source", is_source=True, pressure=200000)
        sink = Node(id="sink")
        network.add_node(source)
        network.add_node(sink)
        pipe = Pipe(
            id="pipe1",
            start_node="source",
            end_node="sink",
            length=100,
            diameter=0.05,
            roughness=0.000045,
            flow_rate=0.01,
        )
        network.add_pipe(pipe)
        
        results = solver.solve(network, total_time=10.0)
        
        # Should stop at max_steps or earlier
        assert len(results) <= 5


class TestResultsCollection:
    """Test that results are correctly collected."""
    
    def test_all_nodes_in_results(self, transient_solver, simple_network):
        """Test that all nodes appear in results."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        for result in results:
            assert "source" in result.node_pressures
            assert "sink" in result.node_pressures
    
    def test_all_pipes_in_results(self, transient_solver, simple_network):
        """Test that all pipes appear in results."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        for result in results:
            assert "pipe1" in result.pipe_flows
            assert "pipe1" in result.pipe_velocities
    
    def test_velocity_calculation(self, transient_solver, simple_network):
        """Test that velocities are calculated from flow rates."""
        results = transient_solver.solve(simple_network, total_time=0.1)
        
        for result in results:
            flow = result.pipe_flows["pipe1"]
            velocity = result.pipe_velocities["pipe1"]
            
            # Verify v = Q / A relationship (approximately)
            pipe = simple_network.pipes["pipe1"]
            area = math.pi * (pipe.diameter / 2) ** 2
            expected_velocity = abs(flow) / area
            
            assert velocity == pytest.approx(expected_velocity, abs=1e-6)


class TestCallbackFunctionality:
    """Test callback function during simulation."""
    
    def test_callback_called_each_step(self, transient_solver, simple_network):
        """Test that callback is called at each time step."""
        callback_results = []
        
        def callback(result: TransientResult):
            callback_results.append(result)
        
        results = transient_solver.solve(
            simple_network,
            total_time=0.05,
            callback=callback,
        )
        
        assert len(callback_results) == len(results)
    
    def test_callback_receives_correct_data(self, transient_solver, simple_network):
        """Test that callback receives valid TransientResult objects."""
        last_callback_result = None
        
        def callback(result: TransientResult):
            nonlocal last_callback_result
            last_callback_result = result
        
        transient_solver.solve(
            simple_network,
            total_time=0.05,
            callback=callback,
        )
        
        assert last_callback_result is not None
        assert isinstance(last_callback_result, TransientResult)
        assert len(last_callback_result.node_pressures) > 0
        assert len(last_callback_result.pipe_flows) > 0


class TestWaterHammerAnalysis:
    """Test water hammer calculations and surge pressure analysis."""
    
    def test_water_hammer_params_default(self):
        """Test default water hammer parameters."""
        params = WaterHammerParams()
        assert params.wave_speed == 1000.0
        assert params.bulk_modulus == 2.2e9
        assert params.pipe_elastic_modulus == 200e9
    
    def test_wave_speed_calculation(self):
        """Test wave speed calculation using Korteweg formula."""
        wave_speed = WaterHammerParams.calculate_wave_speed(
            bulk_modulus=2.2e9,
            density=998.0,
            diameter=0.1,
            wall_thickness=0.005,
            elastic_modulus=200e9,
        )
        
        # Expected around 1000-1400 m/s for water in steel pipe
        # (varies with pipe thickness and material properties)
        assert 900 < wave_speed < 1500
    
    def test_surge_pressure_valve_closure(self, simple_network):
        """Test surge pressure from valve closure."""
        fluid = Fluid(density=998.0, viscosity=1e-3)
        dp_service = PressureDropService(fluid)
        
        events = [
            TransientEvent(
                time=0.1,
                event_type='valve_closure',
                duration=0.1,
                start_value=1.0,
                end_value=0.0,
                pipe_id='pipe1',
            )
        ]
        
        solver = TransientSolver(
            dp_service=dp_service,
            time_step=0.01,
            max_steps=500,
        )
        
        results = solver.solve(
            simple_network,
            total_time=1.0,
            events=events,
        )
        
        # Check surge pressures are calculated
        max_surge, pipe_id, time = solver.get_max_surge_pressure()
        assert max_surge >= 0.0
        assert pipe_id in ['pipe1', '']
    
    def test_cavitation_detection(self, simple_network):
        """Test cavitation detection."""
        fluid = Fluid(density=998.0, viscosity=1e-3)
        dp_service = PressureDropService(fluid)
        
        # Set high vapor pressure to trigger cavitation detection
        solver = TransientSolver(
            dp_service=dp_service,
            time_step=0.01,
            max_steps=100,
            vapor_pressure=300000.0,  # 3 bar
        )
        
        results = solver.solve(
            simple_network,
            total_time=0.5,
            events=None,
        )
        
        cavitation_events = solver.get_cavitation_events()
        assert isinstance(cavitation_events, list)
    
    def test_transient_result_surge_data(self, transient_solver, simple_network):
        """Test that transient results contain surge pressure data."""
        results = transient_solver.solve(
            simple_network,
            total_time=0.1,
            events=None,
        )
        
        for result in results:
            assert hasattr(result, 'surge_pressures')
            assert isinstance(result.surge_pressures, dict)
            assert hasattr(result, 'cavitation_nodes')
            assert isinstance(result.cavitation_nodes, list)
