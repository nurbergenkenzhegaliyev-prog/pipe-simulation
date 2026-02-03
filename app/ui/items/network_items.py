from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QMenu,
    QGraphicsTextItem,
)
from PyQt6.QtGui import QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QPointF
from app.ui.items.item_editors import (
    edit_node_properties,
    edit_pipe_properties,
    edit_pump_properties,
    edit_valve_properties,
)


class NodeItem(QGraphicsEllipseItem):
    RADIUS = 10

    def __init__(self, position: QPointF, node_id: str):
        super().__init__(
            -self.RADIUS,
            -self.RADIUS,
            2 * self.RADIUS,
            2 * self.RADIUS,
        )

        # Basic attributes
        self.pipes = []
        self.node_id = node_id
        self.is_source = False
        self.is_sink = False
        self.is_pump = False
        self.is_valve = False
        self.pressure_ratio = None
        self.valve_k = None
        self.pressure = None  # Pa; only for sources
        self.flow_rate = None  # m³/s; for sources (optional) and sinks (required)
        print("Created node:", node_id)

        # Label in the canvas
        self.label = QGraphicsTextItem(self)
        self.label.setDefaultTextColor(Qt.GlobalColor.black)
        self.label.setFont(QFont("Segoe UI", 9))
        self.label.setPos(self.RADIUS + 6, -self.RADIUS - 6)
        self.update_label()  # initial

        self._update_tooltip()

        self.setPos(position)

        self.setBrush(QBrush(Qt.GlobalColor.lightGray))
        self.setPen(QPen(Qt.GlobalColor.black, 2))

        self.setFlags(
            QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def update_label(self, pressure_pa: float | None = None):
        # If pressure passed, show it; else show just id/type
        if pressure_pa is not None and not getattr(self, "is_pump", False) and not getattr(self, "is_valve", False):
            mp = pressure_pa / 1e6
            self.label.setPlainText(f"{self.node_id}\nP={mp:.3f} MPa")
        else:
            if getattr(self, "is_pump", False):
                ratio = getattr(self, "pressure_ratio", None)
                text = f"{self.node_id}\n(Pump)"
                if ratio is not None:
                    text = f"{self.node_id}\n(Pump x{ratio:.2f})"
                self.label.setPlainText(text)
            elif getattr(self, "is_valve", False):
                k = getattr(self, "valve_k", None)
                text = f"{self.node_id}\n(Valve)"
                if k is not None:
                    text = f"{self.node_id}\n(Valve K={k:.2f})"
                self.label.setPlainText(text)
            elif getattr(self, "is_source", False):
                self.label.setPlainText(f"{self.node_id}\n(Source)")
            elif getattr(self, "is_sink", False):
                self.label.setPlainText(f"{self.node_id}\n(Sink)")
            else:
                self.label.setPlainText(f"{self.node_id}")

    def itemChange(self, change, value):
        # This fires AFTER Qt applies the new position (most reliable)
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            for pipe in getattr(self, "pipes", []):
                pipe.update_position()
        return super().itemChange(change, value)

    def _update_tooltip(self):
        if getattr(self, "is_pump", False):
            ratio = getattr(self, "pressure_ratio", None)
            ratio_text = f"x{ratio:.3f}" if ratio is not None else "n/a"
            self.setToolTip(f"{self.node_id}\nPump\nPressure ratio = {ratio_text}")
        elif getattr(self, "is_valve", False):
            k = getattr(self, "valve_k", None)
            k_text = f"{k:.3f}" if k is not None else "n/a"
            self.setToolTip(f"{self.node_id}\nValve\nK = {k_text}")
        elif getattr(self, "is_source", False):
            p = getattr(self, "pressure", None)
            q = getattr(self, "flow_rate", None)
            tooltip_text = f"{self.node_id}\nSource"
            if p is not None:
                tooltip_text += f"\nP = {p:,.0f} Pa"
            if q is not None:
                tooltip_text += f"\nQ = {q:.6f} m³/s"
            self.setToolTip(tooltip_text)
        elif getattr(self, "is_sink", False):
            q = getattr(self, "flow_rate", None)
            tooltip_text = f"{self.node_id}\nSink"
            if q is not None:
                tooltip_text += f"\nQ = {q:.6f} m³/s"
            self.setToolTip(tooltip_text)
        else:
            self.setToolTip(f"{self.node_id}\nJunction")

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("Edit node properties...")

        chosen = menu.exec(event.screenPos())
        if chosen == edit_action:
            edit_node_properties(self)

        event.accept()


class PipeItem(QGraphicsLineItem):
    def __init__(self, node1: NodeItem, node2: NodeItem, pipe_id: str):
        super().__init__()

        self.pipe_id = pipe_id
        # match your domain Pipe fields/units
        self.length = 1000.0  # m
        self.diameter = 0.2  # m
        self.roughness = 0.005  # (use whatever your solver expects)
        self.flow_rate = 0.05  # m3/s
        self.pump_curve = None
        self.valve = None

        # Label in the canvas
        self.label = QGraphicsTextItem()
        self.label.setDefaultTextColor(Qt.GlobalColor.black)
        self.label.setFont(QFont("Segoe UI", 9))
        self.label.setZValue(10)  # ensure above line
        self.label.setPlainText(self.pipe_id)
        self.scene_label_added = False

        self.node1 = node1
        self.node2 = node2

        self.setPen(QPen(Qt.GlobalColor.darkBlue, 3))

        # Make pipe selectable (so right-click feels natural)
        self.setFlags(
            QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable
        )

        # default properties (SI units internally)

        node1.pipes.append(self)
        node2.pipes.append(self)

        self.update_position()
        self._update_tooltip()

    def _update_tooltip(self):
        self.setToolTip(
            "Pipe\n"
            f"L = {self.length:.3f} m\n"
            f"D = {self.diameter:.4f} m\n"
            f"eps = {self.roughness:.4f}\n"
            f"Q = {self.flow_rate:.4f} m3/s"
        )
        extras = []
        if getattr(self, "pump_curve", None) is not None:
            extras.append("Pump")
        if getattr(self, "valve", None) is not None:
            extras.append("Valve")
        if extras:
            self.setToolTip(self.toolTip() + "\n" + ", ".join(extras))

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("Edit pipe properties...")

        chosen = menu.exec(event.screenPos())
        if chosen == edit_action:
            edit_pipe_properties(self)

        event.accept()

    def update_position(self):
        p1 = self.node1.scenePos()
        p2 = self.node2.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        if hasattr(self, "label"):
            self.update_label_position()

    def attach_label_to_scene(self):
        # call once after item is added to scene
        if not self.scene_label_added and self.scene() is not None:
            self.scene().addItem(self.label)
            self.scene_label_added = True
            self.update_label_position()

    def update_label_position(self):
        line = self.line()
        mx = (line.x1() + line.x2()) / 2
        my = (line.y1() + line.y2()) / 2
        self.label.setPos(mx + 6, my + 6)

    def update_label(self, dp_pa: float | None = None):
        if dp_pa is None:
            self.label.setPlainText(self.pipe_id)
        else:
            mp = dp_pa / 1e6
            self.label.setPlainText(f"{self.pipe_id}\ndP={mp:.3f} MPa")


class PumpItem(NodeItem):
    def __init__(self, position: QPointF, node_id: str):
        super().__init__(position, node_id)
        self.is_pump = True
        self.is_source = False
        self.is_sink = False
        self.is_valve = False
        self.pressure_ratio = 1.2
        self.setBrush(QBrush(Qt.GlobalColor.green))
        self.update_label(None)
        self._update_tooltip()

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("Edit pump properties...")
        chosen = menu.exec(event.screenPos())
        if chosen == edit_action:
            edit_pump_properties(self)
        event.accept()


class ValveItem(NodeItem):
    def __init__(self, position: QPointF, node_id: str):
        super().__init__(position, node_id)
        self.is_valve = True
        self.is_source = False
        self.is_sink = False
        self.is_pump = False
        self.valve_k = 5.0
        self.setBrush(QBrush(Qt.GlobalColor.yellow))
        self.update_label(None)
        self._update_tooltip()

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("Edit valve properties...")
        chosen = menu.exec(event.screenPos())
        if chosen == edit_action:
            edit_valve_properties(self)
        event.accept()
