"""Visualization utilities for pressure and flow overlays on the network"""

from PyQt6.QtGui import QColor, QBrush
from typing import Tuple


class ColorScale:
    """Generate colors based on value range (e.g., for pressure or flow)"""
    
    def __init__(self, min_value: float, max_value: float, color_scheme: str = "pressure"):
        """
        Initialize color scale
        
        Args:
            min_value: Minimum value in range
            max_value: Maximum value in range
            color_scheme: "pressure" (blue to red) or "flow" (green to red)
        """
        self.min_value = min_value
        self.max_value = max_value
        self.color_scheme = color_scheme
        self.range = max(max_value - min_value, 1e-6)  # Avoid division by zero
    
    def get_color(self, value: float) -> QColor:
        """Get color for a value based on the color scheme"""
        if self.range == 0:
            normalized = 0.5
        else:
            normalized = max(0.0, min(1.0, (value - self.min_value) / self.range))
        
        if self.color_scheme == "pressure":
            return self._pressure_color(normalized)
        elif self.color_scheme == "flow":
            return self._flow_color(normalized)
        else:
            return QColor("gray")
    
    def _pressure_color(self, normalized: float) -> QColor:
        """Blue (low) -> Cyan -> Yellow -> Red (high)"""
        if normalized < 0.25:
            # Blue to Cyan
            t = normalized / 0.25
            r = int(0 + (0 - 0) * t)
            g = int(0 + (255 - 0) * t)
            b = int(255)
            return QColor(r, g, b)
        elif normalized < 0.5:
            # Cyan to Green
            t = (normalized - 0.25) / 0.25
            r = int(0)
            g = int(255)
            b = int(255 + (0 - 255) * t)
            return QColor(r, g, b)
        elif normalized < 0.75:
            # Green to Yellow
            t = (normalized - 0.5) / 0.25
            r = int(0 + (255 - 0) * t)
            g = int(255)
            b = int(0)
            return QColor(r, g, b)
        else:
            # Yellow to Red
            t = (normalized - 0.75) / 0.25
            r = int(255)
            g = int(255 + (0 - 255) * t)
            b = int(0)
            return QColor(r, g, b)
    
    def _flow_color(self, normalized: float) -> QColor:
        """Green (low) -> Yellow -> Orange -> Red (high)"""
        if normalized < 0.33:
            # Green to Yellow
            t = normalized / 0.33
            r = int(0 + (255 - 0) * t)
            g = int(255)
            b = int(0)
            return QColor(r, g, b)
        elif normalized < 0.66:
            # Yellow to Orange
            t = (normalized - 0.33) / 0.33
            r = int(255)
            g = int(255 + (165 - 255) * t)
            b = int(0)
            return QColor(r, g, b)
        else:
            # Orange to Red
            t = (normalized - 0.66) / 0.34
            r = int(255)
            g = int(165 + (0 - 165) * t)
            b = int(0)
            return QColor(r, g, b)


class NetworkVisualizer:
    """Apply visualization overlays to network scene based on simulation results"""
    
    @staticmethod
    def apply_pressure_overlay(scene, network) -> None:
        """Color nodes and pipes based on pressure values"""
        # Get pressure range
        pressures = [n.pressure for n in network.nodes.values() if n.pressure is not None]
        if not pressures:
            return
        
        min_pressure = min(pressures)
        max_pressure = max(pressures)
        color_scale = ColorScale(min_pressure, max_pressure, "pressure")
        
        # Color nodes
        for node_item in scene.nodes:
            node = network.nodes.get(node_item.node_id)
            if node and node.pressure is not None:
                color = color_scale.get_color(node.pressure)
                node_item.setBrush(color)
    
    @staticmethod
    def apply_flow_overlay(scene, network) -> None:
        """Color pipes based on flow rate values"""
        # Get flow rate range
        flows = [p.flow_rate for p in network.pipes.values() if p.flow_rate is not None]
        if not flows:
            return
        
        min_flow = min(flows)
        max_flow = max(flows)
        color_scale = ColorScale(min_flow, max_flow, "flow")
        
        # Color pipes
        for pipe_item in scene.pipes:
            pipe = network.pipes.get(pipe_item.pipe_id)
            if pipe and pipe.flow_rate is not None:
                color = color_scale.get_color(pipe.flow_rate)
                pen = pipe_item.pen()
                pen.setColor(color)
                pipe_item.setPen(pen)
    
    @staticmethod
    def reset_colors(scene) -> None:
        """Reset scene items to default colors"""
        from PyQt6.QtGui import QPen
        from PyQt6.QtCore import Qt
        
        # Reset nodes
        for node in scene.nodes:
            node.setBrush(node.__class__.default_brush if hasattr(node.__class__, 'default_brush')
                         else QBrush(Qt.GlobalColor.lightGray))
        
        # Reset pipes
        for pipe in scene.pipes:
            pen = QPen(Qt.GlobalColor.darkBlue, 3)
            pipe.setPen(pen)
