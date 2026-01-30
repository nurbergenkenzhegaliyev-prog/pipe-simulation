from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem


class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.nodes_table = QTableWidget(0, 3)
        self.nodes_table.setHorizontalHeaderLabels(["Node", "Type", "Pressure (MPa)"])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.pipes_table = QTableWidget(0, 4)
        self.pipes_table.setHorizontalHeaderLabels(["Pipe", "From", "To", "dP (MPa)"])
        self.pipes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.nodes_table)
        layout.addWidget(self.pipes_table)

    def update_results(self, network):
        nodes = list(network.nodes.values())
        self.nodes_table.setRowCount(len(nodes))
        for row, node in enumerate(nodes):
            p_mpa = getattr(node, "pressure", None)
            node_type = "Source" if getattr(node, "is_source", False) else "Sink" if getattr(node, "is_sink", False) else "Junction"
            self.nodes_table.setItem(row, 0, QTableWidgetItem(node.id))
            self.nodes_table.setItem(row, 1, QTableWidgetItem(node_type))
            self.nodes_table.setItem(
                row,
                2,
                QTableWidgetItem(f"{(p_mpa or 0)/1e6:.3f}" if p_mpa is not None else "-"),
            )

        pipes = list(network.pipes.values())
        self.pipes_table.setRowCount(len(pipes))
        for row, pipe in enumerate(pipes):
            dp = getattr(pipe, "pressure_drop", None)
            self.pipes_table.setItem(row, 0, QTableWidgetItem(pipe.id))
            self.pipes_table.setItem(row, 1, QTableWidgetItem(pipe.start_node))
            self.pipes_table.setItem(row, 2, QTableWidgetItem(pipe.end_node))
            self.pipes_table.setItem(
                row,
                3,
                QTableWidgetItem(f"{(dp or 0)/1e6:.3f}" if dp is not None else "-"),
            )
