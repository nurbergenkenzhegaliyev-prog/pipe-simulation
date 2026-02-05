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
