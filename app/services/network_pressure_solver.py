"""Network pressure solver for hydraulic simulation.

This module provides the main solver for calculating pressures and flows
in pipe networks using a two-phase approach:
1. Hardy-Cross method for looped networks
2. Pressure propagation for tree-like branches

The solver supports both single-phase and multi-phase flow calculations.
"""

from typing import Optional

from app.map.network import PipeNetwork
from app.services.pressure_drop_service import PressureDropService
from app.services.solver_components import CycleFinder, HardyCrossSolver, PressurePropagation


class NetworkPressureSolver:
    """Main solver for hydraulic network simulation.
    
    Combines cycle detection, Hardy-Cross iteration for loops, and
    pressure propagation for tree structures to solve the complete
    network pressure and flow distribution.
    
    Attributes:
        dp_service: Service for calculating pressure drops in pipes
        cycle_finder: Component for detecting cycles in the network
        hardy_cross: Hardy-Cross solver for looped networks
        propagator: Pressure propagation for tree structures
        
    Example:
        >>> from app.services.pressure_drop_service import PressureDropService
        >>> from app.models.fluid import Fluid
        >>> 
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp_service = PressureDropService(fluid)
        >>> solver = NetworkPressureSolver(dp_service)
        >>> 
        >>> network = PipeNetwork()
        >>> # ... build network ...
        >>> solver.solve(network)
    """
    
    def __init__(
        self,
        dp_service: PressureDropService,
        cycle_finder: Optional[CycleFinder] = None,
        hardy_cross: Optional[HardyCrossSolver] = None,
        propagator: Optional[PressurePropagation] = None,
    ):
        """Initialize the network pressure solver.
        
        Args:
            dp_service: Service for calculating pressure drops in pipes
            cycle_finder: Optional custom cycle finder (default: CycleFinder())
            hardy_cross: Optional custom Hardy-Cross solver (default: HardyCrossSolver(dp_service))
            propagator: Optional custom pressure propagator (default: PressurePropagation(dp_service))
        """
        self.dp_service = dp_service
        self.cycle_finder = cycle_finder or CycleFinder()
        self.hardy_cross = hardy_cross or HardyCrossSolver(dp_service)
        self.propagator = propagator or PressurePropagation(dp_service)

    def solve(self, network: PipeNetwork):
        """Solve the network for pressures and flows.
        
        Uses a two-phase approach:
        1. Find all cycles in the network
        2. If cycles exist, apply Hardy-Cross method to balance flows
        3. Propagate pressures through the entire network
        
        After solving, all nodes will have calculated pressures and all
        pipes will have calculated flow rates.
        
        Args:
            network: The pipe network to solve
            
        Raises:
            ValueError: If network has no source nodes with fixed pressures
            RuntimeError: If Hardy-Cross method fails to converge
            
        Note:
            The network must have at least one source node with a known
            pressure to provide a reference point for the solution.
        """
        cycles = self.cycle_finder.find_cycles(network)
        if cycles:
            self.hardy_cross.apply(network, cycles)

        self.propagator.propagate(network)
