from dataclasses import dataclass


@dataclass
class Fluid:
    density: float = 998.0         # kg/m3
    viscosity: float = 1e-3         # Pa·s (water)
