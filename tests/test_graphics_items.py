"""
Tests for graphics items (NodeItem, PipeItem, flow visualization).

This module tests all graphics items used for network visualization,
including nodes, pipes, pumps, valves, and flow direction indicators.
"""

import pytest
from PyQt6.QtWidgets import QApplication, QGraphicsScene
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QBrush
from PyQt6.QtCore import Qt

# Initialize QApplication for GUI testing
app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestNodeItemBasics:
    """Test basic NodeItem initialization and attributes."""

    def test_node_creation(self):
        """Test creating a basic node item."""
        from app.ui.items.network_items import NodeItem
        
        position = QPointF(100, 200)
        node = NodeItem(position, "node_1")
        
        assert node is not None
        assert node.node_id == "node_1"
        assert node.pos() == position

    def test_node_radius(self):
        """Test node has correct radius."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        # Ellipse is [-radius, -radius, 2*radius, 2*radius]
        rect = node.rect()
        
        assert rect.width() == 2 * NodeItem.RADIUS
        assert rect.height() == 2 * NodeItem.RADIUS

    def test_node_default_attributes(self):
        """Test node initializes with correct default attributes."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert node.is_source is False
        assert node.is_sink is False
        assert node.is_pump is False
        assert node.is_valve is False
        assert node.pressure_ratio is None
        assert node.valve_k is None
        assert node.pressure is None
        assert node.flow_rate is None

    def test_node_has_label(self):
        """Test node creates a text label."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert node.label is not None
        assert "node_1" in node.label.toPlainText()

    def test_node_is_movable(self):
        """Test node is flagged as movable."""
        from app.ui.items.network_items import NodeItem
        from PyQt6.QtWidgets import QGraphicsItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert node.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable

    def test_node_is_selectable(self):
        """Test node is flagged as selectable."""
        from app.ui.items.network_items import NodeItem
        from PyQt6.QtWidgets import QGraphicsItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert node.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable

    def test_node_pipes_list(self):
        """Test node maintains list of connected pipes."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert hasattr(node, "pipes")
        assert node.pipes == []


class TestNodeItemTypes:
    """Test different node types (source, sink, pump, valve)."""

    def test_source_node_label(self):
        """Test source node displays correct label."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "source_1")
        node.is_source = True
        node.update_label()
        
        assert "Source" in node.label.toPlainText()

    def test_sink_node_label(self):
        """Test sink node displays correct label."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "sink_1")
        node.is_sink = True
        node.update_label()
        
        assert "Sink" in node.label.toPlainText()

    def test_pump_node_label(self):
        """Test pump node displays correct label."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "pump_1")
        node.is_pump = True
        node.pressure_ratio = 1.5
        node.update_label()
        
        text = node.label.toPlainText()
        assert "Pump" in text
        assert "1.50" in text

    def test_valve_node_label(self):
        """Test valve node displays correct label."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "valve_1")
        node.is_valve = True
        node.valve_k = 10.0
        node.update_label()
        
        text = node.label.toPlainText()
        assert "Valve" in text
        assert "10.00" in text

    def test_node_with_pressure_label(self):
        """Test node label includes pressure when provided."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        node.update_label(pressure_pa=1e6)  # 1 MPa
        
        text = node.label.toPlainText()
        assert "1.000 MPa" in text

    def test_junction_node_tooltip(self):
        """Test junction node has basic tooltip."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "node_1")
        
        assert "node_1" in node.toolTip()
        assert "Junction" in node.toolTip()

    def test_source_node_tooltip(self):
        """Test source node tooltip shows pressure and flow."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "source_1")
        node.is_source = True
        node.pressure = 101325.0
        node.flow_rate = 0.01
        node._update_tooltip()
        
        tooltip = node.toolTip()
        assert "Source" in tooltip
        assert "101,325" in tooltip or "101325" in tooltip
        assert "0.01" in tooltip

    def test_pump_node_tooltip(self):
        """Test pump node tooltip shows pressure ratio."""
        from app.ui.items.network_items import NodeItem
        
        node = NodeItem(QPointF(0, 0), "pump_1")
        node.is_pump = True
        node.pressure_ratio = 1.75
        node._update_tooltip()
        
        tooltip = node.toolTip()
        assert "Pump" in tooltip
        assert "1.75" in tooltip


class TestPipeItemBasics:
    """Test basic PipeItem initialization and attributes."""

    def test_pipe_creation(self):
        """Test creating a basic pipe item between two nodes."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe is not None
        assert pipe.pipe_id == "pipe_1"
        assert pipe.node1 == node1
        assert pipe.node2 == node2

    def test_pipe_default_properties(self):
        """Test pipe initializes with default properties."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe.length == 1000.0  # Default length in meters
        assert pipe.diameter == 0.2  # Default diameter in meters
        assert pipe.roughness == 0.005  # Default roughness
        assert pipe.flow_rate == 0.05  # Default flow rate
        assert pipe.minor_loss_k == 0.0

    def test_pipe_connects_to_nodes(self):
        """Test pipe adds itself to connected nodes' pipe lists."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe in node1.pipes
        assert pipe in node2.pipes

    def test_pipe_has_label(self):
        """Test pipe creates a text label."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe.label is not None
        assert "pipe_1" in pipe.label.toPlainText()

    def test_pipe_is_selectable(self):
        """Test pipe is flagged as selectable."""
        from app.ui.items.network_items import NodeItem, PipeItem
        from PyQt6.QtWidgets import QGraphicsItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable

    def test_pipe_tooltip(self):
        """Test pipe tooltip shows properties."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        tooltip = pipe.toolTip()
        assert "Pipe" in tooltip
        assert "1000" in tooltip  # Length
        assert "0.2" in tooltip or "0.200" in tooltip  # Diameter


class TestPipeItemPosition:
    """Test pipe position updates and label positioning."""

    def test_pipe_position_update(self):
        """Test pipe line updates when node positions change."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        line = pipe.line()
        assert line.x1() == 0.0
        assert line.y1() == 0.0
        assert line.x2() == 100.0
        assert line.y2() == 0.0

    def test_pipe_updates_when_node_moves(self):
        """Test pipe updates position when node is moved."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        # Move node2
        node2.setPos(QPointF(200, 100))
        # Trigger the itemChange callback manually
        node2.itemChange(NodeItem.GraphicsItemChange.ItemPositionHasChanged, node2.pos())
        
        line = pipe.line()
        assert line.x2() == 200.0
        assert line.y2() == 100.0

    def test_pipe_label_position_at_midpoint(self):
        """Test pipe label is positioned at midpoint."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 100), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        pipe.update_label_position()
        
        # Label should be near midpoint (50, 50) + offset
        label_pos = pipe.label.pos()
        assert 40 < label_pos.x() < 60
        assert 40 < label_pos.y() < 60

    def test_pipe_label_with_pressure_drop(self):
        """Test pipe label shows pressure drop when provided."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        pipe.update_label(dp_pa=500000)  # 0.5 MPa
        
        text = pipe.label.toPlainText()
        assert "dP" in text or "DP" in text.upper()
        assert "0.500" in text


class TestFlowDirectionVisualization:
    """Test flow direction arrow visualization."""

    def test_flow_arrows_initially_empty(self):
        """Test pipe has no flow arrows initially."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        assert pipe.flow_arrows == []
        assert pipe.flow_direction == 0

    def test_show_positive_flow_direction(self):
        """Test showing flow direction for positive flow (node1 -> node2)."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(300, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(pipe)
        pipe.attach_label_to_scene()
        
        pipe.show_flow_direction(flow_rate=0.05)
        
        assert pipe.flow_direction == 1  # Positive flow
        assert len(pipe.flow_arrows) > 0  # At least one arrow

    def test_show_negative_flow_direction(self):
        """Test showing flow direction for negative flow (node2 -> node1)."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(300, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(pipe)
        
        pipe.show_flow_direction(flow_rate=-0.05)
        
        assert pipe.flow_direction == -1  # Negative flow
        assert len(pipe.flow_arrows) > 0

    def test_show_zero_flow(self):
        """Test zero flow shows no arrows."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(300, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(pipe)
        
        pipe.show_flow_direction(flow_rate=0.0)
        
        assert pipe.flow_direction == 0
        assert len(pipe.flow_arrows) == 0

    def test_hide_flow_direction(self):
        """Test hiding flow direction removes arrows."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(300, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(pipe)
        
        # Show arrows first
        pipe.show_flow_direction(flow_rate=0.05)
        assert len(pipe.flow_arrows) > 0
        
        # Hide arrows
        pipe.hide_flow_direction()
        assert len(pipe.flow_arrows) == 0
        assert pipe.flow_direction == 0

    def test_flow_arrows_count_based_on_length(self):
        """Test number of flow arrows scales with pipe length."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        
        # Short pipe
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(50, 0), "node_2")
        pipe_short = PipeItem(node1, node2, "pipe_short")
        scene.addItem(pipe_short)
        pipe_short.show_flow_direction(flow_rate=0.05)
        short_arrow_count = len(pipe_short.flow_arrows)
        
        # Long pipe
        node3 = NodeItem(QPointF(0, 0), "node_3")
        node4 = NodeItem(QPointF(500, 0), "node_4")
        pipe_long = PipeItem(node3, node4, "pipe_long")
        scene.addItem(pipe_long)
        pipe_long.show_flow_direction(flow_rate=0.05)
        long_arrow_count = len(pipe_long.flow_arrows)
        
        # Long pipe should have more arrows (or at least as many)
        assert long_arrow_count >= short_arrow_count


class TestPumpItemSpecialization:
    """Test PumpItem (specialized NodeItem)."""

    def test_pump_item_creation(self):
        """Test creating a pump item."""
        from app.ui.items.network_items import PumpItem
        
        pump = PumpItem(QPointF(100, 100), "pump_1")
        
        assert pump is not None
        assert pump.node_id == "pump_1"
        assert pump.is_pump is True
        assert pump.is_source is False
        assert pump.is_sink is False
        assert pump.is_valve is False

    def test_pump_default_pressure_ratio(self):
        """Test pump has a default pressure ratio."""
        from app.ui.items.network_items import PumpItem
        
        pump = PumpItem(QPointF(100, 100), "pump_1")
        
        assert pump.pressure_ratio is not None
        assert pump.pressure_ratio > 1.0  # Pumps increase pressure

    def test_pump_visual_style(self):
        """Test pump has distinct visual style (green brush)."""
        from app.ui.items.network_items import PumpItem
        
        pump = PumpItem(QPointF(100, 100), "pump_1")
        
        # Pump should have green color
        brush = pump.brush()
        assert brush.color() == Qt.GlobalColor.green

    def test_pump_label_shows_type(self):
        """Test pump label indicates it's a pump."""
        from app.ui.items.network_items import PumpItem
        
        pump = PumpItem(QPointF(100, 100), "pump_1")
        
        text = pump.label.toPlainText()
        assert "Pump" in text


class TestValveItemSpecialization:
    """Test ValveItem (specialized NodeItem)."""

    def test_valve_item_creation(self):
        """Test creating a valve item."""
        from app.ui.items.network_items import ValveItem
        
        valve = ValveItem(QPointF(100, 100), "valve_1")
        
        assert valve is not None
        assert valve.node_id == "valve_1"
        assert valve.is_valve is True
        assert valve.is_source is False
        assert valve.is_sink is False
        assert valve.is_pump is False

    def test_valve_default_k_value(self):
        """Test valve has a default K value."""
        from app.ui.items.network_items import ValveItem
        
        valve = ValveItem(QPointF(100, 100), "valve_1")
        
        assert valve.valve_k is not None
        assert valve.valve_k > 0.0

    def test_valve_visual_style(self):
        """Test valve has distinct visual style (yellow brush)."""
        from app.ui.items.network_items import ValveItem
        
        valve = ValveItem(QPointF(100, 100), "valve_1")
        
        # Valve should have yellow color
        brush = valve.brush()
        assert brush.color() == Qt.GlobalColor.yellow

    def test_valve_label_shows_type(self):
        """Test valve label indicates it's a valve."""
        from app.ui.items.network_items import ValveItem
        
        valve = ValveItem(QPointF(100, 100), "valve_1")
        
        text = valve.label.toPlainText()
        assert "Valve" in text


class TestGraphicsItemIntegration:
    """Test integration scenarios with multiple items."""

    def test_multiple_pipes_on_node(self):
        """Test node can have multiple connected pipes."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        center = NodeItem(QPointF(0, 0), "center")
        node1 = NodeItem(QPointF(100, 0), "node_1")
        node2 = NodeItem(QPointF(0, 100), "node_2")
        node3 = NodeItem(QPointF(-100, 0), "node_3")
        
        pipe1 = PipeItem(center, node1, "pipe_1")
        pipe2 = PipeItem(center, node2, "pipe_2")
        pipe3 = PipeItem(center, node3, "pipe_3")
        
        assert len(center.pipes) == 3
        assert pipe1 in center.pipes
        assert pipe2 in center.pipes
        assert pipe3 in center.pipes

    def test_scene_integration(self):
        """Test items can be added to a graphics scene."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(pipe)
        
        assert node1.scene() == scene
        assert node2.scene() == scene
        assert pipe.scene() == scene

    def test_pipe_label_attached_to_scene(self):
        """Test pipe label can be attached to scene."""
        from app.ui.items.network_items import NodeItem, PipeItem
        
        scene = QGraphicsScene()
        
        node1 = NodeItem(QPointF(0, 0), "node_1")
        node2 = NodeItem(QPointF(100, 0), "node_2")
        pipe = PipeItem(node1, node2, "pipe_1")
        
        scene.addItem(pipe)
        pipe.attach_label_to_scene()
        
        assert pipe.scene_label_added is True
        assert pipe.label.scene() == scene
