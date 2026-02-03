"""Export simulation results to CSV format"""

import csv
from pathlib import Path
from typing import List, Dict, Any


class ResultsExporter:
    """Export network simulation results to CSV files"""
    
    @staticmethod
    def export_nodes_to_csv(network, output_path: str) -> None:
        """Export node results (pressure, flow rate) to CSV"""
        csv_path = Path(output_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Node ID', 'Type', 'Pressure (Pa)', 'Pressure (MPa)', 'Flow Rate (m³/s)'])
            
            for node in network.nodes.values():
                node_type = (
                    'Source' if node.is_source
                    else 'Sink' if node.is_sink
                    else 'Junction'
                )
                pressure_pa = node.pressure or 0.0
                pressure_mpa = pressure_pa / 1e6
                flow_rate = node.flow_rate or 0.0
                
                writer.writerow([
                    node.id,
                    node_type,
                    f'{pressure_pa:.2f}',
                    f'{pressure_mpa:.6f}',
                    f'{flow_rate:.6f}'
                ])
    
    @staticmethod
    def export_pipes_to_csv(network, output_path: str) -> None:
        """Export pipe results (flow rate, pressure drop, velocity) to CSV"""
        csv_path = Path(output_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Pipe ID', 'Start Node', 'End Node', 'Length (m)', 'Diameter (m)',
                'Flow Rate (m³/s)', 'Velocity (m/s)', 'Pressure Drop (Pa)', 'Pressure Drop (MPa)'
            ])
            
            for pipe in network.pipes.values():
                start_node = network.nodes.get(pipe.start_node)
                end_node = network.nodes.get(pipe.end_node)
                
                # Calculate velocity from flow rate
                flow_rate = pipe.flow_rate or 0.0
                if pipe.diameter > 0:
                    area = 3.14159 * (pipe.diameter / 2) ** 2
                    velocity = flow_rate / area if area > 0 else 0.0
                else:
                    velocity = 0.0
                
                # Calculate pressure drop
                if start_node and end_node:
                    pressure_drop = (start_node.pressure or 0.0) - (end_node.pressure or 0.0)
                    pressure_drop_mpa = pressure_drop / 1e6
                else:
                    pressure_drop = 0.0
                    pressure_drop_mpa = 0.0
                
                writer.writerow([
                    pipe.id,
                    pipe.start_node,
                    pipe.end_node,
                    f'{pipe.length:.2f}',
                    f'{pipe.diameter:.6f}',
                    f'{flow_rate:.6f}',
                    f'{velocity:.3f}',
                    f'{pressure_drop:.2f}',
                    f'{pressure_drop_mpa:.6f}'
                ])
    
    @staticmethod
    def export_summary_to_csv(network, output_path: str) -> None:
        """Export network summary statistics to CSV"""
        csv_path = Path(output_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Network statistics
            writer.writerow(['Network Summary'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Nodes', len(network.nodes)])
            writer.writerow(['Total Pipes', len(network.pipes)])
            writer.writerow(['Sources', sum(1 for n in network.nodes.values() if n.is_source)])
            writer.writerow(['Sinks', sum(1 for n in network.nodes.values() if n.is_sink)])
            writer.writerow(['Junctions', sum(1 for n in network.nodes.values() 
                                             if not n.is_source and not n.is_sink)])
            
            # Pressure statistics
            pressures = [n.pressure for n in network.nodes.values() if n.pressure is not None]
            if pressures:
                writer.writerow([])
                writer.writerow(['Pressure Statistics (Pa)'])
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Min Pressure', f'{min(pressures):.2f}'])
                writer.writerow(['Max Pressure', f'{max(pressures):.2f}'])
                writer.writerow(['Avg Pressure', f'{sum(pressures)/len(pressures):.2f}'])
            
            # Flow statistics
            flows = [p.flow_rate for p in network.pipes.values() if p.flow_rate is not None]
            if flows:
                writer.writerow([])
                writer.writerow(['Flow Rate Statistics (m³/s)'])
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Flow', f'{sum(flows):.6f}'])
                writer.writerow(['Min Flow', f'{min(flows):.6f}'])
                writer.writerow(['Max Flow', f'{max(flows):.6f}'])
