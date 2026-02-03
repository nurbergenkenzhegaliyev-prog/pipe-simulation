from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.map.network import PipeNetwork
from app.services.pressure_drop_service import PressureDropService


Cycle = List[Tuple[object, int]]


@dataclass
class CycleFinder:
    def find_cycles(self, network: PipeNetwork) -> List[Cycle]:
        adjacency: Dict[str, List[Tuple[str, object]]] = {}
        for pipe in network.pipes.values():
            adjacency.setdefault(pipe.start_node, []).append((pipe.end_node, pipe))
            adjacency.setdefault(pipe.end_node, []).append((pipe.start_node, pipe))

        cycles: List[Cycle] = []
        seen = set()
        for pipe in network.pipes.values():
            start = pipe.start_node
            end = pipe.end_node
            path = self._find_path_excluding_edge(adjacency, start, end, pipe.id)
            if not path:
                continue
            cycle_pipes = path + [pipe]
            key = frozenset(p.id for p in cycle_pipes)
            if key in seen:
                continue
            seen.add(key)

            cycle: Cycle = []
            current = start
            for p in path:
                if p.start_node == current:
                    cycle.append((p, 1))
                    current = p.end_node
                else:
                    cycle.append((p, -1))
                    current = p.start_node
            if pipe.start_node == current:
                cycle.append((pipe, 1))
            else:
                cycle.append((pipe, -1))
            cycles.append(cycle)
        return cycles

    @staticmethod
    def _find_path_excluding_edge(
        adjacency: Dict[str, List[Tuple[str, object]]],
        start: str,
        end: str,
        exclude_pipe_id: str,
    ) -> Optional[List[object]]:
        queue: List[Tuple[str, List[object]]] = [(start, [])]
        visited = {start}
        while queue:
            node, path = queue.pop(0)
            if node == end:
                return path
            for nxt, pipe in adjacency.get(node, []):
                if pipe.id == exclude_pipe_id:
                    continue
                if nxt in visited:
                    continue
                visited.add(nxt)
                queue.append((nxt, path + [pipe]))
        return None


@dataclass
class HardyCrossSolver:
    dp_service: PressureDropService
    max_iter: int = 50
    tol: float = 1e-2

    def apply(self, network: PipeNetwork, cycles: Sequence[Cycle]) -> None:
        for _ in range(self.max_iter):
            max_imbalance = 0.0
            for cycle in cycles:
                sum_dp = 0.0
                sum_d = 0.0
                for pipe, direction in cycle:
                    if pipe.flow_rate is None:
                        raise ValueError(f"Pipe {pipe.id} has no flow rate for Hardy-Cross")
                    q = pipe.flow_rate
                    if q == 0:
                        q = 1e-6
                    dp = self.dp_service.calculate_pipe_dp(pipe)
                    signed_dp = direction * dp
                    sum_dp += signed_dp
                    sum_d += 2.0 * abs(dp) / abs(q)

                if sum_d == 0:
                    continue

                delta_q = -sum_dp / sum_d
                max_imbalance = max(max_imbalance, abs(sum_dp))

                for pipe, direction in cycle:
                    pipe.flow_rate += direction * delta_q

            if max_imbalance < self.tol:
                break


@dataclass
class PressurePropagation:
    dp_service: PressureDropService

    def propagate(self, network: PipeNetwork) -> None:
        # Find boundary nodes with fixed pressure or flow rate
        boundary_nodes = [
            n for n in network.nodes.values() 
            if n.pressure is not None or n.flow_rate is not None
        ]
        if not boundary_nodes:
            raise ValueError("At least one node with fixed pressure or flow rate is required")

        # Initialize flow rates from sink specifications
        # Sinks must have flow_rate set, which will be propagated upstream
        for node in network.nodes.values():
            if getattr(node, "is_sink", False) and node.flow_rate is not None:
                # Sink: flow_rate is fixed, propagate upstream to find inlet flow
                self._propagate_flow_upstream(network, node)

        # Propagate pressures from sources with fixed pressure
        queue = [n.id for n in boundary_nodes if n.pressure is not None]

        while queue:
            node_id = queue.pop(0)
            node = network.nodes[node_id]

            for pipe in network.get_outgoing_pipes(node_id):
                dp = self.dp_service.calculate_pipe_dp(pipe)
                if getattr(node, "is_valve", False) and getattr(node, "valve_k", None) is not None:
                    dp += self.dp_service.valve_loss(node.valve_k, pipe)
                next_node = network.nodes[pipe.end_node]

                if next_node.pressure is None and node.pressure is not None:
                    pump_gain = self.dp_service.calculate_node_pressure_gain(node, node.pressure)
                    upstream_pressure = node.pressure + pump_gain
                    next_node.pressure = upstream_pressure - dp
                    queue.append(next_node.id)

    def _propagate_flow_upstream(self, network: PipeNetwork, sink_node) -> None:
        """Propagate sink flow rate upstream to determine pipe flows"""
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
