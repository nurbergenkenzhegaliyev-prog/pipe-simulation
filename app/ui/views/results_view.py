from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox

from app.ui.views.results_view_components import ResultsTableBuilder, ResultsUpdater, ResultsViewLayout
from app.services.pressure import PressureDropService
from app.services.pipe_point_analyzer import PipePointAnalyzer
from app.services.exporters.results_exporter import ResultsExporter
from app.services.exporters.pdf_report_generator import PDFReportGenerator
from app.services.exporters.cad_exporter import DXFExporter


class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = None
        self._fluid = None  # Store fluid for PDF report
        self._scene = None  # Store scene for CAD export
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
        
        export_pdf_btn = QPushButton("Export PDF Report")
        export_pdf_btn.clicked.connect(self._export_pdf_report)
        export_pdf_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        export_dxf_btn = QPushButton("Export to DXF")
        export_dxf_btn.clicked.connect(self._export_dxf)
        export_dxf_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        export_layout.addWidget(export_nodes_btn)
        export_layout.addWidget(export_pipes_btn)
        export_layout.addWidget(export_summary_btn)
        export_layout.addWidget(export_pdf_btn)
        export_layout.addWidget(export_dxf_btn)
        export_layout.addStretch()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(export_layout)
        ResultsViewLayout(self, self._tables, main_layout)

    def set_pipe_analyzer(self, analyzer: PipePointAnalyzer):
        """Set the pipe analyzer for multi-point analysis"""
        self._pipe_analyzer = analyzer
        self._updater._pipe_analyzer = analyzer

    def update_results(self, network, fluid=None, scene=None):
        self._network = network
        self._fluid = fluid  # Store fluid for PDF report
        self._scene = scene  # Store scene for CAD export
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
    
    def _export_pdf_report(self):
        """Export comprehensive PDF report with charts"""
        if self._network is None:
            QMessageBox.warning(self, "No Results", "Please run a simulation first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF Report", "", "PDF Files (*.pdf)"
        )
        if path:
            try:
                generator = PDFReportGenerator()
                generator.generate_report(
                    self._network, 
                    path, 
                    include_charts=True,
                    fluid=self._fluid
                )
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"PDF report with charts exported to {path}"
                )
            except ImportError as e:
                QMessageBox.critical(
                    self, 
                    "Missing Dependencies", 
                    "PDF export requires reportlab and matplotlib.\n"
                    "Install with: pip install reportlab matplotlib"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
    
    def _export_dxf(self):
        """Export network geometry to DXF CAD file"""
        if self._scene is None or not self._scene.nodes:
            QMessageBox.warning(self, "No Network", "Please create a network first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export to DXF", "", "DXF Files (*.dxf)"
        )
        if path:
            try:
                exporter = DXFExporter(node_radius=0.5, text_height=0.3)
                exporter.export_from_scene(
                    self._scene, 
                    path,
                    include_labels=True,
                    include_equipment=True
                )
                QMessageBox.information(
                    self, 
                    "Export Successful", 
                    f"Network geometry exported to DXF:\n{path}\n\n"
                    "You can now open this file in AutoCAD or other CAD software."
                )
            except ImportError as e:
                QMessageBox.critical(
                    self, 
                    "Missing Dependencies", 
                    "DXF export requires the ezdxf library.\n"
                    "Install with: pip install ezdxf"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
