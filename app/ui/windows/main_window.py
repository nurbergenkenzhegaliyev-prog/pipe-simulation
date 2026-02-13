import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStatusBar, QMessageBox, QDialog, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor

from app.ui.tooling.tool_types import Tool
from app.models.fluid import Fluid
from app.controllers.main_controller import MainController
from app.ui.views import TopTabsWidget, LeftPanelWidget, WorkspaceWidget, ResultsView
from app.ui.dialogs import FluidPropertiesDialog
from app.ui.windows.main_window_components import ResultsDialogManager, SceneSerializer, SceneValidator
from app.services.pressure import PressureDropService
from app.services.analysis import PipePointAnalyzer
from app.ui.visualization.network_visualizer import NetworkVisualizer
from app.services.solvers import SolverMethod


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Pipesim-like App")
        self.resize(1400, 800)

        # Initialize default fluid (single-phase water) BEFORE creating layout
        self.current_fluid = Fluid()
        
        # Initialize default solver method (Newton-Raphson)
        self.solver_method = SolverMethod.NEWTON_RAPHSON
        
        self.top_tabs = TopTabsWidget(self)
        self.setMenuWidget(self.top_tabs)

        self._create_central_layout()
        self._create_statusbar()
        self._create_shortcuts()

        self.top_tabs.tool_changed.connect(self._on_tool_changed)
        self.top_tabs.run_clicked.connect(self._on_run_clicked)
        self.top_tabs.results_clicked.connect(self._show_results)
        self.top_tabs.open_clicked.connect(self._open_json)
        self.top_tabs.save_as_clicked.connect(self._save_as_json)
        self.top_tabs.import_clicked.connect(self._open_json)
        self.top_tabs.import_epanet_clicked.connect(self._import_epanet)
        self.top_tabs.fluid_settings_clicked.connect(self._show_fluid_settings)
        self.top_tabs.simulation_settings_clicked.connect(self._show_simulation_settings)
        self.top_tabs.transient_simulation_clicked.connect(self._show_transient_simulation)
        self.top_tabs.gis_clicked.connect(self._show_gis)

        self.results_view = ResultsView()
        self._results_manager = ResultsDialogManager(self, self.results_view)
        self._serializer = SceneSerializer()
        self._validator = SceneValidator()
        self._last_transient_config = None
        self._transient_log_dialog = None
        self._transient_log_view = None
        
        # Initialize pipe analyzer with current fluid
        pressure_service = PressureDropService(self.current_fluid)
        self._pipe_analyzer = PipePointAnalyzer(pressure_service)
        self.results_view.set_pipe_analyzer(self._pipe_analyzer)

    # ---------------- CENTRAL ----------------
    def _create_central_layout(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        self.left_panel = LeftPanelWidget()
        splitter.addWidget(self.left_panel)
        self.left_panel.setMinimumWidth(260)

        self.workspace = WorkspaceWidget()
        splitter.addWidget(self.workspace)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        self.scene = self.workspace.scene
        self.controller = MainController(self.scene)
        self.scene.nodes_changed.connect(lambda: self.left_panel.refresh_from_scene(self.scene))
        self.scene.validation_changed.connect(self._on_validation_changed)
        self.scene.tool_changed.connect(self._on_scene_tool_changed)
        self.left_panel.refresh_from_scene(self.scene)
        
        # Link fluid settings to scene so items can access it
        self.scene.current_fluid = self.current_fluid

    def _show_results(self):
        self._results_manager.show()

    def _show_fluid_settings(self):
        """Show the fluid properties dialog"""
        dialog = FluidPropertiesDialog(self.current_fluid, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_fluid = dialog.get_fluid()
            
            # Update status bar to show current mode
            mode = "Multi-Phase" if self.current_fluid.is_multiphase else "Single-Phase"
            self.statusBar().showMessage(f"Fluid settings updated: {mode} mode", 3000)
            
            # Update controller and scene with new fluid
            self.controller.set_fluid(self.current_fluid)
            self.scene.current_fluid = self.current_fluid
            
            # Update pipe analyzer with new fluid
            pressure_service = PressureDropService(self.current_fluid)
            self._pipe_analyzer = PipePointAnalyzer(pressure_service)
            self.results_view.set_pipe_analyzer(self._pipe_analyzer)
    
    def _show_simulation_settings(self):
        """Show the simulation settings dialog"""
        from app.ui.dialogs import SimulationSettingsDialog
        
        dialog = SimulationSettingsDialog(self.solver_method, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.solver_method = dialog.get_solver_method()
            
            # Update status bar
            method_name = "Newton-Raphson" if self.solver_method == SolverMethod.NEWTON_RAPHSON else "Hardy-Cross"
            self.statusBar().showMessage(f"Solver method changed to: {method_name}", 3000)
            
            # Update controller with new solver method
            self.controller.set_solver_method(self.solver_method)
    
    def _show_transient_simulation(self):
        """Show the transient simulation dialog and run transient analysis"""
        from app.ui.dialogs import TransientSimulationDialog
        from app.ui.visualization.transient_plotter import TransientPlotWidget
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        # Get available pipes and nodes from scene
        pipe_ids = [pipe.pipe_id for pipe in self.scene.pipes]
        node_ids = [node.node_id for node in self.scene.nodes]
        pump_ids = [node.node_id for node in self.scene.nodes if getattr(node, "is_pump", False)]
        
        # Show transient configuration dialog
        dialog = TransientSimulationDialog(
            available_pipes=pipe_ids,
            available_nodes=node_ids,
            available_pumps=pump_ids,
            initial_config=self._last_transient_config,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get configuration
        config = dialog.get_configuration()
        self._last_transient_config = config
        
        # Update controller with current fluid
        self.controller.set_fluid(self.current_fluid)
        
        # Run transient simulation
        self.statusBar().showMessage("Running transient simulation...", 0)
        try:
            shown_events = set()

            self._ensure_transient_log_window()
            self._clear_transient_log()
            self._transient_log_dialog.show()

            def on_event_applied(event, time_s, value):
                target = event.node_id or event.pipe_id or "unknown"
                key = (event.event_type, target)
                if key in shown_events:
                    return
                shown_events.add(key)
                self.statusBar().showMessage(
                    f"Transient event applied: {event.event_type} on {target} at t={time_s:.2f}s",
                    5000,
                )
                if event.event_type == "demand_change":
                    self._append_transient_log(
                        f"t={time_s:.2f}s demand_change target={target} value={value:.6g}\n"
                    )

            results = self.controller.run_transient_simulation(
                config,
                event_callback=on_event_applied,
            )
            self.statusBar().showMessage(
                f"Transient simulation complete: {len(results)} time steps", 3000
            )
            
            # Show results in plot widget
            results_dialog = QDialog(self)
            results_dialog.setWindowTitle("Transient Analysis Results")
            results_dialog.resize(1200, 700)
            
            layout = QVBoxLayout(results_dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            plot_widget = TransientPlotWidget()
            plot_widget.set_results(results)
            layout.addWidget(plot_widget)
            
            results_dialog.exec()
            
        except Exception as e:
            self.statusBar().showMessage(f"Transient simulation failed: {str(e)}", 5000)
            QMessageBox.critical(self, "Simulation Error", 
                               f"Transient simulation failed:\n{str(e)}")

    def _show_gis(self):
        self.workspace.show_gis_tab()

    def _serialize_scene(self):
        return self._serializer.serialize(self.scene)

    def _save_as_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path = f"{path}.json"
        data = self._serialize_scene()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def _open_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._load_from_json(data)
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))

    def _load_from_json(self, data):
        self._serializer.load(self.scene, data)
    
    def _import_epanet(self):
        """Import network from EPANET INP file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import EPANET File", "", "EPANET Files (*.inp);;All Files (*)"
        )
        if not path:
            return
        
        try:
            from app.services.parsers.epanet_parser import EPANETParser
            
            parser = EPANETParser()
            network = parser.parse_file(path)
            
            # Clear existing scene
            self.scene.clear_all()
            
            # Create nodes in scene
            import random
            node_positions = {}
            for i, (node_id, node) in enumerate(network.nodes.items()):
                # Simple grid layout for positioning
                x = (i % 10) * 150 - 500
                y = (i // 10) * 150 - 500
                pos = QPointF(x, y)
                node_positions[node_id] = pos
                
                # Add to scene based on type
                if node.is_source:
                    self.scene._node_ops.add_source(pos, node_id)
                    source_item = self.scene.nodes[-1]
                    if node.pressure is not None:
                        source_item.pressure = node.pressure
                elif node.is_sink:
                    self.scene._node_ops.add_sink(pos, node_id)
                    sink_item = self.scene.nodes[-1]
                    if node.flow_rate is not None:
                        sink_item.flow_rate = node.flow_rate
                else:
                    self.scene._node_ops.add_node(pos, node_id)
            
            # Create pipes in scene
            for pipe_id, pipe in network.pipes.items():
                # Find nodes in scene
                node1 = next((n for n in self.scene.nodes if n.node_id == pipe.start_node), None)
                node2 = next((n for n in self.scene.nodes if n.node_id == pipe.end_node), None)
                
                if node1 and node2:
                    self.scene._pipe_ops.add_pipe(node1, node2, pipe_id)
                    pipe_item = self.scene.pipes[-1]
                    pipe_item.length = pipe.length
                    pipe_item.diameter = pipe.diameter
                    pipe_item.roughness = pipe.roughness
                    pipe_item.flow_rate = pipe.flow_rate or 0.01
            
            # Update fluid settings to water
            from app.services.parsers.epanet_parser import EPANETParser
            self.current_fluid = EPANETParser.get_default_fluid()
            self.controller.set_fluid(self.current_fluid)
            self.scene.current_fluid = self.current_fluid
            
            self.statusBar().showMessage(
                f"Imported EPANET file: {len(network.nodes)} nodes, {len(network.pipes)} pipes",
                5000
            )
            
        except ImportError:
            QMessageBox.critical(
                self,
                "Import Failed",
                "EPANET parser module not found."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def _on_tool_changed(self, tool):
        self.scene.set_tool(tool)
        self.statusBar().showMessage(f"Tool: {tool.name}")

    def _on_scene_tool_changed(self, tool):
        """Handle tool changes from the scene (e.g., when Escape key is pressed)"""
        # Update the tool palette UI to reflect the new tool
        for action in self.top_tabs._tool_group.actions():
            if action.property("tool") == tool:
                action.setChecked(True)
                break
        self.statusBar().showMessage(f"Tool: {tool.name}")

    def _on_run_clicked(self):
        if not self._validate_scene():
            return
        try:
            network = self.controller.run_network_simulation()
            self.scene.apply_results(network)
            self.results_view.update_results(network, fluid=self.current_fluid, scene=self.scene)
            
            # Apply color overlays
            NetworkVisualizer.apply_pressure_overlay(self.scene, network)
            NetworkVisualizer.apply_flow_overlay(self.scene, network)
            
            self.statusBar().showMessage("Simulation complete. Network colored by pressure and flow.", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Simulation failed", str(exc))

    def _ensure_transient_log_window(self) -> None:
        if self._transient_log_dialog is not None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Transient Demand Change Log")
        dialog.resize(520, 300)

        layout = QVBoxLayout(dialog)
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        layout.addWidget(log_view)

        self._transient_log_dialog = dialog
        self._transient_log_view = log_view

    def _clear_transient_log(self) -> None:
        if self._transient_log_view is not None:
            self._transient_log_view.clear()

    def _append_transient_log(self, text: str) -> None:
        if self._transient_log_view is not None:
            self._transient_log_view.moveCursor(QTextCursor.MoveOperation.End)
            self._transient_log_view.insertPlainText(text)

    def _validate_scene(self) -> bool:
        issues = self._validator.validate(self.scene, self.current_fluid)
        if issues:
            QMessageBox.warning(self, "Validation issues", "\n".join(i.message for i in issues))
            return False
        return True

    # ---------------- STATUS BAR ----------------
    def _create_statusbar(self):
        status = QStatusBar()
        status.showMessage("Workspace ready.")
        self.setStatusBar(status)
    
    def _on_validation_changed(self, issues):
        """Update status bar with validation feedback"""
        if not issues:
            self.statusBar().showMessage("✓ Network ready for simulation", 5000)
            return
        
        # Count errors and warnings
        error_count = sum(1 for i in issues if hasattr(i, 'level') and i.level.name == 'ERROR')
        warning_count = sum(1 for i in issues if hasattr(i, 'level') and i.level.name == 'WARNING')
        
        message_parts = []
        if error_count > 0:
            message_parts.append(f"⚠ {error_count} error{'s' if error_count != 1 else ''}")
        if warning_count > 0:
            message_parts.append(f"⚠ {warning_count} warning{'s' if warning_count != 1 else ''}")
        
        message = " | ".join(message_parts) if message_parts else "Network has issues"
        self.statusBar().showMessage(message)
    
    
    # ---------------- SHORTCUTS ----------------
    def _create_shortcuts(self):
        """Create keyboard shortcuts for undo/redo"""
        # Undo: Ctrl+Z
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._undo)
        self.addAction(undo_action)
        
        # Redo: Ctrl+Y or Ctrl+Shift+Z
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._redo)
        self.addAction(redo_action)
    
    def _undo(self):
        """Undo the last action"""
        if self.scene.command_manager.can_undo():
            description = self.scene.command_manager.undo()
            if description:
                self.statusBar().showMessage(f"Undo: {description}", 3000)
        else:
            self.statusBar().showMessage("Nothing to undo", 2000)
    
    def _redo(self):
        """Redo the last undone action"""
        if self.scene.command_manager.can_redo():
            description = self.scene.command_manager.redo()
            if description:
                self.statusBar().showMessage(f"Redo: {description}", 3000)
        else:
            self.statusBar().showMessage("Nothing to redo", 2000)
