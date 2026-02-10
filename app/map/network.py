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
    
    def get_connected_pipes(self, node_id: str):
        """Get all pipes connected to a node (both incoming and outgoing).
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of pipes connected to the node
        """
        return [
            p for p in self.pipes.values()
            if p.start_node == node_id or p.end_node == node_id
        ]
    
    def remove_node(self, node_id: str):
        """Remove a node from the network.
        
        Args:
            node_id: ID of the node to remove
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def remove_pipe(self, pipe_id: str):
        """Remove a pipe from the network.
        
        Args:
            pipe_id: ID of the pipe to remove
        """
        if pipe_id in self.pipes:
            del self.pipes[pipe_id]
    
    def get_source_nodes(self):
        """Get all source nodes in the network.
        
        Returns:
            List of nodes marked as sources (is_source=True)
        """
        return [node for node in self.nodes.values() if node.is_source]
    
    def get_sink_nodes(self):
        """Get all sink nodes in the network.
        
        Returns:
            List of nodes marked as sinks (is_sink=True)
        """
        return [node for node in self.nodes.values() if node.is_sink]
