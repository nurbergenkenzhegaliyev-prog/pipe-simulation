from dataclasses import dataclass


@dataclass
class PumpCurve:
    # Simple quadratic pump curve: dp = a + b*Q + c*Q^2 (Pa)
    a: float
    b: float
    c: float

    def pressure_gain(self, flow_rate: float) -> float:
        return self.a + self.b * flow_rate + self.c * (flow_rate ** 2)


@dataclass
class Valve:
    # Simple valve loss coefficient K (dimensionless)
    k: float

    def pressure_drop(self, rho: float, velocity: float) -> float:
        # dp = K * (rho * v^2 / 2)
        return self.k * (rho * velocity ** 2 / 2)
