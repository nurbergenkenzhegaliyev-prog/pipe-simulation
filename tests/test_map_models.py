"""
Tests for map/network models - the foundational data structures.

Tests cover:
- Node: Junction points with properties
- Pipe: Connections with equipment  
- PipeNetwork: Graph operations and queries
"""

import pytest
import math
from app.map.node import Node
from app.map.pipe import Pipe
from app.map.network import PipeNetwork


class TestNode:
    """Test Node model."""
    
    def test_node_creation_minimal(self):
        """Should create node with just an ID."""
        node = Node(id="N1")
        
        assert node.id == "N1"
        assert node.pressure is None
        assert node.flow_rate is None
        assert node.elevation == 0.0
        assert node.is_source is False
        assert node.is_sink is False
        assert node.is_pump is False
        assert node.is_valve is False
    
    def test_node_creation_source(self):
        """Should create source node with fixed pressure."""
        node = Node(id="SOURCE", pressure=1000000.0, is_source=True)
        
        assert node.id == "SOURCE"
        assert node.pressure == 1000000.0
        assert node.is_source is True
        assert node.is_sink is False
    
    def test_node_creation_sink(self):
        """Should create sink node with flow rate."""
        node = Node(id="SINK", flow_rate=0.05, is_sink=True)
        
        assert node.id == "SINK"
        assert node.flow_rate == 0.05
        assert node.is_sink is True
        assert node.is_source is False
    
    def test_node_creation_pump(self):
        """Should create pump node with pressure ratio."""
        node = Node(id="PUMP", is_pump=True, pressure_ratio=1.5)
        
        assert node.id == "PUMP"
        assert node.is_pump is True
        assert node.pressure_ratio == 1.5
    
    def test_node_creation_valve(self):
        """Should create valve node with loss coefficient."""
        node = Node(id="VALVE", is_valve=True, valve_k=10.0)
        
        assert node.id == "VALVE"
        assert node.is_valve is True
        assert node.valve_k == 10.0
    
    def test_node_with_elevation(self):
        """Should support elevation for gravity calculations."""
        node = Node(id="N1", elevation=50.0)
        
        assert node.elevation == 50.0


class TestPipe:
    """Test Pipe model."""
    
    def test_pipe_creation_minimal(self):
        """Should create pipe with required properties."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.1,
            roughness=0.0001
        )
        
        assert pipe.id == "P1"
        assert pipe.start_node == "N1"
        assert pipe.end_node == "N2"
        assert pipe.length == 100.0
        assert pipe.diameter == 0.1
        assert pipe.roughness == 0.0001
        assert pipe.flow_rate is None
        assert pipe.minor_loss_k == 0.0
    
    def test_pipe_creation_with_flow(self):
        """Should create pipe with initial flow rate."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.1,
            roughness=0.0001,
            flow_rate=0.05
        )
        
        assert pipe.flow_rate == 0.05
    
    def test_pipe_creation_with_minor_loss(self):
        """Should create pipe with minor loss coefficient."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.1,
            roughness=0.0001,
            minor_loss_k=5.0
        )
        
        assert pipe.minor_loss_k == 5.0
    
    def test_pipe_area_calculation(self):
        """Should calculate cross-sectional area correctly."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.2,  # 200mm
            roughness=0.0001
        )
        
        expected_area = math.pi * (0.2 / 2) ** 2
        assert pipe.area() == pytest.approx(expected_area, rel=1e-6)
    
    def test_pipe_velocity_calculation(self):
        """Should calculate velocity from flow rate."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.2,
            roughness=0.0001,
            flow_rate=0.05  # m³/s
        )
        
        area = math.pi * (0.2 / 2) ** 2
        expected_velocity = 0.05 / area
        assert pipe.velocity() == pytest.approx(expected_velocity, rel=1e-6)
    
    def test_pipe_velocity_zero_flow(self):
        """Should return zero velocity when flow_rate is None or zero."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.2,
            roughness=0.0001
        )
        
        assert pipe.velocity() == 0.0
        
        pipe.flow_rate = 0.0
        assert pipe.velocity() == 0.0
    
    def test_pipe_reynolds_number_calculation(self):
        """Should calculate Reynolds number correctly."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.1,
            roughness=0.0001,
            flow_rate=0.05
        )
        
        density = 1000.0  # kg/m³
        viscosity = 0.001  # Pa·s
        
        velocity = pipe.velocity()
        reynolds = pipe.reynolds_number(density, viscosity)
        
        expected_re = (density * velocity * pipe.diameter) / viscosity
        assert reynolds == pytest.approx(expected_re, rel=1e-6)
    
    def test_pipe_zero_diameter_area(self):
        """Should handle zero diameter gracefully."""
        pipe = Pipe(
            id="P1",
            start_node="N1",
            end_node="N2",
            length=100.0,
            diameter=0.0,
            roughness=0.0001
        )
        
        assert pipe.area() == 0.0


class TestPipeNetwork:
    """Test PipeNetwork graph operations."""
    
    def test_network_creation(self):
        """Should create empty network."""
        network = PipeNetwork()
        
        assert len(network.nodes) == 0
        assert len(network.pipes) == 0
    
    def test_add_single_node(self):
        """Should add node to network."""
        network = PipeNetwork()
        node = Node(id="N1", pressure=500000.0)
        
        network.add_node(node)
        
        assert len(network.nodes) == 1
        assert "N1" in network.nodes
        assert network.nodes["N1"].pressure == 500000.0
    
    def test_add_multiple_nodes(self):
        """Should add multiple nodes."""
        network = PipeNetwork()
        
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        network.add_node(Node(id="N3"))
        
        assert len(network.nodes) == 3
        assert "N1" in network.nodes
        assert "N2" in network.nodes
        assert "N3" in network.nodes
    
    def test_add_pipe(self):
        """Should add pipe to network."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        
        pipe = Pipe(id="P1", start_node="N1", end_node="N2",
                    length=100, diameter=0.1, roughness=0.0001)
        network.add_pipe(pipe)
        
        assert len(network.pipes) == 1
        assert "P1" in network.pipes
        assert network.pipes["P1"].start_node == "N1"
        assert network.pipes["P1"].end_node == "N2"
    
    def test_get_outgoing_pipes(self):
        """Should retrieve all pipes leaving a node."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        network.add_node(Node(id="N3"))
        
        network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="N1", end_node="N3",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="N2", end_node="N3",
                              length=100, diameter=0.1, roughness=0.0001))
        
        outgoing_from_n1 = network.get_outgoing_pipes("N1")
        
        assert len(outgoing_from_n1) == 2
        pipe_ids = [p.id for p in outgoing_from_n1]
        assert "P1" in pipe_ids
        assert "P2" in pipe_ids
        assert "P3" not in pipe_ids
    
    def test_get_incoming_pipes(self):
        """Should retrieve all pipes entering a node."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        network.add_node(Node(id="N3"))
        
        network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N3",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="N2", end_node="N3",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="N1", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        
        incoming_to_n3 = network.get_incoming_pipes("N3")
        
        assert len(incoming_to_n3) == 2
        pipe_ids = [p.id for p in incoming_to_n3]
        assert "P1" in pipe_ids
        assert "P2" in pipe_ids
        assert "P3" not in pipe_ids
    
    def test_get_connected_pipes(self):
        """Should retrieve all pipes connected to a node."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        network.add_node(Node(id="N3"))
        network.add_node(Node(id="N4"))
        
        network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="N3", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="N2", end_node="N4",
                              length=100, diameter=0.1, roughness=0.0001))
        
        connected_to_n2 = network.get_connected_pipes("N2")
        
        assert len(connected_to_n2) == 3
        pipe_ids = [p.id for p in connected_to_n2]
        assert "P1" in pipe_ids
        assert "P2" in pipe_ids
        assert "P3" in pipe_ids
    
    def test_remove_node(self):
        """Should remove node from network."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        
        assert len(network.nodes) == 2
        
        network.remove_node("N1")
        
        assert len(network.nodes) == 1
        assert "N1" not in network.nodes
        assert "N2" in network.nodes
    
    def test_remove_pipe(self):
        """Should remove pipe from network."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="N1", end_node="N2",
                              length=200, diameter=0.15, roughness=0.0001))
        
        assert len(network.pipes) == 2
        
        network.remove_pipe("P1")
        
        assert len(network.pipes) == 1
        assert "P1" not in network.pipes
        assert "P2" in network.pipes
    
    def test_get_source_nodes(self):
        """Should retrieve all source nodes."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC1", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="SRC2", pressure=800000.0, is_source=True))
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.1))
        
        sources = network.get_source_nodes()
        
        assert len(sources) == 2
        source_ids = [n.id for n in sources]
        assert "SRC1" in source_ids
        assert "SRC2" in source_ids
    
    def test_get_sink_nodes(self):
        """Should retrieve all sink nodes."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="SINK1", is_sink=True, flow_rate=0.05))
        network.add_node(Node(id="SINK2", is_sink=True, flow_rate=0.03))
        network.add_node(Node(id="N1"))
        
        sinks = network.get_sink_nodes()
        
        assert len(sinks) == 2
        sink_ids = [n.id for n in sinks]
        assert "SINK1" in sink_ids
        assert "SINK2" in sink_ids
    
    def test_network_topology_simple_chain(self):
        """Should handle simple chain topology: A -> B -> C."""
        network = PipeNetwork()
        network.add_node(Node(id="A", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="B"))
        network.add_node(Node(id="C", is_sink=True, flow_rate=0.05))
        
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="B", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # A should have 1 outgoing, 0 incoming
        assert len(network.get_outgoing_pipes("A")) == 1
        assert len(network.get_incoming_pipes("A")) == 0
        
        # B should have 1 outgoing, 1 incoming
        assert len(network.get_outgoing_pipes("B")) == 1
        assert len(network.get_incoming_pipes("B")) == 1
        
        # C should have 0 outgoing, 1 incoming
        assert len(network.get_outgoing_pipes("C")) == 0
        assert len(network.get_incoming_pipes("C")) == 1
    
    def test_network_topology_branched(self):
        """Should handle branched topology: A splits to B and C."""
        network = PipeNetwork()
        network.add_node(Node(id="A", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="B", is_sink=True, flow_rate=0.03))
        network.add_node(Node(id="C", is_sink=True, flow_rate=0.02))
        
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="A", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # A should have 2 outgoing pipes
        assert len(network.get_outgoing_pipes("A")) == 2
        
        # B and C should each have 1 incoming pipe
        assert len(network.get_incoming_pipes("B")) == 1
        assert len(network.get_incoming_pipes("C")) == 1
    
    def test_network_topology_loop(self):
        """Should handle looped topology: A -> B -> C -> A."""
        network = PipeNetwork()
        network.add_node(Node(id="A", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="B"))
        network.add_node(Node(id="C"))
        
        network.add_pipe(Pipe(id="P1", start_node="A", end_node="B",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P2", start_node="B", end_node="C",
                              length=100, diameter=0.1, roughness=0.0001))
        network.add_pipe(Pipe(id="P3", start_node="C", end_node="A",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # Each node should have 1 incoming and 1 outgoing
        for node_id in ["A", "B", "C"]:
            assert len(network.get_outgoing_pipes(node_id)) == 1
            assert len(network.get_incoming_pipes(node_id)) == 1
    
    def test_empty_queries_on_missing_node(self):
        """Should return empty lists for queries on non-existent nodes."""
        network = PipeNetwork()
        
        assert len(network.get_outgoing_pipes("MISSING")) == 0
        assert len(network.get_incoming_pipes("MISSING")) == 0
        assert len(network.get_connected_pipes("MISSING")) == 0
    
    def test_duplicate_node_id_overwrites(self):
        """Adding node with duplicate ID should raise ValueError."""
        network = PipeNetwork()
        network.add_node(Node(id="N1", pressure=500000.0))
        
        with pytest.raises(ValueError, match="Node 'N1' already exists"):
            network.add_node(Node(id="N1", pressure=800000.0))
        
        # Original node should remain
        assert len(network.nodes) == 1
        assert network.nodes["N1"].pressure == 500000.0
    
    def test_duplicate_pipe_id_overwrites(self):
        """Adding pipe with duplicate ID should raise ValueError."""
        network = PipeNetwork()
        network.add_node(Node(id="N1"))
        network.add_node(Node(id="N2"))
        
        network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N2",
                              length=100, diameter=0.1, roughness=0.0001))
        
        with pytest.raises(ValueError, match="Pipe 'P1' already exists"):
            network.add_pipe(Pipe(id="P1", start_node="N1", end_node="N2",
                                  length=200, diameter=0.2, roughness=0.0002))
        
        # Original pipe should remain
        assert len(network.pipes) == 1
        assert network.pipes["P1"].length == 100
        assert network.pipes["P1"].diameter == 0.1


class TestNetworkValidation:
    """Test network validation scenarios."""
    
    def test_valid_simple_network(self):
        """A simple valid network should have source and sink."""
        network = PipeNetwork()
        network.add_node(Node(id="SRC", pressure=1000000.0, is_source=True))
        network.add_node(Node(id="SINK", is_sink=True, flow_rate=0.05))
        network.add_pipe(Pipe(id="P1", start_node="SRC", end_node="SINK",
                              length=100, diameter=0.1, roughness=0.0001))
        
        sources = network.get_source_nodes()
        sinks = network.get_sink_nodes()
        
        assert len(sources) >= 1
        assert len(sinks) >= 1
        assert len(network.pipes) >= 1
    
    def test_disconnected_components(self):
        """Should detect disconnected network components."""
        network = PipeNetwork()
        # Component 1
        network.add_node(Node(id="A1"))
        network.add_node(Node(id="A2"))
        network.add_pipe(Pipe(id="PA", start_node="A1", end_node="A2",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # Component 2 (disconnected)
        network.add_node(Node(id="B1"))
        network.add_node(Node(id="B2"))
        network.add_pipe(Pipe(id="PB", start_node="B1", end_node="B2",
                              length=100, diameter=0.1, roughness=0.0001))
        
        # These components are not connected
        a2_connected = network.get_connected_pipes("A2")
        b1_connected = network.get_connected_pipes("B1")
        
        # A2 is only connected to PA
        assert len(a2_connected) == 1
        assert a2_connected[0].id == "PA"
        
        # B1 is only connected to PB
        assert len(b1_connected) == 1
        assert b1_connected[0].id == "PB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
