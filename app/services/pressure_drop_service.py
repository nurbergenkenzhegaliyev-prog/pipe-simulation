"""Pressure drop calculation service for pipe networks.

This module provides the main service for calculating pressure drops
in pipes and pressure gains at nodes (pumps). Supports both single-phase
and multi-phase flow calculations using different correlations.

The service delegates calculations to specialized components:
- SinglePhasePressureDrop: Darcy-Weisbach equation
- MultiPhasePressureDrop: Lockhart-Martinelli correlation
- NodePressureGain: Pump pressure calculations
"""

import logging

from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure_drop_components import (
    FlowProperties,
    MultiPhasePressureDrop,
    NodePressureGain,
    SinglePhasePressureDrop,
)


# Configure logging
# Configure logging to always print to console, even with pytest
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
logger = logging.getLogger(__name__)


class PressureDropService:
    """Service for calculating pressure drops in pipes and gains at nodes.
    
    Provides a unified interface for pressure calculations supporting:
    - Single-phase flow (Darcy-Weisbach)
    - Multi-phase flow (Lockhart-Martinelli)
    - Valve losses
    - Pump pressure gains
    
    Attributes:
        fluid: Fluid properties (density, viscosity, phase info)
        flow: Flow properties calculator (Reynolds, friction factor)
        single_phase: Single-phase pressure drop calculator
        multi_phase: Multi-phase pressure drop calculator
        node_gain: Node pressure gain calculator (pumps)
        
    Example:
        >>> from app.models.fluid import Fluid
        >>> from app.map.pipe import Pipe
        >>> 
        >>> # Single-phase flow
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> service = PressureDropService(fluid)
        >>> pipe = Pipe(id="P1", diameter=0.1, length=100, roughness=0.045)
        >>> pipe.flow_rate = 0.01  # 10 L/s
        >>> dp = service.calculate_pipe_dp(pipe)
        >>> print(f"Pressure drop: {dp:.2f} Pa")
        
        >>> # Multi-phase flow
        >>> mf_fluid = Fluid(is_multiphase=True, liquid_density=998.0, 
        ...                  gas_density=1.2, liquid_viscosity=1e-3,
        ...                  gas_viscosity=1.8e-5, surface_tension=0.072)
        >>> mf_service = PressureDropService(mf_fluid)
        >>> dp_multiphase = mf_service.calculate_pipe_dp(pipe)
    """
    
    def __init__(
        self,
        fluid: Fluid,
        flow: FlowProperties | None = None,
        single_phase: SinglePhasePressureDrop | None = None,
        multi_phase: MultiPhasePressureDrop | None = None,
        node_gain: NodePressureGain | None = None,
    ):
        """Initialize the pressure drop service.
        
        Args:
            fluid: Fluid properties for the simulation
            flow: Optional flow properties calculator (default: FlowProperties())
            single_phase: Optional single-phase calculator (default: SinglePhasePressureDrop())
            multi_phase: Optional multi-phase calculator (default: MultiPhasePressureDrop())
            node_gain: Optional node gain calculator (default: NodePressureGain())
        """
        self.fluid = fluid
        self.flow = flow or FlowProperties()
        self.single_phase = single_phase or SinglePhasePressureDrop(self.flow)
        self.multi_phase = multi_phase or MultiPhasePressureDrop(self.flow)
        self.node_gain = node_gain or NodePressureGain()

    def calculate_pipe_dp(self, pipe: Pipe) -> float:
        """Calculate pressure drop in a pipe.
        
        Automatically selects single-phase or multi-phase calculation
        based on fluid properties.
        
        Args:
            pipe: Pipe object with geometry and flow rate
            
        Returns:
            Pressure drop in Pa (always positive)
            
        Raises:
            ValueError: If pipe has no flow rate set
            
        Note:
            For multi-phase flow, uses Lockhart-Martinelli correlation.
            For single-phase flow, uses Darcy-Weisbach equation with
            Colebrook-White friction factor.
        """
        if self.fluid.is_multiphase:
            return self.multi_phase.calculate(pipe, self.fluid)
        return self.single_phase.calculate(pipe, self.fluid)

    def calculate_multiphase_dp(self, pipe: Pipe) -> float:
        """Calculate multi-phase pressure drop explicitly.
        
        Forces multi-phase calculation regardless of fluid.is_multiphase flag.
        Useful for testing or comparing calculation methods.
        
        Args:
            pipe: Pipe object with geometry and flow rate
            
        Returns:
            Multi-phase pressure drop in Pa
            
        Note:
            Uses Lockhart-Martinelli correlation for gas-liquid flow.
        """
        return self.multi_phase.calculate(pipe, self.fluid)

    def valve_loss(self, k: float, pipe: Pipe) -> float:
        """Calculate pressure loss through a valve.
        
        Uses the loss coefficient method: ΔP = K × (ρv²/2)
        
        Args:
            k: Valve loss coefficient (dimensionless)
            pipe: Pipe containing the valve (for flow rate and area)
            
        Returns:
            Pressure loss in Pa
            
        Raises:
            ValueError: If pipe has no flow rate
            
        Example:
            >>> # Globe valve with K=10
            >>> pipe.flow_rate = 0.01
            >>> loss = service.valve_loss(k=10.0, pipe=pipe)
        """
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")
        rho = self.fluid.density
        v = pipe.flow_rate / pipe.area()
        return k * (rho * v**2 / 2)

    def calculate_node_pressure_gain(self, node, inlet_pressure: float) -> float:
        """Calculate pressure gain at a node (pump).
        
        Args:
            node: Node object (must have pump attribute if pressure gain is expected)
            inlet_pressure: Upstream pressure in Pa
            
        Returns:
            Pressure gain in Pa (positive for pumps, zero for regular nodes)
            
        Example:
            >>> from app.models.equipment import Pump
            >>> from app.map.node import Node
            >>> 
            >>> pump = Pump(a=-1e5, b=2e6, c=1e7)  # Quadratic curve
            >>> node = Node(id="N1", pump=pump)
            >>> gain = service.calculate_node_pressure_gain(node, 1e5)
        """
        return self.node_gain.calculate(node, inlet_pressure)
