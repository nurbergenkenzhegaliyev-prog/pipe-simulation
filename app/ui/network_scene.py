from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor
from app.models.equipment import PumpCurve, Valve
from app.ui.tool_palette import Tool
from app.ui.network_items import NodeItem, PipeItem, PumpItem, ValveItem


class NetworkScene(QGraphicsScene):
    nodes_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)

        self.current_tool = Tool.SELECT

        self.nodes = []
        self.pipes = []

        self._node_counter = 0
        self._pipe_counter = 0
        self._pump_counter = 0
        self._valve_counter = 0

        # for PIPE tool
        self._pipe_start_node = None

    # ---------- API FROM UI ----------
    def set_tool(self, tool: Tool):
        self.current_tool = tool
        self._pipe_start_node = None
        self.clearSelection()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._delete_selected()
            return
        super().keyPressEvent(event)

    # ---------- MOUSE ----------
    def mousePressEvent(self, event):
        pos = event.scenePos()
        item = self.itemAt(pos, self.views()[0].transform())

        if event.button() == Qt.MouseButton.LeftButton:

            # --- NODE TOOL ---
            if self.current_tool == Tool.NODE:
                if not isinstance(item, NodeItem):
                    self._create_node(pos)

            # --- SOURCE TOOL ---
            elif self.current_tool == Tool.SOURCE:
                if isinstance(item, NodeItem):
                    self._make_source(item)
                else:
                    node = self._create_node(pos, is_source=True)
                    self._make_source(node)

            # --- SINK TOOL ---
            elif self.current_tool == Tool.SINK:
                if isinstance(item, NodeItem):
                    self._make_sink(item)
                else:
                    node = self._create_node(pos, is_sink=True)
                    self._make_sink(node)

            # --- PIPE TOOL ---
            elif self.current_tool == Tool.PIPE:
                if isinstance(item, NodeItem):
                    self._handle_pipe_click(item)

            # --- PUMP TOOL ---
            elif self.current_tool == Tool.PUMP:
                if not isinstance(item, NodeItem):
                    self._create_pump(pos)

            # --- VALVE TOOL ---
            elif self.current_tool == Tool.VALVE:
                if not isinstance(item, NodeItem):
                    self._create_valve(pos)

            # --- SELECT TOOL ---
            else:
                super().mousePressEvent(event)
                return

        super().mousePressEvent(event)

    # ---------- NODE HELPERS ----------
    def _create_node(self, pos, is_source: bool = False, is_sink: bool = False) -> NodeItem:
        self._node_counter += 1
        node_id = f"N{self._node_counter}"

        node = NodeItem(pos, node_id)
        node.is_source = is_source
        node.is_sink = is_sink and not is_source
        if node.is_source and node.pressure is None:
            node.pressure = 10e6  # Pa default
        node.update_label(node.pressure if node.is_source else None)
        node._update_tooltip()

        self.addItem(node)
        self.nodes.append(node)
        self.nodes_changed.emit()
        return node

    def _create_pump(self, pos) -> PumpItem:
        self._pump_counter += 1
        node_id = f"PU{self._pump_counter}"
        node = PumpItem(pos, node_id)
        self.addItem(node)
        self.nodes.append(node)
        self.nodes_changed.emit()
        return node

    def _create_valve(self, pos) -> ValveItem:
        self._valve_counter += 1
        node_id = f"V{self._valve_counter}"
        node = ValveItem(pos, node_id)
        self.addItem(node)
        self.nodes.append(node)
        self.nodes_changed.emit()
        return node

    def create_node_with_id(
        self,
        pos: QPointF,
        node_id: str,
        is_source: bool = False,
        is_sink: bool = False,
        pressure: float | None = None,
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
            node.update_label(node.pressure)
        else:
            node.pressure = None
            node.update_label(None)
        if is_pump:
            node.pressure_ratio = pressure_ratio if pressure_ratio is not None else 1.2
            node.update_label(None)
        if is_valve:
            node.valve_k = valve_k if valve_k is not None else 5.0
            node.update_label(None)
        node._update_tooltip()

        self.addItem(node)
        self.nodes.append(node)
        if is_pump:
            self._update_counter_from_id(node_id, "PU")
        elif is_valve:
            self._update_counter_from_id(node_id, "V")
        else:
            self._update_counter_from_id(node_id, "N")
        self.nodes_changed.emit()
        return node

    def _make_source(self, node: NodeItem):
        node.is_source = True
        node.is_sink = False
        if node.pressure is None:
            node.pressure = 10e6  # Pa default
        node.update_label(node.pressure)
        node._update_tooltip()
        self.nodes_changed.emit()

    def _make_sink(self, node: NodeItem):
        node.is_sink = True
        node.is_source = False
        node.update_label(None)
        node._update_tooltip()
        self.nodes_changed.emit()

    # ---------- DELETE ----------
    def _delete_selected(self):
        selected = list(self.selectedItems())

        # Remove pipes first
        for item in selected:
            if isinstance(item, PipeItem):
                self._remove_pipe(item)

        # Remove nodes (also removes any attached pipes)
        for item in selected:
            if isinstance(item, NodeItem):
                self._remove_node(item)

    def _remove_pipe(self, pipe: PipeItem):
        if pipe in self.pipes:
            self.pipes.remove(pipe)
        if pipe.label is not None and pipe.label.scene() is self:
            self.removeItem(pipe.label)
        for node in (pipe.node1, pipe.node2):
            if hasattr(node, "pipes") and pipe in node.pipes:
                node.pipes.remove(pipe)
        self.removeItem(pipe)
        self.nodes_changed.emit()

    def _remove_node(self, node: NodeItem):
        # Remove attached pipes first
        for pipe in list(getattr(node, "pipes", [])):
            self._remove_pipe(pipe)

        if node in self.nodes:
            self.nodes.remove(node)
        self.removeItem(node)
        self.nodes_changed.emit()

    # ---------- PIPE LOGIC ----------
    def _handle_pipe_click(self, node: NodeItem):
        if self._pipe_start_node is None:
            self._pipe_start_node = node
            node.setSelected(True)
        else:
            if node is not self._pipe_start_node:
                self._pipe_counter += 1
                pipe_id = f"P{self._pipe_counter}"

                pipe = PipeItem(self._pipe_start_node, node, pipe_id)
                self.addItem(pipe)
                self.pipes.append(pipe)
                pipe.attach_label_to_scene()
                self.nodes_changed.emit()

            self._pipe_start_node.setSelected(False)
            self._pipe_start_node = None

    def _add_pump(self, pipe: PipeItem):
        if pipe.pump_curve is None:
            # Default pump curve (Pa) for placeholder behavior
            pipe.pump_curve = PumpCurve(a=1.0e5, b=-2.0e5, c=-1.0e6)
        self.nodes_changed.emit()

    def _add_valve(self, pipe: PipeItem):
        if pipe.valve is None:
            # Default K value for placeholder behavior
            pipe.valve = Valve(k=5.0)
        self.nodes_changed.emit()

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
        self.addItem(pipe)
        self.pipes.append(pipe)
        pipe.attach_label_to_scene()
        self._update_counter_from_id(pipe_id, "P")
        self.nodes_changed.emit()
        return pipe

    def clear_network(self):
        for pipe in list(self.pipes):
            self._remove_pipe(pipe)
        for node in list(self.nodes):
            self._remove_node(node)
        self._node_counter = 0
        self._pipe_counter = 0
        self._pump_counter = 0
        self._valve_counter = 0
        self._pump_counter = 0
        self._valve_counter = 0
        self._pipe_start_node = None
        self.nodes_changed.emit()

    def _update_counter_from_id(self, item_id: str, prefix: str):
        if not item_id.startswith(prefix):
            return
        suffix = item_id[len(prefix):]
        digits = "".join(ch for ch in suffix if ch.isdigit())
        if not digits:
            return
        value = int(digits)
        if prefix == "N":
            self._node_counter = max(self._node_counter, value)
        elif prefix == "P":
            self._pipe_counter = max(self._pipe_counter, value)
        elif prefix == "PU":
            self._pump_counter = max(self._pump_counter, value)
        elif prefix == "V":
            self._valve_counter = max(self._valve_counter, value)

    def apply_results(self, network):
        # Build lookup tables
        node_by_id = {n.node_id: n for n in self.nodes}
        pipe_by_id = {p.pipe_id: p for p in self.pipes}

        # Nodes: update displayed pressure
        for node_id, node in network.nodes.items():
            if node_id in node_by_id:
                node_by_id[node_id].update_label(
                    getattr(node, "pressure", None)
                    )

        # Pipes: update displayed dp + optionally thickness
        # Find max dp for scaling
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

                # Optional: thickness proportional to dp
                if isinstance(dp, (int, float)) and max_dp > 0:
                    # width from 2..8
                    width = 2 + 6 * (dp / max_dp)
                    pen = item.pen()
                    pen.setWidthF(width)
                    # color from blue (low) to red (high)
                    ratio = max(0.0, min(1.0, dp / max_dp))
                    pen.setColor(QColor.fromRgbF(ratio, 0.0, 1.0 - ratio))
                    item.setPen(pen)

