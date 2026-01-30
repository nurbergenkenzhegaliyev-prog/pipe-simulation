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
    flow_rate: float | None = None      # m3/s
    pressure_drop: float | None = None  # Pa
    pump_curve: PumpCurve | None = None
    valve: Valve | None = None

    def area(self) -> float:
        return math.pi * (self.diameter / 2) ** 2
