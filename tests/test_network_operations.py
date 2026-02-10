"""Tests for advanced network scenarios and operations.

Tests cover:
- Network creation and manipulation
- Large network handling
- Network topology validation
- Graph operations (traversal, connectivity)
- Network modification safety
"""

import pytest
import math

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid


class TestNetworkBasics:
    """Test basic network creation and operations"""
    
    def test_create_empty_network(self):
        """Should create empty network"""
        network = PipeNetwork()
        
        assert len(network.nodes) == 0
        assert len(network.pipes) == 0
    
    def test_add_single_node(self):
        """Should add node to network"""
        network = PipeNetwork()
        node = Node(id='N1')
        
        network.add_node(node)
        
        assert len(network.nodes) == 1
        assert 'N1' in network.nodes
    
    def test_add_multiple_nodes(self):
        """Should add multiple nodes"""
        network = PipeNetwork()
        
        for i in range(5):
            network.add_node(Node(id=f'N{i}'))
        
        assert len(network.nodes) == 5
    
    def test_duplicate_node_error(self):
        """Should raise error for duplicate node ID"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        
        with pytest.raises(ValueError):
            network.add_node(Node(id='N1'))
    
    def test_add_simple_pipe(self):
        """Should add pipe between nodes"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045
        )
        network.add_pipe(pipe)
        
        assert len(network.pipes) == 1
        assert 'P1' in network.pipes
    
    def test_pipe_validation_missing_start_node(self):
        """Should validate start node exists"""
        network = PipeNetwork()
        network.add_node(Node(id='N2'))
        
        pipe = Pipe(
            id='P1',
            start_node='N1',  # Missing!
            end_node='N2',
            length=100.0,
            diameter=0.05,
            roughness=0.000045
        )
        
        with pytest.raises(ValueError):
            network.add_pipe(pipe)
    
    def test_pipe_validation_missing_end_node(self):
        """Should validate end node exists"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        
        pipe = Pipe(
            id='P1',
            start_node='N1',
            end_node='N2',  # Missing!
            length=100.0,
            diameter=0.05,
            roughness=0.000045
        )
        
        with pytest.raises(ValueError):
            network.add_pipe(pipe)


class TestNetworkTopologies:
    """Test different network configurations"""
    
    def test_linear_topology(self):
        """Should create linear pipe topology"""
        network = PipeNetwork()
        
        # Create chain: N0 -> N1 -> N2 -> N3
        for i in range(4):
            network.add_node(Node(id=f'N{i}'))
        
        for i in range(3):
            pipe = Pipe(
                id=f'P{i}',
                start_node=f'N{i}',
                end_node=f'N{i+1}',
                length=100.0,
                diameter=0.05,
                roughness=0.000045
            )
            network.add_pipe(pipe)
        
        assert len(network.nodes) == 4
        assert len(network.pipes) == 3
    
    def test_branching_topology(self):
        """Should create branching topology"""
        network = PipeNetwork()
        
        # Create branching: N0 -> N1 -> N2
        #                              -> N3
        #                              -> N4
        nodes = ['N0', 'N1', 'N2', 'N3', 'N4']
        for nid in nodes:
            network.add_node(Node(id=nid))
        
        edges = [
            ('N0', 'N1'),
            ('N1', 'N2'),
            ('N1', 'N3'),
            ('N1', 'N4'),
        ]
        
        for i, (start, end) in enumerate(edges):
            pipe = Pipe(
                id=f'P{i}',
                start_node=start,
                end_node=end,
                length=100.0,
                diameter=0.05,
                roughness=0.000045
            )
            network.add_pipe(pipe)
        
        assert len(network.nodes) == 5
        assert len(network.pipes) == 4
    
    def test_loop_topology(self):
        """Should create network with loop"""
        network = PipeNetwork()
        
        # Create loop: N0 -> N1 -> N2 -> N3 -> N0
        nodes = ['N0', 'N1', 'N2', 'N3']
        for nid in nodes:
            network.add_node(Node(id=nid))
        
        edges = [
            ('N0', 'N1'),
            ('N1', 'N2'),
            ('N2', 'N3'),
            ('N3', 'N0'),  # Closes loop
        ]
        
        for i, (start, end) in enumerate(edges):
            pipe = Pipe(
                id=f'P{i}',
                start_node=start,
                end_node=end,
                length=100.0,
                diameter=0.05,
                roughness=0.000045
            )
            network.add_pipe(pipe)
        
        assert len(network.pipes) == 4  # Full loop
    
    def test_mesh_topology(self):
        """Should create mesh topology"""
        network = PipeNetwork()
        
        # Create 3x3 grid mesh
        for i in range(3):
            for j in range(3):
                nid = f'N_{i}_{j}'
                network.add_node(Node(id=nid))
        
        # Connect horizontally and vertically
        pipe_id = 0
        
        # Horizontal connections
        for i in range(3):
            for j in range(2):
                pipe = Pipe(
                    id=f'P{pipe_id}',
                    start_node=f'N_{i}_{j}',
                    end_node=f'N_{i}_{j+1}',
                    length=100.0,
                    diameter=0.05,
                    roughness=0.000045
                )
                network.add_pipe(pipe)
                pipe_id += 1
        
        # Vertical connections
        for i in range(2):
            for j in range(3):
                pipe = Pipe(
                    id=f'P{pipe_id}',
                    start_node=f'N_{i}_{j}',
                    end_node=f'N_{i+1}_{j}',
                    length=100.0,
                    diameter=0.05,
                    roughness=0.000045
                )
                network.add_pipe(pipe)
                pipe_id += 1
        
        assert len(network.nodes) == 9
        assert len(network.pipes) == 12  # 6 horizontal + 6 vertical


class TestNetworkGraphOperations:
    """Test graph traversal and connectivity operations"""
    
    def test_get_outgoing_pipes(self):
        """Should find all outgoing pipes from node"""
        network = PipeNetwork()
        
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        network.add_node(Node(id='N3'))
        
        network.add_pipe(Pipe('P1', 'N1', 'N2', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P2', 'N1', 'N3', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P3', 'N2', 'N3', 100, 0.05, 0.000045))
        
        outgoing = network.get_outgoing_pipes('N1')
        
        assert len(outgoing) == 2
        assert all(p.start_node == 'N1' for p in outgoing)
    
    def test_get_incoming_pipes(self):
        """Should find all incoming pipes to node"""
        network = PipeNetwork()
        
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        network.add_node(Node(id='N3'))
        
        network.add_pipe(Pipe('P1', 'N1', 'N3', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P2', 'N2', 'N3', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P3', 'N1', 'N2', 100, 0.05, 0.000045))
        
        incoming = network.get_incoming_pipes('N3')
        
        assert len(incoming) == 2
        assert all(p.end_node == 'N3' for p in incoming)
    
    def test_get_connected_pipes(self):
        """Should find all pipes connected to node"""
        network = PipeNetwork()
        
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        network.add_node(Node(id='N3'))
        
        network.add_pipe(Pipe('P1', 'N1', 'N2', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P2', 'N2', 'N3', 100, 0.05, 0.000045))
        network.add_pipe(Pipe('P3', 'N1', 'N3', 100, 0.05, 0.000045))
        
        connected = network.get_connected_pipes('N1')
        
        # N1 has outgoing P1, P3 and no incoming
        assert len(connected) == 2


class TestLargeNetworks:
    """Test network handling with many nodes and pipes"""
    
    def test_large_network_100_nodes(self):
        """Should handle network with 100 nodes"""
        network = PipeNetwork()
        
        for i in range(100):
            network.add_node(Node(id=f'N{i}'))
        
        assert len(network.nodes) == 100
    
    def test_large_network_100_pipes(self):
        """Should handle network with 100 pipes"""
        network = PipeNetwork()
        
        # Create 101 nodes for 100 pipes in chain
        for i in range(101):
            network.add_node(Node(id=f'N{i}'))
        
        # Create chain of 100 pipes
        for i in range(100):
            pipe = Pipe(
                id=f'P{i}',
                start_node=f'N{i}',
                end_node=f'N{i+1}',
                length=100.0,
                diameter=0.05,
                roughness=0.000045
            )
            network.add_pipe(pipe)
        
        assert len(network.pipes) == 100
    
    def test_large_network_node_lookup(self):
        """Should have fast node lookups in large network"""
        network = PipeNetwork()
        
        for i in range(500):
            network.add_node(Node(id=f'N{i}'))
        
        # Lookup should work for all nodes
        assert 'N250' in network.nodes
        assert network.nodes['N250'].id == 'N250'
    
    def test_large_network_iteration(self):
        """Should iterate efficiently over large network"""
        network = PipeNetwork()
        
        # Create 200 nodes and pipes
        for i in range(200):
            network.add_node(Node(id=f'N{i}'))
        
        for i in range(199):
            pipe = Pipe(
                id=f'P{i}',
                start_node=f'N{i}',
                end_node=f'N{i+1}',
                length=100.0,
                diameter=0.05,
                roughness=0.000045
            )
            network.add_pipe(pipe)
        
        # Count nodes and pipes
        node_count = sum(1 for _ in network.nodes.values())
        pipe_count = sum(1 for _ in network.pipes.values())
        
        assert node_count == 200
        assert pipe_count == 199


class TestNetworkProperties:
    """Test network analysis and properties"""
    
    def test_network_node_count(self):
        """Should accurately count nodes"""
        network = PipeNetwork()
        
        for i in range(10):
            network.add_node(Node(id=f'N{i}'))
        
        assert len(network.nodes) == 10
    
    def test_network_pipe_count(self):
        """Should accurately count pipes"""
        network = PipeNetwork()
        
        for i in range(5):
            network.add_node(Node(id=f'N{i}'))
        
        for i in range(4):
            network.add_pipe(Pipe(
                f'P{i}',
                f'N{i}',
                f'N{i+1}',
                100.0,
                0.05,
                0.000045
            ))
        
        assert len(network.pipes) == 4
    
    def test_network_source_and_sink_nodes(self):
        """Should identify source and sink nodes"""
        network = PipeNetwork()
        
        source = Node(id='SOURCE', is_source=True)
        sink = Node(id='SINK', is_sink=True)
        junction = Node(id='JUNCTION')
        
        network.add_node(source)
        network.add_node(sink)
        network.add_node(junction)
        
        assert network.nodes['SOURCE'].is_source is True
        assert network.nodes['SINK'].is_sink is True
        assert network.nodes['JUNCTION'].is_source is False
    
    def test_network_pump_nodes(self):
        """Should identify pump nodes"""
        network = PipeNetwork()
        
        pump = Node(id='PUMP', is_pump=True)
        regular = Node(id='NODE')
        
        network.add_node(pump)
        network.add_node(regular)
        
        assert network.nodes['PUMP'].is_pump is True
        assert network.nodes['NODE'].is_pump is False


class TestNetworkModification:
    """Test modifying existing networks"""
    
    def test_modify_node_elevation(self):
        """Should modify node elevation"""
        network = PipeNetwork()
        node = Node(id='N1', elevation=10.0)
        network.add_node(node)
        
        # Modify elevation
        network.nodes['N1'].elevation = 20.0
        
        assert network.nodes['N1'].elevation == 20.0
    
    def test_modify_node_pressure(self):
        """Should set node pressure"""
        network = PipeNetwork()
        node = Node(id='N1')
        network.add_node(node)
        
        # Set pressure
        network.nodes['N1'].pressure = 100000.0  # 1 bar
        
        assert network.nodes['N1'].pressure == 100000.0
    
    def test_modify_node_flow_rate(self):
        """Should set node flow rate"""
        network = PipeNetwork()
        node = Node(id='N1')
        network.add_node(node)
        
        # Set flow
        network.nodes['N1'].flow_rate = 0.05  # 50 L/s
        
        assert network.nodes['N1'].flow_rate == 0.05
    
    def test_modify_pipe_flow_rate(self):
        """Should set pipe flow rate"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        network.add_pipe(pipe)
        
        # Set flow
        network.pipes['P1'].flow_rate = 0.05
        
        assert network.pipes['P1'].flow_rate == 0.05
    
    def test_modify_pipe_pressure_drop(self):
        """Should set pipe pressure drop"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        network.add_pipe(pipe)
        
        # Set pressure drop
        network.pipes['P1'].pressure_drop = 5000.0  # 50 mbar
        
        assert network.pipes['P1'].pressure_drop == 5000.0


class TestNetworkValidityChecks:
    """Test network validity and consistency checks"""
    
    def test_pipe_connects_valid_nodes(self):
        """Should verify pipe connects valid nodes"""
        network = PipeNetwork()
        network.add_node(Node(id='N1'))
        network.add_node(Node(id='N2'))
        
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        
        # Both nodes should exist
        assert pipe.start_node in network.nodes
        assert pipe.end_node in network.nodes
    
    def test_pipe_has_positive_length(self):
        """Should validate pipe has positive length"""
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        
        assert pipe.length > 0
    
    def test_pipe_has_positive_diameter(self):
        """Should validate pipe has positive diameter"""
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        
        assert pipe.diameter > 0
    
    def test_pipe_roughness_in_range(self):
        """Should validate pipe roughness"""
        # Steel pipe roughness ~ 0.000045 m
        pipe = Pipe('P1', 'N1', 'N2', 100.0, 0.05, 0.000045)
        
        assert 0 <= pipe.roughness <= 0.1  # Reasonable range


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
