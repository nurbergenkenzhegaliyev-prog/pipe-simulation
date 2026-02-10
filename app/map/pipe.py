import math
from dataclasses import dataclass
from app.models.equipment import PumpCurve, Valve


@dataclass
class Pipe:
    id: str
    start_node: str
    end_node: str
    length: float                       # m
    diameter: float                     # m
    roughness: float                    # none
    flow_rate: float | None = None      # m3/s (total for single-phase)
    liquid_flow_rate: float | None = None  # m3/s (for multi-phase)
    gas_flow_rate: float | None = None     # m3/s (for multi-phase)
    pressure_drop: float | None = None  # Pa
    pump_curve: PumpCurve | None = None
    valve: Valve | None = None
    minor_loss_k: float = 0.0           # dimensionless (fittings, bends)

    def area(self) -> float:
        return math.pi * (self.diameter / 2) ** 2
    
    def velocity(self) -> float:
        """Calculate flow velocity from flow rate and pipe diameter.
        
        Returns:
            Flow velocity in m/s. Returns 0 if flow_rate is None or diameter is 0.
        """
        if self.flow_rate is None or self.flow_rate == 0:
            return 0.0
        
        area = self.area()
        if area == 0:
            return 0.0
        
        return abs(self.flow_rate) / area
    
    def reynolds_number(self, density: float, viscosity: float) -> float:
        """Calculate Reynolds number for the flow in this pipe.
        
        Args:
            density: Fluid density in kg/m³
            viscosity: Dynamic viscosity in Pa·s
            
        Returns:
            Reynolds number (dimensionless)
        """
        if viscosity == 0:
            return 0.0
        
        velocity = self.velocity()
        return (density * velocity * self.diameter) / viscosity
