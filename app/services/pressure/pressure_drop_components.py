from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional

from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure.friction_correlations import FrictionFactorCalculator, FrictionCorrelation

logger = logging.getLogger(__name__)


@dataclass
class FlowProperties:
    """Flow properties calculator with configurable friction correlation.
    
    Attributes:
        friction_calculator: Calculator for friction factor (optional)
    """
    friction_calculator: Optional[FrictionFactorCalculator] = None
    
    def __post_init__(self):
        """Initialize with default friction calculator if none provided."""
        if self.friction_calculator is None:
            # Default to Colebrook-White for backward compatibility
            self.friction_calculator = FrictionFactorCalculator(
                FrictionCorrelation.COLEBROOK_WHITE
            )
    
    def reynolds_number(self, velocity: float, diameter: float, rho: float, mu: float) -> float:
        return rho * velocity * diameter / mu

    def friction_factor(self, velocity: float, diameter: float, roughness: float, rho: float, mu: float) -> float:
        """Calculate friction factor using configured correlation method.
        
        Args:
            velocity: Flow velocity (m/s)
            diameter: Pipe diameter (m)
            roughness: Pipe roughness (m)
            rho: Fluid density (kg/m³)
            mu: Fluid dynamic viscosity (Pa·s)
            
        Returns:
            Darcy-Weisbach friction factor
        """
        re = self.reynolds_number(velocity, diameter, rho, mu)
        logger.debug(f"Re: {re}")

        # Calculate relative roughness
        relative_roughness = roughness / diameter
        
        # Use friction calculator
        return self.friction_calculator.calculate(re, relative_roughness)


@dataclass
class SinglePhasePressureDrop:
    flow: FlowProperties

    def calculate(self, pipe: Pipe, fluid: Fluid) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")

        rho = fluid.effective_density()
        q = pipe.flow_rate
        area = pipe.area()

        if area <= 0:
            pipe.pressure_drop = 0.0
            return 0.0

        v = q / area
        logger.info(f"v: {v}")

        if abs(v) < 1e-9:
            pipe.pressure_drop = 0.0
            return 0.0

        f = self.flow.friction_factor(
            velocity=v,
            diameter=pipe.diameter,
            roughness=pipe.roughness,
            rho=rho,
            mu=fluid.effective_viscosity(),
        )
        logger.debug(f"friction: {f}")

        dp = f * (pipe.length / pipe.diameter) * (rho * v**2 / 2)

        minor_k = getattr(pipe, "minor_loss_k", 0.0)
        if minor_k:
            dp += minor_k * (rho * v**2 / 2)

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

        minor_k = getattr(pipe, "minor_loss_k", 0.0)
        if minor_k:
            dp_friction += minor_k * (rho_m * vm**2 / 2)

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
