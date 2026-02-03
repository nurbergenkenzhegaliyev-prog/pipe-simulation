from __future__ import annotations

from typing import TYPE_CHECKING

from app.ui.dialogs import (
    NodePropertiesDialog,
    PipePropertiesDialog,
    PumpPropertiesDialog,
    ValvePropertiesDialog,
)

if TYPE_CHECKING:
    from app.ui.items.network_items import NodeItem, PipeItem, PumpItem, ValveItem


def edit_node_properties(node: "NodeItem") -> None:
    dlg = NodePropertiesDialog(
        is_source=getattr(node, "is_source", False),
        is_sink=getattr(node, "is_sink", False),
        pressure_pa=getattr(node, "pressure", None),
        flow_rate_m3s=getattr(node, "flow_rate", None),
    )
    if dlg.exec():
        is_source, is_sink, pressure, flow_rate = dlg.values()
        node.is_source = is_source
        node.is_sink = is_sink
        node.pressure = pressure
        node.flow_rate = flow_rate
        
        # Default pressure for source if not set
        if node.is_source and node.pressure is None:
            node.pressure = 10e6
            
        node.update_label(node.pressure if node.is_source else None)
        node._update_tooltip()
        scene = node.scene()
        if scene is not None and hasattr(scene, "nodes_changed"):
            scene.nodes_changed.emit()


def edit_pipe_properties(pipe: "PipeItem") -> None:
    is_multiphase = False
    if pipe.scene() and hasattr(pipe.scene(), "current_fluid"):
        is_multiphase = pipe.scene().current_fluid.is_multiphase if pipe.scene().current_fluid else False

    liquid_flow = getattr(pipe, "liquid_flow_rate", 0.0) or 0.0
    gas_flow = getattr(pipe, "gas_flow_rate", 0.0) or 0.0

    dlg = PipePropertiesDialog(
        pipe.length,
        pipe.diameter,
        pipe.roughness,
        pipe.flow_rate,
        is_multiphase,
        liquid_flow,
        gas_flow,
    )
    if dlg.exec():
        length, diameter, roughness, flow_rate, liquid_flow_rate, gas_flow_rate = dlg.values()
        pipe.length = length
        pipe.diameter = diameter
        pipe.roughness = roughness
        pipe.flow_rate = flow_rate
        pipe.liquid_flow_rate = liquid_flow_rate
        pipe.gas_flow_rate = gas_flow_rate
        pipe._update_tooltip()


def edit_pump_properties(pump: "PumpItem") -> None:
    dlg = PumpPropertiesDialog(pump.pressure_ratio or 1.0)
    if dlg.exec():
        pump.pressure_ratio = dlg.value()
        pump.update_label(None)
        pump._update_tooltip()


def edit_valve_properties(valve: "ValveItem") -> None:
    dlg = ValvePropertiesDialog(valve.valve_k or 0.0)
    if dlg.exec():
        valve.valve_k = dlg.value()
        valve.update_label(None)
        valve._update_tooltip()
