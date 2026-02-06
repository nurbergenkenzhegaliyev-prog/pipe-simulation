"""Cycle detection algorithm for pipe networks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.map.network import PipeNetwork


Cycle = List[Tuple[object, int]]


@dataclass
class CycleFinder:
    """Finds cycles (loops) in pipe networks using graph traversal.
    
    Uses breadth-first search to identify independent cycles in the network.
    Each cycle is represented as a list of (pipe, direction) tuples where
    direction is +1 or -1 indicating flow direction around the loop.
    
    Example:
        >>> finder = CycleFinder()
        >>> cycles = finder.find_cycles(network)
        >>> print(f"Found {len(cycles)} independent loops")
    """
    
    def find_cycles(self, network: PipeNetwork) -> List[Cycle]:
        """Find all independent cycles in the network.
        
        Args:
            network: The pipe network to analyze
            
        Returns:
            List of cycles, where each cycle is a list of (pipe, direction) tuples
        """
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
        """Find a path between two nodes excluding a specific edge.
        
        Uses BFS to find an alternative path that doesn't use the excluded pipe.
        
        Args:
            adjacency: Network adjacency list
            start: Starting node ID
            end: Ending node ID
            exclude_pipe_id: Pipe ID to exclude from search
            
        Returns:
            List of pipes forming the path, or None if no path exists
        """
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
