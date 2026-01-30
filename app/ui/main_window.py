import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QStatusBar, QMessageBox, QDialog, QFileDialog, QVBoxLayout
)
from PyQt6.QtCore import Qt, QPointF

from app.ui.tool_palette import Tool
from app.models.equipment import PumpCurve, Valve
from app.controllers.main_controller import MainController
from app.ui.components import TopTabsWidget, LeftPanelWidget, WorkspaceWidget, ResultsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Pipesim-like App")
        self.resize(1400, 800)

        self.top_tabs = TopTabsWidget(self)
        self.setMenuWidget(self.top_tabs)

        self._create_central_layout()
        self._create_statusbar()

        self.top_tabs.tool_changed.connect(self._on_tool_changed)
        self.top_tabs.run_clicked.connect(self._on_run_clicked)
        self.top_tabs.results_clicked.connect(self._show_results)
        self.top_tabs.open_clicked.connect(self._open_json)
        self.top_tabs.save_as_clicked.connect(self._save_as_json)
        self.top_tabs.import_clicked.connect(self._open_json)

        self.results_view = ResultsView()
        self.results_dialog = None

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

    def _show_results(self):
        if self.results_dialog is None:
            self.results_dialog = QDialog(self)
            self.results_dialog.setWindowTitle("Results")
            self.results_dialog.resize(800, 600)
            layout = QVBoxLayout(self.results_dialog)
            layout.addWidget(self.results_view)
        self.results_dialog.show()
        self.results_dialog.raise_()
        self.results_dialog.activateWindow()

    def _serialize_scene(self):
        nodes = []
        for node in getattr(self.scene, "nodes", []):
            pos = node.scenePos()
            nodes.append({
                "id": node.node_id,
                "x": pos.x(),
                "y": pos.y(),
                "is_source": bool(getattr(node, "is_source", False)),
                "is_sink": bool(getattr(node, "is_sink", False)),
                "is_pump": bool(getattr(node, "is_pump", False)),
                "is_valve": bool(getattr(node, "is_valve", False)),
                "pressure_ratio": getattr(node, "pressure_ratio", None),
                "valve_k": getattr(node, "valve_k", None),
                "pressure": getattr(node, "pressure", None),
            })

        pipes = []
        for pipe in getattr(self.scene, "pipes", []):
            pipes.append({
                "id": pipe.pipe_id,
                "start": pipe.node1.node_id,
                "end": pipe.node2.node_id,
                "length": getattr(pipe, "length", None),
                "diameter": getattr(pipe, "diameter", None),
                "roughness": getattr(pipe, "roughness", None),
                "flow_rate": getattr(pipe, "flow_rate", None),
                "pump_curve": (
                    {"a": pipe.pump_curve.a, "b": pipe.pump_curve.b, "c": pipe.pump_curve.c}
                    if getattr(pipe, "pump_curve", None) is not None
                    else None
                ),
                "valve_k": getattr(getattr(pipe, "valve", None), "k", None),
            })

        return {"version": 1, "nodes": nodes, "pipes": pipes}

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
        nodes = data.get("nodes", [])
        pipes = data.get("pipes", [])

        self.scene.clear_network()
        node_by_id = {}
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            pos = QPointF(float(node.get("x", 0.0)), float(node.get("y", 0.0)))
            item = self.scene.create_node_with_id(
                pos,
                node_id,
                is_source=bool(node.get("is_source", False)),
                is_sink=bool(node.get("is_sink", False)),
                pressure=node.get("pressure", None),
                is_pump=bool(node.get("is_pump", False)),
                is_valve=bool(node.get("is_valve", False)),
                pressure_ratio=node.get("pressure_ratio", None),
                valve_k=node.get("valve_k", None),
            )
            node_by_id[node_id] = item

        for pipe in pipes:
            pipe_id = pipe.get("id")
            start = pipe.get("start")
            end = pipe.get("end")
            if not pipe_id or start not in node_by_id or end not in node_by_id:
                continue
            pump_curve = pipe.get("pump_curve", None)
            valve_k = pipe.get("valve_k", None)
            created = self.scene.create_pipe_with_id(
                node_by_id[start],
                node_by_id[end],
                pipe_id,
                length=pipe.get("length", None),
                diameter=pipe.get("diameter", None),
                roughness=pipe.get("roughness", None),
                flow_rate=pipe.get("flow_rate", None),
            )
            if isinstance(pump_curve, dict):
                created.pump_curve = PumpCurve(
                    pump_curve.get("a", 0.0),
                    pump_curve.get("b", 0.0),
                    pump_curve.get("c", 0.0),
                )
            if valve_k is not None:
                created.valve = Valve(float(valve_k))
        self.scene.nodes_changed.emit()

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
            self.statusBar().showMessage("Simulation complete.", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Simulation failed", str(exc))

    def _validate_scene(self) -> bool:
        errors = []

        boundary_nodes = [n for n in self.scene.nodes if getattr(n, "pressure", None) is not None]
        if len(boundary_nodes) == 0:
            errors.append("Add at least one node with a pressure boundary.")

        for node in self.scene.nodes:
            if getattr(node, "is_source", False) and getattr(node, "pressure", None) is None:
                errors.append(f"{node.node_id}: source node needs a pressure value.")

        for pipe in self.scene.pipes:
            if pipe.length <= 0:
                errors.append(f"{pipe.pipe_id}: length must be > 0.")
            if pipe.diameter <= 0:
                errors.append(f"{pipe.pipe_id}: diameter must be > 0.")
            if pipe.flow_rate is None or pipe.flow_rate <= 0:
                errors.append(f"{pipe.pipe_id}: flow rate must be > 0.")

        if errors:
            QMessageBox.warning(self, "Validation issues", "\n".join(errors))
            return False
        return True

    # ---------------- STATUS BAR ----------------
    def _create_statusbar(self):
        status = QStatusBar()
        status.showMessage("Workspace ready.")
        self.setStatusBar(status)
