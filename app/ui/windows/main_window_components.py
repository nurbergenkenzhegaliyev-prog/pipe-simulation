from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QDialog, QVBoxLayout

from app.models.equipment import PumpCurve, Valve


class SceneSerializer:
    def serialize(self, scene) -> Dict[str, Any]:
        nodes = []
        for node in getattr(scene, "nodes", []):
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
                "flow_rate": getattr(node, "flow_rate", None),
            })

        pipes = []
        for pipe in getattr(scene, "pipes", []):
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

    def load(self, scene, data: Dict[str, Any]) -> None:
        nodes = data.get("nodes", [])
        pipes = data.get("pipes", [])

        scene.clear_network()
        node_by_id = {}
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            pos = QPointF(float(node.get("x", 0.0)), float(node.get("y", 0.0)))
            item = scene.create_node_with_id(
                pos,
                node_id,
                is_source=bool(node.get("is_source", False)),
                is_sink=bool(node.get("is_sink", False)),
                pressure=node.get("pressure", None),
                flow_rate=node.get("flow_rate", None),
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
            created = scene.create_pipe_with_id(
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
        scene.nodes_changed.emit()


@dataclass
class ValidationIssue:
    message: str


class SceneValidator:
    def validate(self, scene, fluid) -> List[ValidationIssue]:
        errors: List[ValidationIssue] = []

        # Check for boundary conditions: sources with pressure/flow or sinks with flow
        sources = [n for n in scene.nodes if getattr(n, "is_source", False)]
        sinks = [n for n in scene.nodes if getattr(n, "is_sink", False)]
        
        if len(sources) == 0 and len(sinks) == 0:
            errors.append(ValidationIssue("Add at least one source or sink node."))
        
        # Validate sources: must have either pressure or flow_rate
        for node in sources:
            pressure = getattr(node, "pressure", None)
            flow_rate = getattr(node, "flow_rate", None)
            if pressure is None and flow_rate is None:
                errors.append(ValidationIssue(
                    f"{node.node_id}: source node needs either a pressure or flow rate value."
                ))
        
        # Validate sinks: must have flow_rate (required)
        for node in sinks:
            flow_rate = getattr(node, "flow_rate", None)
            if flow_rate is None or flow_rate <= 0:
                errors.append(ValidationIssue(
                    f"{node.node_id}: sink node requires a flow rate value > 0."
                ))

        for pipe in scene.pipes:
            if pipe.length <= 0:
                errors.append(ValidationIssue(f"{pipe.pipe_id}: length must be > 0."))
            if pipe.diameter <= 0:
                errors.append(ValidationIssue(f"{pipe.pipe_id}: diameter must be > 0."))

        return errors


class ResultsDialogManager:
    def __init__(self, parent, results_view):
        self._parent = parent
        self._results_view = results_view
        self._dialog = None

    def show(self) -> None:
        if self._dialog is None:
            self._dialog = QDialog(self._parent)
            self._dialog.setWindowTitle("Results")
            self._dialog.resize(800, 600)
            layout = QVBoxLayout(self._dialog)
            layout.addWidget(self._results_view)
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()
