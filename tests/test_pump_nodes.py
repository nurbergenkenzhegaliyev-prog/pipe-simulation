"""Tests for pump nodes in pipe networks.

Verifies that node-based pumps (is_pump=True with pressure_ratio)
correctly increase pressure in the network.
"""

import pytest

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver, SolverMethod


@pytest.fixture
def fluid():
    """Standard water properties."""
    return Fluid(density=998.0, viscosity=0.001)


@pytest.fixture
def dp_service(fluid):
    """Pressure drop service."""
    return PressureDropService(fluid)


class TestNodeBasedPumps:
    """Test pump nodes (is_pump=True) with pressure_ratio."""
    
    def test_single_pump_increases_pressure(self, dp_service):
        """Test that a pump node increases downstream pressure."""
        network = PipeNetwork()
        
        # Source at 10 bar
        n1 = Node(id="N1", pressure=1000000.0, is_source=True)
        network.add_node(n1)
        
        # Pump with 1.5x pressure ratio
        n2 = Node(id="N2", is_pump=True, pressure_ratio=1.5)
        network.add_node(n2)
        
        # Sink
        n3 = Node(id="N3", is_sink=True, flow_rate=0.01)
        network.add_node(n3)
        
        # Pipes
        p1 = Pipe(id="P1", start_node="N1", end_node="N2", 
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p1)
        
        p2 = Pipe(id="P2", start_node="N2", end_node="N3",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p2)
        
        # Solve
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # Pump should show discharge pressure > source pressure
        assert n2.pressure > n1.pressure, "Pump discharge should be higher than source"
        
        # Output should be higher than source (minus pipe losses)
        assert n3.pressure > n1.pressure, "Output should be higher than source due to pump"
        
        # Calculate expected pump gain
        # Pump inlet ≈ source - pipe1_drop
        # Pump gain = inlet * (ratio - 1)
        # Discharge = inlet + gain = inlet * ratio
        inlet_estimate = n1.pressure - p1.pressure_drop
        expected_discharge = inlet_estimate * n2.pressure_ratio
        
        # Pump node should show discharge pressure
        assert abs(n2.pressure - expected_discharge) < 1000, \
            f"Pump discharge {n2.pressure/1e5:.2f} bar should be ≈ {expected_discharge/1e5:.2f} bar"
    
    def test_pump_with_different_ratios(self, dp_service):
        """Test pumps with different pressure ratios."""
        for ratio in [1.2, 1.5, 2.0, 3.0]:
            network = PipeNetwork()
            
            n1 = Node(id="N1", pressure=1000000.0, is_source=True)
            network.add_node(n1)
            
            n2 = Node(id="N2", is_pump=True, pressure_ratio=ratio)
            network.add_node(n2)
            
            n3 = Node(id="N3", is_sink=True, flow_rate=0.01)
            network.add_node(n3)
            
            p1 = Pipe(id="P1", start_node="N1", end_node="N2",
                      length=50.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
            network.add_pipe(p1)
            
            p2 = Pipe(id="P2", start_node="N2", end_node="N3",
                      length=50.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
            network.add_pipe(p2)
            
            solver = NetworkSolver(dp_service)
            solver.solve(network)
            
            # Pump discharge should reflect the ratio
            inlet_pressure = n1.pressure - p1.pressure_drop
            expected_discharge = inlet_pressure * ratio
            
            assert abs(n2.pressure - expected_discharge) / expected_discharge < 0.01, \
                f"Pump with ratio {ratio} should show discharge ≈ {expected_discharge/1e5:.2f} bar"
    
    def test_series_pumps(self, dp_service):
        """Test multiple pumps in series."""
        network = PipeNetwork()
        
        # Source at 5 bar
        n1 = Node(id="N1", pressure=500000.0, is_source=True)
        network.add_node(n1)
        
        # First pump: 1.5x
        n2 = Node(id="N2", is_pump=True, pressure_ratio=1.5)
        network.add_node(n2)
        
        # Second pump: 1.5x
        n3 = Node(id="N3", is_pump=True, pressure_ratio=1.5)
        network.add_node(n3)
        
        # Sink
        n4 = Node(id="N4", is_sink=True, flow_rate=0.01)
        network.add_node(n4)
        
        # Pipes
        for i, (start, end) in enumerate([("N1", "N2"), ("N2", "N3"), ("N3", "N4")], 1):
            p = Pipe(id=f"P{i}", start_node=start, end_node=end,
                     length=50.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
            network.add_pipe(p)
        
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # Each pump should increase pressure
        assert n2.pressure > n1.pressure, "First pump should boost pressure"
        assert n3.pressure > n2.pressure, "Second pump should boost pressure further"
        
        # Final pressure should be significantly higher than source
        # (accounting for pipe losses between pumps)
        assert n4.pressure > n1.pressure * 1.5, \
            "Series pumps should provide significant pressure boost"
    
    def test_pump_without_pressure_ratio(self, dp_service):
        """Test that pump node without pressure_ratio acts as regular node."""
        network = PipeNetwork()
        
        n1 = Node(id="N1", pressure=1000000.0, is_source=True)
        network.add_node(n1)
        
        # Pump flag but no pressure_ratio (should not boost)
        n2 = Node(id="N2", is_pump=True, pressure_ratio=None)
        network.add_node(n2)
        
        n3 = Node(id="N3", is_sink=True, flow_rate=0.01)
        network.add_node(n3)
        
        p1 = Pipe(id="P1", start_node="N1", end_node="N2",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p1)
        
        p2 = Pipe(id="P2", start_node="N2", end_node="N3",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p2)
        
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # Without pressure_ratio, should act like regular node
        # Pressure should only drop (never increase)
        assert n2.pressure <= n1.pressure, "Node without pressure_ratio should not boost"
        assert n3.pressure <= n2.pressure, "Pressure continues to drop"
    
    def test_pump_with_pressure_ratio_one(self, dp_service):
        """Test pump with pressure_ratio=1.0 (no boost)."""
        network = PipeNetwork()
        
        n1 = Node(id="N1", pressure=1000000.0, is_source=True)
        network.add_node(n1)
        
        # Ratio of 1.0 means no pressure gain
        n2 = Node(id="N2", is_pump=True, pressure_ratio=1.0)
        network.add_node(n2)
        
        n3 = Node(id="N3", is_sink=True, flow_rate=0.01)
        network.add_node(n3)
        
        p1 = Pipe(id="P1", start_node="N1", end_node="N2",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p1)
        
        p2 = Pipe(id="P2", start_node="N2", end_node="N3",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        network.add_pipe(p2)
        
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # With ratio=1.0, pump gain = inlet * (1.0 - 1.0) = 0
        # So pump discharge = inlet (no boost)
        inlet = n1.pressure - p1.pressure_drop
        
        # Pump should show inlet pressure (no boost)
        assert abs(n2.pressure - inlet) < 1000, \
            "Pump with ratio=1.0 should not change pressure"


class TestPumpVsRegularNodes:
    """Compare pump nodes to regular nodes."""
    
    def test_pump_delivers_higher_pressure_than_regular(self, dp_service):
        """Compare network with pump vs without pump."""
        # Network WITH pump
        net_with_pump = PipeNetwork()
        n1 = Node(id="N1", pressure=1000000.0, is_source=True)
        n2 = Node(id="N2", is_pump=True, pressure_ratio=1.5)
        n3 = Node(id="N3", is_sink=True, flow_rate=0.01)
        net_with_pump.add_node(n1)
        net_with_pump.add_node(n2)
        net_with_pump.add_node(n3)
        
        p1 = Pipe(id="P1", start_node="N1", end_node="N2",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        p2 = Pipe(id="P2", start_node="N2", end_node="N3",
                  length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        net_with_pump.add_pipe(p1)
        net_with_pump.add_pipe(p2)
        
        solver = NetworkSolver(dp_service)
        solver.solve(net_with_pump)
        pressure_with_pump = net_with_pump.nodes["N3"].pressure
        
        # Network WITHOUT pump (regular junction)
        net_no_pump = PipeNetwork()
        n1_reg = Node(id="N1", pressure=1000000.0, is_source=True)
        n2_reg = Node(id="N2")  # Regular node
        n3_reg = Node(id="N3", is_sink=True, flow_rate=0.01)
        net_no_pump.add_node(n1_reg)
        net_no_pump.add_node(n2_reg)
        net_no_pump.add_node(n3_reg)
        
        p1_reg = Pipe(id="P1", start_node="N1", end_node="N2",
                      length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        p2_reg = Pipe(id="P2", start_node="N2", end_node="N3",
                      length=100.0, diameter=0.1, roughness=0.00005, flow_rate=0.01)
        net_no_pump.add_pipe(p1_reg)
        net_no_pump.add_pipe(p2_reg)
        
        solver.solve(net_no_pump)
        pressure_no_pump = net_no_pump.nodes["N3"].pressure
        
        # Pump should deliver significantly higher pressure
        assert pressure_with_pump > pressure_no_pump, \
            "Network with pump should have higher output pressure"
        
        improvement = (pressure_with_pump - pressure_no_pump) / pressure_no_pump
        assert improvement > 0.3, \
            f"Pump should provide >30% pressure improvement, got {improvement*100:.1f}%"
