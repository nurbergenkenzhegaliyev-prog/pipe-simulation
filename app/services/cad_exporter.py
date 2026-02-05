"""CAD file export service for pipe networks.

This module provides export functionality to DXF (AutoCAD Drawing Exchange Format)
for integration with CAD software. Exports network geometry with organized layers
for nodes, pipes, pumps, and valves.

Supports:
- DXF R2010 format (widely compatible)
- Layer organization (nodes, pipes, equipment)
- Node markers (circles)
- Pipe centerlines
- Equipment symbols
- Text labels with IDs and properties
"""

import logging
from pathlib import Path
from typing import Optional, List

try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


logger = logging.getLogger(__name__)


class DXFExporter:
    """Export pipe networks to AutoCAD DXF format.
    
    Creates DXF files with organized layers for different network components.
    Exports geometry from the UI scene items (NodeItem, PipeItem) which have
    visual position information.
    
    Layers created:
        - NODES: Node circles and labels
        - PIPES: Pipe centerlines
        - EQUIPMENT: Pumps and valves
        - LABELS: Text annotations
        - SOURCES: Source nodes (green)
        - SINKS: Sink nodes (red)
        
    Attributes:
        layer_config: Dictionary of layer names and colors
        node_radius: Radius for node circles (default: 0.5 units)
        text_height: Height for text labels (default: 0.3 units)
        
    Example:
        >>> from app.ui.scenes.network_scene import NetworkScene
        >>> scene = NetworkScene()
        >>> # ... build network ...
        >>> 
        >>> exporter = DXFExporter()
        >>> exporter.export_from_scene(scene, "my_network.dxf")
        >>> print("Network exported to CAD")
    """
    
    def __init__(
        self,
        layer_config: Optional[dict] = None,
        node_radius: float = 0.5,
        text_height: float = 0.3,
    ):
        """Initialize the DXF exporter.
        
        Args:
            layer_config: Custom layer configuration (name: color)
            node_radius: Radius for node circles in drawing units
            text_height: Height for text labels in drawing units
            
        Raises:
            ImportError: If ezdxf library is not installed
        """
        if not EZDXF_AVAILABLE:
            raise ImportError(
                "ezdxf library is required for DXF export. "
                "Install with: pip install ezdxf"
            )
        
        self.layer_config = layer_config or {
            "NODES": colors.CYAN,
            "PIPES": colors.WHITE,
            "EQUIPMENT": colors.MAGENTA,
            "LABELS": colors.YELLOW,
            "SOURCES": colors.GREEN,
            "SINKS": colors.RED,
        }
        
        self.node_radius = node_radius
        self.text_height = text_height
        
    def export_from_scene(
        self,
        scene,  # NetworkScene
        filepath: str,
        include_labels: bool = True,
        include_equipment: bool = True,
    ) -> None:
        """Export pipe network from UI scene to DXF file.
        
        Creates a DXF file with the network geometry organized in layers.
        Nodes are represented as circles, pipes as lines.
        
        Args:
            scene: NetworkScene object with nodes and pipes
            filepath: Output DXF file path
            include_labels: Whether to include text labels (default: True)
            include_equipment: Whether to include pump/valve symbols (default: True)
            
        Raises:
            ValueError: If scene is empty
            IOError: If file cannot be written
            
        Example:
            >>> exporter = DXFExporter(node_radius=1.0, text_height=0.5)
            >>> exporter.export_from_scene(scene, "output.dxf", include_labels=True)
        """
        if not scene.nodes:
            raise ValueError("Cannot export empty scene")
        
        logger.info(f"Exporting network to DXF: {filepath}")
        
        # Create new DXF document (R2010 format for compatibility)
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        
        # Create layers
        self._create_layers(doc)
        
        # Export nodes
        self._export_nodes_from_scene(scene.nodes, msp, include_labels)
        
        # Export pipes
        self._export_pipes_from_scene(scene.pipes, msp, include_labels)
        
        # Export equipment if requested
        if include_equipment:
            self._export_equipment_from_scene(scene.nodes, msp, include_labels)
        
        # Save document
        doc.saveas(filepath)
        logger.info(f"Successfully exported {len(scene.nodes)} nodes and {len(scene.pipes)} pipes")
        
    def _create_layers(self, doc):
        """Create layers with configured colors."""
        for layer_name, color in self.layer_config.items():
            doc.layers.add(layer_name, color=color)
            
    def _export_nodes_from_scene(self, node_items: List, msp, include_labels: bool):
        """Export nodes from scene items as circles."""
        for node_item in node_items:
            # Get node position from scene
            pos = node_item.scenePos()
            x, y = pos.x(), pos.y()
            
            # Determine layer based on node type
            if node_item.is_source:
                layer = "SOURCES"
            elif node_item.is_sink:
                layer = "SINKS"
            else:
                layer = "NODES"
            
            # Draw circle for node
            msp.add_circle(
                center=(x, y),
                radius=self.node_radius,
                dxfattribs={"layer": layer}
            )
            
            # Add label if requested
            if include_labels:
                label_text = node_item.node_id
                if node_item.pressure is not None:
                    label_text += f"\nP={node_item.pressure/1e5:.2f} bar"
                
                msp.add_text(
                    label_text,
                    dxfattribs={
                        "layer": "LABELS",
                        "height": self.text_height,
                    }
                ).set_placement((x, y + self.node_radius * 1.5))
                
    def _export_pipes_from_scene(self, pipe_items: List, msp, include_labels: bool):
        """Export pipes from scene items as lines."""
        for pipe_item in pipe_items:
            # Get start and end node positions
            start_node = pipe_item.node1
            end_node = pipe_item.node2
            
            if not start_node or not end_node:
                logger.warning(f"Skipping pipe {pipe_item.pipe_id}: missing nodes")
                continue
            
            start_pos = start_node.scenePos()
            end_pos = end_node.scenePos()
            x1, y1 = start_pos.x(), start_pos.y()
            x2, y2 = end_pos.x(), end_pos.y()
            
            # Draw line for pipe
            msp.add_line(
                start=(x1, y1),
                end=(x2, y2),
                dxfattribs={"layer": "PIPES"}
            )
            
            # Add label if requested
            if include_labels:
                # Calculate midpoint
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                
                label_text = pipe_item.pipe_id
                if hasattr(pipe_item, 'diameter') and pipe_item.diameter:
                    label_text += f"\nD={pipe_item.diameter*1000:.1f}mm"
                if hasattr(pipe_item, 'flow_rate') and pipe_item.flow_rate is not None:
                    label_text += f"\nQ={pipe_item.flow_rate*1000:.2f} L/s"
                
                msp.add_text(
                    label_text,
                    dxfattribs={
                        "layer": "LABELS",
                        "height": self.text_height * 0.8,
                    }
                ).set_placement((mx, my))
                
    def _export_equipment_from_scene(self, node_items: List, msp, include_labels: bool):
        """Export pumps and valves as symbols."""
        for node_item in node_items:
            pos = node_item.scenePos()
            x, y = pos.x(), pos.y()
            
            # Export pump symbol
            if node_item.is_pump:
                self._draw_pump_symbol(msp, x, y, node_item.node_id, include_labels)
            
            # Export valve symbol
            if node_item.is_valve:
                self._draw_valve_symbol(msp, x, y, node_item.node_id, include_labels)
                
    def _draw_pump_symbol(self, msp, x: float, y: float, node_id: str, include_labels: bool):
        """Draw a simple pump symbol (triangle)."""
        size = self.node_radius * 1.5
        
        # Triangle pointing right
        points = [
            (x - size, y - size),
            (x - size, y + size),
            (x + size, y),
            (x - size, y - size),  # Close the triangle
        ]
        
        msp.add_lwpolyline(
            points,
            dxfattribs={"layer": "EQUIPMENT"}
        )
        
        if include_labels:
            msp.add_text(
                "PUMP",
                dxfattribs={
                    "layer": "LABELS",
                    "height": self.text_height * 0.7,
                }
            ).set_placement((x, y - size * 1.8))
            
    def _draw_valve_symbol(self, msp, x: float, y: float, node_id: str, include_labels: bool):
        """Draw a simple valve symbol (bow-tie)."""
        size = self.node_radius * 1.2
        
        # Bow-tie shape
        msp.add_line(
            start=(x - size, y - size),
            end=(x + size, y + size),
            dxfattribs={"layer": "EQUIPMENT"}
        )
        msp.add_line(
            start=(x - size, y + size),
            end=(x + size, y - size),
            dxfattribs={"layer": "EQUIPMENT"}
        )
        
        if include_labels:
            msp.add_text(
                "VALVE",
                dxfattribs={
                    "layer": "LABELS",
                    "height": self.text_height * 0.7,
                }
            ).set_placement((x, y - size * 1.8))


class DWGExporter:
    """Export pipe networks to AutoCAD DWG format (future implementation).
    
    Note:
        DWG export requires additional libraries and is not yet implemented.
        Use DXFExporter for now, as DXF can be imported into AutoCAD and
        converted to DWG.
    """
    
    def __init__(self):
        """Initialize DWG exporter (not yet implemented)."""
        raise NotImplementedError(
            "DWG export is not yet implemented. "
            "Please use DXFExporter and convert to DWG in AutoCAD."
        )
