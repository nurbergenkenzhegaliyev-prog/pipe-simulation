"""Transient analysis plotting and visualization.

Provides interactive plots for time-series data from transient simulations
including pressure histories, flow rate changes, and water hammer events.
"""

from typing import List, Dict, Optional, Tuple
import logging

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QGroupBox, QCheckBox, QListWidget, QSplitter
)
from PyQt6.QtCore import Qt

from app.services.transient_solver import TransientResult

logger = logging.getLogger(__name__)


class TransientPlotWidget(QWidget):
    """Widget for displaying transient simulation results with interactive plots.
    
    Features:
    - Pressure vs time plots for selected nodes
    - Flow rate vs time plots for selected pipes
    - Water hammer surge pressure visualization
    - Cavitation event markers
    - Multiple plot modes (line, overlay, subplots)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results: List[TransientResult] = []
        self.node_ids: List[str] = []
        self.pipe_ids: List[str] = []
        self.selected_nodes: List[str] = []
        self.selected_pipes: List[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        
        # Create splitter for controls and plot
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Controls panel
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        # Plot type selection
        plot_type_group = QGroupBox("Plot Type")
        plot_type_layout = QVBoxLayout()
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems([
            "Pressure vs Time",
            "Flow Rate vs Time",
            "Velocity vs Time",
            "Surge Pressure",
            "Pressure & Flow (Dual)",
        ])
        self.plot_type_combo.currentIndexChanged.connect(self._update_plot)
        plot_type_layout.addWidget(self.plot_type_combo)
        
        plot_type_group.setLayout(plot_type_layout)
        controls_layout.addWidget(plot_type_group)
        
        # Node selection
        nodes_group = QGroupBox("Nodes to Plot")
        nodes_layout = QVBoxLayout()
        
        self.node_list = QListWidget()
        self.node_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.node_list.itemSelectionChanged.connect(self._on_node_selection_changed)
        nodes_layout.addWidget(self.node_list)
        
        node_buttons = QHBoxLayout()
        select_all_nodes_btn = QPushButton("All")
        select_all_nodes_btn.clicked.connect(self._select_all_nodes)
        clear_nodes_btn = QPushButton("Clear")
        clear_nodes_btn.clicked.connect(self._clear_node_selection)
        node_buttons.addWidget(select_all_nodes_btn)
        node_buttons.addWidget(clear_nodes_btn)
        nodes_layout.addLayout(node_buttons)
        
        nodes_group.setLayout(nodes_layout)
        controls_layout.addWidget(nodes_group)
        
        # Pipe selection
        pipes_group = QGroupBox("Pipes to Plot")
        pipes_layout = QVBoxLayout()
        
        self.pipe_list = QListWidget()
        self.pipe_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.pipe_list.itemSelectionChanged.connect(self._on_pipe_selection_changed)
        pipes_layout.addWidget(self.pipe_list)
        
        pipe_buttons = QHBoxLayout()
        select_all_pipes_btn = QPushButton("All")
        select_all_pipes_btn.clicked.connect(self._select_all_pipes)
        clear_pipes_btn = QPushButton("Clear")
        clear_pipes_btn.clicked.connect(self._clear_pipe_selection)
        pipe_buttons.addWidget(select_all_pipes_btn)
        pipe_buttons.addWidget(clear_pipes_btn)
        pipes_layout.addLayout(pipe_buttons)
        
        pipes_group.setLayout(pipes_layout)
        controls_layout.addWidget(pipes_group)
        
        # Plot options
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout()
        
        self.show_grid_check = QCheckBox("Show Grid")
        self.show_grid_check.setChecked(True)
        self.show_grid_check.toggled.connect(self._update_plot)
        options_layout.addWidget(self.show_grid_check)
        
        self.show_markers_check = QCheckBox("Show Markers")
        self.show_markers_check.setChecked(False)
        self.show_markers_check.toggled.connect(self._update_plot)
        options_layout.addWidget(self.show_markers_check)
        
        self.show_cavitation_check = QCheckBox("Mark Cavitation Events")
        self.show_cavitation_check.setChecked(True)
        self.show_cavitation_check.toggled.connect(self._update_plot)
        options_layout.addWidget(self.show_cavitation_check)
        
        options_group.setLayout(options_layout)
        controls_layout.addWidget(options_group)
        
        controls_layout.addStretch()
        
        # Export button
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self._export_to_csv)
        controls_layout.addWidget(export_btn)
        
        splitter.addWidget(controls_widget)
        
        # Right: Plot area
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        splitter.addWidget(plot_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
    
    def set_results(self, results: List[TransientResult]):
        """Set the transient simulation results to display.
        
        Args:
            results: List of TransientResult objects
        """
        self.results = results
        
        if not results:
            return
        
        # Extract unique node and pipe IDs
        self.node_ids = sorted(set(results[0].node_pressures.keys()))
        self.pipe_ids = sorted(set(results[0].pipe_flows.keys()))
        
        # Update node list
        self.node_list.clear()
        self.node_list.addItems(self.node_ids)
        
        # Update pipe list
        self.pipe_list.clear()
        self.pipe_list.addItems(self.pipe_ids)
        
        # Auto-select first few nodes/pipes
        if self.node_ids:
            self.node_list.item(0).setSelected(True)
        if self.pipe_ids and len(self.pipe_ids) > 0:
            self.pipe_list.item(0).setSelected(True)
        
        self._update_plot()
    
    def _select_all_nodes(self):
        """Select all nodes in the list."""
        for i in range(self.node_list.count()):
            self.node_list.item(i).setSelected(True)
    
    def _clear_node_selection(self):
        """Clear node selection."""
        self.node_list.clearSelection()
    
    def _select_all_pipes(self):
        """Select all pipes in the list."""
        for i in range(self.pipe_list.count()):
            self.pipe_list.item(i).setSelected(True)
    
    def _clear_pipe_selection(self):
        """Clear pipe selection."""
        self.pipe_list.clearSelection()
    
    def _on_node_selection_changed(self):
        """Handle node selection changes."""
        self.selected_nodes = [item.text() for item in self.node_list.selectedItems()]
        self._update_plot()
    
    def _on_pipe_selection_changed(self):
        """Handle pipe selection changes."""
        self.selected_pipes = [item.text() for item in self.pipe_list.selectedItems()]
        self._update_plot()
    
    def _update_plot(self):
        """Update the plot based on current selection and settings."""
        if not self.results:
            return
        
        self.figure.clear()
        plot_type = self.plot_type_combo.currentText()
        
        if plot_type == "Pressure vs Time":
            self._plot_pressure_vs_time()
        elif plot_type == "Flow Rate vs Time":
            self._plot_flow_vs_time()
        elif plot_type == "Velocity vs Time":
            self._plot_velocity_vs_time()
        elif plot_type == "Surge Pressure":
            self._plot_surge_pressure()
        elif plot_type == "Pressure & Flow (Dual)":
            self._plot_pressure_and_flow()
        
        self.canvas.draw()
    
    def _plot_pressure_vs_time(self):
        """Plot pressure vs time for selected nodes."""
        ax = self.figure.add_subplot(111)
        
        times = [r.time for r in self.results]
        
        for node_id in self.selected_nodes:
            pressures = [r.node_pressures.get(node_id, 0.0) / 1e5 for r in self.results]  # Convert to bar
            marker = 'o' if self.show_markers_check.isChecked() else None
            ax.plot(times, pressures, marker=marker, markersize=3, label=node_id)
        
        # Mark cavitation events
        if self.show_cavitation_check.isChecked():
            for result in self.results:
                for node_id in result.cavitation_nodes:
                    if node_id in self.selected_nodes:
                        pressure = result.node_pressures.get(node_id, 0.0) / 1e5
                        ax.plot(result.time, pressure, 'rx', markersize=8, markeredgewidth=2)
        
        ax.set_xlabel('Time (s)', fontsize=11)
        ax.set_ylabel('Pressure (bar)', fontsize=11)
        ax.set_title('Pressure vs Time', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        
        if self.show_grid_check.isChecked():
            ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _plot_flow_vs_time(self):
        """Plot flow rate vs time for selected pipes."""
        ax = self.figure.add_subplot(111)
        
        times = [r.time for r in self.results]
        
        for pipe_id in self.selected_pipes:
            flows = [r.pipe_flows.get(pipe_id, 0.0) for r in self.results]
            marker = 'o' if self.show_markers_check.isChecked() else None
            ax.plot(times, flows, marker=marker, markersize=3, label=pipe_id)
        
        ax.set_xlabel('Time (s)', fontsize=11)
        ax.set_ylabel('Flow Rate (m³/s)', fontsize=11)
        ax.set_title('Flow Rate vs Time', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        
        if self.show_grid_check.isChecked():
            ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _plot_velocity_vs_time(self):
        """Plot velocity vs time for selected pipes."""
        ax = self.figure.add_subplot(111)
        
        times = [r.time for r in self.results]
        
        for pipe_id in self.selected_pipes:
            velocities = [r.pipe_velocities.get(pipe_id, 0.0) for r in self.results]
            marker = 'o' if self.show_markers_check.isChecked() else None
            ax.plot(times, velocities, marker=marker, markersize=3, label=pipe_id)
        
        ax.set_xlabel('Time (s)', fontsize=11)
        ax.set_ylabel('Velocity (m/s)', fontsize=11)
        ax.set_title('Velocity vs Time', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        
        if self.show_grid_check.isChecked():
            ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _plot_surge_pressure(self):
        """Plot water hammer surge pressure vs time."""
        ax = self.figure.add_subplot(111)
        
        times = [r.time for r in self.results]
        
        for pipe_id in self.selected_pipes:
            surges = [r.surge_pressures.get(pipe_id, 0.0) / 1e5 for r in self.results]  # Convert to bar
            marker = 'o' if self.show_markers_check.isChecked() else None
            ax.plot(times, surges, marker=marker, markersize=3, label=f"{pipe_id} Surge")
        
        ax.set_xlabel('Time (s)', fontsize=11)
        ax.set_ylabel('Surge Pressure (bar)', fontsize=11)
        ax.set_title('Water Hammer Surge Pressure', fontsize=13, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        
        if self.show_grid_check.isChecked():
            ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _plot_pressure_and_flow(self):
        """Plot pressure and flow rate on dual y-axes."""
        if not self.selected_nodes or not self.selected_pipes:
            return
        
        ax1 = self.figure.add_subplot(111)
        ax2 = ax1.twinx()
        
        times = [r.time for r in self.results]
        
        # Plot pressures on left axis
        for node_id in self.selected_nodes[:3]:  # Limit to 3 for clarity
            pressures = [r.node_pressures.get(node_id, 0.0) / 1e5 for r in self.results]
            ax1.plot(times, pressures, label=f"{node_id} (P)", linestyle='-')
        
        # Plot flows on right axis
        for pipe_id in self.selected_pipes[:3]:  # Limit to 3 for clarity
            flows = [r.pipe_flows.get(pipe_id, 0.0) for r in self.results]
            ax2.plot(times, flows, label=f"{pipe_id} (Q)", linestyle='--')
        
        ax1.set_xlabel('Time (s)', fontsize=11)
        ax1.set_ylabel('Pressure (bar)', fontsize=11, color='blue')
        ax2.set_ylabel('Flow Rate (m³/s)', fontsize=11, color='red')
        ax1.set_title('Pressure & Flow Rate vs Time', fontsize=13, fontweight='bold')
        
        ax1.tick_params(axis='y', labelcolor='blue')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9)
        
        if self.show_grid_check.isChecked():
            ax1.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
    
    def _export_to_csv(self):
        """Export current results to CSV file."""
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.results:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transient Results",
            "transient_results.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                from app.services.transient_solver import TransientSolver
                # Create temporary solver to use export method
                # We'll export all data, user can filter in Excel
                import csv
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Header
                    header = ['Time (s)']
                    for node_id in self.node_ids:
                        header.append(f'{node_id} Pressure (bar)')
                    for pipe_id in self.pipe_ids:
                        header.append(f'{pipe_id} Flow (m³/s)')
                    writer.writerow(header)
                    
                    # Data
                    for result in self.results:
                        row = [f"{result.time:.4f}"]
                        for node_id in self.node_ids:
                            pressure = result.node_pressures.get(node_id, 0.0) / 1e5
                            row.append(f"{pressure:.4f}")
                        for pipe_id in self.pipe_ids:
                            flow = result.pipe_flows.get(pipe_id, 0.0)
                            row.append(f"{flow:.6f}")
                        writer.writerow(row)
                
                logger.info(f"Exported transient results to {filename}")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Export Complete", 
                                       f"Results exported to:\n{filename}")
            except Exception as e:
                logger.error(f"Failed to export results: {e}")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Export Failed", 
                                   f"Failed to export results:\n{str(e)}")
