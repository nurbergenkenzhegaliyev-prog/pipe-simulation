"""Real-time validation service for network integrity"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Severity level of validation issues"""
    ERROR = "error"      # Critical - prevents simulation
    WARNING = "warning"  # Should fix but might work
    INFO = "info"        # Informational


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: ValidationLevel
    message: str
    item_id: Optional[str] = None  # Node or pipe ID
    item_type: Optional[str] = None  # "node", "pipe", "network"


class RealtimeNetworkValidator:
    """Validates network in real-time as user builds"""
    
    def __init__(self):
        self._issues: List[ValidationIssue] = []
        self._problematic_items: Dict[str, ValidationLevel] = {}  # item_id -> level
    
    def validate(self, scene) -> List[ValidationIssue]:
        """Validate the current scene state"""
        self._issues.clear()
        self._problematic_items.clear()
        
        # Check nodes
        self._validate_nodes(scene)
        
        # Check pipes
        self._validate_pipes(scene)
        
        # Check network connectivity
        self._validate_network(scene)
        
        return self._issues
    
    def _validate_nodes(self, scene) -> None:
        """Validate individual nodes"""
        sources = [n for n in scene.nodes if getattr(n, "is_source", False)]
        sinks = [n for n in scene.nodes if getattr(n, "is_sink", False)]
        
        # Check for at least one source
        if not sources:
            self._issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Network requires at least one source",
                item_type="network"
            ))
        
        # Validate sources
        for node in sources:
            pressure = getattr(node, "pressure", None)
            flow_rate = getattr(node, "flow_rate", None)
            
            if pressure is None and flow_rate is None:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Source '{node.node_id}' needs pressure or flow rate",
                    item_id=node.node_id,
                    item_type="node"
                ))
                self._problematic_items[node.node_id] = ValidationLevel.ERROR
            elif pressure is not None and pressure < 0:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Source '{node.node_id}' pressure cannot be negative",
                    item_id=node.node_id,
                    item_type="node"
                ))
                self._problematic_items[node.node_id] = ValidationLevel.ERROR
            elif flow_rate is not None and flow_rate < 0:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Source '{node.node_id}' flow rate cannot be negative",
                    item_id=node.node_id,
                    item_type="node"
                ))
                self._problematic_items[node.node_id] = ValidationLevel.ERROR
        
        # Validate sinks
        for node in sinks:
            flow_rate = getattr(node, "flow_rate", None)
            
            if flow_rate is None or flow_rate <= 0:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Sink '{node.node_id}' requires flow rate > 0",
                    item_id=node.node_id,
                    item_type="node"
                ))
                self._problematic_items[node.node_id] = ValidationLevel.ERROR
    
    def _validate_pipes(self, scene) -> None:
        """Validate pipes"""
        for pipe in scene.pipes:
            issues = []
            
            # Check length
            if pipe.length <= 0:
                issues.append(f"length must be > 0")
            
            # Check diameter
            if pipe.diameter <= 0:
                issues.append(f"diameter must be > 0")
            
            # Check roughness
            if pipe.roughness < 0:
                issues.append(f"roughness cannot be negative")
            
            if issues:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Pipe '{pipe.pipe_id}': {', '.join(issues)}",
                    item_id=pipe.pipe_id,
                    item_type="pipe"
                ))
                self._problematic_items[pipe.pipe_id] = ValidationLevel.ERROR
    
    def _validate_network(self, scene) -> None:
        """Validate network connectivity and structure"""
        if not scene.nodes or not scene.pipes:
            return
        
        # Check for isolated nodes (nodes with no connected pipes)
        for node in scene.nodes:
            if getattr(node, "is_pump", False) or getattr(node, "is_valve", False):
                continue  # Equipment doesn't need connections for warning
            
            pipes = getattr(node, "pipes", [])
            if not pipes and not (getattr(node, "is_source", False) or getattr(node, "is_sink", False)):
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Node '{node.node_id}' is isolated (not connected to any pipes)",
                    item_id=node.node_id,
                    item_type="node"
                ))
                self._problematic_items[node.node_id] = ValidationLevel.WARNING
            
            # Check sink pipe limit: sinks can only have 1 pipe connected
            if getattr(node, "is_sink", False):
                if pipes and len(pipes) > 1:
                    self._issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Sink '{node.node_id}' cannot have more than 1 pipe connected (found {len(pipes)})",
                        item_id=node.node_id,
                        item_type="node"
                    ))
                    self._problematic_items[node.node_id] = ValidationLevel.ERROR
        
        # Check for pipe parameter combinations
        for pipe in scene.pipes:
            # Check if pipe connects two different nodes
            if pipe.node1 == pipe.node2:
                self._issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Pipe '{pipe.pipe_id}' connects the same node to itself",
                    item_id=pipe.pipe_id,
                    item_type="pipe"
                ))
                self._problematic_items[pipe.pipe_id] = ValidationLevel.ERROR
    
    def get_problematic_items(self) -> Dict[str, ValidationLevel]:
        """Get dict of item IDs and their validation levels"""
        return self._problematic_items
    
    def get_errors_only(self) -> List[ValidationIssue]:
        """Get only error-level issues"""
        return [i for i in self._issues if i.level == ValidationLevel.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues"""
        return [i for i in self._issues if i.level == ValidationLevel.WARNING]
    
    def is_valid_for_simulation(self) -> bool:
        """Check if network is ready for simulation"""
        return len(self.get_errors_only()) == 0
