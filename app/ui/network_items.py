from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QMenu,
    QGraphicsTextItem,
)
from PyQt6.QtGui import QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QPointF
from app.ui.dialogs import PipePropertiesDialog, NodePropertiesDialog, PumpPropertiesDialog, ValvePropertiesDialog


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
            p = getattr(self, "pressure", 0.0) or 0.0
            self.setToolTip(f"{self.node_id}\nSource\nP = {p:,.0f} Pa")
        elif getattr(self, "is_sink", False):
            self.setToolTip(f"{self.node_id}\nSink")
        else:
            self.setToolTip(f"{self.node_id}\nJunction")

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = menu.addAction("Edit node properties...")

        chosen = menu.exec(event.screenPos())
        if chosen == edit_action:
            dlg = NodePropertiesDialog(
                is_source=getattr(self, "is_source", False),
                is_sink=getattr(self, "is_sink", False),
                pressure_pa=getattr(self, "pressure", None),
            )
            if dlg.exec():
                self.is_source, self.is_sink, self.pressure = dlg.values()
                if self.is_source and self.pressure is None:
                    self.pressure = 10e6  # default if user leaves 0
                self.update_label(self.pressure if self.is_source else None)
                self._update_tooltip()
                scene = self.scene()
                if scene is not None and hasattr(scene, "nodes_changed"):
                    scene.nodes_changed.emit()

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
            # Check if multi-phase mode is enabled
            is_multiphase = False
            if self.scene() and hasattr(self.scene(), 'current_fluid'):
                is_multiphase = self.scene().current_fluid.is_multiphase if self.scene().current_fluid else False
            
            liquid_flow = getattr(self, 'liquid_flow_rate', 0.0) or 0.0
            gas_flow = getattr(self, 'gas_flow_rate', 0.0) or 0.0
            
            dlg = PipePropertiesDialog(
                self.length, self.diameter, self.roughness, self.flow_rate,
                is_multiphase, liquid_flow, gas_flow
            )
            if dlg.exec():
                length, diameter, roughness, flow_rate, liquid_flow_rate, gas_flow_rate = dlg.values()
                self.length = length
                self.diameter = diameter
                self.roughness = roughness
                self.flow_rate = flow_rate
                self.liquid_flow_rate = liquid_flow_rate
                self.gas_flow_rate = gas_flow_rate
                self._update_tooltip()

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
            dlg = PumpPropertiesDialog(self.pressure_ratio or 1.0)
            if dlg.exec():
                self.pressure_ratio = dlg.value()
                self.update_label(None)
                self._update_tooltip()
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
            dlg = ValvePropertiesDialog(self.valve_k or 0.0)
            if dlg.exec():
                self.valve_k = dlg.value()
                self.update_label(None)
                self._update_tooltip()
        event.accept()
