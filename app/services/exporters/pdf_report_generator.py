"""Export simulation results to PDF format with charts and visualizations"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import io

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PDFReportGenerator:
    """Generate comprehensive PDF reports of network simulation results"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f497d'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f497d'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#4f81bd'),
            spaceAfter=6
        ))
    
    def generate_report(self, network, output_path: str, 
                       include_charts: bool = True,
                       fluid=None) -> None:
        """Generate a complete PDF report of the network simulation
        
        Args:
            network: PipeNetwork with simulation results
            output_path: Path to save the PDF file
            include_charts: Whether to include charts and graphs
            fluid: Fluid object for additional info
        """
        pdf_path = Path(output_path)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build the report content
        story = []
        
        # Title page
        story.extend(self._create_title_page())
        
        # Network summary
        story.extend(self._create_summary_section(network, fluid))
        
        # Node results table
        story.extend(self._create_nodes_section(network))
        
        # Pipe results table
        story.extend(self._create_pipes_section(network))
        
        # Charts and visualizations
        if include_charts and MATPLOTLIB_AVAILABLE:
            story.extend(self._create_charts_section(network))
        
        # Build the PDF
        doc.build(story)
    
    def _create_title_page(self):
        """Create the title page"""
        story = []
        
        story.append(Spacer(1, 2*inch))
        
        title = Paragraph("Pipe Network Simulation Report", self.styles['CustomTitle'])
        story.append(title)
        
        story.append(Spacer(1, 0.3*inch))
        
        date_str = datetime.now().strftime("%B %d, %Y at %H:%M")
        date_para = Paragraph(f"Generated on {date_str}", self.styles['Normal'])
        date_para.alignment = TA_CENTER
        story.append(date_para)
        
        story.append(PageBreak())
        
        return story
    
    def _create_summary_section(self, network, fluid=None):
        """Create network summary section"""
        story = []
        
        story.append(Paragraph("Network Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary statistics
        total_nodes = len(network.nodes)
        total_pipes = len(network.pipes)
        sources = sum(1 for n in network.nodes.values() if n.is_source)
        sinks = sum(1 for n in network.nodes.values() if n.is_sink)
        junctions = total_nodes - sources - sinks
        
        data = [
            ['Metric', 'Value'],
            ['Total Nodes', str(total_nodes)],
            ['Total Pipes', str(total_pipes)],
            ['Source Nodes', str(sources)],
            ['Sink Nodes', str(sinks)],
            ['Junction Nodes', str(junctions)],
        ]
        
        # Add fluid properties if available
        if fluid:
            data.append(['Fluid Type', 'Multi-phase' if fluid.is_multiphase else 'Single-phase'])
            data.append(['Fluid Density (kg/m³)', f'{fluid.density:.2f}'])
            data.append(['Fluid Viscosity (Pa·s)', f'{fluid.viscosity:.6f}'])
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f81bd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_nodes_section(self, network):
        """Create nodes results section"""
        story = []
        
        story.append(Paragraph("Node Results", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.15*inch))
        
        # Prepare node data
        data = [['Node ID', 'Type', 'Pressure (Pa)', 'Pressure (MPa)', 'Flow (m³/s)']]
        
        for node in network.nodes.values():
            node_type = (
                'Source' if node.is_source
                else 'Sink' if node.is_sink
                else 'Junction'
            )
            pressure_pa = node.pressure or 0.0
            pressure_mpa = pressure_pa / 1e6
            flow_rate = node.flow_rate or 0.0
            
            data.append([
                node.id,
                node_type,
                f'{pressure_pa:.2f}',
                f'{pressure_mpa:.6f}',
                f'{flow_rate:.6f}'
            ])
        
        table = Table(data, colWidths=[1.2*inch, 1*inch, 1.3*inch, 1.3*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f81bd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        story.append(KeepTogether(table))
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_pipes_section(self, network):
        """Create pipes results section"""
        story = []
        
        story.append(Paragraph("Pipe Results", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.15*inch))
        
        # Prepare pipe data
        data = [['Pipe ID', 'Start→End', 'Length (m)', 'Flow (m³/s)', 'Velocity (m/s)', 'ΔP (Pa)']]
        
        for pipe in network.pipes.values():
            start_node = network.nodes.get(pipe.start_node)
            end_node = network.nodes.get(pipe.end_node)
            
            # Calculate velocity
            flow_rate = pipe.flow_rate or 0.0
            area = pipe.area()
            velocity = flow_rate / area if area > 0 else 0.0
            
            # Calculate pressure drop
            if start_node and end_node:
                pressure_drop = (start_node.pressure or 0.0) - (end_node.pressure or 0.0)
            else:
                pressure_drop = 0.0
            
            data.append([
                pipe.id,
                f'{pipe.start_node}→{pipe.end_node}',
                f'{pipe.length:.2f}',
                f'{flow_rate:.6f}',
                f'{velocity:.3f}',
                f'{pressure_drop:.2f}'
            ])
        
        table = Table(data, colWidths=[1*inch, 1.3*inch, 1*inch, 1.2*inch, 1.2*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f81bd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        story.append(KeepTogether(table))
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_charts_section(self, network):
        """Create charts and visualizations section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Visualization & Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # Pressure profile chart
        pressure_chart = self._create_pressure_chart(network)
        if pressure_chart:
            story.append(Paragraph("Pressure Distribution", self.styles['SubHeader']))
            story.append(pressure_chart)
            story.append(Spacer(1, 0.3*inch))
        
        # Flow distribution chart
        flow_chart = self._create_flow_chart(network)
        if flow_chart:
            story.append(Paragraph("Flow Distribution", self.styles['SubHeader']))
            story.append(flow_chart)
            story.append(Spacer(1, 0.3*inch))
        
        # Velocity distribution chart
        velocity_chart = self._create_velocity_chart(network)
        if velocity_chart:
            story.append(Paragraph("Pipe Velocity Distribution", self.styles['SubHeader']))
            story.append(velocity_chart)
            story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_pressure_chart(self, network):
        """Create pressure distribution bar chart"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        node_ids = []
        pressures_mpa = []
        colors_list = []
        
        for node in network.nodes.values():
            node_ids.append(node.id)
            pressure = (node.pressure or 0.0) / 1e6  # Convert to MPa
            pressures_mpa.append(pressure)
            
            # Color code by node type
            if node.is_source:
                colors_list.append('#4CAF50')  # Green
            elif node.is_sink:
                colors_list.append('#F44336')  # Red
            else:
                colors_list.append('#2196F3')  # Blue
        
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(node_ids, pressures_mpa, color=colors_list, alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Node ID', fontsize=10, fontweight='bold')
        ax.set_ylabel('Pressure (MPa)', fontsize=10, fontweight='bold')
        ax.set_title('Node Pressure Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Rotate x-axis labels if many nodes
        if len(node_ids) > 5:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        # Create Image object
        img = Image(img_buffer, width=6*inch, height=3*inch)
        return img
    
    def _create_flow_chart(self, network):
        """Create flow distribution bar chart"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        pipe_ids = []
        flow_rates = []
        
        for pipe in network.pipes.values():
            pipe_ids.append(pipe.id)
            flow_rates.append(pipe.flow_rate or 0.0)
        
        if not flow_rates:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(pipe_ids, flow_rates, color='#FF9800', alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Pipe ID', fontsize=10, fontweight='bold')
        ax.set_ylabel('Flow Rate (m³/s)', fontsize=10, fontweight='bold')
        ax.set_title('Pipe Flow Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        if len(pipe_ids) > 5:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        img = Image(img_buffer, width=6*inch, height=3*inch)
        return img
    
    def _create_velocity_chart(self, network):
        """Create velocity distribution bar chart"""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        pipe_ids = []
        velocities = []
        
        for pipe in network.pipes.values():
            pipe_ids.append(pipe.id)
            flow_rate = pipe.flow_rate or 0.0
            area = pipe.area()
            velocity = flow_rate / area if area > 0 else 0.0
            velocities.append(velocity)
        
        if not velocities:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(pipe_ids, velocities, color='#9C27B0', alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Pipe ID', fontsize=10, fontweight='bold')
        ax.set_ylabel('Velocity (m/s)', fontsize=10, fontweight='bold')
        ax.set_title('Pipe Velocity Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        if len(pipe_ids) > 5:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        img = Image(img_buffer, width=6*inch, height=3*inch)
        return img
