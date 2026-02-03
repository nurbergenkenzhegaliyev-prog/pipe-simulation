from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from app.map.pipe import Pipe
from app.models.fluid import Fluid

logger = logging.getLogger(__name__)


@dataclass
class FlowProperties:
    def reynolds_number(self, velocity: float, diameter: float, rho: float, mu: float) -> float:
        return rho * velocity * diameter / mu

    def friction_factor(self, velocity: float, diameter: float, roughness: float, rho: float, mu: float) -> float:
        re = self.reynolds_number(velocity, diameter, rho, mu)
        logger.debug(f"Re: {re}")

        if re < 2300:
            return 64.0 / re

        eps = roughness
        d = diameter

        return 0.25 / (
            math.log10(
                (eps / (3.7 * d)) + (5.74 / (re ** 0.9))
            ) ** 2
        )


@dataclass
class SinglePhasePressureDrop:
    flow: FlowProperties

    def calculate(self, pipe: Pipe, fluid: Fluid) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")

        rho = fluid.density
        q = pipe.flow_rate
        area = pipe.area()

        v = q / area
        logger.info(f"v: {v}")

        f = self.flow.friction_factor(
            velocity=v,
            diameter=pipe.diameter,
            roughness=pipe.roughness,
            rho=rho,
            mu=fluid.viscosity,
        )
        logger.debug(f"friction: {f}")

        dp = f * (pipe.length / pipe.diameter) * (rho * v**2 / 2)

        if pipe.valve is not None:
            dp += pipe.valve.pressure_drop(rho, v)

        if pipe.pump_curve is not None:
            dp -= pipe.pump_curve.pressure_gain(q)

        pipe.pressure_drop = dp
        return dp


@dataclass
class MultiPhasePressureDrop:
    flow: FlowProperties

    def calculate(self, pipe: Pipe, fluid: Fluid) -> float:
        if pipe.liquid_flow_rate is None or pipe.gas_flow_rate is None:
            raise ValueError(
                f"Pipe {pipe.id} needs liquid_flow_rate and gas_flow_rate for multi-phase"
            )

        area = pipe.area()
        d = pipe.diameter
        l = pipe.length
        eps = pipe.roughness

        vs_l = pipe.liquid_flow_rate / area
        vs_g = pipe.gas_flow_rate / area
        vm = vs_l + vs_g

        lambda_l = vs_l / vm if vm > 0 else 0

        rho_l = fluid.liquid_density
        rho_g = fluid.gas_density
        mu_l = fluid.liquid_viscosity
        mu_g = fluid.gas_viscosity

        rho_m = lambda_l * rho_l + (1 - lambda_l) * rho_g
        mu_m = lambda_l * mu_l + (1 - lambda_l) * mu_g

        f = self.flow.friction_factor(vm, d, eps, rho_m, mu_m)

        dp_friction = f * (l / d) * (rho_m * vm**2 / 2)

        if pipe.valve is not None:
            dp_friction += pipe.valve.pressure_drop(rho_m, vm)
        if pipe.pump_curve is not None:
            total_q = pipe.liquid_flow_rate + pipe.gas_flow_rate
            dp_friction -= pipe.pump_curve.pressure_gain(total_q)

        pipe.pressure_drop = dp_friction
        return dp_friction


class NodePressureGain:
    @staticmethod
    def calculate(node, inlet_pressure: float) -> float:
        if getattr(node, "is_pump", False) and getattr(node, "pressure_ratio", None) is not None:
            return inlet_pressure * (node.pressure_ratio - 1.0)
        return 0.0
