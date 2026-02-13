"""Pressure propagation for tree-structured pipe networks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.map.network import PipeNetwork
    from app.services.pressure import PressureDropService


@dataclass
class PressurePropagation:
    """Propagates pressures from sources through the network.
    
    Starting from nodes with known pressures (sources), calculates pressures
    at downstream nodes by accounting for pressure drops and pump gains.
    
    Attributes:
        dp_service: Pressure drop calculation service
        
    Example:
        >>> propagator = PressurePropagation(dp_service)
        >>> propagator.propagate(network)
    """
    
    dp_service: 'PressureDropService'

    def propagate(self, network: 'PipeNetwork') -> None:
        """Propagate pressures from boundary nodes through the network.
        
        Args:
            network: The pipe network
            
        Raises:
            ValueError: If no boundary nodes with fixed pressure/flow exist
        """
        # Find boundary nodes with fixed pressure or flow rate
        boundary_nodes = [
            n for n in network.nodes.values() 
            if n.pressure is not None or n.flow_rate is not None
        ]
        if not boundary_nodes:
            raise ValueError("At least one node with fixed pressure or flow rate is required")

        # Initialize flow rates from sink specifications
        for node in network.nodes.values():
            if getattr(node, "is_sink", False) and node.flow_rate is not None:
                self._propagate_flow_upstream(network, node)

        # Propagate pressures from sources with fixed pressure
        queue = [n.id for n in boundary_nodes if n.pressure is not None]

        while queue:
            node_id = queue.pop(0)
            node = network.nodes[node_id]

            for pipe in network.get_outgoing_pipes(node_id):
                dp = self.dp_service.calculate_pipe_dp(pipe)
                
                # Add valve losses if present
                if getattr(node, "is_valve", False) and getattr(node, "valve_k", None) is not None:
                    dp += self.dp_service.valve_loss(node.valve_k, pipe)
                
                next_node = network.nodes[pipe.end_node]

                if next_node.pressure is None and node.pressure is not None:
                    # Calculate pump gain if present at current node
                    pump_gain = self.dp_service.calculate_node_pressure_gain(node, node.pressure)
                    
                    # If current node is a pump, update its pressure to discharge pressure
                    if pump_gain > 0:
                        discharge_pressure = node.pressure + pump_gain
                        node.pressure = discharge_pressure
                        upstream_pressure = discharge_pressure
                    else:
                        upstream_pressure = node.pressure
                    
                    # Set downstream pressure
                    next_node.pressure = upstream_pressure - dp
                    queue.append(next_node.id)

    def _propagate_flow_upstream(self, network: 'PipeNetwork', sink_node) -> None:
        """Propagate sink flow rate upstream to determine pipe flows.
        
        Args:
            network: The pipe network
            sink_node: Sink node with fixed flow rate
        """
        queue = [(sink_node.id, sink_node.flow_rate)]
        visited = set()
        
        while queue:
            node_id, accumulated_flow = queue.pop(0)
            
            if node_id in visited:
                continue
            visited.add(node_id)
            
            node = network.nodes[node_id]
            incoming_pipes = network.get_incoming_pipes(node_id)
            
            # Distribute accumulated flow among incoming pipes
            if incoming_pipes:
                flow_per_pipe = accumulated_flow / len(incoming_pipes)
                for pipe in incoming_pipes:
                    if pipe.flow_rate is None:
                        pipe.flow_rate = flow_per_pipe
                    upstream_node = network.nodes[pipe.start_node]
                    if not getattr(upstream_node, "is_source", False):
                        queue.append((pipe.start_node, accumulated_flow))
