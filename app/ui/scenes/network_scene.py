"""Network scene for visual pipe network modeling.

This module provides the main QGraphicsScene for the network editor,
handling user interactions, tool management, and network manipulation.

The scene supports:
- Multiple drawing tools (nodes, pipes, pumps, valves)
- Undo/redo command history
- Real-time network validation
- Result visualization after simulation
"""

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import Qt, pyqtSignal, QPointF

from app.ui.tooling.tool_types import Tool
from app.ui.items.network_items import NodeItem, PipeItem, PumpItem, ValveItem
from app.ui.scenes.scene_components import NetworkResultApplier, NodeOperations, PipeOperations, SceneCounters
from app.ui.commands.command_manager import CommandManager
from app.ui.commands.scene_commands import (
    AddNodeCommand, DeleteNodeCommand, AddPipeCommand, DeletePipeCommand,
    AddPumpCommand, AddValveCommand
)
from app.ui.validation.realtime_validator import RealtimeNetworkValidator
from app.ui.validation.validation_visualizer import ValidationVisualizer


class NetworkScene(QGraphicsScene):
    """Graphics scene for building and visualizing pipe networks.
    
    Provides a visual canvas for creating and editing pipe networks with
    interactive tools. Supports undo/redo, validation, and result display.
    
    Signals:
        nodes_changed: Emitted when nodes or pipes are added/removed/modified
        validation_changed: Emitted with list of validation issues
        
    Attributes:
        current_tool: Active drawing tool (SELECT, NODE, PIPE, etc.)
        nodes: List of all NodeItem objects in the scene
        pipes: List of all PipeItem objects in the scene
        command_manager: Manages undo/redo command history
        validator: Real-time network validation
        current_fluid: Current fluid properties for simulation
        
    Example:
        >>> scene = NetworkScene()
        >>> scene.set_tool(Tool.NODE)
        >>> # Click on canvas to add nodes
        >>> scene.set_tool(Tool.PIPE)
        >>> # Click nodes to connect with pipes
    """
    
    nodes_changed = pyqtSignal()
    validation_changed = pyqtSignal(object)  # Emits validation issues list

    def __init__(self):
        """Initialize the network scene with empty network."""
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self.current_tool = Tool.SELECT

        self.nodes = []
        self.pipes = []

        self._counters = SceneCounters()
        self._node_ops = NodeOperations(self, self.nodes, self._counters, self.nodes_changed.emit)
        self._pipe_ops = PipeOperations(self, self.pipes, self._counters, self.nodes_changed.emit)
        self._result_applier = NetworkResultApplier(self.nodes, self.pipes)
        
        # Command manager for undo/redo
        self.command_manager = CommandManager()
        
        # Real-time validation
        self.validator = RealtimeNetworkValidator()
        self.nodes_changed.connect(self._on_network_changed)

        # for PIPE tool
        self._pipe_start_node = None
        
        # Fluid settings (will be set by main window)
        self.current_fluid = None

    # ---------- API FROM UI ----------
    def set_tool(self, tool: Tool):
        """Set the active drawing tool.
        
        Args:
            tool: Tool to activate (SELECT, NODE, PIPE, PUMP, VALVE)
            
        Note:
            Resets pipe drawing state when switching tools.
        """
        self.current_tool = tool
        self._pipe_start_node = None
        self._pipe_ops.reset_pipe_builder()
        self.clearSelection()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected()
            return
        super().keyPressEvent(event)
    
    def _on_network_changed(self):
        """Run validation whenever network changes"""
        try:
            issues = self.validator.validate(self)
            problematic_items = self.validator.get_problematic_items()
            ValidationVisualizer.apply_highlights(self, problematic_items)
            self.validation_changed.emit(issues)
        except Exception:
            # Silently handle validation errors during initialization
            pass

    # ---------- MOUSE ----------
    def mousePressEvent(self, event):
        pos = event.scenePos()
        item = self.itemAt(pos, self.views()[0].transform())

        if event.button() == Qt.MouseButton.LeftButton:

            # --- NODE TOOL ---
            if self.current_tool == Tool.NODE:
                if not isinstance(item, NodeItem):
                    cmd = AddNodeCommand(self, pos)
                    self.command_manager.execute(cmd)

            # --- SOURCE TOOL ---
            elif self.current_tool == Tool.SOURCE:
                if isinstance(item, NodeItem):
                    self._make_source(item)
                else:
                    cmd = AddNodeCommand(self, pos, is_source=True)
                    self.command_manager.execute(cmd)

            # --- SINK TOOL ---
            elif self.current_tool == Tool.SINK:
                if isinstance(item, NodeItem):
                    self._make_sink(item)
                else:
                    cmd = AddNodeCommand(self, pos, is_sink=True)
                    self.command_manager.execute(cmd)

            # --- PIPE TOOL ---
            elif self.current_tool == Tool.PIPE:
                if isinstance(item, NodeItem):
                    self._handle_pipe_click(item)

            # --- PUMP TOOL ---
            elif self.current_tool == Tool.PUMP:
                if not isinstance(item, NodeItem):
                    cmd = AddPumpCommand(self, pos)
                    self.command_manager.execute(cmd)

            # --- VALVE TOOL ---
            elif self.current_tool == Tool.VALVE:
                if not isinstance(item, NodeItem):
                    cmd = AddValveCommand(self, pos)
                    self.command_manager.execute(cmd)

            # --- SELECT TOOL ---
            else:
                super().mousePressEvent(event)
                return

        super().mousePressEvent(event)

    # ---------- NODE HELPERS ----------
    def _create_node(self, pos, is_source: bool = False, is_sink: bool = False) -> NodeItem:
        return self._node_ops.create_node(pos, is_source=is_source, is_sink=is_sink)

    def _create_pump(self, pos) -> PumpItem:
        return self._node_ops.create_pump(pos)

    def _create_valve(self, pos) -> ValveItem:
        return self._node_ops.create_valve(pos)

    def create_node_with_id(
        self,
        pos: QPointF,
        node_id: str,
        is_source: bool = False,
        is_sink: bool = False,
        pressure: float | None = None,
        flow_rate: float | None = None,
        is_pump: bool = False,
        is_valve: bool = False,
        pressure_ratio: float | None = None,
        valve_k: float | None = None,
    ) -> NodeItem:
        return self._node_ops.create_node_with_id(
            pos,
            node_id,
            is_source=is_source,
            is_sink=is_sink,
            pressure=pressure,
            flow_rate=flow_rate,
            is_pump=is_pump,
            is_valve=is_valve,
            pressure_ratio=pressure_ratio,
            valve_k=valve_k,
        )

    def _make_source(self, node: NodeItem):
        self._node_ops.make_source(node)

    def _make_sink(self, node: NodeItem):
        self._node_ops.make_sink(node)

    # ---------- DELETE ----------
    def _delete_selected(self):
        selected = list(self.selectedItems())

        # Remove pipes first
        for item in selected:
            if isinstance(item, PipeItem):
                cmd = DeletePipeCommand(self, item)
                self.command_manager.execute(cmd)

        # Remove nodes (also removes any attached pipes)
        for item in selected:
            if isinstance(item, NodeItem):
                cmd = DeleteNodeCommand(self, item)
                self.command_manager.execute(cmd)

    def _remove_pipe(self, pipe: PipeItem):
        self._pipe_ops.remove_pipe(pipe)

    def _remove_node(self, node: NodeItem):
        self._node_ops.remove_node(node, self._pipe_ops.remove_pipe)

    # ---------- PIPE LOGIC ----------
    def _handle_pipe_click(self, node: NodeItem):
        # Handle pipe creation with command pattern
        if self._pipe_start_node is None:
            self._pipe_start_node = node
            self._pipe_ops.pipe_start_node = node
        else:
            if node != self._pipe_start_node:
                cmd = AddPipeCommand(self, self._pipe_start_node, node)
                self.command_manager.execute(cmd)
            self._pipe_start_node = None
            self._pipe_ops.reset_pipe_builder()

    def _add_pump(self, pipe: PipeItem):
        self._pipe_ops.add_pump(pipe)

    def _add_valve(self, pipe: PipeItem):
        self._pipe_ops.add_valve(pipe)

    def create_pipe_with_id(
        self,
        node1: NodeItem,
        node2: NodeItem,
        pipe_id: str,
        length: float | None = None,
        diameter: float | None = None,
        roughness: float | None = None,
        flow_rate: float | None = None,
    ) -> PipeItem:
        return self._pipe_ops.create_pipe_with_id(
            node1,
            node2,
            pipe_id,
            length=length,
            diameter=diameter,
            roughness=roughness,
            flow_rate=flow_rate,
        )

    def clear_network(self):
        for pipe in list(self.pipes):
            self._remove_pipe(pipe)
        for node in list(self.nodes):
            self._remove_node(node)
        self._counters.reset()
        self._pipe_start_node = None
        self._pipe_ops.reset_pipe_builder()
        self.nodes_changed.emit()

    def apply_results(self, network):
        self._result_applier.apply_results(network)
        
        # Show flow direction arrows on pipes
        for pipe_item in self.pipes:
            # Get the flow rate from the network
            network_pipe = network.pipes.get(pipe_item.pipe_id)
            if network_pipe and network_pipe.flow_rate is not None:
                pipe_item.show_flow_direction(network_pipe.flow_rate)
    
    def clear_flow_arrows(self):
        """Remove all flow direction arrows from pipes"""
        for pipe_item in self.pipes:
            pipe_item.hide_flow_direction()

