"""Highlight invalid nodes and pipes with visual feedback"""

from PyQt6.QtGui import QPen, QColor, QBrush
from PyQt6.QtCore import Qt
from app.ui.validation.realtime_validator import ValidationLevel


class ValidationVisualizer:
    """Applies visual feedback for validation issues"""
    
    # Colors for different validation levels
    COLORS = {
        ValidationLevel.ERROR: QColor(255, 0, 0, 200),      # Red
        ValidationLevel.WARNING: QColor(255, 165, 0, 200),  # Orange
        ValidationLevel.INFO: QColor(0, 0, 255, 200),       # Blue
    }
    
    BORDER_COLORS = {
        ValidationLevel.ERROR: QColor(255, 0, 0),           # Bright red
        ValidationLevel.WARNING: QColor(255, 165, 0),       # Bright orange
        ValidationLevel.INFO: QColor(0, 0, 255),            # Bright blue
    }
    
    @staticmethod
    def highlight_item(item, level: ValidationLevel) -> None:
        """Highlight a node or pipe with validation level color"""
        if level is None:
            ValidationVisualizer.clear_highlight(item)
            return
        
        border_color = ValidationVisualizer.BORDER_COLORS[level]
        
        # Check if it's a node or pipe
        if hasattr(item, 'is_source'):  # It's a node
            # Add red border to node
            pen = QPen(border_color, 3)
            pen.setStyle(Qt.PenStyle.SolidLine)
            item.setPen(pen)
        elif hasattr(item, 'pipe_id'):  # It's a pipe
            # Add red border to pipe
            pen = QPen(border_color, 4)
            pen.setStyle(Qt.PenStyle.SolidLine)
            item.setPen(pen)
    
    @staticmethod
    def clear_highlight(item) -> None:
        """Remove validation highlight from an item"""
        if hasattr(item, 'is_source'):  # It's a node
            # Create new pen with default node styling
            pen = QPen(QColor("black"), 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            item.setPen(pen)
        elif hasattr(item, 'pipe_id'):  # It's a pipe
            # Create new pen with default pipe styling
            pen = QPen(QColor("darkBlue"), 3)
            pen.setStyle(Qt.PenStyle.SolidLine)
            item.setPen(pen)
    
    @staticmethod
    def clear_all_highlights(scene) -> None:
        """Remove all validation highlights from scene"""
        if not hasattr(scene, 'nodes') or not hasattr(scene, 'pipes'):
            return
        
        for node in scene.nodes:
            ValidationVisualizer.clear_highlight(node)
        for pipe in scene.pipes:
            ValidationVisualizer.clear_highlight(pipe)
    
    @staticmethod
    def apply_highlights(scene, problematic_items: dict) -> None:
        """Apply highlights for all problematic items"""
        if not scene:
            return
        
        if not hasattr(scene, 'nodes') or not hasattr(scene, 'pipes'):
            return
        
        # Always clear all highlights first
        ValidationVisualizer.clear_all_highlights(scene)
        
        # If there are problematic items, highlight them
        if problematic_items:
            # Highlight problematic nodes
            for node in scene.nodes:
                if hasattr(node, 'node_id') and node.node_id in problematic_items:
                    level = problematic_items[node.node_id]
                    ValidationVisualizer.highlight_item(node, level)
            
            # Highlight problematic pipes
            for pipe in scene.pipes:
                if hasattr(pipe, 'pipe_id') and pipe.pipe_id in problematic_items:
                    level = problematic_items[pipe.pipe_id]
                    ValidationVisualizer.highlight_item(pipe, level)
