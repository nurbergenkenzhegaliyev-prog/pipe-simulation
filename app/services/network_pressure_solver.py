from app.map.network import PipeNetwork
from app.services.pressure_drop_service import PressureDropService


class NetworkPressureSolver:
    def __init__(self, dp_service: PressureDropService):
        self.dp_service = dp_service

    def solve(self, network: PipeNetwork):
        # Apply Hardy-Cross for looped networks to improve convergence
        cycles = self._find_cycles(network)
        if cycles:
            self._apply_hardy_cross(network, cycles)

        # Boundary nodes: any node with fixed pressure
        boundary_nodes = [n for n in network.nodes.values() if n.pressure is not None]
        if not boundary_nodes:
            raise ValueError("At least one node with fixed pressure is required")

        # BFS / forward propagation from all boundary nodes
        queue = [n.id for n in boundary_nodes]

        while queue:
            node_id = queue.pop(0)
            node = network.nodes[node_id]

            for pipe in network.get_outgoing_pipes(node_id):
                dp = self.dp_service.calculate_pipe_dp(pipe)
                if getattr(node, "is_valve", False) and getattr(node, "valve_k", None) is not None:
                    dp += self.dp_service.valve_loss(node.valve_k, pipe)
                next_node = network.nodes[pipe.end_node]

                if next_node.pressure is None and node.pressure is not None:
                    upstream_pressure = node.pressure
                    if getattr(node, "is_pump", False) and getattr(node, "pressure_ratio", None) is not None:
                        upstream_pressure = node.pressure * node.pressure_ratio
                    next_node.pressure = upstream_pressure - dp
                    queue.append(next_node.id)

    def _find_cycles(self, network: PipeNetwork):
        # Find simple cycles by checking alternative paths for each edge.
        # Returns list of cycles where each cycle is list of (pipe, direction) tuples.
        # direction: +1 if traversed along pipe.start->pipe.end, -1 otherwise.
        adjacency = {}
        for pipe in network.pipes.values():
            adjacency.setdefault(pipe.start_node, []).append((pipe.end_node, pipe))
            adjacency.setdefault(pipe.end_node, []).append((pipe.start_node, pipe))

        cycles = []
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

            # Build directed cycle list
            cycle = []
            current = start
            for p in path:
                if p.start_node == current:
                    cycle.append((p, 1))
                    current = p.end_node
                else:
                    cycle.append((p, -1))
                    current = p.start_node
            # Add the closing edge
            if pipe.start_node == current:
                cycle.append((pipe, 1))
            else:
                cycle.append((pipe, -1))
            cycles.append(cycle)
        return cycles

    def _find_path_excluding_edge(self, adjacency, start, end, exclude_pipe_id):
        # BFS to find any path from start to end without using excluded pipe.
        queue = [(start, [])]
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

    def _apply_hardy_cross(self, network: PipeNetwork, cycles):
        # Hardy-Cross assumes dp ~ Q|Q|, so d(dp)/dQ = 2*dp/Q
        max_iter = 50
        tol = 1e-2

        for _ in range(max_iter):
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

            if max_imbalance < tol:
                break
