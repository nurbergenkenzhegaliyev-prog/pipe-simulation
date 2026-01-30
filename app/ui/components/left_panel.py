from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem


class LeftPanelWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setStyleSheet(
            "QTabWidget::pane { border-top: 1px solid #cfcfcf; }"
            "QTabBar::tab { height: 24px; padding: 4px 12px; font-weight: 600; }"
            "QTabBar::tab:selected { background: #f2f2f2; }"
        )

        inputs_widget = QWidget()
        inputs_layout = QVBoxLayout(inputs_widget)
        inputs_layout.setContentsMargins(6, 6, 6, 6)
        inputs_layout.setSpacing(6)

        self.inputs_tree = QTreeWidget()
        self.inputs_tree.setHeaderHidden(True)
        self.inputs_tree.setStyleSheet(
            "QTreeWidget { background: #f7f7f7; border: 1px solid #cfcfcf; }"
            "QTreeWidget::item { padding: 4px 6px; }"
            "QTreeWidget::item:selected { background: #dbe8f8; color: #000000; }"
        )

        self.wells_item = QTreeWidgetItem(self.inputs_tree, ["Wells"])
        self.sources_item = QTreeWidgetItem(self.inputs_tree, ["Sources"])
        self.sinks_item = QTreeWidgetItem(self.inputs_tree, ["Sinks"])
        self.connections_item = QTreeWidgetItem(self.inputs_tree, ["Connections"])
        self.junctions_item = QTreeWidgetItem(self.inputs_tree, ["Junctions"])
        self.equipment_item = QTreeWidgetItem(self.inputs_tree, ["Equipment"])
        QTreeWidgetItem(self.inputs_tree, ["Fluids"])
        self.inputs_tree.expandAll()

        inputs_layout.addWidget(self.inputs_tree)
        self.addTab(inputs_widget, "Inputs")

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
        self.addTab(tasks_widget, "Tasks")

    def refresh_from_scene(self, scene):
        self.sources_item.takeChildren()
        self.sinks_item.takeChildren()
        self.connections_item.takeChildren()
        self.junctions_item.takeChildren()
        self.equipment_item.takeChildren()

        for node in getattr(scene, "nodes", []):
            if getattr(node, "is_source", False):
                QTreeWidgetItem(self.sources_item, [node.node_id])
            elif getattr(node, "is_sink", False):
                QTreeWidgetItem(self.sinks_item, [node.node_id])
            elif getattr(node, "is_pump", False):
                QTreeWidgetItem(self.equipment_item, [f"{node.node_id}: Pump"])
            elif getattr(node, "is_valve", False):
                QTreeWidgetItem(self.equipment_item, [f"{node.node_id}: Valve"])
            else:
                QTreeWidgetItem(self.junctions_item, [node.node_id])

        for pipe in getattr(scene, "pipes", []):
            QTreeWidgetItem(self.connections_item, [pipe.pipe_id])

        self.inputs_tree.expandAll()
