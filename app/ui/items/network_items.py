from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QMenu,
    QGraphicsTextItem,
    QGraphicsPolygonItem,
)
from PyQt6.QtGui import QPen, QBrush, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF
import math
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
        
        # Flow direction arrows
        self.flow_arrows = []  # List of arrow graphics items
        self.flow_direction = 0  # 1 = node1->node2, -1 = node2->node1, 0 = unknown

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
    
    def show_flow_direction(self, flow_rate: float = None):
        """Display flow direction arrows on the pipe
        
        Args:
            flow_rate: Flow rate in m³/s. If None, uses self.flow_rate
        """
        # Remove existing arrows
        self.hide_flow_direction()
        
        if flow_rate is None:
            flow_rate = self.flow_rate or 0.0
        
        # Determine direction (0 means no flow or unknown)
        if abs(flow_rate) < 1e-9:
            self.flow_direction = 0
            return
        
        # Positive flow: node1 -> node2, Negative flow: node2 -> node1
        self.flow_direction = 1 if flow_rate >= 0 else -1
        
        # Create arrow along the pipe
        line = self.line()
        start_x, start_y = line.x1(), line.y1()
        end_x, end_y = line.x2(), line.y2()
        
        # Reverse if negative flow
        if self.flow_direction < 0:
            start_x, start_y, end_x, end_y = end_x, end_y, start_x, start_y
        
        # Calculate pipe angle
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx**2 + dy**2)
        
        if length < 1e-6:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Create multiple arrows along the pipe (2-3 arrows)
        num_arrows = min(3, max(1, int(length / 100)))
        
        for i in range(num_arrows):
            # Position arrows evenly along pipe (but not at endpoints)
            t = (i + 1) / (num_arrows + 1)
            arrow_x = start_x + t * (end_x - start_x)
            arrow_y = start_y + t * (end_y - start_y)
            
            # Create arrowhead
            arrow = self._create_arrowhead(arrow_x, arrow_y, dx, dy)
            
            if self.scene():
                self.scene().addItem(arrow)
                self.flow_arrows.append(arrow)
    
    def _create_arrowhead(self, x: float, y: float, dx: float, dy: float):
        """Create an arrowhead polygon pointing in direction (dx, dy)"""
        arrow_size = 12
        arrow_width = 8
        
        # Calculate perpendicular vector
        perp_x = -dy
        perp_y = dx
        
        # Arrow points
        tip = QPointF(x + dx * arrow_size, y + dy * arrow_size)
        left = QPointF(
            x - dx * arrow_size/2 + perp_x * arrow_width/2,
            y - dy * arrow_size/2 + perp_y * arrow_width/2
        )
        right = QPointF(
            x - dx * arrow_size/2 - perp_x * arrow_width/2,
            y - dy * arrow_size/2 - perp_y * arrow_width/2
        )
        
        # Create polygon
        polygon = QPolygonF([tip, left, right])
        arrow_item = QGraphicsPolygonItem(polygon)
        
        # Style the arrow
        arrow_item.setBrush(QBrush(Qt.GlobalColor.darkRed))
        arrow_item.setPen(QPen(Qt.GlobalColor.darkRed, 1))
        arrow_item.setZValue(5)  # Above pipe, below label
        
        return arrow_item
    
    def hide_flow_direction(self):
        """Remove flow direction arrows"""
        for arrow in self.flow_arrows:
            if arrow.scene():
                arrow.scene().removeItem(arrow)
        self.flow_arrows.clear()
        self.flow_direction = 0


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
