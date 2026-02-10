"""Tests for export functionality (CSV, PDF, DXF exporters).

Tests cover:
- CSV export for nodes, pipes, and summaries
- PDF report generation
- DXF CAD file export
- File format correctness
- Error handling for missing data
- Path handling and directory creation
"""

import pytest
import tempfile
from pathlib import Path
import csv

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver
from app.services.exporters.results_exporter import ResultsExporter


@pytest.fixture
def simple_network():
    """Create a simple test network with results"""
    network = PipeNetwork()
    
    # Add nodes
    source = Node(id='N1', is_source=True, pressure=1000000.0)
    sink = Node(id='N2', is_sink=True, flow_rate=0.05)
    
    network.add_node(source)
    network.add_node(sink)
    
    # Add pipe
    pipe = Pipe(
        id='P1',
        start_node='N1',
        end_node='N2',
        length=100.0,
        diameter=0.1,
        roughness=0.0001
    )
    network.add_pipe(pipe)
    
    # Run solver to get results
    fluid = Fluid()
    dp_service = PressureDropService(fluid)
    solver = NetworkSolver(dp_service)
    solver.solve(network)
    
    return network


@pytest.fixture
def complex_network():
    """Create a more complex network with branches"""
    network = PipeNetwork()
    
    # Add nodes
    nodes = {
        'SRC': Node(id='SRC', is_source=True, pressure=500000.0),
        'J1': Node(id='J1'),
        'J2': Node(id='J2'),
        'SNK1': Node(id='SNK1', is_sink=True, flow_rate=0.03),
        'SNK2': Node(id='SNK2', is_sink=True, flow_rate=0.02),
    }
    
    for node in nodes.values():
        network.add_node(node)
    
    # Add pipes
    pipes = {
        'P1': Pipe(id='P1', start_node='SRC', end_node='J1', length=50.0, diameter=0.15, roughness=0.0001),
        'P2': Pipe(id='P2', start_node='J1', end_node='J2', length=30.0, diameter=0.1, roughness=0.0001),
        'P3': Pipe(id='P3', start_node='J1', end_node='SNK1', length=40.0, diameter=0.1, roughness=0.0001),
        'P4': Pipe(id='P4', start_node='J2', end_node='SNK2', length=50.0, diameter=0.1, roughness=0.0001),
    }
    
    for pipe in pipes.values():
        network.add_pipe(pipe)
    
    # Solve
    fluid = Fluid()
    dp_service = PressureDropService(fluid)
    solver = NetworkSolver(dp_service)
    solver.solve(network)
    
    return network


class TestResultsExporterNodes:
    """Test CSV export of node results"""
    
    def test_export_nodes_to_csv_creates_file(self, simple_network):
        """Should create CSV file with node results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(simple_network, str(output_path))
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
    
    def test_export_nodes_csv_format(self, simple_network):
        """CSV should have correct headers and data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Check header - m³ might show differently due to encoding
            assert rows[0][0] == 'Node ID'
            assert rows[0][1] == 'Type'
            assert rows[0][2] == 'Pressure (Pa)'
            assert rows[0][3] == 'Pressure (MPa)'
            assert 'Flow Rate' in rows[0][4]  # Flexible check for encoding variations
            
            # Check data rows exist
            assert len(rows) >= 3  # header + 2 nodes
    
    def test_export_nodes_csv_content_source(self, simple_network):
        """Source node should be labeled correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            source_row = [r for r in rows if r[0] == 'N1'][0]
            assert source_row[1] == 'Source'
            assert float(source_row[2]) == pytest.approx(1000000.0, abs=1.0)
    
    def test_export_nodes_csv_content_sink(self, simple_network):
        """Sink node should be labeled correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            sink_row = [r for r in rows if r[0] == 'N2'][0]
            assert sink_row[1] == 'Sink'
    
    def test_export_nodes_creates_subdirectories(self, simple_network):
        """Should create parent directories if they don't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(simple_network, str(output_path))
            
            assert output_path.exists()


class TestResultsExporterPipes:
    """Test CSV export of pipe results"""
    
    def test_export_pipes_to_csv_creates_file(self, simple_network):
        """Should create CSV file with pipe results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pipes.csv"
            
            ResultsExporter.export_pipes_to_csv(simple_network, str(output_path))
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
    
    def test_export_pipes_csv_format(self, simple_network):
        """CSV should have correct headers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pipes.csv"
            
            ResultsExporter.export_pipes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Check header structure (m³ might have encoding variations)
            assert rows[0][0] == 'Pipe ID'
            assert rows[0][1] == 'Start Node'
            assert rows[0][2] == 'End Node'
            assert rows[0][3] == 'Length (m)'
            assert rows[0][4] == 'Diameter (m)'
            assert 'Flow Rate' in rows[0][5]
            assert 'Velocity' in rows[0][6]
            assert 'Pressure Drop' in rows[0][7]
    
    def test_export_pipes_csv_data_presence(self, simple_network):
        """Pipe data should be present in CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pipes.csv"
            
            ResultsExporter.export_pipes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Should have header + pipe data
            assert len(rows) >= 2
            assert rows[1][0] == 'P1'  # Pipe ID
    
    def test_export_pipes_calculates_velocity(self, simple_network):
        """Should calculate and export velocity"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pipes.csv"
            
            ResultsExporter.export_pipes_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            pipe_row = rows[1]
            velocity = float(pipe_row[6])
            assert velocity >= 0.0  # Velocity should be non-negative
    
    def test_export_pipes_branched_network(self, complex_network):
        """Should export all pipes from branched network"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pipes.csv"
            
            ResultsExporter.export_pipes_to_csv(complex_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # header + 4 pipes
            assert len(rows) == 5


class TestResultsExporterSummary:
    """Test CSV export of network summary"""
    
    def test_export_summary_creates_file(self, simple_network):
        """Should create summary CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            
            ResultsExporter.export_summary_to_csv(simple_network, str(output_path))
            
            assert output_path.exists()
    
    def test_export_summary_content(self, simple_network):
        """Summary should contain network statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            
            ResultsExporter.export_summary_to_csv(simple_network, str(output_path))
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert 'Network Summary' in content
            assert 'Total Nodes' in content
            assert 'Total Pipes' in content
    
    def test_export_summary_counts(self, complex_network):
        """Summary should have correct node and pipe counts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            
            ResultsExporter.export_summary_to_csv(complex_network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Find the metrics
            nodes_row = [r for r in rows if len(r) >= 2 and r[0] == 'Total Nodes']
            pipes_row = [r for r in rows if len(r) >= 2 and r[0] == 'Total Pipes']
            
            assert len(nodes_row) > 0
            assert int(nodes_row[0][1]) == 5
            assert int(pipes_row[0][1]) == 4


class TestPDFExportConditional:
    """Test PDF export if reportlab is available"""
    
    @pytest.mark.skipif(
        True,  # reportlab may not be installed
        reason="reportlab optional dependency"
    )
    def test_pdf_requires_reportlab(self):
        """PDF exporter should check for reportlab availability"""
        try:
            from app.services.exporters.pdf_report_generator import PDFReportGenerator
            from app.services.exporters.pdf_report_generator import REPORTLAB_AVAILABLE
            
            if not REPORTLAB_AVAILABLE:
                pytest.skip("reportlab not installed")
            
            generator = PDFReportGenerator()
            assert generator is not None
        except ImportError:
            pytest.skip("reportlab not installed")
    
    @pytest.mark.skipif(
        True,  # Skip for now since reportlab might not be available
        reason="reportlab conditional availability"
    )
    def test_pdf_generation_creates_file(self, simple_network):
        """PDF should be created successfully"""
        try:
            from app.services.exporters.pdf_report_generator import PDFReportGenerator
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "report.pdf"
                
                generator = PDFReportGenerator()
                generator.generate_report(simple_network, str(output_path), include_charts=False)
                
                assert output_path.exists()
        except ImportError:
            pytest.skip("reportlab not installed")


class TestDXFExportConditional:
    """Test DXF export if ezdxf is available"""
    
    def test_dxf_requires_ezdxf(self):
        """DXF exporter should check for ezdxf availability"""
        try:
            from app.services.exporters.cad_exporter import DXFExporter
            from app.services.exporters.cad_exporter import EZDXF_AVAILABLE
            
            assert EZDXF_AVAILABLE is True
            exporter = DXFExporter()
            assert exporter is not None
        except ImportError:
            # ezdxf not installed, skip test
            pytest.skip("ezdxf not installed")


class TestExporterEdgeCases:
    """Test exporter edge cases and error handling"""
    
    def test_export_empty_network(self):
        """Should handle export of empty network"""
        network = PipeNetwork()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.csv"
            
            # Should not crash on empty network
            ResultsExporter.export_nodes_to_csv(network, str(output_path))
            
            assert output_path.exists()
    
    def test_export_network_with_missing_pressures(self):
        """Should handle nodes with no pressure data"""
        network = PipeNetwork()
        node = Node(id='N1')  # No pressure set
        network.add_node(node)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nodes.csv"
            
            ResultsExporter.export_nodes_to_csv(network, str(output_path))
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Should have default value for missing pressure
            assert len(rows) == 2  # header + node


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
