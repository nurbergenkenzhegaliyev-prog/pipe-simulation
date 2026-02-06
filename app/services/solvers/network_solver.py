"""Main network solver with multiple solution methods.

Provides a unified interface for solving pipe networks with different
numerical methods (Hardy-Cross, Newton-Raphson, etc.).
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional, TYPE_CHECKING

from app.services.solvers.cycle_finder import CycleFinder
from app.services.solvers.hardy_cross_solver import HardyCrossSolver
from app.services.solvers.newton_raphson_solver import NewtonRaphsonSolver
from app.services.solvers.pressure_propagation import PressurePropagation

if TYPE_CHECKING:
    from app.map.network import PipeNetwork
    from app.services.pressure_drop_service import PressureDropService

logger = logging.getLogger(__name__)


class SolverMethod(Enum):
    """Available solver methods for network simulation."""
    HARDY_CROSS = "hardy_cross"
    NEWTON_RAPHSON = "newton_raphson"


class NetworkSolver:
    """Main solver for hydraulic network simulation with method selection.
    
    Supports multiple solution algorithms:
    - Hardy-Cross: Traditional iterative method for looped networks
    - Newton-Raphson: More accurate and faster for complex networks (default)
    
    Attributes:
        dp_service: Service for calculating pressure drops in pipes
        method: Selected solution method (default: Newton-Raphson)
        cycle_finder: Component for detecting cycles
        hardy_cross: Hardy-Cross solver instance
        newton_raphson: Newton-Raphson solver instance
        propagator: Pressure propagation component
        
    Example:
        >>> from app.services.pressure.pressure_drop_service import PressureDropService
        >>> from app.models.fluid import Fluid
        >>> 
        >>> fluid = Fluid(density=998.0, viscosity=1e-3)
        >>> dp_service = PressureDropService(fluid)
        >>> solver = NetworkSolver(dp_service, method=SolverMethod.NEWTON_RAPHSON)
        >>> 
        >>> network = PipeNetwork()
        >>> # ... build network ...
        >>> solver.solve(network)
    """
    
    def __init__(
        self,
        dp_service: 'PressureDropService',
        method: SolverMethod = SolverMethod.NEWTON_RAPHSON,
        cycle_finder: Optional[CycleFinder] = None,
        hardy_cross: Optional[HardyCrossSolver] = None,
        newton_raphson: Optional[NewtonRaphsonSolver] = None,
        propagator: Optional[PressurePropagation] = None,
    ):
        """Initialize the network solver.
        
        Args:
            dp_service: Service for calculating pressure drops in pipes
            method: Solution method to use (default: Newton-Raphson)
            cycle_finder: Optional custom cycle finder
            hardy_cross: Optional custom Hardy-Cross solver
            newton_raphson: Optional custom Newton-Raphson solver
            propagator: Optional custom pressure propagator
        """
        self.dp_service = dp_service
        self.method = method
        self.cycle_finder = cycle_finder or CycleFinder()
        self.hardy_cross = hardy_cross or HardyCrossSolver(dp_service)
        self.newton_raphson = newton_raphson or NewtonRaphsonSolver(dp_service)
        self.propagator = propagator or PressurePropagation(dp_service)

    def solve(self, network: 'PipeNetwork') -> None:
        """Solve the network for pressures and flows.
        
        Workflow:
        1. Find all cycles in the network
        2. If cycles exist, apply selected solver method
        3. Propagate pressures through the entire network
        
        After solving, all nodes will have calculated pressures and all
        pipes will have calculated flow rates.
        
        Args:
            network: The pipe network to solve
            
        Raises:
            ValueError: If network has no source nodes with fixed pressures
            RuntimeError: If solver fails to converge
        """
        logger.info(f"Solving network using {self.method.value} method")
        
        # Find cycles in the network
        cycles = self.cycle_finder.find_cycles(network)
        logger.info(f"Found {len(cycles)} cycles in network")
        
        # Apply solver for looped networks
        if cycles:
            if self.method == SolverMethod.HARDY_CROSS:
                logger.info("Using Hardy-Cross method for looped network")
                self.hardy_cross.apply(network, cycles)
            elif self.method == SolverMethod.NEWTON_RAPHSON:
                logger.info("Using Newton-Raphson method for looped network")
                self.newton_raphson.solve(network, cycles)
            else:
                raise ValueError(f"Unknown solver method: {self.method}")
        
        # Propagate pressures through network
        logger.info("Propagating pressures through network")
        self.propagator.propagate(network)
        logger.info("Network solution complete")
    
    def set_method(self, method: SolverMethod) -> None:
        """Change the solver method.
        
        Args:
            method: New solver method to use
        """
        self.method = method
        logger.info(f"Solver method changed to: {method.value}")


# Legacy compatibility - NetworkPressureSolver alias
class NetworkPressureSolver(NetworkSolver):
    """Legacy alias for NetworkSolver.
    
    Maintained for backward compatibility with existing code.
    """
    pass
