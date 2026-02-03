from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


@dataclass
class LeftPanelState:
    inputs_tree: QTreeWidget
    sources_item: QTreeWidgetItem
    sinks_item: QTreeWidgetItem
    connections_item: QTreeWidgetItem
    junctions_item: QTreeWidgetItem
    equipment_item: QTreeWidgetItem


class LeftPanelBuilder:
    def build_inputs_tab(self) -> tuple[QWidget, LeftPanelState]:
        inputs_widget = QWidget()
        inputs_layout = QVBoxLayout(inputs_widget)
        inputs_layout.setContentsMargins(6, 6, 6, 6)
        inputs_layout.setSpacing(6)

        inputs_tree = QTreeWidget()
        inputs_tree.setHeaderHidden(True)
        inputs_tree.setStyleSheet(
            "QTreeWidget { background: #f7f7f7; border: 1px solid #cfcfcf; }"
            "QTreeWidget::item { padding: 4px 6px; }"
            "QTreeWidget::item:selected { background: #dbe8f8; color: #000000; }"
        )

        QTreeWidgetItem(inputs_tree, ["Wells"])
        sources_item = QTreeWidgetItem(inputs_tree, ["Sources"])
        sinks_item = QTreeWidgetItem(inputs_tree, ["Sinks"])
        connections_item = QTreeWidgetItem(inputs_tree, ["Connections"])
        junctions_item = QTreeWidgetItem(inputs_tree, ["Junctions"])
        equipment_item = QTreeWidgetItem(inputs_tree, ["Equipment"])
        QTreeWidgetItem(inputs_tree, ["Fluids"])
        inputs_tree.expandAll()

        inputs_layout.addWidget(inputs_tree)

        state = LeftPanelState(
            inputs_tree=inputs_tree,
            sources_item=sources_item,
            sinks_item=sinks_item,
            connections_item=connections_item,
            junctions_item=junctions_item,
            equipment_item=equipment_item,
        )
        return inputs_widget, state

    def build_tasks_tab(self) -> QWidget:
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(6, 6, 6, 6)
        tasks_layout.setSpacing(6)

        tasks = QTreeWidget()
        tasks.setHeaderHidden(True)
        tasks.setStyleSheet(
            "QTreeWidget { background: #f7f7f7; border: 1px solid #cfcfcf; }"
            "QTreeWidget::item { padding: 4px 6px; }"
            "QTreeWidget::item:selected { background: #dbe8f8; color: #000000; }"
        )
        QTreeWidgetItem(tasks, ["Network simulation"])
        QTreeWidgetItem(tasks, ["Network optimizer"])
        QTreeWidgetItem(tasks, ["System analysis"])
        QTreeWidgetItem(tasks, ["ESP design"])

        tasks_layout.addWidget(tasks)
        return tasks_widget


class SceneTreeRefresher:
    def __init__(self, state: LeftPanelState):
        self._state = state

    def refresh(self, scene) -> None:
        self._state.sources_item.takeChildren()
        self._state.sinks_item.takeChildren()
        self._state.connections_item.takeChildren()
        self._state.junctions_item.takeChildren()
        self._state.equipment_item.takeChildren()

        for node in getattr(scene, "nodes", []):
            if getattr(node, "is_source", False):
                QTreeWidgetItem(self._state.sources_item, [node.node_id])
            elif getattr(node, "is_sink", False):
                QTreeWidgetItem(self._state.sinks_item, [node.node_id])
            elif getattr(node, "is_pump", False):
                QTreeWidgetItem(self._state.equipment_item, [f"{node.node_id}: Pump"])
            elif getattr(node, "is_valve", False):
                QTreeWidgetItem(self._state.equipment_item, [f"{node.node_id}: Valve"])
            else:
                QTreeWidgetItem(self._state.junctions_item, [node.node_id])

        for pipe in getattr(scene, "pipes", []):
            QTreeWidgetItem(self._state.connections_item, [pipe.pipe_id])

        self._state.inputs_tree.expandAll()
