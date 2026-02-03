from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal


@dataclass
class ResultsTables:
    nodes_table: QTableWidget
    flowlines_list: QListWidget
    flowline_detail_table: QTableWidget


class ResultsTableBuilder:
    def build(self, parent: QWidget) -> ResultsTables:
        nodes_table = QTableWidget(0, 4, parent)
        nodes_table.setHorizontalHeaderLabels(["Node", "Type", "Pressure (MPa)", "Flow Rate (m³/s)"])
        nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        flowlines_list = QListWidget(parent)
        
        flowline_detail_table = QTableWidget(0, 5, parent)
        flowline_detail_table.setHorizontalHeaderLabels(
            ["Distance (m)", "Pressure (MPa)", "Velocity (m/s)", "Pressure Drop (MPa)", "Flow Rate (m³/s)"]
        )
        flowline_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        return ResultsTables(
            nodes_table=nodes_table,
            flowlines_list=flowlines_list,
            flowline_detail_table=flowline_detail_table
        )


class ResultsViewLayout:
    def __init__(self, parent: QWidget, tables: ResultsTables, main_layout: QVBoxLayout = None):
        if main_layout is None:
            main_layout = QVBoxLayout(parent)
        
        # Create tab widget
        tabs = QTabWidget(parent)
        
        # Nodes tab
        nodes_tab = QWidget()
        nodes_layout = QVBoxLayout(nodes_tab)
        nodes_layout.addWidget(tables.nodes_table)
        tabs.addTab(nodes_tab, "Nodes")
        
        # Flowlines tab with split view
        flowlines_tab = QWidget()
        flowlines_layout = QVBoxLayout(flowlines_tab)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(tables.flowlines_list)
        splitter.addWidget(tables.flowline_detail_table)
        splitter.setSizes([200, 400])  # Default sizes for left and right panels
        
        flowlines_layout.addWidget(splitter)
        tabs.addTab(flowlines_tab, "Flowlines")
        
        main_layout.addWidget(tabs)


class ResultsUpdater:
    def __init__(self):
        self._network = None
        self._pipe_analyzer = None

    def set_dependencies(self, network, pipe_analyzer):
        """Set network and pipe analyzer for detailed analysis"""
        self._network = network
        self._pipe_analyzer = pipe_analyzer

    def update(self, tables: ResultsTables, network) -> None:
        self._network = network
        self._update_nodes(tables, network)
        self._update_flowlines(tables, network)
        
        # Connect flowline list selection to detail view
        tables.flowlines_list.itemSelectionChanged.connect(
            lambda: self._on_flowline_selected(tables, network)
        )

    def _update_nodes(self, tables: ResultsTables, network) -> None:
        """Update nodes table"""
        nodes = list(network.nodes.values())
        tables.nodes_table.setRowCount(len(nodes))
        for row, node in enumerate(nodes):
            p_mpa = getattr(node, "pressure", None)
            flow_rate = getattr(node, "flow_rate", None)
            node_type = (
                "Source"
                if getattr(node, "is_source", False)
                else "Sink"
                if getattr(node, "is_sink", False)
                else "Junction"
            )
            tables.nodes_table.setItem(row, 0, QTableWidgetItem(node.id))
            tables.nodes_table.setItem(row, 1, QTableWidgetItem(node_type))
            tables.nodes_table.setItem(
                row,
                2,
                QTableWidgetItem(f"{(p_mpa or 0)/1e6:.3f}" if p_mpa is not None else "-"),
            )
            tables.nodes_table.setItem(
                row,
                3,
                QTableWidgetItem(f"{flow_rate:.6f}" if flow_rate is not None else "-"),
            )

    def _update_flowlines(self, tables: ResultsTables, network) -> None:
        """Update flowlines list"""
        pipes = list(network.pipes.values())
        tables.flowlines_list.clear()
        
        for pipe in pipes:
            item = QListWidgetItem(f"{pipe.id} ({pipe.start_node} → {pipe.end_node})")
            item.setData(Qt.ItemDataRole.UserRole, pipe.id)
            tables.flowlines_list.addItem(item)

    def _on_flowline_selected(self, tables: ResultsTables, network) -> None:
        """Handle flowline selection to show detail"""
        selected_items = tables.flowlines_list.selectedItems()
        if not selected_items:
            tables.flowline_detail_table.setRowCount(0)
            return
        
        pipe_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        pipe = network.pipes.get(pipe_id)
        
        if pipe and self._pipe_analyzer:
            self._update_flowline_detail(tables, pipe, network)
        else:
            tables.flowline_detail_table.setRowCount(0)

    def _update_flowline_detail(self, tables: ResultsTables, pipe, network) -> None:
        """Update detailed analysis for a selected flowline"""
        if self._pipe_analyzer is None:
            return
        
        # Get start node pressure
        start_node = network.nodes.get(pipe.start_node)
        start_pressure = getattr(start_node, "pressure", None) if start_node else None
        
        # If no pressure is available, don't show detailed analysis
        if start_pressure is None:
            tables.flowline_detail_table.setRowCount(0)
            return
        
        pipe_flow_rate = getattr(pipe, "flow_rate", None)
        
        # Analyze pipe at multiple points
        points = self._pipe_analyzer.analyze_pipe(pipe, start_pressure, num_points=4)
        
        tables.flowline_detail_table.setRowCount(len(points))
        for row, point in enumerate(points):
            tables.flowline_detail_table.setItem(
                row, 0, QTableWidgetItem(f"{point.distance:.2f}")
            )
            tables.flowline_detail_table.setItem(
                row, 1, QTableWidgetItem(f"{point.pressure/1e6:.3f}")
            )
            tables.flowline_detail_table.setItem(
                row, 2, QTableWidgetItem(f"{point.velocity:.3f}")
            )
            tables.flowline_detail_table.setItem(
                row, 3, QTableWidgetItem(f"{point.pressure_drop/1e6:.3f}")
            )
            tables.flowline_detail_table.setItem(
                row, 4, QTableWidgetItem(f"{pipe_flow_rate:.6f}" if pipe_flow_rate is not None else "-")
            )
