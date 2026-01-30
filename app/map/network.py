from .node import Node
from .pipe import Pipe

class PipeNetwork:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.pipes: dict[str, Pipe] = {}

    # ---------- Nodes ----------
    def add_node(self, node: Node):
        if node.id in self.nodes:
            raise ValueError(f"Node '{node.id}' already exists")
        self.nodes[node.id] = node

    # ---------- Pipes ----------
    def add_pipe(self, pipe: Pipe):
        if pipe.id in self.pipes:
            raise ValueError(f"Pipe '{pipe.id}' already exists")

        if pipe.start_node not in self.nodes:
            raise ValueError(f"Start node '{pipe.start_node}' not found")

        if pipe.end_node not in self.nodes:
            raise ValueError(f"End node '{pipe.end_node}' not found")

        self.pipes[pipe.id] = pipe

    # ---------- Graph helpers ----------
    def get_outgoing_pipes(self, node_id: str):
        return [
            p for p in self.pipes.values()
            if p.start_node == node_id
        ]

    def get_incoming_pipes(self, node_id: str):
        return [
            p for p in self.pipes.values()
            if p.end_node == node_id
        ]
