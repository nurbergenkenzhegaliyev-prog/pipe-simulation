"""Tests for network optimization functionality.

Tests cover:
- Optimization objective functions
- Constraint satisfaction
- Power minimization
- Flow balancing
- Edge cases and error handling
"""

import pytest
import math

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.models.equipment import PumpCurve, Valve
from app.services.pressure import PressureDropService
from app.services.optimization import (
    NetworkOptimizer,
    ObjectiveType,
    OptimizationConstraint,
    OptimizationResult,
)


@pytest.fixture
def fluid():
    """Standard test fluid."""
    return Fluid(density=998.0, viscosity=1e-3)


@pytest.fixture
def pressure_drop_service(fluid):
    """Pressure drop service with standard fluid."""
    return PressureDropService(fluid)


@pytest.fixture
def optimizer(pressure_drop_service):
    """Network optimizer."""
    return NetworkOptimizer(pressure_drop_service)


@pytest.fixture
def simple_network_with_pump():
    """Create a simple network with a pump."""
    network = PipeNetwork()
    
    source = Node(id="source", is_source=True, pressure=200000)
    sink = Node(id="sink")
    
    network.add_node(source)
    network.add_node(sink)
    
    pump_curve = PumpCurve(a=200000, b=-100000, c=-50000)
    pipe = Pipe(
        id="main_pipe",
        start_node="source",
        end_node="sink",
        length=100,
        diameter=0.05,
        roughness=0.000045,
        flow_rate=0.01,
        pump_curve=pump_curve,
    )
    network.add_pipe(pipe)
    
    return network


@pytest.fixture
def branched_network():
    """Create a branched network for balancing tests."""
    network = PipeNetwork()
    
    source = Node(id="source", is_source=True, pressure=300000)
    branch1 = Node(id="branch1")
    branch2 = Node(id="branch2")
    sink = Node(id="sink")
    
    network.add_node(source)
    network.add_node(branch1)
    network.add_node(branch2)
    network.add_node(sink)
    
    # Pipes from source to branches
    pipe1 = Pipe(
        id="pipe1",
        start_node="source",
        end_node="branch1",
        length=50,
        diameter=0.04,
        roughness=0.000045,
        flow_rate=0.005,
    )
    pipe2 = Pipe(
        id="pipe2",
        start_node="source",
        end_node="branch2",
        length=50,
        diameter=0.04,
        roughness=0.000045,
        flow_rate=0.005,
    )
    
    # Pipes from branches to sink
    pipe3 = Pipe(
        id="pipe3",
        start_node="branch1",
        end_node="sink",
        length=50,
        diameter=0.04,
        roughness=0.000045,
        flow_rate=0.005,
    )
    pipe4 = Pipe(
        id="pipe4",
        start_node="branch2",
        end_node="sink",
        length=50,
        diameter=0.04,
        roughness=0.000045,
        flow_rate=0.005,
    )
    
    network.add_pipe(pipe1)
    network.add_pipe(pipe2)
    network.add_pipe(pipe3)
    network.add_pipe(pipe4)
    
    return network


class TestOptimizationConstraint:
    """Test OptimizationConstraint dataclass."""
    
    def test_pressure_constraint(self):
        """Test creating a pressure constraint."""
        constraint = OptimizationConstraint(
            constraint_type='pressure',
            node_id='outlet',
            min_value=100000,
            max_value=300000,
        )
        assert constraint.constraint_type == 'pressure'
        assert constraint.node_id == 'outlet'
        assert constraint.min_value == 100000
        assert constraint.max_value == 300000
    
    def test_velocity_constraint(self):
        """Test creating a velocity constraint."""
        constraint = OptimizationConstraint(
            constraint_type='velocity',
            pipe_id='main_pipe',
            min_value=0.5,
            max_value=2.5,
            priority=1,
        )
        assert constraint.constraint_type == 'velocity'
        assert constraint.pipe_id == 'main_pipe'
        assert constraint.priority == 1


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""
    
    def test_result_creation(self):
        """Test creating optimization result."""
        result = OptimizationResult(
            success=True,
            iterations=25,
            objective_value=1234.5,
            improvement_percent=15.2,
        )
        assert result.success is True
        assert result.iterations == 25
        assert result.objective_value == 1234.5
        assert result.improvement_percent == 15.2
    
    def test_result_with_data(self):
        """Test result with optimization data."""
        result = OptimizationResult(
            success=True,
            iterations=50,
            objective_value=500.0,
            improvement_percent=25.0,
            optimized_flows={'pipe1': 0.01, 'pipe2': 0.012},
            optimized_pressures={'n1': 200000, 'n2': 150000},
        )
        assert len(result.optimized_flows) == 2
        assert result.optimized_flows['pipe1'] == 0.01
        assert result.optimized_pressures['n1'] == 200000


class TestNetworkOptimizerBasic:
    """Test basic optimizer functionality."""
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.dp_service is not None
        assert optimizer.solver is not None
        assert optimizer.last_result is None
    
    def test_invalid_network(self, optimizer):
        """Test that invalid network raises ValueError."""
        network = PipeNetwork()
        
        with pytest.raises(ValueError):
            optimizer.optimize(network, objective=ObjectiveType.MINIMIZE_POWER)
    
    def test_optimization_without_pump(self, optimizer):
        """Test optimization on network without pumps."""
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
        
        # Should still work, just no pumps to optimize
        result = optimizer.optimize(network, objective=ObjectiveType.MINIMIZE_POWER)
        assert isinstance(result, OptimizationResult)


class TestPowerMinimization:
    """Test pump power minimization optimization."""
    
    def test_minimize_power_objective(self, optimizer, simple_network_with_pump):
        """Test power minimization objective."""
        result = optimizer.optimize(
            simple_network_with_pump,
            objective=ObjectiveType.MINIMIZE_POWER,
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.objective_value >= 0
        assert result.iterations >= 0
        assert len(result.optimized_flows) > 0
    
    def test_power_calculation(self, optimizer, simple_network_with_pump):
        """Test power calculation method."""
        power = optimizer._calculate_total_power(simple_network_with_pump, ["main_pipe"])
        assert power >= 0  # Power should be non-negative
    
    def test_pump_multiplier_extraction(self, optimizer, simple_network_with_pump):
        """Test pump parameter extraction."""
        params = optimizer._extract_pump_parameters(simple_network_with_pump, ["main_pipe"])
        assert len(params) == 1
        assert isinstance(params[0], float)


class TestConstraintHandling:
    """Test constraint satisfaction."""
    
    def test_velocity_constraint(self, optimizer, simple_network_with_pump):
        """Test velocity constraint."""
        constraint = OptimizationConstraint(
            constraint_type='velocity',
            pipe_id='main_pipe',
            min_value=0.1,
            max_value=1.5,
        )
        
        result = optimizer.optimize(
            simple_network_with_pump,
            objective=ObjectiveType.MINIMIZE_POWER,
            constraints=[constraint],
        )
        
        assert isinstance(result, OptimizationResult)
        # Check that velocity is within constraint bounds
        pipe = simple_network_with_pump.pipes['main_pipe']
        flow = result.optimized_flows.get('main_pipe', 0.0)
        area = math.pi * (pipe.diameter / 2) ** 2
        velocity = abs(flow) / area if area > 0 else 0.0
        
        assert velocity >= constraint.min_value - 0.01  # Small tolerance
        assert velocity <= constraint.max_value + 0.01
    
    def test_multiple_constraints(self, optimizer, simple_network_with_pump):
        """Test with multiple constraints."""
        constraints = [
            OptimizationConstraint(
                constraint_type='velocity',
                pipe_id='main_pipe',
                min_value=0.1,
                max_value=2.0,
            ),
            OptimizationConstraint(
                constraint_type='pressure',
                node_id='sink',
                min_value=50000,
                max_value=250000,
            ),
        ]
        
        result = optimizer.optimize(
            simple_network_with_pump,
            objective=ObjectiveType.MINIMIZE_POWER,
            constraints=constraints,
        )
        
        assert isinstance(result, OptimizationResult)


class TestFlowBalancing:
    """Test flow balancing optimization."""
    
    def test_balance_flows_method(self, optimizer, branched_network):
        """Test flow balancing method."""
        result = optimizer.balance_flows(
            branched_network,
            pipe_ids=['pipe1', 'pipe2'],
        )
        
        assert isinstance(result, OptimizationResult)
        assert len(result.optimized_flows) > 0
    
    def test_flow_balance_cost(self, optimizer, branched_network):
        """Test flow balance cost calculation."""
        cost = optimizer._calculate_flow_balance_cost(branched_network)
        assert cost >= 0  # Standard deviation is non-negative


class TestObjectiveExtraction:
    """Test network value extraction."""
    
    def test_extract_pipe_flows(self, optimizer, simple_network_with_pump):
        """Test pipe flow extraction."""
        flows = optimizer._extract_pipe_flows(simple_network_with_pump)
        
        assert isinstance(flows, dict)
        assert len(flows) > 0
        assert 'main_pipe' in flows
    
    def test_extract_node_pressures(self, optimizer, simple_network_with_pump):
        """Test node pressure extraction."""
        pressures = optimizer._extract_node_pressures(simple_network_with_pump)
        
        assert isinstance(pressures, dict)
        assert len(pressures) > 0
        assert 'source' in pressures or 'sink' in pressures
    
    def test_extract_network_values(self, optimizer, simple_network_with_pump):
        """Test complete network value extraction."""
        values = optimizer._extract_network_values(simple_network_with_pump)
        
        assert 'flows' in values
        assert 'pressures' in values
        assert len(values['flows']) > 0
        assert len(values['pressures']) > 0


class TestMaxPressureCalculation:
    """Test maximum pressure calculation."""
    
    def test_calculate_max_pressure(self, optimizer, simple_network_with_pump):
        """Test maximum pressure calculation."""
        optimizer.solver.solve(simple_network_with_pump)
        max_pressure = optimizer._calculate_max_pressure(simple_network_with_pump)
        assert max_pressure >= 0
        assert max_pressure == pytest.approx(200000, rel=0.1)


class TestOptimizationSummary:
    """Test optimization summary generation."""
    
    def test_summary_before_optimization(self, optimizer):
        """Test summary before any optimization."""
        summary = optimizer.get_optimization_summary()
        assert "No optimization performed" in summary
    
    def test_summary_after_optimization(self, optimizer, simple_network_with_pump):
        """Test summary after optimization."""
        optimizer.optimize(simple_network_with_pump)
        summary = optimizer.get_optimization_summary()
        
        assert "Optimization Success" in summary
        assert "Iterations" in summary
        assert "Objective Value" in summary


class TestParameterApplication:
    """Test pump parameter application."""
    
    def test_apply_pump_parameters(self, optimizer, simple_network_with_pump):
        """Test applying pump parameters."""
        import numpy as np
        
        new_values = np.array([1.5])
        optimizer._apply_pump_parameters(simple_network_with_pump, ["main_pipe"], new_values)
        
        pipe = simple_network_with_pump.pipes['main_pipe']
        multiplier = getattr(pipe, 'pump_multiplier', 1.0)
        assert multiplier == 1.5


class TestObjectiveTypes:
    """Test different objective types."""
    
    def test_minimize_pressure_objective(self, optimizer, simple_network_with_pump):
        """Test pressure minimization objective."""
        result = optimizer.optimize(
            simple_network_with_pump,
            objective=ObjectiveType.MINIMIZE_PRESSURE,
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.objective_value >= 0
    
    def test_balance_flows_objective(self, optimizer, branched_network):
        """Test flow balancing objective."""
        result = optimizer.optimize(
            branched_network,
            objective=ObjectiveType.BALANCE_FLOWS,
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.objective_value >= 0
