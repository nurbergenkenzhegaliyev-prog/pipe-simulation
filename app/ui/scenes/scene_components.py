from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsScene

from app.models.equipment import PumpCurve, Valve
from app.ui.items.network_items import NodeItem, PipeItem, PumpItem, ValveItem


@dataclass
class SceneCounters:
    node: int = 0
    pipe: int = 0
    pump: int = 0
    valve: int = 0

    def next_node_id(self) -> str:
        self.node += 1
        return f"N{self.node}"

    def next_pipe_id(self) -> str:
        self.pipe += 1
        return f"P{self.pipe}"

    def next_pump_id(self) -> str:
        self.pump += 1
        return f"PU{self.pump}"

    def next_valve_id(self) -> str:
        self.valve += 1
        return f"V{self.valve}"

    def reset(self) -> None:
        self.node = 0
        self.pipe = 0
        self.pump = 0
        self.valve = 0

    def update_from_id(self, item_id: str, prefix: str) -> None:
        if not item_id.startswith(prefix):
            return
        suffix = item_id[len(prefix):]
        digits = "".join(ch for ch in suffix if ch.isdigit())
        if not digits:
            return
        value = int(digits)
        if prefix == "N":
            self.node = max(self.node, value)
        elif prefix == "P":
            self.pipe = max(self.pipe, value)
        elif prefix == "PU":
            self.pump = max(self.pump, value)
        elif prefix == "V":
            self.valve = max(self.valve, value)


class NodeOperations:
    def __init__(
        self,
        scene: QGraphicsScene,
        nodes: List[NodeItem],
        counters: SceneCounters,
        on_changed: Callable[[], None],
    ):
        self._scene = scene
        self._nodes = nodes
        self._counters = counters
        self._on_changed = on_changed

    def create_node(self, pos, is_source: bool = False, is_sink: bool = False) -> NodeItem:
        node_id = self._counters.next_node_id()
        node = NodeItem(pos, node_id)
        node.is_source = is_source
        node.is_sink = is_sink and not is_source
        if node.is_source and node.pressure is None:
            node.pressure = 10e6
        node.update_label(node.pressure if node.is_source else None)
        node._update_tooltip()

        self._scene.addItem(node)
        self._nodes.append(node)
        self._on_changed()
        return node

    def add_node(self, pos, node_id: str | None = None) -> NodeItem:
        """Compatibility wrapper used by tests to add a node."""
        if node_id:
            return self.create_node_with_id(pos, node_id)
        return self.create_node(pos)

    def add_source(self, pos, node_id: str | None = None) -> NodeItem:
        """Add a source node (compatibility wrapper)."""
        if node_id:
            return self.create_node_with_id(pos, node_id, is_source=True)
        return self.create_node(pos, is_source=True)

    def add_sink(self, pos, node_id: str | None = None) -> NodeItem:
        """Add a sink node (compatibility wrapper)."""
        if node_id:
            return self.create_node_with_id(pos, node_id, is_sink=True)
        return self.create_node(pos, is_sink=True)

    def create_pump(self, pos) -> PumpItem:
        node_id = self._counters.next_pump_id()
        node = PumpItem(pos, node_id)
        self._scene.addItem(node)
        self._nodes.append(node)
        self._on_changed()
        return node

    def create_valve(self, pos) -> ValveItem:
        node_id = self._counters.next_valve_id()
        node = ValveItem(pos, node_id)
        self._scene.addItem(node)
        self._nodes.append(node)
        self._on_changed()
        return node

    def create_node_with_id(
        self,
        pos,
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
        if is_pump:
            node = PumpItem(pos, node_id)
        elif is_valve:
            node = ValveItem(pos, node_id)
        else:
            node = NodeItem(pos, node_id)
        node.is_source = is_source
        node.is_sink = is_sink and not is_source
        node.is_pump = is_pump
        node.is_valve = is_valve
        if node.is_source:
            node.pressure = pressure if pressure is not None else 10e6
            node.flow_rate = flow_rate
            node.update_label(node.pressure)
        else:
            node.pressure = None
            node.flow_rate = flow_rate
            node.update_label(None)
        if is_pump:
            node.pressure_ratio = pressure_ratio if pressure_ratio is not None else 1.2
            node.update_label(None)
        if is_valve:
            node.valve_k = valve_k if valve_k is not None else 5.0
            node.update_label(None)
        node._update_tooltip()

        self._scene.addItem(node)
        self._nodes.append(node)
        if is_pump:
            self._counters.update_from_id(node_id, "PU")
        elif is_valve:
            self._counters.update_from_id(node_id, "V")
        else:
            self._counters.update_from_id(node_id, "N")
        self._on_changed()
        return node

    def make_source(self, node: NodeItem) -> None:
        node.is_source = True
        node.is_sink = False
        if node.pressure is None:
            node.pressure = 10e6
        node.update_label(node.pressure)
        node._update_tooltip()
        self._on_changed()

    def make_sink(self, node: NodeItem) -> None:
        node.is_sink = True
        node.is_source = False
        node.update_label(None)
        node._update_tooltip()
        self._on_changed()

    def remove_node(self, node: NodeItem, remove_pipe: Callable[[PipeItem], None]) -> None:
        for pipe in list(getattr(node, "pipes", [])):
            remove_pipe(pipe)

        if node in self._nodes:
            self._nodes.remove(node)
        self._scene.removeItem(node)
        self._on_changed()


class PipeOperations:
    def __init__(
        self,
        scene: QGraphicsScene,
        pipes: List[PipeItem],
        counters: SceneCounters,
        on_changed: Callable[[], None],
    ):
        self._scene = scene
        self._pipes = pipes
        self._counters = counters
        self._on_changed = on_changed
        self.pipe_start_node: Optional[NodeItem] = None

    def reset_pipe_builder(self) -> None:
        self.pipe_start_node = None

    def create_pipe(self, node1: NodeItem, node2: NodeItem) -> PipeItem:
        """Create a pipe between two nodes with auto-generated ID"""
        pipe_id = self._counters.next_pipe_id()
        pipe = PipeItem(node1, node2, pipe_id)
        self._scene.addItem(pipe)
        self._pipes.append(pipe)
        pipe.attach_label_to_scene()
        self._on_changed()
        return pipe

    def add_pipe(self, node1: NodeItem, node2: NodeItem, pipe_id: str | None = None) -> PipeItem:
        """Compatibility wrapper used by tests to add a pipe."""
        if pipe_id:
            return self.create_pipe_with_id(node1, node2, pipe_id)
        return self.create_pipe(node1, node2)

    def handle_pipe_click(self, node: NodeItem) -> None:
        if self.pipe_start_node is None:
            self.pipe_start_node = node
            node.setSelected(True)
        else:
            if node is not self.pipe_start_node:
                pipe_id = self._counters.next_pipe_id()

                pipe = PipeItem(self.pipe_start_node, node, pipe_id)
                self._scene.addItem(pipe)
                self._pipes.append(pipe)
                pipe.attach_label_to_scene()
                self._on_changed()

            self.pipe_start_node.setSelected(False)
            self.pipe_start_node = None

    def add_pump(self, pipe: PipeItem) -> None:
        if pipe.pump_curve is None:
            pipe.pump_curve = PumpCurve(a=1.0e5, b=-2.0e5, c=-1.0e6)
        self._on_changed()

    def add_valve(self, pipe: PipeItem) -> None:
        if pipe.valve is None:
            pipe.valve = Valve(k=5.0)
        self._on_changed()

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
        pipe = PipeItem(node1, node2, pipe_id)
        if length is not None:
            pipe.length = length
        if diameter is not None:
            pipe.diameter = diameter
        if roughness is not None:
            pipe.roughness = roughness
        if flow_rate is not None:
            pipe.flow_rate = flow_rate
        pipe._update_tooltip()
        self._scene.addItem(pipe)
        self._pipes.append(pipe)
        pipe.attach_label_to_scene()
        self._counters.update_from_id(pipe_id, "P")
        self._on_changed()
        return pipe

    def remove_pipe(self, pipe: PipeItem) -> None:
        if pipe in self._pipes:
            self._pipes.remove(pipe)
        if pipe.label is not None and pipe.label.scene() is self._scene:
            self._scene.removeItem(pipe.label)
        for node in (pipe.node1, pipe.node2):
            if hasattr(node, "pipes") and pipe in node.pipes:
                node.pipes.remove(pipe)
        self._scene.removeItem(pipe)
        self._on_changed()


class NetworkResultApplier:
    def __init__(self, nodes: List[NodeItem], pipes: List[PipeItem]):
        self._nodes = nodes
        self._pipes = pipes

    def apply_results(self, network) -> None:
        node_by_id = {n.node_id: n for n in self._nodes}
        pipe_by_id = {p.pipe_id: p for p in self._pipes}

        for node_id, node in network.nodes.items():
            if node_id in node_by_id:
                node_by_id[node_id].update_label(getattr(node, "pressure", None))

        dps = []
        for pipe_id, pipe in network.pipes.items():
            dp = getattr(pipe, "pressure_drop", None)
            if isinstance(dp, (int, float)):
                dps.append(dp)
        max_dp = max(dps) if dps else 0.0

        for pipe_id, pipe in network.pipes.items():
            if pipe_id in pipe_by_id:
                item = pipe_by_id[pipe_id]
                dp = getattr(pipe, "pressure_drop", None)
                item.update_label(dp)

                if isinstance(dp, (int, float)) and max_dp > 0:
                    width = 2 + 6 * (dp / max_dp)
                    pen = item.pen()
                    pen.setWidthF(width)
                    ratio = max(0.0, min(1.0, dp / max_dp))
                    pen.setColor(QColor.fromRgbF(ratio, 0.0, 1.0 - ratio))
                    item.setPen(pen)
