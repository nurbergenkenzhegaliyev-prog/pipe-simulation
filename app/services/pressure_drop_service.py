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

    def reynolds_number(self, velocity, diameter, rho=None, mu=None):
        """
        Re = rho * v * D / mu
        """
        if rho is None:
            rho = self.fluid.density
        if mu is None:
            mu = self.fluid.viscosity
        return rho * velocity * diameter / mu

    def friction_factor(self, velocity, diameter, roughness, rho=None, mu=None):
        """
        PIPESIM-style friction factor
        """
        Re = self.reynolds_number(velocity, diameter, rho, mu)
        logger.debug(f'Re: {Re}')

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
        if self.fluid.is_multiphase:
            return self.calculate_multiphase_dp(pipe)
        
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
        logger.debug(f'friction: {f}')

        dp = f * (pipe.length / pipe.diameter) * (rho * v**2 / 2)

        # Valve loss (if configured)
        if pipe.valve is not None:
            dp += pipe.valve.pressure_drop(rho, v)

        # Pump gain (subtract from losses)
        if pipe.pump_curve is not None:
            dp -= pipe.pump_curve.pressure_gain(Q)

        pipe.pressure_drop = dp
        return dp

    def calculate_multiphase_dp(self, pipe: Pipe) -> float:
        """
        Simplified Beggs-Brill correlation for two-phase flow pressure drop.
        Assumes horizontal pipe.
        """
        if pipe.liquid_flow_rate is None or pipe.gas_flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} needs liquid_flow_rate and gas_flow_rate for multi-phase")

        A = pipe.area()
        D = pipe.diameter
        L = pipe.length
        eps = pipe.roughness

        # Superficial velocities
        VsL = pipe.liquid_flow_rate / A  # m/s
        VsG = pipe.gas_flow_rate / A     # m/s
        Vm = VsL + VsG                   # mixture velocity

        # No-slip holdup
        lambda_L = VsL / Vm if Vm > 0 else 0

        # Mixture properties
        rho_L = self.fluid.liquid_density
        rho_G = self.fluid.gas_density
        mu_L = self.fluid.liquid_viscosity
        mu_G = self.fluid.gas_viscosity
        sigma = self.fluid.surface_tension

        # Simplified flow pattern (assume segregated for horizontal)
        # For full Beggs-Brill, calculate L1-L4, but simplified
        HL = lambda_L  # approximate holdup

        # Friction factor using mixture Re
        rho_m = lambda_L * rho_L + (1 - lambda_L) * rho_G
        mu_m = lambda_L * mu_L + (1 - lambda_L) * mu_G
        Re_m = rho_m * Vm * D / mu_m

        f = self.friction_factor(Vm, D, eps, rho_m, mu_m)

        # Pressure drop: elevation + friction
        # For horizontal, elevation term is 0
        dp_friction = f * (L / D) * (rho_m * Vm**2 / 2)

        # Add valve and pump if present (simplified)
        if pipe.valve is not None:
            dp_friction += pipe.valve.pressure_drop(rho_m, Vm)
        if pipe.pump_curve is not None:
            total_Q = pipe.liquid_flow_rate + pipe.gas_flow_rate  # approximate
            dp_friction -= pipe.pump_curve.pressure_gain(total_Q)

        pipe.pressure_drop = dp_friction
        return dp_friction

    def valve_loss(self, k: float, pipe: Pipe) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")
        rho = self.fluid.density
        v = pipe.flow_rate / pipe.area()
        return k * (rho * v**2 / 2)

    def calculate_node_pressure_gain(self, node, inlet_pressure: float) -> float:
        """
        Calculates pressure gain across a node (e.g. pump).
        """
        if getattr(node, "is_pump", False) and getattr(node, "pressure_ratio", None) is not None:
            return inlet_pressure * (node.pressure_ratio - 1.0)
        return 0.0
