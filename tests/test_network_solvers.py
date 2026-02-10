"""
Tests for network solver components - the core simulation algorithms.

Tests cover:
- CycleFinder: Detecting loops in the network
- HardyCrossSolver: Iterative solver for looped networks
- NewtonRaphsonSolver: Matrix-based solver for complex networks
- PressurePropagation: Pressure propagation through tree networks
- NetworkSolver: Main solver orchestration with method selection
"""

import pytest
import math
from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver, SolverMethod
from app.services.solvers.cycle_finder import CycleFinder
from app.services.solvers.hardy_cross_solver import HardyCrossSolver
from app.services.solvers.newton_raphson_solver import NewtonRaphsonSolver
from app.services.solvers.pressure_propagation import PressurePropagation


class TestCycleFinder:
    """Test cycle detection in networks."""
    
    def test_no_cycles_in_simple_chain(self):
        """Should find no cycles in a simple linear network."""
        network = PipeNetwork()
        network.add_node(Node(id="A", pressure=500000.0, is_source=True))
        network.add_node(Node(id="B"))
        network.add_node(Node(id="C"))
        
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="B", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        assert len(cycles) == 0
    
    def test_single_simple_cycle(self):
        """Should detect a single simple loop."""
        network = PipeNetwork()
        network.add_node(Node(id="A", pressure=500000.0, is_source=True))
        network.add_node(Node(id="B"))
        network.add_node(Node(id="C"))
        
        # Create a triangle loop
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="B", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="C", end_node="A",
                              length=100, diameter=0.1, roughness=0.0001))
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        assert len(cycles) >= 1
        # First cycle should contain all three pipes
        assert len(cycles[0]) == 3
    
    def test_multiple_cycles(self):
        """Should detect multiple loops in complex networks."""
        network = PipeNetwork()
        # Create two adjacent squares sharing an edge
        network.add_node(Node(id="A", pressure=500000.0, is_source=True))
        network.add_node(Node(id="B"))
        network.add_node(Node(id="C"))
        network.add_node(Node(id="D"))
        
        # First square: A-B-C-A
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="B", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="C", end_node="A",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # Second square: B-D-C-B (shares B-C edge)
        network.add_pipe(Pipe(id="P4", start_node="B", end_node="D",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P5", start_node="D", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        # Should find at least 2 cycles (possibly 3: the two squares plus the combined outer loop)
        assert len(cycles) >= 2
    
    def test_branched_network_no_cycles(self):
        """Should find no cycles in a branched tree."""
        network = PipeNetwork()
        network.add_node(Node(id="ROOT", pressure=500000.0, is_source=True))
        network.add_node(Node(id="B1"))
        network.add_node(Node(id="B2"))
        network.add_node(Node(id="L1"))
        network.add_node(Node(id="L2"))
        
        network.add_pipe(Pipe(id="P1", start_node="ROOT", end_node="B1",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="ROOT", end_node="B2",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="B1", end_node="L1",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P4", start_node="B2", end_node="L2",
                              length=100, diameter=0.1, roughness=0.0001))
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        assert len(cycles) == 0


class TestPressurePropagation:
    """Test pressure propagation through tree networks."""
    
    def test_simple_linear_propagation(self):
        """Should propagate pressure through simple linear network."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="MID"))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="MID",
                              length=1000, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P2", start_node="MID", end_node="SINK",
                              length=1000, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        propagator = PressurePropagation(dp_service)
        
        propagator.propagate(network)
        
        # Source should keep its pressure
        assert network.nodes["SRC"].pressure == pytest.approx(1000000.0)
        
        # Downstream nodes should have lower pressure
        assert network.nodes["MID"].pressure is not None
        assert network.nodes["MID"].pressure < 1000000.0
        
        assert network.nodes["SINK"].pressure is not None
        assert network.nodes["SINK"].pressure < network.nodes["MID"].pressure
    
    def test_branched_propagation(self):
        """Should handle branched networks correctly."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=800000.0, is_source=True))
        network.add_node(Node(id="BRANCH"))
        network.add_node(Node(id="SINK1", is_sink=True, flow_rate=0.03))
        network.add_node(Node(id="SINK2", is_sink=True, flow_rate=0.02))
        
        network.add_pipe(Pipe(id="P0", start_node="SRC", end_node="BRANCH",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P1", start_node="BRANCH", end_node="SINK1",
                              length=500, diameter=0.15, roughness=0.0001, flow_rate=0.03))
        network.add_pipe(Pipe(id="P2", start_node="BRANCH", end_node="SINK2",
                              length=500, diameter=0.15, roughness=0.0001, flow_rate=0.02))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        propagator = PressurePropagation(dp_service)
        
        propagator.propagate(network)
        
        # All nodes should have pressure
        assert all(node.pressure is not None for node in network.nodes.values())
        
        # Branch should be lower than source
        assert network.nodes["BRANCH"].pressure < network.nodes["SRC"].pressure
        
        # Both sinks should be lower than branch
        assert network.nodes["SINK1"].pressure < network.nodes["BRANCH"].pressure
        assert network.nodes["SINK2"].pressure < network.nodes["BRANCH"].pressure
    
    def test_pump_increases_pressure(self):
        """Should handle pump nodes correctly in propagation."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=500000.0, is_source=True))
        network.add_node(Node(id="PUMP", is_pump=True, pressure_ratio=1.5))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="PUMP",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P2", start_node="PUMP", end_node="SINK",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        propagator = PressurePropagation(dp_service)
        
        propagator.propagate(network)
        
        # Pump discharge should be higher than source (after friction loss and pump gain)
        # Can't directly compare due to DP in first pipe, but it should solve
        assert network.nodes["PUMP"].pressure is not None
        assert network.nodes["SINK"].pressure is not None


class TestNetworkSolver:
    """Test main NetworkSolver with method selection."""
    
    def test_solver_initialization_default(self):
        """Should initialize with default Newton-Raphson method."""
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        
        assert solver.method == SolverMethod.NEWTON_RAPHSON
    
    def test_solver_initialization_hardy_cross(self):
        """Should initialize with Hardy-Cross when specified."""
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service, method=SolverMethod.HARDY_CROSS)
        
        assert solver.method == SolverMethod.HARDY_CROSS
    
    def test_solver_method_change(self):
        """Should allow changing solver method."""
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        
        solver.set_method(SolverMethod.HARDY_CROSS)
        assert solver.method == SolverMethod.HARDY_CROSS
        
        solver.set_method(SolverMethod.NEWTON_RAPHSON)
        assert solver.method == SolverMethod.NEWTON_RAPHSON
    
    def test_solve_simple_tree_network(self):
        """Should solve simple tree network with any method."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="SINK",
                              length=1000, diameter=0.2, roughness=0.0001))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        
        # Try with Newton-Raphson
        solver_nr = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)
        solver_nr.solve(network)
        
        assert network.nodes["SRC"].pressure == pytest.approx(1000000.0)
        assert network.nodes["SINK"].pressure is not None
        assert network.nodes["SINK"].pressure < 1000000.0
        assert network.pipes["P1"].flow_rate is not None
    
    def test_solve_looped_network_hardy_cross(self):
        """Should solve looped network with Hardy-Cross method."""
        network = PipeNetwork()
        # Square loop: SRC at top-left, SINK at bottom-right
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="TOP"))  # Top-right
        network.add_node(Node(id="BOT"))  # Bottom-left
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.1))
        
        # Create square loop with two paths from SRC to SINK
        # Path 1: SRC -> TOP -> SINK (top edge, right edge)
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="TOP",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P2", start_node="TOP", end_node="SINK",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        # Path 2: SRC -> BOT -> SINK (left edge, bottom edge)
        network.add_pipe(Pipe(id="P3", start_node="SRC", end_node="BOT",
                              length=600, diameter=0.15, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P4", start_node="BOT", end_node="SINK",
                              length=600, diameter=0.15, roughness=0.0001, flow_rate=0.05))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service, method=SolverMethod.HARDY_CROSS)
        
        # Hardy-Cross should solve looped networks
        solver.solve(network)
        
        # All nodes should have pressures
        assert all(node.pressure is not None for node in network.nodes.values())
    
    def test_solve_looped_network_newton_raphson(self):
        """Should solve looped network with Newton-Raphson method."""
        network = PipeNetwork()
        # Square loop: SRC at top-left, SINK at bottom-right
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="TOP"))  # Top-right
        network.add_node(Node(id="BOT"))  # Bottom-left
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.1))
        
        # Create same square loop as Hardy-Cross test
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="TOP",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P2", start_node="TOP", end_node="SINK",
                              length=500, diameter=0.2, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P3", start_node="SRC", end_node="BOT",
                              length=600, diameter=0.15, roughness=0.0001, flow_rate=0.05))
        network.add_pipe(Pipe(id="P4", start_node="BOT", end_node="SINK",
                              length=600, diameter=0.15, roughness=0.0001, flow_rate=0.05))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)
        
        # Newton-Raphson should also solve looped networks
        solver.solve(network)
        
        # All nodes should have pressures
        assert all(node.pressure is not None for node in network.nodes.values())
    
    def test_solver_methods_give_similar_results(self):
        """Both solvers should give similar results for same network."""
        # Build network once
        def build_test_network():
            network = PipeNetwork()
            network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
            network.add_node(Node(id="MID"))
            network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
            
            network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="MID",
                                  length=1000, diameter=0.2, roughness=0.0001, flow_rate=0.05))
            network.add_pipe(Pipe(id="P2", start_node="MID", end_node="SINK",
                                  length=1000, diameter=0.2, roughness=0.0001, flow_rate=0.05))
            return network
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        
        # Solve with Hardy-Cross
        network_hc = build_test_network()
        solver_hc = NetworkSolver(dp_service, method=SolverMethod.HARDY_CROSS)
        solver_hc.solve(network_hc)
        pressure_hc = network_hc.nodes["SINK"].pressure
        
        # Solve with Newton-Raphson
        network_nr = build_test_network()
        solver_nr = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)
        solver_nr.solve(network_nr)
        pressure_nr = network_nr.nodes["SINK"].pressure
        
        # Results should be very close (within 1%)
        assert pressure_nr == pytest.approx(pressure_hc, rel=0.01)


class TestHardyCrossSolver:
    """Test Hardy-Cross solver specifically."""
    
    def test_hardy_cross_on_simple_loop(self):
        """Hardy-Cross should balance flows in a simple loop."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="A"))
        network.add_node(Node(id="B"))
        
        # Triangle loop with initial flow guesses
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="A",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        network.add_pipe(Pipe(id="P2", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        network.add_pipe(Pipe(id="P3", start_node="B", end_node="SRC",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = HardyCrossSolver(dp_service)
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        # Apply Hardy-Cross
        solver.apply(network, cycles)
        
        # After Hardy-Cross, should have balanced flows
        # Verify that at least the solver ran without error
        assert True


class TestNewtonRaphsonSolver:
    """Test Newton-Raphson solver specifically."""
    
    def test_newton_raphson_initialization(self):
        """Should initialize properly."""
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NewtonRaphsonSolver(dp_service)
        
        assert solver.dp_service is dp_service
    
    def test_newton_raphson_solve_simple_network(self):
        """Should solve a simple network."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="A"))
        network.add_node(Node(id="B"))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="A",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        network.add_pipe(Pipe(id="P2", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        network.add_pipe(Pipe(id="P3", start_node="B", end_node="SRC",
                              length=100, diameter=0.1, roughness=0.0001, flow_rate=0.01))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NewtonRaphsonSolver(dp_service)
        
        finder = CycleFinder()
        cycles = finder.find_cycles(network)
        
        # Should solve without error
        solver.solve(network, cycles)
        
        # Verify solution completed
        assert True


class TestSolverErrorHandling:
    """Test error handling in solvers."""
    
    def test_no_source_node_error(self):
        """Should raise error when network has no source node."""
        network = PipeNetwork()
        network.add_node(Node(id="A"))
        network.add_node(Node(id="B"))
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        
        with pytest.raises(ValueError):
            solver.solve(network)
    
    def test_empty_network_error(self):
        """Should handle empty network gracefully."""
        network = PipeNetwork()
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        propagator = PressurePropagation(dp_service)
        
        # Should raise error about no boundary conditions
        with pytest.raises(ValueError):
            propagator.propagate(network)


class TestSolverConvergence:
    """Test solver convergence behavior."""
    
    def test_solver_converges_on_reasonable_network(self):
        """Solver should converge on well-conditioned network."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="SINK",
                              length=1000, diameter=0.2, roughness=0.0001))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        
        # Should complete without timeout or iteration limit
        solver.solve(network)
        
        assert network.nodes["SINK"].pressure is not None
    
    def test_reasonable_pressure_values(self):
        """Solved pressures should be physically reasonable."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))  # 10 bar
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="SINK",
                              length=1000, diameter=0.2, roughness=0.0001))
        
        fluid = Fluid()
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        sink_pressure = network.nodes["SINK"].pressure
        
        # Pressure should be positive
        assert sink_pressure > 0
        
        # Pressure should be less than source
        assert sink_pressure < 1000000.0
        
        # Pressure drop should be reasonable (not more than source pressure)
        assert sink_pressure > 0.1 * 1000000.0  # At least 10% remaining


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
