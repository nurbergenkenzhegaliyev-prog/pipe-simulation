"""EPANET INP file parser for importing hydraulic network models"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid


@dataclass
class EPANETSection:
    """Represents a section in an EPANET INP file"""
    name: str
    lines: List[str]


class EPANETParser:
    """Parse EPANET INP files and convert to PipeNetwork"""
    
    def __init__(self):
        self.sections: Dict[str, List[str]] = {}
        self.junctions: Dict[str, dict] = {}
        self.reservoirs: Dict[str, dict] = {}
        self.tanks: Dict[str, dict] = {}
        self.pipes_data: Dict[str, dict] = {}
        self.demands: Dict[str, float] = {}
    
    def parse_file(self, file_path: str) -> PipeNetwork:
        """Parse an EPANET INP file and return a PipeNetwork
        
        Args:
            file_path: Path to the .inp file
            
        Returns:
            PipeNetwork object
        """
        # Read and parse sections
        self._read_sections(file_path)
        
        # Parse each section
        self._parse_junctions()
        self._parse_reservoirs()
        self._parse_tanks()
        self._parse_pipes()
        self._parse_demands()
        
        # Build network
        network = self._build_network()
        
        return network
    
    def _read_sections(self, file_path: str):
        """Read file and organize into sections"""
        current_section = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove comments and strip whitespace
                line = re.split(';', line)[0].strip()
                
                if not line:
                    continue
                
                # Check for section header
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].upper()
                    self.sections[current_section] = []
                elif current_section:
                    self.sections[current_section].append(line)
    
    def _parse_junctions(self):
        """Parse [JUNCTIONS] section"""
        if 'JUNCTIONS' not in self.sections:
            return
        
        for line in self.sections['JUNCTIONS']:
            parts = line.split()
            if len(parts) >= 2:
                junction_id = parts[0]
                elevation = float(parts[1]) if len(parts) > 1 else 0.0
                demand = float(parts[2]) if len(parts) > 2 else 0.0
                
                self.junctions[junction_id] = {
                    'elevation': elevation,
                    'demand': demand
                }
    
    def _parse_reservoirs(self):
        """Parse [RESERVOIRS] section"""
        if 'RESERVOIRS' not in self.sections:
            return
        
        for line in self.sections['RESERVOIRS']:
            parts = line.split()
            if len(parts) >= 2:
                reservoir_id = parts[0]
                head = float(parts[1])  # Total head (m)
                
                self.reservoirs[reservoir_id] = {
                    'head': head,
                    'pressure': head * 9810  # Convert head to pressure (Pa), assuming water
                }
    
    def _parse_tanks(self):
        """Parse [TANKS] section"""
        if 'TANKS' not in self.sections:
            return
        
        for line in self.sections['TANKS']:
            parts = line.split()
            if len(parts) >= 2:
                tank_id = parts[0]
                elevation = float(parts[1])
                init_level = float(parts[2]) if len(parts) > 2 else 0.0
                
                self.tanks[tank_id] = {
                    'elevation': elevation,
                    'init_level': init_level,
                    'pressure': (elevation + init_level) * 9810
                }
    
    def _parse_pipes(self):
        """Parse [PIPES] section"""
        if 'PIPES' not in self.sections:
            return
        
        for line in self.sections['PIPES']:
            parts = line.split()
            if len(parts) >= 6:
                pipe_id = parts[0]
                node1 = parts[1]
                node2 = parts[2]
                length = float(parts[3])
                diameter = float(parts[4]) / 1000.0  # Convert mm to m
                roughness = float(parts[5])
                
                # EPANET uses different roughness units based on formula
                # For Darcy-Weisbach (default), roughness is in mm
                # Convert to dimensionless (assuming pipe diameter in m)
                roughness_m = roughness / 1000.0  # mm to m
                relative_roughness = roughness_m / diameter if diameter > 0 else 0.005
                
                self.pipes_data[pipe_id] = {
                    'start_node': node1,
                    'end_node': node2,
                    'length': length,
                    'diameter': diameter,
                    'roughness': relative_roughness
                }
    
    def _parse_demands(self):
        """Parse [DEMANDS] section (if separate from junctions)"""
        if 'DEMANDS' not in self.sections:
            return
        
        for line in self.sections['DEMANDS']:
            parts = line.split()
            if len(parts) >= 2:
                junction_id = parts[0]
                demand = float(parts[1])
                self.demands[junction_id] = demand
    
    def _build_network(self) -> PipeNetwork:
        """Build PipeNetwork from parsed data"""
        network = PipeNetwork()
        
        # Add junction nodes
        for junction_id, data in self.junctions.items():
            demand = self.demands.get(junction_id, data.get('demand', 0.0))
            
            # Negative demand = source, positive = sink
            is_sink = demand > 0
            is_source = demand < 0
            
            node = Node(
                id=junction_id,
                elevation=data['elevation'],
                flow_rate=abs(demand) if (is_sink or is_source) else None,
                is_source=is_source,
                is_sink=is_sink
            )
            network.add_node(node)
        
        # Add reservoir nodes (sources with fixed pressure)
        for reservoir_id, data in self.reservoirs.items():
            node = Node(
                id=reservoir_id,
                pressure=data['pressure'],
                is_source=True
            )
            network.add_node(node)
        
        # Add tank nodes (can be sources or sinks)
        for tank_id, data in self.tanks.items():
            node = Node(
                id=tank_id,
                pressure=data['pressure'],
                elevation=data['elevation'],
                is_source=True  # Treat tanks as sources initially
            )
            network.add_node(node)
        
        # Add pipes
        for pipe_id, data in self.pipes_data.items():
            pipe = Pipe(
                id=pipe_id,
                start_node=data['start_node'],
                end_node=data['end_node'],
                length=data['length'],
                diameter=data['diameter'],
                roughness=data['roughness'],
                flow_rate=0.01  # Default initial flow rate
            )
            network.add_pipe(pipe)
        
        return network
    
    @staticmethod
    def get_default_fluid() -> Fluid:
        """Return default fluid for EPANET import (water at 20°C)"""
        return Fluid(
            density=998.0,  # kg/m³
            viscosity=1.002e-3  # Pa·s at 20°C
        )


class EPANETExporter:
    """Export PipeNetwork to EPANET INP format"""
    
    @staticmethod
    def export_to_inp(network: PipeNetwork, output_path: str, title: str = "Pipe Network"):
        """Export network to EPANET INP file format
        
        Args:
            network: PipeNetwork to export
            output_path: Path to save the .inp file
            title: Title for the EPANET file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"[TITLE]\n{title}\n\n")
            
            # Junctions
            f.write("[JUNCTIONS]\n")
            f.write(";ID\tElev\tDemand\n")
            for node in network.nodes.values():
                if not node.is_source and not node.is_sink:
                    elevation = getattr(node, 'elevation', 0.0)
                    f.write(f"{node.id}\t{elevation:.2f}\t0.0\n")
            f.write("\n")
            
            # Reservoirs
            f.write("[RESERVOIRS]\n")
            f.write(";ID\tHead\n")
            for node in network.nodes.values():
                if node.is_source and node.pressure is not None:
                    head = node.pressure / 9810.0  # Convert Pa to m of water
                    f.write(f"{node.id}\t{head:.2f}\n")
            f.write("\n")
            
            # Pipes
            f.write("[PIPES]\n")
            f.write(";ID\tNode1\tNode2\tLength\tDiameter\tRoughness\n")
            for pipe in network.pipes.values():
                diameter_mm = pipe.diameter * 1000  # m to mm
                roughness_mm = pipe.roughness * pipe.diameter * 1000  # relative to mm
                f.write(
                    f"{pipe.id}\t{pipe.start_node}\t{pipe.end_node}\t"
                    f"{pipe.length:.2f}\t{diameter_mm:.2f}\t{roughness_mm:.4f}\n"
                )
            f.write("\n")
            
            # Demands (sinks)
            f.write("[DEMANDS]\n")
            f.write(";Junction\tDemand\n")
            for node in network.nodes.values():
                if node.is_sink and node.flow_rate is not None:
                    f.write(f"{node.id}\t{node.flow_rate:.6f}\n")
            f.write("\n")
            
            # End
            f.write("[END]\n")
