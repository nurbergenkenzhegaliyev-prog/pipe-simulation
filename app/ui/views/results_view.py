from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox

from app.ui.views.results_view_components import ResultsTableBuilder, ResultsUpdater, ResultsViewLayout
from app.services.pressure_drop_service import PressureDropService
from app.services.pipe_point_analyzer import PipePointAnalyzer
from app.services.results_exporter import ResultsExporter


class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = None
        self._tables = ResultsTableBuilder().build(self)
        self._updater = ResultsUpdater()
        self._pipe_analyzer = None
        
        # Create export buttons
        export_layout = QHBoxLayout()
        export_layout.setContentsMargins(6, 6, 6, 6)
        export_layout.setSpacing(6)
        
        export_nodes_btn = QPushButton("Export Nodes to CSV")
        export_nodes_btn.clicked.connect(self._export_nodes_csv)
        
        export_pipes_btn = QPushButton("Export Pipes to CSV")
        export_pipes_btn.clicked.connect(self._export_pipes_csv)
        
        export_summary_btn = QPushButton("Export Summary to CSV")
        export_summary_btn.clicked.connect(self._export_summary_csv)
        
        export_layout.addWidget(export_nodes_btn)
        export_layout.addWidget(export_pipes_btn)
        export_layout.addWidget(export_summary_btn)
        export_layout.addStretch()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(export_layout)
        ResultsViewLayout(self, self._tables, main_layout)

    def set_pipe_analyzer(self, analyzer: PipePointAnalyzer):
        """Set the pipe analyzer for multi-point analysis"""
        self._pipe_analyzer = analyzer
        self._updater._pipe_analyzer = analyzer

    def update_results(self, network):
        self._network = network
        self._updater.set_dependencies(network, self._pipe_analyzer)
        self._updater.update(self._tables, network)
    
    def _export_nodes_csv(self):
        """Export node results to CSV"""
        if self._network is None:
            QMessageBox.warning(self, "No Results", "Please run a simulation first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Nodes", "", "CSV Files (*.csv)"
        )
        if path:
            try:
                ResultsExporter.export_nodes_to_csv(self._network, path)
                QMessageBox.information(self, "Export Successful", f"Nodes exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
    
    def _export_pipes_csv(self):
        """Export pipe results to CSV"""
        if self._network is None:
            QMessageBox.warning(self, "No Results", "Please run a simulation first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Pipes", "", "CSV Files (*.csv)"
        )
        if path:
            try:
                ResultsExporter.export_pipes_to_csv(self._network, path)
                QMessageBox.information(self, "Export Successful", f"Pipes exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
    
    def _export_summary_csv(self):
        """Export network summary to CSV"""
        if self._network is None:
            QMessageBox.warning(self, "No Results", "Please run a simulation first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Summary", "", "CSV Files (*.csv)"
        )
        if path:
            try:
                ResultsExporter.export_summary_to_csv(self._network, path)
                QMessageBox.information(self, "Export Successful", f"Summary exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
