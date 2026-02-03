import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QStatusBar, QMessageBox, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from app.ui.tooling.tool_types import Tool
from app.models.fluid import Fluid
from app.controllers.main_controller import MainController
from app.ui.views import TopTabsWidget, LeftPanelWidget, WorkspaceWidget, ResultsView
from app.ui.dialogs import FluidPropertiesDialog
from app.ui.windows.main_window_components import ResultsDialogManager, SceneSerializer, SceneValidator
from app.services.pressure_drop_service import PressureDropService
from app.services.pipe_point_analyzer import PipePointAnalyzer
from app.ui.visualization.network_visualizer import NetworkVisualizer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Pipesim-like App")
        self.resize(1400, 800)

        # Initialize default fluid (single-phase water) BEFORE creating layout
        self.current_fluid = Fluid()
        
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
        self.top_tabs.fluid_settings_clicked.connect(self._show_fluid_settings)

        self.results_view = ResultsView()
        self._results_manager = ResultsDialogManager(self, self.results_view)
        self._serializer = SceneSerializer()
        self._validator = SceneValidator()
        
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

    def _on_tool_changed(self, tool):
        self.scene.set_tool(tool)
        self.statusBar().showMessage(f"Tool: {tool.name}")

    def _on_run_clicked(self):
        if not self._validate_scene():
            return
        try:
            network = self.controller.run_network_simulation()
            self.scene.apply_results(network)
            self.results_view.update_results(network)
            
            # Apply color overlays
            NetworkVisualizer.apply_pressure_overlay(self.scene, network)
            NetworkVisualizer.apply_flow_overlay(self.scene, network)
            
            self.statusBar().showMessage("Simulation complete. Network colored by pressure and flow.", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Simulation failed", str(exc))

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
