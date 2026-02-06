"""Performance benchmarks for pipe network simulation"""

import pytest
import time
from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver


class TestPerformanceBenchmarks:
    """Performance tests for network simulation scalability"""
    
    def test_small_network_10_nodes(self):
        """Benchmark: 10 nodes, 9 pipes (tree structure)"""
        network, fluid = self._create_linear_network(10)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n10 nodes: {elapsed:.4f} seconds")
        assert elapsed < 1.0, "Small network should solve in under 1 second"
    
    def test_medium_network_50_nodes(self):
        """Benchmark: 50 nodes, 49 pipes (tree structure)"""
        network, fluid = self._create_linear_network(50)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n50 nodes: {elapsed:.4f} seconds")
        assert elapsed < 2.0, "Medium network should solve in under 2 seconds"
    
    def test_large_network_100_nodes(self):
        """Benchmark: 100 nodes, 99 pipes (tree structure)"""
        network, fluid = self._create_linear_network(100)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n100 nodes: {elapsed:.4f} seconds")
        assert elapsed < 5.0, "Large network should solve in under 5 seconds"
    
    def test_very_large_network_200_nodes(self):
        """Benchmark: 200 nodes, 199 pipes (tree structure)"""
        network, fluid = self._create_linear_network(200)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n200 nodes: {elapsed:.4f} seconds")
        assert elapsed < 10.0, "Very large network should solve in under 10 seconds"
    
    def test_branched_network_50_nodes(self):
        """Benchmark: 50 nodes in branched structure"""
        network, fluid = self._create_branched_network(50)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n50 nodes (branched): {elapsed:.4f} seconds")
        assert elapsed < 3.0, "Branched network should solve in under 3 seconds"
    
    def test_grid_network_25_nodes(self):
        """Benchmark: 5x5 grid with loops"""
        network, fluid = self._create_grid_network(5, 5)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n25 nodes (5x5 grid with loops): {elapsed:.4f} seconds")
        assert elapsed < 5.0, "Grid with loops should solve in under 5 seconds"
    
    def test_multiphase_performance(self):
        """Benchmark: Multi-phase flow simulation with 50 nodes"""
        network, fluid = self._create_linear_network(50, multiphase=True)
        
        start = time.time()
        self._run_simulation(network, fluid)
        elapsed = time.time() - start
        
        print(f"\n50 nodes (multi-phase): {elapsed:.4f} seconds")
        assert elapsed < 3.0, "Multi-phase should solve in under 3 seconds"
    
    def test_solver_iterations_performance(self):
        """Benchmark: Test solver iteration count for looped network"""
        network, fluid = self._create_grid_network(4, 4)
        
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        
        start = time.time()
        solver.solve(network)
        elapsed = time.time() - start
        
        print(f"\n16 nodes (4x4 grid): {elapsed:.4f} seconds")
        # Hardy-Cross iterations should converge quickly
        assert elapsed < 2.0, "Looped network should converge in under 2 seconds"
    
    # Helper methods
    
    def _create_linear_network(self, num_nodes: int, multiphase: bool = False) -> tuple:
        """Create a linear network (tree structure)"""
        network = PipeNetwork()
        
        # Create fluid
        if multiphase:
            fluid = Fluid(
                is_multiphase=True,
                liquid_density=998.0,
                gas_density=1.2,
                liquid_viscosity=1e-3,
                gas_viscosity=1.8e-5
            )
        else:
            fluid = Fluid()
        
        # Add source node
        network.add_node(Node(
            id=f"N0",
            pressure=1_000_000.0,  # 10 bar
            is_source=True
        ))
        
        # Add junction nodes
        for i in range(1, num_nodes - 1):
            network.add_node(Node(id=f"N{i}"))
        
        # Add sink node
        network.add_node(Node(
            id=f"N{num_nodes - 1}",
            flow_rate=0.05,
            is_sink=True
        ))
        
        # Add pipes
        for i in range(num_nodes - 1):
            if multiphase:
                pipe = Pipe(
                    id=f"P{i}",
                    start_node=f"N{i}",
                    end_node=f"N{i+1}",
                    length=100.0,
                    diameter=0.1,
                    roughness=0.005,
                    liquid_flow_rate=0.03,
                    gas_flow_rate=0.02
                )
            else:
                pipe = Pipe(
                    id=f"P{i}",
                    start_node=f"N{i}",
                    end_node=f"N{i+1}",
                    length=100.0,
                    diameter=0.1,
                    roughness=0.005,
                    flow_rate=0.05
                )
            network.add_pipe(pipe)
        
        return network, fluid
    
    def _create_branched_network(self, num_nodes: int) -> tuple:
        """Create a branched tree network"""
        network = PipeNetwork()
        fluid = Fluid()
        
        # Add source
        network.add_node(Node(
            id="N0",
            pressure=1_000_000.0,
            is_source=True
        ))
        
        # Create branches (binary tree-like structure)
        nodes_created = 1
        current_level = [0]
        
        while nodes_created < num_nodes:
            next_level = []
            for parent_idx in current_level:
                for child in range(2):  # 2 children per node
                    if nodes_created >= num_nodes:
                        break
                    
                    child_id = f"N{nodes_created}"
                    
                    # Last nodes are sinks
                    is_sink = nodes_created >= num_nodes - 5
                    
                    if is_sink:
                        network.add_node(Node(
                            id=child_id,
                            flow_rate=0.01,
                            is_sink=True
                        ))
                    else:
                        network.add_node(Node(id=child_id))
                    
                    # Add pipe
                    network.add_pipe(Pipe(
                        id=f"P{parent_idx}_{nodes_created}",
                        start_node=f"N{parent_idx}",
                        end_node=child_id,
                        length=50.0,
                        diameter=0.08,
                        roughness=0.005,
                        flow_rate=0.02
                    ))
                    
                    next_level.append(nodes_created)
                    nodes_created += 1
            
            current_level = next_level
        
        return network, fluid
    
    def _create_grid_network(self, rows: int, cols: int) -> tuple:
        """Create a grid network with loops"""
        network = PipeNetwork()
        fluid = Fluid()
        
        # Create nodes in grid
        for i in range(rows):
            for j in range(cols):
                node_id = f"N{i}_{j}"
                
                # Top-left is source
                if i == 0 and j == 0:
                    network.add_node(Node(
                        id=node_id,
                        pressure=1_000_000.0,
                        is_source=True
                    ))
                # Bottom-right is sink
                elif i == rows - 1 and j == cols - 1:
                    network.add_node(Node(
                        id=node_id,
                        flow_rate=0.05,
                        is_sink=True
                    ))
                else:
                    network.add_node(Node(id=node_id))
        
        # Create horizontal pipes
        pipe_id = 0
        for i in range(rows):
            for j in range(cols - 1):
                network.add_pipe(Pipe(
                    id=f"P{pipe_id}",
                    start_node=f"N{i}_{j}",
                    end_node=f"N{i}_{j+1}",
                    length=50.0,
                    diameter=0.1,
                    roughness=0.005,
                    flow_rate=0.01
                ))
                pipe_id += 1
        
        # Create vertical pipes
        for i in range(rows - 1):
            for j in range(cols):
                network.add_pipe(Pipe(
                    id=f"P{pipe_id}",
                    start_node=f"N{i}_{j}",
                    end_node=f"N{i+1}_{j}",
                    length=50.0,
                    diameter=0.1,
                    roughness=0.005,
                    flow_rate=0.01
                ))
                pipe_id += 1
        
        return network, fluid
    
    def _run_simulation(self, network: PipeNetwork, fluid: Fluid):
        """Run the pressure solver on a network"""
        dp_service = PressureDropService(fluid)
        solver = NetworkSolver(dp_service)
        solver.solve(network)
        
        # Verify results
        assert all(node.pressure is not None for node in network.nodes.values()), \
            "All nodes should have pressure calculated"


if __name__ == "__main__":
    # Run benchmarks and report results
    pytest.main([__file__, "-v", "-s"])
