import logging
import math
from app.map.pipe import Pipe
from app.models.fluid import Fluid


# Configure logging
# Configure logging to always print to console, even with pytest
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
logger = logging.getLogger(__name__)


class PressureDropService:
    def __init__(self, fluid: Fluid):
        self.fluid = fluid

    def reynolds_number(self, velocity, diameter):
        """
        Re = rho * v * D / mu
        """
        rho = self.fluid.density       # kg/m3
        mu = self.fluid.viscosity      # Pa*s
        return rho * velocity * diameter / mu

    def friction_factor(self, velocity, diameter, roughness):
        """
        PIPESIM-style friction factor
        """
        Re = self.reynolds_number(velocity, diameter)
        print(f'Re: {Re}')

        # Laminar flow
        if Re < 2300:
            return 64.0 / Re

        # Turbulent flow (Swamee-Jain)
        eps = roughness
        D = diameter

        return 0.25 / (
            math.log10(
                (eps / (3.7 * D)) + (5.74 / (Re ** 0.9))
            ) ** 2
        )

    def calculate_pipe_dp(self, pipe: Pipe) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")

        rho = self.fluid.density
        Q = pipe.flow_rate
        A = pipe.area()

        v = Q / A
        logger.info(f"v: {v}")

        f = self.friction_factor(
            velocity=v,
            diameter=pipe.diameter,
            roughness=pipe.roughness
        )
        print(f'friction: {f}')

        dp = f * (pipe.length / pipe.diameter) * (rho * v**2 / 2)

        # Valve loss (if configured)
        if pipe.valve is not None:
            dp += pipe.valve.pressure_drop(rho, v)

        # Pump gain (subtract from losses)
        if pipe.pump_curve is not None:
            dp -= pipe.pump_curve.pressure_gain(Q)

        pipe.pressure_drop = dp
        return dp

    def valve_loss(self, k: float, pipe: Pipe) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")
        rho = self.fluid.density
        v = pipe.flow_rate / pipe.area()
        return k * (rho * v**2 / 2)
