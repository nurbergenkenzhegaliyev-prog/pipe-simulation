from dataclasses import dataclass


@dataclass
class Fluid:
    # Single-phase properties
    density: float = 998.0         # kg/m3
    viscosity: float = 1e-3         # Pa·s (water)

    # Multi-phase flag and properties
    is_multiphase: bool = False
    liquid_density: float = 998.0   # kg/m3 (for multi-phase)
    gas_density: float = 1.2        # kg/m3 (air at STP)
    liquid_viscosity: float = 1e-3  # Pa·s
    gas_viscosity: float = 1.8e-5   # Pa·s (air)
    surface_tension: float = 0.072  # N/m (water-air)
