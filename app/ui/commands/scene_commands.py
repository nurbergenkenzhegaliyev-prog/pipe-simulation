"""Commands for scene editing operations"""

from PyQt6.QtCore import QPointF
from app.ui.commands.command_manager import Command
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from app.ui.scenes.network_scene import NetworkScene
    from app.ui.items.network_items import NodeItem, PipeItem


class AddNodeCommand(Command):
    """Command to add a node to the scene"""
    
    def __init__(self, scene: 'NetworkScene', pos: QPointF, is_source: bool = False, is_sink: bool = False):
        self._scene = scene
        self._pos = pos
        self._is_source = is_source
        self._is_sink = is_sink
        self._node: 'NodeItem' = None
    
    def execute(self) -> None:
        """Add the node"""
        from app.ui.scenes.scene_components import NodeOperations
        self._node = self._scene._node_ops.create_node(self._pos, self._is_source, self._is_sink)
    
    def undo(self) -> None:
        """Remove the node"""
        if self._node:
            self._scene._node_ops.remove_node(self._node, self._scene._pipe_ops.remove_pipe)
    
    def description(self) -> str:
        node_type = "Source" if self._is_source else "Sink" if self._is_sink else "Node"
        return f"Add {node_type}"


class DeleteNodeCommand(Command):
    """Command to delete a node from the scene"""
    
    def __init__(self, scene: 'NetworkScene', node: 'NodeItem'):
        self._scene = scene
        self._node = node
        self._node_data = self._save_node_data(node)
        self._connected_pipes = []
    
    def _save_node_data(self, node: 'NodeItem') -> Dict[str, Any]:
        """Save node data for restoration"""
        return {
            'id': node.node_id,
            'pos': node.scenePos(),
            'is_source': node.is_source,
            'is_sink': node.is_sink,
            'is_pump': node.is_pump,
            'is_valve': node.is_valve,
            'pressure': getattr(node, 'pressure', None),
            'flow_rate': getattr(node, 'flow_rate', None),
            'pressure_ratio': getattr(node, 'pressure_ratio', None),
            'valve_k': getattr(node, 'valve_k', None),
        }
    
    def execute(self) -> None:
        """Delete the node and connected pipes"""
        # Save connected pipes for potential restoration
        self._connected_pipes = list(self._node.pipes) if hasattr(self._node, 'pipes') else []
        self._scene._node_ops.remove_node(self._node, self._scene._pipe_ops.remove_pipe)
    
    def undo(self) -> None:
        """Restore the node"""
        data = self._node_data
        self._node = self._scene.create_node_with_id(
            data['pos'], data['id'],
            is_source=data['is_source'],
            is_sink=data['is_sink'],
            pressure=data['pressure'],
            flow_rate=data['flow_rate'],
            is_pump=data['is_pump'],
            is_valve=data['is_valve'],
            pressure_ratio=data['pressure_ratio'],
            valve_k=data['valve_k']
        )
    
    def description(self) -> str:
        return f"Delete Node {self._node_data['id']}"


class AddPipeCommand(Command):
    """Command to add a pipe between two nodes"""
    
    def __init__(self, scene: 'NetworkScene', node1: 'NodeItem', node2: 'NodeItem'):
        self._scene = scene
        self._node1 = node1
        self._node2 = node2
        self._pipe: 'PipeItem' = None
    
    def execute(self) -> None:
        """Add the pipe"""
        self._pipe = self._scene._pipe_ops.create_pipe(self._node1, self._node2)
    
    def undo(self) -> None:
        """Remove the pipe"""
        if self._pipe:
            self._scene._pipe_ops.remove_pipe(self._pipe)
    
    def description(self) -> str:
        return f"Add Pipe ({self._node1.node_id} → {self._node2.node_id})"


class DeletePipeCommand(Command):
    """Command to delete a pipe from the scene"""
    
    def __init__(self, scene: 'NetworkScene', pipe: 'PipeItem'):
        self._scene = scene
        self._pipe = pipe
        self._pipe_data = self._save_pipe_data(pipe)
    
    def _save_pipe_data(self, pipe: 'PipeItem') -> Dict[str, Any]:
        """Save pipe data for restoration"""
        return {
            'id': pipe.pipe_id,
            'node1_id': pipe.node1.node_id,
            'node2_id': pipe.node2.node_id,
            'length': pipe.length,
            'diameter': pipe.diameter,
            'roughness': pipe.roughness,
            'flow_rate': pipe.flow_rate,
            'liquid_flow_rate': getattr(pipe, 'liquid_flow_rate', None),
            'gas_flow_rate': getattr(pipe, 'gas_flow_rate', None),
        }
    
    def execute(self) -> None:
        """Delete the pipe"""
        self._scene._pipe_ops.remove_pipe(self._pipe)
    
    def undo(self) -> None:
        """Restore the pipe"""
        data = self._pipe_data
        # Find nodes by ID
        node1 = next((n for n in self._scene.nodes if n.node_id == data['node1_id']), None)
        node2 = next((n for n in self._scene.nodes if n.node_id == data['node2_id']), None)
        
        if node1 and node2:
            self._pipe = self._scene.create_pipe_with_id(
                node1, node2, data['id'],
                length=data['length'],
                diameter=data['diameter'],
                roughness=data['roughness'],
                flow_rate=data['flow_rate']
            )
            if data['liquid_flow_rate'] is not None:
                self._pipe.liquid_flow_rate = data['liquid_flow_rate']
            if data['gas_flow_rate'] is not None:
                self._pipe.gas_flow_rate = data['gas_flow_rate']
    
    def description(self) -> str:
        return f"Delete Pipe {self._pipe_data['id']}"


class AddPumpCommand(Command):
    """Command to add a pump to the scene"""
    
    def __init__(self, scene: 'NetworkScene', pos: QPointF):
        self._scene = scene
        self._pos = pos
        self._pump: 'NodeItem' = None
    
    def execute(self) -> None:
        """Add the pump"""
        self._pump = self._scene._node_ops.create_pump(self._pos)
    
    def undo(self) -> None:
        """Remove the pump"""
        if self._pump:
            self._scene._node_ops.remove_node(self._pump, self._scene._pipe_ops.remove_pipe)
    
    def description(self) -> str:
        return "Add Pump"


class AddValveCommand(Command):
    """Command to add a valve to the scene"""
    
    def __init__(self, scene: 'NetworkScene', pos: QPointF):
        self._scene = scene
        self._pos = pos
        self._valve: 'NodeItem' = None
    
    def execute(self) -> None:
        """Add the valve"""
        self._valve = self._scene._node_ops.create_valve(self._pos)
    
    def undo(self) -> None:
        """Remove the valve"""
        if self._valve:
            self._scene._node_ops.remove_node(self._valve, self._scene._pipe_ops.remove_pipe)
    
    def description(self) -> str:
        return "Add Valve"
