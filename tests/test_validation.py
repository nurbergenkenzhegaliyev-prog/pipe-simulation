"""
Tests for network validation system.

This module tests the real-time validation service that checks
network integrity, node properties, and pipe configurations.
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF

# Initialize QApplication for GUI testing
app = QApplication.instance()
if app is None:
    app = QApplication([])


class MockScene:
    """Mock graphics scene for validation testing."""
    def __init__(self):
        self.nodes = []
        self.pipes = []


class TestValidationLevelsAndIssues:
    """Test ValidationLevel enum and ValidationIssue dataclass."""

    def test_validation_level_enum(self):
        """Test ValidationLevel enum values."""
        from app.ui.validation.realtime_validator import ValidationLevel
        
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"

    def test_validation_issue_creation(self):
        """Test creating a validation issue."""
        from app.ui.validation.realtime_validator import ValidationIssue, ValidationLevel
        
        issue = ValidationIssue(
            level=ValidationLevel.ERROR,
            message="Test error",
            item_id="node_1",
            item_type="node"
        )
        
        assert issue.level == ValidationLevel.ERROR
        assert issue.message == "Test error"
        assert issue.item_id == "node_1"
        assert issue.item_type == "node"

    def test_validation_issue_without_item(self):
        """Test validation issue can be created without item reference."""
        from app.ui.validation.realtime_validator import ValidationIssue, ValidationLevel
        
        issue = ValidationIssue(
            level=ValidationLevel.INFO,
            message="General info"
        )
        
        assert issue.item_id is None
        assert issue.item_type is None


class TestValidatorBasics:
    """Test basic validator initialization and methods."""

    def test_validator_creation(self):
        """Test creating a validator instance."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        
        validator = RealtimeNetworkValidator()
        assert validator is not None

    def test_validator_empty_scene(self):
        """Test validating an empty scene."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        issues = validator.validate(scene)
        # Should at least report missing source
        assert any("source" in issue.message.lower() for issue in issues)

    def test_validator_clears_previous_issues(self):
        """Test validator clears issues from previous validation."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        # First validation - empty
        issues1 = validator.validate(scene)
        count1 = len(issues1)
        
        # Add a node and revalidate
        node = NodeItem(QPointF(0, 0), "node_1")
        scene.nodes.append(node)
        issues2 = validator.validate(scene)
        
        # Issues should be recalculated, not accumulated
        assert len(issues2) >= 1  # Still missing source


class TestSourceNodeValidation:
    """Test validation of source nodes."""

    def test_no_source_is_error(self):
        """Test network without source generates error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator, ValidationLevel
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        scene.nodes.append(NodeItem(QPointF(0, 0), "node_1"))
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("source" in e.message.lower() for e in errors)

    def test_source_without_pressure_or_flow_is_error(self):
        """Test source without pressure or flow rate is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator, ValidationLevel
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = None
        source.flow_rate = None
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("source_1" in e.message and ("pressure" in e.message.lower() or "flow" in e.message.lower()) for e in errors)

    def test_source_with_negative_pressure_is_error(self):
        """Test source with negative pressure is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = -1000.0
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("negative" in e.message.lower() and "source_1" in e.message for e in errors)

    def test_source_with_negative_flow_is_error(self):
        """Test source with negative flow rate is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.flow_rate = -0.01
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("negative" in e.message.lower() and "source_1" in e.message for e in errors)

    def test_source_with_valid_pressure(self):
        """Test source with valid pressure passes validation."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        # Should not have errors about source_1
        assert not any("source_1" in e.message and e.level.value == "error" for e in errors)

    def test_source_with_valid_flow_rate(self):
        """Test source with valid flow rate passes validation."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.flow_rate = 0.01
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        # Should not have errors about source_1's properties
        assert not any("source_1" in e.message and ("pressure" in e.message.lower() or "flow" in e.message.lower()) for e in errors)


class TestSinkNodeValidation:
    """Test validation of sink nodes."""

    def test_sink_without_flow_rate_is_error(self):
        """Test sink without flow rate is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        # Add source first
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = None
        scene.nodes.append(sink)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("sink_1" in e.message and "flow rate" in e.message.lower() for e in errors)

    def test_sink_with_zero_flow_rate_is_error(self):
        """Test sink with zero flow rate is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.0
        scene.nodes.append(sink)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("sink_1" in e.message and "flow rate" in e.message.lower() for e in errors)

    def test_sink_with_valid_flow_rate(self):
        """Test sink with valid flow rate passes validation."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        # Add pipe
        pipe = PipeItem(source, sink, "pipe_1")
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        # Should not have errors about sink_1's flow rate
        assert not any("sink_1" in e.message and "flow rate" in e.message.lower() for e in errors)

    def test_sink_with_multiple_pipes_is_error(self):
        """Test sink with multiple pipes connected is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        junction = NodeItem(QPointF(50, 0), "junction_1")
        scene.nodes.append(junction)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        # Connect two pipes to sink
        pipe1 = PipeItem(source, sink, "pipe_1")
        pipe2 = PipeItem(junction, sink, "pipe_2")
        scene.pipes.extend([pipe1, pipe2])
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        # Sink should have error about multiple pipes
        assert any("sink_1" in e.message and "more than 1 pipe" in e.message.lower() for e in errors)


class TestPipeValidation:
    """Test validation of pipe properties."""

    def test_pipe_with_zero_length_is_error(self):
        """Test pipe with zero length is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        pipe = PipeItem(source, sink, "pipe_1")
        pipe.length = 0.0
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("pipe_1" in e.message and "length" in e.message.lower() for e in errors)

    def test_pipe_with_negative_length_is_error(self):
        """Test pipe with negative length is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        pipe = PipeItem(source, sink, "pipe_1")
        pipe.length = -10.0
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("pipe_1" in e.message and "length" in e.message.lower() for e in errors)

    def test_pipe_with_zero_diameter_is_error(self):
        """Test pipe with zero diameter is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        pipe = PipeItem(source, sink, "pipe_1")
        pipe.diameter = 0.0
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("pipe_1" in e.message and "diameter" in e.message.lower() for e in errors)

    def test_pipe_with_negative_roughness_is_error(self):
        """Test pipe with negative roughness is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        pipe = PipeItem(source, sink, "pipe_1")
        pipe.roughness = -0.001
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("pipe_1" in e.message and "roughness" in e.message.lower() for e in errors)

    def test_pipe_connecting_same_node_is_error(self):
        """Test pipe connecting node to itself is error."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        # Pipe connecting source to itself
        pipe = PipeItem(source, source, "pipe_1")
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert any("pipe_1" in e.message and "same node" in e.message.lower() for e in errors)


class TestNetworkConnectivity:
    """Test validation of network connectivity."""

    def test_isolated_junction_is_warning(self):
        """Test isolated junction node generates warning."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        # Isolated junction
        junction = NodeItem(QPointF(50, 50), "junction_1")
        scene.nodes.append(junction)
        
        pipe = PipeItem(source, sink, "pipe_1")
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        warnings = validator.get_warnings()
        
        assert any("junction_1" in w.message and "isolated" in w.message.lower() for w in warnings)


class TestValidatorUtilityMethods:
    """Test validator utility methods."""

    def test_get_errors_only(self):
        """Test get_errors_only() returns only error-level issues."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator, ValidationLevel
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        # This will generate errors
        scene.nodes.append(NodeItem(QPointF(0, 0), "node_1"))
        
        issues = validator.validate(scene)
        errors = validator.get_errors_only()
        
        assert all(e.level == ValidationLevel.ERROR for e in errors)

    def test_get_warnings(self):
        """Test get_warnings() returns warning-level issues."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator, ValidationLevel
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        # Isolated junction generates warning
        junction = NodeItem(QPointF(50, 50), "junction_1")
        scene.nodes.append(junction)
        
        issues = validator.validate(scene)
        warnings = validator.get_warnings()
        
        assert all(w.level == ValidationLevel.WARNING for w in warnings)

    def test_is_valid_for_simulation_with_errors(self):
        """Test is_valid_for_simulation() returns False with errors."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        # Empty scene has errors (no source)
        issues = validator.validate(scene)
        
        assert validator.is_valid_for_simulation() is False

    def test_is_valid_for_simulation_without_errors(self):
        """Test is_valid_for_simulation() returns True without errors."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem, PipeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = 101325.0
        scene.nodes.append(source)
        
        sink = NodeItem(QPointF(100, 0), "sink_1")
        sink.is_sink = True
        sink.flow_rate = 0.01
        scene.nodes.append(sink)
        
        pipe = PipeItem(source, sink, "pipe_1")
        scene.pipes.append(pipe)
        
        issues = validator.validate(scene)
        
        # May have warnings but no errors
        assert validator.is_valid_for_simulation() is True

    def test_get_problematic_items(self):
        """Test get_problematic_items() returns dict of item IDs."""
        from app.ui.validation.realtime_validator import RealtimeNetworkValidator
        from app.ui.items.network_items import NodeItem
        
        validator = RealtimeNetworkValidator()
        scene = MockScene()
        
        source = NodeItem(QPointF(0, 0), "source_1")
        source.is_source = True
        source.pressure = -1000.0  # Error
        scene.nodes.append(source)
        
        issues = validator.validate(scene)
        problematic = validator.get_problematic_items()
        
        assert "source_1" in problematic
        assert problematic["source_1"].value == "error"
