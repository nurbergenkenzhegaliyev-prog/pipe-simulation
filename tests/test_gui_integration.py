"""GUI Integration Tests for PyQt6 Application"""

import pytest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtTest import QTest

from app.ui.windows.main_window import MainWindow
from app.ui.tooling.tool_types import Tool


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - let pytest handle cleanup


@pytest.fixture
def main_window(qapp):
    """Create MainWindow instance for each test"""
    window = MainWindow()
    window.show()
    QTest.qWait(100)  # Wait for window to render
    yield window
    window.close()


class TestMainWindowInitialization:
    """Test main window initialization and basic functionality"""
    
    def test_window_creation(self, main_window):
        """Test that main window is created successfully"""
        assert main_window is not None
        assert main_window.isVisible()
        assert main_window.windowTitle() == "My Pipesim-like App"
    
    def test_initial_components_exist(self, main_window):
        """Test that all major components are initialized"""
        assert main_window.top_tabs is not None
        assert main_window.left_panel is not None
        assert main_window.workspace is not None
        assert main_window.scene is not None
        assert main_window.controller is not None
        assert main_window.results_view is not None
    
    def test_initial_scene_empty(self, main_window):
        """Test that scene starts empty"""
        assert len(main_window.scene.nodes) == 0
        assert len(main_window.scene.pipes) == 0


class TestToolSelection:
    """Test tool selection and switching"""
    
    def test_default_tool_is_select(self, main_window):
        """Test that default tool is SELECT"""
        assert main_window.scene.current_tool == Tool.SELECT
    
    def test_tool_switching(self, main_window):
        """Test switching between tools"""
        main_window.scene.set_tool(Tool.NODE)
        assert main_window.scene.current_tool == Tool.NODE
        
        main_window.scene.set_tool(Tool.PIPE)
        assert main_window.scene.current_tool == Tool.PIPE
        
        main_window.scene.set_tool(Tool.SOURCE)
        assert main_window.scene.current_tool == Tool.SOURCE


class TestNodeCreation:
    """Test node creation workflow"""
    
    def test_create_node_programmatically(self, main_window):
        """Test creating a node programmatically"""
        initial_count = len(main_window.scene.nodes)
        
        pos = QPointF(0, 0)
        main_window.scene._node_ops.add_node(pos, "TestNode1")
        
        assert len(main_window.scene.nodes) == initial_count + 1
        assert main_window.scene.nodes[-1].node_id == "TestNode1"
    
    def test_create_source_node(self, main_window):
        """Test creating a source node"""
        pos = QPointF(100, 100)
        main_window.scene._node_ops.add_source(pos, "Source1")
        
        source_node = main_window.scene.nodes[-1]
        assert source_node.is_source is True
        assert source_node.node_id == "Source1"
    
    def test_create_sink_node(self, main_window):
        """Test creating a sink node"""
        pos = QPointF(200, 200)
        main_window.scene._node_ops.add_sink(pos, "Sink1")
        
        sink_node = main_window.scene.nodes[-1]
        assert sink_node.is_sink is True
        assert sink_node.node_id == "Sink1"


class TestPipeCreation:
    """Test pipe creation workflow"""
    
    def test_create_pipe_between_nodes(self, main_window):
        """Test creating a pipe connecting two nodes"""
        # Create two nodes
        node1_pos = QPointF(0, 0)
        node2_pos = QPointF(100, 100)
        
        main_window.scene._node_ops.add_node(node1_pos, "N1")
        main_window.scene._node_ops.add_node(node2_pos, "N2")
        
        node1 = main_window.scene.nodes[-2]
        node2 = main_window.scene.nodes[-1]
        
        # Create pipe
        initial_pipe_count = len(main_window.scene.pipes)
        main_window.scene._pipe_ops.add_pipe(node1, node2, "P1")
        
        assert len(main_window.scene.pipes) == initial_pipe_count + 1
        assert main_window.scene.pipes[-1].pipe_id == "P1"
        assert main_window.scene.pipes[-1].node1 == node1
        assert main_window.scene.pipes[-1].node2 == node2


class TestNetworkBuilding:
    """Test building a complete network"""
    
    def test_build_simple_network(self, main_window):
        """Test building a simple 3-node network"""
        # Create source
        main_window.scene._node_ops.add_source(QPointF(0, 0), "Source")
        source = main_window.scene.nodes[-1]
        source.pressure = 1_000_000.0  # 10 bar
        
        # Create junction
        main_window.scene._node_ops.add_node(QPointF(100, 0), "Junction")
        junction = main_window.scene.nodes[-1]
        
        # Create sink
        main_window.scene._node_ops.add_sink(QPointF(200, 0), "Sink")
        sink = main_window.scene.nodes[-1]
        sink.flow_rate = 0.05
        
        # Connect with pipes
        main_window.scene._pipe_ops.add_pipe(source, junction, "Pipe1")
        main_window.scene._pipe_ops.add_pipe(junction, sink, "Pipe2")
        
        assert len(main_window.scene.nodes) == 3
        assert len(main_window.scene.pipes) == 2
        
        # Verify network connectivity
        network = main_window.controller.build_network_from_scene()
        assert len(network.nodes) == 3
        assert len(network.pipes) == 2


class TestSimulationWorkflow:
    """Test simulation execution workflow"""
    
    def test_run_simulation_on_simple_network(self, main_window):
        """Test running simulation on a simple network"""
        # Build network
        main_window.scene._node_ops.add_source(QPointF(0, 0), "S1")
        source = main_window.scene.nodes[-1]
        source.pressure = 1_000_000.0
        
        main_window.scene._node_ops.add_sink(QPointF(100, 0), "Sink1")
        sink = main_window.scene.nodes[-1]
        sink.flow_rate = 0.05
        
        main_window.scene._pipe_ops.add_pipe(source, sink, "P1")
        pipe = main_window.scene.pipes[-1]
        pipe.length = 100.0
        pipe.diameter = 0.1
        pipe.flow_rate = 0.05
        
        # Run simulation
        network = main_window.controller.run_network_simulation()
        
        # Check results
        assert network is not None
        assert len(network.nodes) == 2
        assert network.nodes["Sink1"].pressure is not None


class TestUndoRedo:
    """Test undo/redo functionality"""
    
    def test_undo_node_creation(self, main_window):
        """Test undoing node creation"""
        initial_count = len(main_window.scene.nodes)
        
        # Create node
        pos = QPointF(50, 50)
        from app.ui.commands.scene_commands import AddNodeCommand
        cmd = AddNodeCommand(main_window.scene, pos)
        main_window.scene.command_manager.execute(cmd)
        
        assert len(main_window.scene.nodes) == initial_count + 1
        
        # Undo
        main_window.scene.command_manager.undo()
        assert len(main_window.scene.nodes) == initial_count
    
    def test_redo_node_creation(self, main_window):
        """Test redoing node creation"""
        initial_count = len(main_window.scene.nodes)
        
        # Create and undo
        pos = QPointF(50, 50)
        from app.ui.commands.scene_commands import AddNodeCommand
        cmd = AddNodeCommand(main_window.scene, pos)
        main_window.scene.command_manager.execute(cmd)
        main_window.scene.command_manager.undo()
        
        # Redo
        main_window.scene.command_manager.redo()
        assert len(main_window.scene.nodes) == initial_count + 1


class TestValidation:
    """Test real-time validation"""
    
    def test_validation_detects_missing_source(self, main_window):
        """Test that validation detects missing source nodes"""
        # Create only a sink
        main_window.scene._node_ops.add_sink(QPointF(0, 0), "Sink1")
        sink = main_window.scene.nodes[-1]
        sink.flow_rate = 0.05
        
        # Trigger validation
        issues = main_window.scene.validator.validate(main_window.scene)
        
        # Should have at least one error about missing source
        error_messages = [issue.message for issue in issues]
        assert any("source" in msg.lower() for msg in error_messages)
    
    def test_validation_passes_for_valid_network(self, main_window):
        """Test that validation passes for a valid network"""
        # Build valid network
        main_window.scene._node_ops.add_source(QPointF(0, 0), "Source1")
        source = main_window.scene.nodes[-1]
        source.pressure = 1_000_000.0
        
        main_window.scene._node_ops.add_sink(QPointF(100, 0), "Sink1")
        sink = main_window.scene.nodes[-1]
        sink.flow_rate = 0.05
        
        main_window.scene._pipe_ops.add_pipe(source, sink, "Pipe1")
        
        # Trigger validation
        issues = main_window.scene.validator.validate(main_window.scene)
        
        # Should have no critical errors
        errors = [i for i in issues if hasattr(i, 'level') and i.level.name == 'ERROR']
        assert len(errors) == 0


class TestResultsView:
    """Test results view functionality"""
    
    def test_results_view_updates(self, main_window):
        """Test that results view updates after simulation"""
        # Build and run simulation
        main_window.scene._node_ops.add_source(QPointF(0, 0), "S1")
        source = main_window.scene.nodes[-1]
        source.pressure = 1_000_000.0
        
        main_window.scene._node_ops.add_sink(QPointF(100, 0), "Sink1")
        sink = main_window.scene.nodes[-1]
        sink.flow_rate = 0.05
        
        main_window.scene._pipe_ops.add_pipe(source, sink, "P1")
        
        network = main_window.controller.run_network_simulation()
        main_window.results_view.update_results(network, main_window.current_fluid)
        
        # Verify results view has network
        assert main_window.results_view._network is not None
        assert main_window.results_view._fluid is not None


class TestEscapeKeyFunctionality:
    """Test Escape key functionality for tool switching"""
    
    def test_escape_key_switches_to_select_tool(self, main_window):
        """Test that pressing Escape key switches to SELECT tool"""
        from PyQt6.QtGui import QKeyEvent
        
        # Start with SOURCE tool
        main_window.scene.set_tool(Tool.SOURCE)
        assert main_window.scene.current_tool == Tool.SOURCE
        
        # Create and send Escape key press event
        escape_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        main_window.scene.keyPressEvent(escape_event)
        
        # Check that tool changed to SELECT
        assert main_window.scene.current_tool == Tool.SELECT
    
    def test_escape_key_from_pipe_tool(self, main_window):
        """Test Escape key switches from PIPE tool to SELECT"""
        from PyQt6.QtGui import QKeyEvent
        
        main_window.scene.set_tool(Tool.PIPE)
        assert main_window.scene.current_tool == Tool.PIPE
        
        escape_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        main_window.scene.keyPressEvent(escape_event)
        
        assert main_window.scene.current_tool == Tool.SELECT
    
    def test_escape_key_resets_pipe_drawing_state(self, main_window):
        """Test that Escape key also resets pipe drawing state"""
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QPointF
        
        # Create a source node for pipe starting
        main_window.scene._node_ops.add_source(QPointF(0, 0), "Source1")
        source_node = main_window.scene.nodes[-1]
        
        # Set PIPE tool and simulate starting a pipe
        main_window.scene.set_tool(Tool.PIPE)
        main_window.scene._pipe_start_node = source_node
        assert main_window.scene._pipe_start_node is not None
        
        # Send Escape key
        escape_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        main_window.scene.keyPressEvent(escape_event)
        
        # Check that pipe state is reset and tool switched
        assert main_window.scene._pipe_start_node is None
        assert main_window.scene.current_tool == Tool.SELECT
    
    def test_tool_changed_signal_emitted_on_escape(self, main_window):
        """Test that tool_changed signal is emitted when Escape is pressed"""
        from PyQt6.QtGui import QKeyEvent
        
        signal_emitted = []
        main_window.scene.tool_changed.connect(lambda tool: signal_emitted.append(tool))
        
        # Start with NODE tool
        main_window.scene.set_tool(Tool.NODE)
        signal_emitted.clear()  # Clear the signal from set_tool
        
        # Send Escape key
        escape_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        main_window.scene.keyPressEvent(escape_event)
        
        # Check that signal was emitted with SELECT tool
        assert len(signal_emitted) > 0
        assert signal_emitted[-1] == Tool.SELECT


