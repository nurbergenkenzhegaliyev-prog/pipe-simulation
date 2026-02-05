from dataclasses import dataclass
import math


@dataclass
class Fluid:
    # Single-phase properties
    density: float = 998.0         # kg/m3
    viscosity: float = 1e-3         # Pa·s (water)

    # Temperature effects (single-phase)
    temperature_c: float | None = None
    reference_temperature_c: float = 20.0
    reference_density: float = 998.0
    reference_viscosity: float = 1e-3
    thermal_expansion_coeff: float = 0.0003  # 1/°C
    viscosity_temp_coeff: float = 0.02       # 1/°C (simple exponential)

    # Multi-phase flag and properties
    is_multiphase: bool = False
    liquid_density: float = 998.0   # kg/m3 (for multi-phase)
    gas_density: float = 1.2        # kg/m3 (air at STP)
    liquid_viscosity: float = 1e-3  # Pa·s
    gas_viscosity: float = 1.8e-5   # Pa·s (air)
    surface_tension: float = 0.072  # N/m (water-air)

    def effective_density(self) -> float:
        """Return temperature-adjusted density for single-phase flow."""
        if self.temperature_c is None:
            return self.density

        delta_t = self.temperature_c - self.reference_temperature_c
        rho = self.reference_density * (1.0 - self.thermal_expansion_coeff * delta_t)
        return max(rho, 0.1)

    def effective_viscosity(self) -> float:
        """Return temperature-adjusted viscosity for single-phase flow."""
        if self.temperature_c is None:
            return self.viscosity

        delta_t = self.temperature_c - self.reference_temperature_c
        mu = self.reference_viscosity * math.exp(-self.viscosity_temp_coeff * delta_t)
        return max(mu, 1e-9)
